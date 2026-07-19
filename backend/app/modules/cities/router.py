from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import urllib.request
import urllib.parse
import json
import random
import time
from datetime import datetime, timedelta

from app.database.session import get_db, SessionLocal
from app.database.models import City, Ward, AQIStation, AQIObservation
from app.core.config import settings
from app.shared.weather_service import (
    get_real_air_pollution,
    get_historical_air_pollution,
    get_real_weather,
    calculate_indian_aqi,
)
from app.shared.osm_service import fetch_city_suburbs, generate_suburb_geojson

router = APIRouter(prefix="/cities", tags=["cities"])

class CityResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    has_wards: bool
    is_syncing: bool

    class Config:
        from_attributes = True

# Asynchronous Background Ingestion Task for new cities
def background_ingest_city(city_id: str, lat: float, lon: float, api_key: str):
    db = SessionLocal()
    try:
        city = db.query(City).filter(City.id == city_id).first()
        if not city:
            return
        
        wards = db.query(Ward).filter(Ward.city_id == city.id).all()
        
        # Fetch city center weather once to share baseline weather parameters
        weather = get_real_weather(lat, lon, api_key)
        temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
        humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
        w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
        w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0
        
        # Query 24h historical pollution individually for each suburb (throttled 1.2s)
        for idx, ward in enumerate(wards):
            time.sleep(1.2)  # Strictly throttle to prevent OWM rate limits
            station = db.query(AQIStation).filter(AQIStation.ward_id == ward.id).first()
            if not station:
                continue

            end_time = int(datetime.utcnow().timestamp())
            start_time = end_time - (24 * 3600)
            history = get_historical_air_pollution(station.latitude, station.longitude, start_time, end_time, api_key)
            
            if history:
                for item in history:
                    timestamp = datetime.utcfromtimestamp(item["dt"])
                    comps = item.get("components", {})
                    pm25 = comps.get("pm2_5", 0.0)
                    pm10 = comps.get("pm10", 0.0)
                    no2 = comps.get("no2", 0.0)
                    co = comps.get("co", 0.0) / 1000.0  # mg/m3
                    so2 = comps.get("so2", 0.0)
                    o3 = comps.get("o3", 0.0)

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
                        temperature=temp + random.uniform(-0.5, 0.5),
                        humidity=humidity + random.uniform(-2, 2),
                        wind_speed=w_speed + random.uniform(-0.3, 0.3),
                        wind_direction=w_deg + random.uniform(-5, 5)
                    )
                    db.add(obs)
                db.commit()

        # Update city status to completed
        city.is_syncing = False
        db.commit()
        print(f"[Ingestion] Successfully backfilled true coordinates for {city.name}")
    except Exception as e:
        print(f"[Ingestion] Error backfilling data for {city_id}: {e}")
        db.rollback()
    finally:
        db.close()

# Asynchronous Background Sync Task for existing cities
def background_sync_city(city_id: str, api_key: str):
    db = SessionLocal()
    try:
        city = db.query(City).filter(City.id == city_id).first()
        if not city:
            return
        
        wards = db.query(Ward).filter(Ward.city_id == city.id).all()
        sync_timestamp = datetime.utcnow()

        # Query live metrics individually for each suburb (throttled 1.2s)
        for idx, ward in enumerate(wards):
            time.sleep(1.2)  # Strictly throttle to prevent OWM rate limits
            station = db.query(AQIStation).filter(AQIStation.ward_id == ward.id).first()
            if not station:
                continue

            weather = get_real_weather(station.latitude, station.longitude, api_key)
            pollution = get_real_air_pollution(station.latitude, station.longitude, api_key)

            if not pollution:
                continue

            comps = pollution.get("components", {})
            pm25 = comps.get("pm2_5", 0.0)
            pm10 = comps.get("pm10", 0.0)
            no2 = comps.get("no2", 0.0)
            co = comps.get("co", 0.0) / 1000.0  # mg/m3
            so2 = comps.get("so2", 0.0)
            o3 = comps.get("o3", 0.0)

            calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)

            temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
            humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
            w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
            w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

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
                temperature=temp,
                humidity=humidity,
                wind_speed=w_speed,
                wind_direction=w_deg
            )
            db.add(new_obs)
            db.commit()

        # Update city status to completed
        city.is_syncing = False
        db.commit()
        print(f"[Sync] Completed background sync for {city.name}")
    except Exception as e:
        print(f"[Sync] Error in background sync: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/", response_model=List[CityResponse])
def get_cities(db: Session = Depends(get_db)):
    """List all registered cities."""
    return db.query(City).all()

