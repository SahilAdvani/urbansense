import asyncio
from datetime import datetime
import random
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
                # Fetch live weather and pollution parameters
                weather = get_real_weather(city.latitude, city.longitude, api_key)
                pollution = get_real_air_pollution(city.latitude, city.longitude, api_key)

                if not pollution:
                    print(f"[Scheduler] Failed to fetch pollution data for {city.name}. Skipping.")
                    continue

                # Find the first ward for the city
                ward = db.query(Ward).filter(Ward.city_id == city.id).first()
                if not ward:
                    print(f"[Scheduler] No ward associated with {city.name}. Skipping.")
                    continue

                # Find or create AQI station
                station = db.query(AQIStation).filter(AQIStation.ward_id == ward.id).first()
                if not station:
                    station = AQIStation(
                        name=f"Synced Station - {city.name}",
                        ward_id=ward.id,
                        latitude=city.latitude,
                        longitude=city.longitude
                    )
                    db.add(station)
                    db.commit()
                    db.refresh(station)

                # Parse pollution components
                comps = pollution.get("components", {})
                pm25 = comps.get("pm2_5", 0.0)
                pm10 = comps.get("pm10", 0.0)
                no2 = comps.get("no2", 0.0)
                co = comps.get("co", 0.0) / 1000.0  # mg/m3
                so2 = comps.get("so2", 0.0)
                o3 = comps.get("o3", 0.0)

                calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)

                # Parse weather parameters
                temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
                humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
                w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
                w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

                new_obs = AQIObservation(
                    station_id=station.id,
                    ward_id=ward.id,
                    timestamp=datetime.utcnow(),
                    aqi=calculated_aqi,
                    pm25=pm25,
                    pm10=pm10,
                    no2=no2,
                    co=co,
                    so2=so2,
                    o3=o3,
                    temperature=temp,
                    humidity=humidity,
                    wind_speed=w_speed,
                    wind_direction=w_deg
                )
                db.add(new_obs)
                db.commit()
                print(f"[Scheduler] Successfully synced live observations for {city.name}. AQI: {calculated_aqi}")
            except Exception as e:
                print(f"[Scheduler] Error syncing city {city.name}: {e}")
                db.rollback()
    finally:
        db.close()

async def start_background_tasks():
    """Background loop that runs hourly synchronization indefinitely."""
    print("[Scheduler] Initializing Scheduled Background Sync Worker...")
    
    # Optional delay before initial sync to avoid startup bottleneck
    await asyncio.sleep(5)
    
    # Run first sync immediately on startup
    await sync_all_cities()
    
    while True:
        # Wait for 1 hour (3600 seconds)
        await asyncio.sleep(3600)
        try:
            await sync_all_cities()
        except Exception as e:
            print(f"[Scheduler] Loop encountered unexpected failure: {e}")
