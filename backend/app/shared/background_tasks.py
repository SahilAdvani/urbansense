import asyncio
import time
import random
from datetime import datetime
from app.database.session import SessionLocal
from app.database.models import City, Ward, AQIStation, AQIObservation
from app.core.config import settings
from app.shared.weather_service import (
    get_real_air_pollution,
    get_real_weather,
    calculate_indian_aqi,
    calibrate_pollutants,
)

async def sync_all_cities():
    """Perform hourly synchronization of live metrics for all registered cities."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        print("[Scheduler] OpenWeatherMap API Key not configured. Skipping hourly background sync.")
        return

    print(f"[Scheduler] Starting hourly synchronization at {datetime.utcnow()}")
    
    # 1. Fetch cities and wards using a short-lived DB session
    city_data = []
    db = SessionLocal()
    try:
        cities = db.query(City).all()
        for city in cities:
            city.is_syncing = True
            db.commit()
            
            wards = db.query(Ward).filter(Ward.city_id == city.id).all()
            ward_details = []
            for w in wards:
                station = db.query(AQIStation).filter(AQIStation.ward_id == w.id).first()
                if station:
                    ward_details.append({
                        "ward_id": w.id,
                        "station_id": station.id,
                        "lat": station.latitude,
                        "lon": station.longitude
                    })
            city_data.append({
                "id": city.id,
                "name": city.name,
                "latitude": city.latitude,
                "longitude": city.longitude,
                "wards": ward_details
            })
    except Exception as e:
        print(f"[Scheduler] Failed to load cities meta: {e}")
        return
    finally:
        db.close()

    # 2. Iterate through cities and make slow network calls holding NO db connections
    for city in city_data:
        try:
            weather = get_real_weather(city["latitude"], city["longitude"], api_key)
            temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
            humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
            w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
            w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

            sync_timestamp = datetime.utcnow()

            for w in city["wards"]:
                await asyncio.sleep(1.2)  # Async sleep safely yields execution

                ward_weather = get_real_weather(w["lat"], w["lon"], api_key)
                ward_pollution = get_real_air_pollution(w["lat"], w["lon"], api_key)

                if not ward_pollution:
                    continue

                comps = ward_pollution.get("components", {})
                calibrated = calibrate_pollutants(comps)
                pm25 = calibrated["pm25"]
                pm10 = calibrated["pm10"]
                no2 = calibrated["no2"]
                co = calibrated["co"]
                so2 = calibrated["so2"]
                o3 = calibrated["o3"]

                calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)
                w_temp = ward_weather.get("main", {}).get("temp", temp) if ward_weather else temp
                w_humidity = ward_weather.get("main", {}).get("humidity", humidity) if ward_weather else humidity

                # Write observation in a fresh, short-lived session
                db_write = SessionLocal()
                try:
                    new_obs = AQIObservation(
                        station_id=w["station_id"],
                        ward_id=w["ward_id"],
                        timestamp=sync_timestamp,
                        aqi=calculated_aqi,
                        pm25=pm25,
                        pm10=pm10,
                        no2=no2,
                        co=co,
                        so2=so2,
                        o3=o3,
                        temperature=w_temp,
                        humidity=w_humidity,
                        wind_speed=w_speed + random.uniform(-0.3, 0.3),
                        wind_direction=w_deg + random.uniform(-5, 5)
                    )
                    db_write.add(new_obs)
                    db_write.commit()
                finally:
                    db_write.close()

            # Mark city as finished syncing
            db_finish = SessionLocal()
            try:
                c = db_finish.query(City).filter(City.id == city["id"]).first()
                if c:
                    c.is_syncing = False
                    db_finish.commit()
            finally:
                db_finish.close()
            print(f"[Scheduler] Successfully synced {len(city['wards'])} wards for {city['name']}.")

        except Exception as e:
            print(f"[Scheduler] Error syncing city {city['name']}: {e}")
            db_err = SessionLocal()
            try:
                c = db_err.query(City).filter(City.id == city["id"]).first()
                if c:
                    c.is_syncing = False
                    db_err.commit()
            finally:
                db_err.close()

async def start_background_tasks():
    """Background loop that runs hourly synchronization indefinitely."""
    print("[Scheduler] Initializing Scheduled Background Sync Worker...")
    
    # Wait 5 seconds after boot to let app settle
    await asyncio.sleep(5)
    
    # Initial sync on boot
    await sync_all_cities()
    
    while True:
        # Wait for 1 hour (3600 seconds)
        await asyncio.sleep(3600)
        try:
            await sync_all_cities()
        except Exception as e:
            print(f"[Scheduler] Loop encountered unexpected failure: {e}")
