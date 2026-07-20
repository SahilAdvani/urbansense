import sys
import os
import time
from datetime import datetime, timedelta
import random

# Add parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal, Base, engine
from app.database.models import User, City, Ward, AQIStation, AQIObservation, AIRecommendation
from app.shared.security import hash_password
from app.core.config import settings
from app.shared.weather_service import (
    get_historical_air_pollution,
    get_real_weather,
    calculate_indian_aqi,
    calibrate_pollutants,
)
from app.shared.osm_service import fetch_city_suburbs, generate_suburb_geojson

CITIES_TO_SEED = [
    # Level 2 Cities (Ward-level intelligence enabled)
    {"id": "delhi", "name": "Delhi", "lat": 28.6139, "lon": 77.2090, "has_wards": True},
    {"id": "mumbai", "name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "has_wards": True},
    {"id": "bengaluru", "name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "has_wards": True},
    {"id": "hyderabad", "name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "has_wards": True},
    {"id": "chennai", "name": "Chennai", "lat": 13.0827, "lon": 80.2707, "has_wards": True},
    {"id": "ahmedabad", "name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "has_wards": True},
    # Level 1 Cities (City-level intelligence only)
    {"id": "kolkata", "name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "has_wards": False},
    {"id": "pune", "name": "Pune", "lat": 18.5204, "lon": 73.8567, "has_wards": False},
    {"id": "jaipur", "name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "has_wards": False},
    {"id": "lucknow", "name": "Lucknow", "lat": 26.8467, "lon": 80.9462, "has_wards": False},
    {"id": "surat", "name": "Surat", "lat": 21.1702, "lon": 72.8311, "has_wards": False},
    {"id": "patna", "name": "Patna", "lat": 25.5941, "lon": 85.1376, "has_wards": False},
]

def seed():
    db = SessionLocal()
    api_key = settings.OPENWEATHER_API_KEY
    if api_key:
        print("Using OpenWeatherMap API key to fetch actual historical environmental data...")
    else:
        print("No OpenWeatherMap API Key found. Seeding with simulated observations.")

    try:
        print("Recreating database tables...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized cleanly.")

        # 1. Seed Admin User
        admin_email = "admin@urbansense.gov"
        admin = User(
            email=admin_email,
            hashed_password=hash_password("admin123"),
            role="municipal_admin"
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Seeded Admin Credentials: {admin_email} / admin123")

        # 2. Seed Cities
        for city_data in CITIES_TO_SEED:
            city = City(
                id=city_data["id"],
                name=city_data["name"],
                latitude=city_data["lat"],
                longitude=city_data["lon"],
                has_wards=city_data["has_wards"]
            )
            db.add(city)
            db.commit()
            print(f"\n--- Seeding City: {city.name} ({'Level 2' if city.has_wards else 'Level 1'}) ---")

            # Resolve suburbs via OSM Overpass
            suburbs = []
            if city.has_wards:
                print(f"Fetching real suburbs for {city.name} from OpenStreetMap...")
                time.sleep(2.0)  # Throttling delay to avoid Overpass rate limit timeouts
                suburbs = fetch_city_suburbs(city.latitude, city.longitude, limit=6)
                if not suburbs:
                    print(f"No suburbs resolved for {city.name}. Generating fallbacks.")
                    # Fallback suburbs if Overpass call fails
                    suburbs = [
                        {"name": f"{city.name} North", "latitude": city.latitude + 0.02, "longitude": city.longitude},
                        {"name": f"{city.name} South", "latitude": city.latitude - 0.02, "longitude": city.longitude},
                        {"name": f"{city.name} East", "latitude": city.latitude, "longitude": city.longitude + 0.02},
                        {"name": f"{city.name} West", "latitude": city.latitude, "longitude": city.longitude - 0.02},
                    ]
            else:
                # Level 1 has only a single central ward representing the citywide average
                suburbs = [{"name": "City Center", "latitude": city.latitude, "longitude": city.longitude}]

            # Fetch OWM data exactly ONCE per city (city center) to prevent rate limits
            history = None
            temp = 25.0
            humidity = 60.0
            w_speed = 4.0
            w_deg = 180.0

            if api_key:
                time.sleep(1.0)  # Throttling delay between cities
                weather = get_real_weather(city.latitude, city.longitude, api_key)
                if weather:
                    temp = weather.get("main", {}).get("temp", 25.0)
                    humidity = weather.get("main", {}).get("humidity", 60.0)
                    w_speed = weather.get("wind", {}).get("speed", 4.0)
                    w_deg = weather.get("wind", {}).get("deg", 180.0)

                end_time = int(datetime.utcnow().timestamp())
                start_time = end_time - (24 * 3600)
                history = get_historical_air_pollution(city.latitude, city.longitude, start_time, end_time, api_key)

            # Ingest wards and observations
            for idx, sub in enumerate(suburbs):
                sub_name = sub["name"]
                sub_lat = sub["latitude"]
                sub_lon = sub["longitude"]

                ward = Ward(
                    city_id=city.id,
                    name=f"{city.name} - {sub_name}" if city.has_wards else f"{city.name} Center",
                    geojson_boundary=generate_suburb_geojson(sub_lat, sub_lon, sub_name) if city.has_wards else None
                )
                db.add(ward)
                db.commit()
                db.refresh(ward)

                station = AQIStation(
                    name=f"Monitoring Station - {sub_name}" if city.has_wards else f"{city.name} City Station",
                    ward_id=ward.id,
                    latitude=sub_lat,
                    longitude=sub_lon
                )
                db.add(station)
                db.commit()
                db.refresh(station)

                real_seeded = False
                if history:
                    # Distribute central values with suburb offsets
                    offset_multiplier = 1.0 + ((idx % 3 - 1) * 0.12)  # -12%, 0%, +12% variation
                    for item in history:
                        timestamp = datetime.utcfromtimestamp(item["dt"])
                        comps = item.get("components", {})
                        calibrated = calibrate_pollutants(comps)
                        pm25 = calibrated["pm25"] * offset_multiplier
                        pm10 = calibrated["pm10"] * offset_multiplier
                        no2 = calibrated["no2"] * offset_multiplier
                        co = calibrated["co"] * offset_multiplier
                        so2 = calibrated["so2"] * offset_multiplier
                        o3 = calibrated["o3"] * offset_multiplier

                        calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)
                        obs = AQIObservation(
                            station_id=station.id,
                            ward_id=ward.id,
                            timestamp=timestamp,
                            aqi=calculated_aqi,
                            pm25=pm25,
                            pm10=pm10,
                            no2=no2,
                            co=co,
                            so2=so2,
                            o3=o3,
                            temperature=temp + random.uniform(-1, 1),
                            humidity=humidity + random.uniform(-3, 3),
                            wind_speed=w_speed + random.uniform(-0.5, 0.5),
                            wind_direction=w_deg + random.uniform(-10, 10)
                        )
                        db.add(obs)
                    db.commit()
                    real_seeded = True

                if not real_seeded:
                    now = datetime.utcnow()
                    base_aqi = 65 if idx == 2 else (220 if idx == 1 else 135)
                    for h in range(24):
                        obs_aqi = max(20, base_aqi + random.randint(-15, 15))
                        obs = AQIObservation(
                            station_id=station.id,
                            ward_id=ward.id,
                            timestamp=now - timedelta(hours=h),
                            aqi=obs_aqi,
                            pm25=obs_aqi * 0.6 + random.uniform(-4, 4),
                            pm10=obs_aqi * 1.2 + random.uniform(-8, 8),
                            no2=random.uniform(15, 55),
                            co=random.uniform(0.1, 1.1),
                            so2=random.uniform(4, 14),
                            o3=random.uniform(8, 38),
                            temperature=26.0 + random.uniform(-2, 2),
                            humidity=62.0 + random.uniform(-6, 6),
                            wind_speed=random.uniform(2.0, 10.0),
                            wind_direction=random.uniform(0, 360)
                        )
                        db.add(obs)
                    db.commit()

                # Seed dynamic pending AI recommendations for high AQI wards
                obs_vals = db.query(AQIObservation.aqi).filter(AQIObservation.ward_id == ward.id).all()
                avg_aqi = int(sum(o[0] for o in obs_vals) / len(obs_vals)) if obs_vals else 100
                if avg_aqi > 150:
                    rec = AIRecommendation(
                        ward_id=ward.id,
                        trigger_aqi=avg_aqi,
                        primary_pollutant="PM2.5",
                        estimated_source="Traffic Exhaust & Industrial Emissions",
                        confidence_score=0.92,
                        recommendation_text=f"Enforce high-density vehicle restrictions and halt major commercial construction operations in {ward.name}.",
                        action_plan={
                            "steps": [
                                "Deploy mechanical sweepers and vacuum vehicles",
                                "Establish construction inspection checkpoints",
                                "Advise senior citizens to stay indoors"
                            ]
                        },
                        status="pending"
                    )
                    db.add(rec)
                    db.commit()

        print("\nDatabase Seeding Completed Successfully with Real Suburbs!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