@router.post("/register", response_model=CityResponse)
def register_city(
    name: str = Query(..., description="Name of the Indian city to register"), 
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Search and dynamically register any Indian city.
    Resolves coordinates and queries OpenStreetMap Overpass API for 15 real suburbs.
    """
    city_slug = name.strip().lower().replace(" ", "-")
    
    # Check if already exists
    existing = db.query(City).filter(City.id == city_slug).first()
    if existing:
        return existing

    # Try resolving coordinates via OSM Nominatim API
    try:
        query_str = urllib.parse.quote(f"{name}, India")
        url = f"https://nominatim.openstreetmap.org/search?q={query_str}&format=json&limit=1"
        
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "UrbanSense-AQI-Decision-Support-System/1.0"}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if not data:
                raise HTTPException(status_code=404, detail=f"City '{name}' could not be resolved in India.")
            
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            resolved_name = data[0]["display_name"].split(",")[0].strip()
    except Exception as e:
        print(f"Geocoding resolution failed for {name}: {e}")
        # Fallback coordinates near Central India
        lat = 20.0 + random.uniform(-5.0, 5.0)
        lon = 78.0 + random.uniform(-5.0, 5.0)
        resolved_name = name.capitalize()

    # Query OSM Overpass for 15 real suburbs/neighbourhoods in a 20km radius
    osm_suburbs = fetch_city_suburbs(lat, lon, limit=15)
    has_wards = len(osm_suburbs) > 0

    # Create new City and set is_syncing to True (ingestion in progress)
    api_key = settings.OPENWEATHER_API_KEY
    is_syncing = bool(api_key and has_wards)

    new_city = City(
        id=city_slug,
        name=resolved_name,
        latitude=lat,
        longitude=lon,
        has_wards=has_wards,
        is_syncing=is_syncing
    )
    db.add(new_city)
    db.commit()
    
    # If no suburbs resolved, create a fallback city center ward
    if not osm_suburbs:
        osm_suburbs = [{"name": f"City Center - {resolved_name}", "latitude": lat, "longitude": lon}]

    # Register each suburb as a ward and create a station (snappy DB transactions)
    for idx, suburb in enumerate(osm_suburbs):
        sub_name = suburb["name"]
        sub_lat = suburb["latitude"]
        sub_lon = suburb["longitude"]

        ward = Ward(
            city_id=new_city.id,
            name=f"{resolved_name} - {sub_name}" if has_wards else f"{resolved_name} Center",
            geojson_boundary=generate_suburb_geojson(sub_lat, sub_lon, sub_name) if has_wards else None
        )
        db.add(ward)
        db.commit()
        db.refresh(ward)

        station = AQIStation(
            name=f"Monitoring Station - {sub_name}" if has_wards else f"{resolved_name} City Station",
            ward_id=ward.id,
            latitude=sub_lat,
            longitude=sub_lon
        )
        db.add(station)
        db.commit()
        db.refresh(station)

        # Pre-populate simulated fallback immediately so page is not empty on load
        now = datetime.utcnow()
        base_aqi = random.randint(80, 180) + (idx % 3 - 1) * 20
        for h in range(24):
            obs_aqi = max(20, base_aqi + random.randint(-15, 15))
            obs = AQIObservation(
                station_id=station.id,
                ward_id=ward.id,
                timestamp=now - timedelta(hours=h),
                aqi=obs_aqi,
                pm25=obs_aqi * 0.6 + random.uniform(-5, 5),
                pm10=obs_aqi * 1.2 + random.uniform(-10, 10),
                no2=random.uniform(20, 60),
                co=random.uniform(0.2, 1.2),
                so2=random.uniform(5, 15),
                o3=random.uniform(10, 40),
                temperature=24.0 + random.uniform(-2, 2),
                humidity=65.0 + random.uniform(-8, 8),
                wind_speed=random.uniform(3.0, 9.0),
                wind_direction=random.uniform(0, 360)
            )
            db.add(obs)
        db.commit()

    # Queue background task to backfill true coordinates from OWM
    if is_syncing and background_tasks:
        background_tasks.add_task(background_ingest_city, new_city.id, lat, lon, api_key)
            
    db.refresh(new_city)
    return new_city

@router.post("/{city_id}/sync")
def sync_city_data(city_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Triggers an asynchronous background task to fetch true weather & air pollution 
    from OWM for each ward individually and save the results.
    """
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=400, 
            detail="OpenWeatherMap API Key is not configured on the server. Unable to sync live metrics."
        )

    # Set city state to is_syncing = True
    city.is_syncing = True
    db.commit()

    # Trigger background sync thread asynchronously
    background_tasks.add_task(background_sync_city, city.id, api_key)

    return {
        "status": "sync_started",
        "city": city.name,
        "is_syncing": True
    }
