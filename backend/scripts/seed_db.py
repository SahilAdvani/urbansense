import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal, Base, engine
from app.database.models import User, City, Ward, AQIStation, AQIObservation, Intervention, CitizenAdvisory, AIRecommendation
from app.shared.security import hash_password

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

def make_dynamic_geojson(idx: int, lat: float, lon: float):
    # Generates a valid rectangle centered offset from lat, lon
    offset_x = ((idx - 1) % 2 - 0.5) * 0.05
    offset_y = ((idx - 1) // 2 - 0.5) * 0.05
    c_lat = lat + offset_y
    c_lon = lon + offset_x
    coords = [
        [c_lon - 0.02, c_lat - 0.02],
        [c_lon + 0.02, c_lat - 0.02],
        [c_lon + 0.02, c_lat + 0.02],
        [c_lon - 0.02, c_lat + 0.02],
        [c_lon - 0.02, c_lat - 0.02]
    ]
    return {
        "type": "Feature",
        "properties": {"name": f"Zone {idx}"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }

def seed():
    db = SessionLocal()
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
            print(f"Seeded City: {city.name} ({'Level 2' if city.has_wards else 'Level 1'})")

            # Seed Wards
            if city.has_wards:
                wards = []
                for i in range(1, 5):
                    w_name = f"{city.name} - Ward {i}"
                    ward = Ward(
                        city_id=city.id,
                        name=w_name,
                        geojson_boundary=make_dynamic_geojson(i, city.latitude, city.longitude)
                    )
                    db.add(ward)
                    db.commit()
                    db.refresh(ward)
                    wards.append(ward)
                    
                    # Seed 1 Station per ward
                    station = AQIStation(
                        name=f"Monitoring Station - Ward {i}",
                        ward_id=ward.id,
                        latitude=city.latitude + ((i - 1) // 2 - 0.5) * 0.05 + 0.005,
                        longitude=city.longitude + ((i - 1) % 2 - 0.5) * 0.05 + 0.005
                    )
                    db.add(station)
                    db.commit()
                    db.refresh(station)

                    # Seed 24 hours of observations
                    now = datetime.utcnow()
                    base_aqi = 60 if i == 3 else (210 if i == 2 else 130)  # Make ward 2 a hotspot, ward 3 very clean
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
                    if base_aqi > 150:
                        rec = AIRecommendation(
                            ward_id=ward.id,
                            trigger_aqi=base_aqi,
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
            else:
                # Level 1 Cities: just seed 1 generic Ward + 1 Station to hold citywide measurements
                ward = Ward(
                    city_id=city.id,
                    name=f"{city.name} Center",
                    geojson_boundary=None
                )
                db.add(ward)
                db.commit()
                db.refresh(ward)

                station = AQIStation(
                    name=f"{city.name} City Station",
                    ward_id=ward.id,
                    latitude=city.latitude,
                    longitude=city.longitude
                )
                db.add(station)
                db.commit()
                db.refresh(station)

                now = datetime.utcnow()
                base_aqi = random.randint(90, 160)
                for h in range(24):
                    obs_aqi = max(30, base_aqi + random.randint(-20, 20))
                    obs = AQIObservation(
                        station_id=station.id,
                        ward_id=ward.id,
                        timestamp=now - timedelta(hours=h),
                        aqi=obs_aqi,
                        pm25=obs_aqi * 0.65,
                        pm10=obs_aqi * 1.15,
                        no2=random.uniform(10, 45),
                        co=random.uniform(0.1, 0.9),
                        so2=random.uniform(3, 11),
                        o3=random.uniform(10, 35),
                        temperature=27.0 + random.uniform(-3, 3),
                        humidity=58.0 + random.uniform(-10, 10),
                        wind_speed=random.uniform(4.0, 12.0),
                        wind_direction=random.uniform(0, 360)
                    )
                    db.add(obs)
                db.commit()

        print("Database Seeding Completed Successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
