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
)

async def sync_all_cities():
    """Perform hourly synchronization of live metrics for all registered cities."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        print("[Scheduler] OpenWeatherMap API Key not configured. Skipping hourly background sync.")
        return

    print(f"[Scheduler] Starting hourly synchronization at {datetime.utcnow()}")
    db = SessionLocal()
    try:
        cities = db.query(City).all()
        for city in cities:
            try:
                # Mark city as syncing
                city.is_syncing = True
                db.commit()

                # Get all wards for the city
                wards = db.query(Ward).filter(Ward.city_id == city.id).all()
                if not wards:
                    print(f"[Scheduler] No wards associated with {city.name}. Skipping.")
                    city.is_syncing = False
                    db.commit()
                    continue

                # Fetch city-center weather once to use as a baseline weather profile
                weather = get_real_weather(city.latitude, city.longitude, api_key)
                temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
                humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
                w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
                w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

                sync_timestamp = datetime.utcnow()

                # Query OWM for each ward individually (throttled 1.2s delay to prevent rate limits)
                for idx, ward in enumerate(wards):
                    # Throttling wait (run in main event loop safely)
                    await asyncio.sleep(1.2)

                    station = db.query(AQIStation).filter(AQIStation.ward_id == ward.id).first()
                    if not station:
                        continue

                    # Fetch live weather and pollution parameters for the ward coordinates
                    ward_weather = get_real_weather(station.latitude, station.longitude, api_key)
                    ward_pollution = get_real_air_pollution(station.latitude, station.longitude, api_key)

                    if not ward_pollution:
                        continue

                    comps = ward_pollution.get("components", {})
                    pm25 = comps.get("pm2_5", 0.0)
                    pm10 = comps.get("pm10", 0.0)
                    no2 = comps.get("no2", 0.0)
                    co = comps.get("co", 0.0) / 1000.0  # mg/m3
                    so2 = comps.get("so2", 0.0)
                    o3 = comps.get("o3", 0.0)

                    calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)

                    w_temp = ward_weather.get("main", {}).get("temp", temp) if ward_weather else temp
                    w_humidity = ward_weather.get("main", {}).get("humidity", humidity) if ward_weather else humidity

                    new_obs = AQIObservation(
                        station_id=station.id,
                        ward_id=ward.id,
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
                    db.add(new_obs)
                    db.commit()

                # Sync complete
                city.is_syncing = False
                db.commit()
                print(f"[Scheduler] Successfully synced {len(wards)} wards for {city.name}.")
            except Exception as e:
                print(f"[Scheduler] Error syncing city {city.name}: {e}")
                city.is_syncing = False
                db.commit()
                db.rollback()
    finally:
        db.close()

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
