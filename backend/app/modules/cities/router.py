from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import urllib.request
import urllib.parse
import json
import random
from datetime import datetime, timedelta

from app.database.session import get_db
from app.database.models import City, Ward, AQIStation, AQIObservation
from app.core.config import settings
from app.shared.weather_service import (
    get_real_air_pollution,
    get_historical_air_pollution,
    get_real_weather,
    calculate_indian_aqi,
)

router = APIRouter(prefix="/cities", tags=["cities"])

class CityResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    has_wards: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CityResponse])
def get_cities(db: Session = Depends(get_db)):
    """List all registered cities."""
    return db.query(City).all()

@router.post("/register", response_model=CityResponse)
def register_city(name: str = Query(..., description="Name of the Indian city to register"), db: Session = Depends(get_db)):
    """
    Search and dynamically register any Indian city.
    Uses OpenStreetMap Nominatim Geocoding API to resolve coordinates.
    """
    city_slug = name.strip().lower().replace(" ", "-")
    
    # Check if already exists
    existing = db.query(City).filter(City.id == city_slug).first()
    if existing:
        return existing

    # Try resolving via OSM Nominatim API
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
        # Fallback coordinates near Central India if API call fails
        lat = 20.0 + random.uniform(-5.0, 5.0)
        lon = 78.0 + random.uniform(-5.0, 5.0)
        resolved_name = name.capitalize()

    # Create new Level 1 City
    new_city = City(
        id=city_slug,
        name=resolved_name,
        latitude=lat,
        longitude=lon,
        has_wards=False
    )
    db.add(new_city)
    db.commit()
    
    # Initialize 1 dynamic Ward for the city
    dynamic_ward = Ward(
        city_id=new_city.id,
        name=f"City Center - {resolved_name}",
        geojson_boundary=None
    )
    db.add(dynamic_ward)
    db.commit()
    db.refresh(dynamic_ward)

    # Initialize 1 dynamic AQI Station
    dynamic_station = AQIStation(
        name=f"Central Station - {resolved_name}",
        ward_id=dynamic_ward.id,
        latitude=lat,
        longitude=lon
    )
    db.add(dynamic_station)
    db.commit()
    db.refresh(dynamic_station)

    # Ingest Current & Historical Observations
    api_key = settings.OPENWEATHER_API_KEY
    real_data_loaded = False

    if api_key:
        # Fetch weather parameters
        weather = get_real_weather(lat, lon, api_key)
        temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
        humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
        w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
        w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

        # Fetch 24 hours of historical air pollution
        end_time = int(datetime.utcnow().timestamp())
        start_time = end_time - (24 * 3600)
        history = get_historical_air_pollution(lat, lon, start_time, end_time, api_key)

        if history:
            print(f"Dynamically loading {len(history)} real observations from OWM for {resolved_name}")
            for item in history:
                timestamp = datetime.utcfromtimestamp(item["dt"])
                comps = item.get("components", {})
                pm25 = comps.get("pm2_5", 0.0)
                pm10 = comps.get("pm10", 0.0)
                no2 = comps.get("no2", 0.0)
                co = comps.get("co", 0.0) / 1000.0  # Convert μg/m3 to mg/m3
                so2 = comps.get("so2", 0.0)
                o3 = comps.get("o3", 0.0)

                calculated_aqi = calculate_indian_aqi(pm25, pm10, no2, co, so2, o3)
                obs = AQIObservation(
                    station_id=dynamic_station.id,
                    ward_id=dynamic_ward.id,
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
            real_data_loaded = True

    # Fallback to simulated data if API key is missing or fails
    if not real_data_loaded:
        print(f"Generating simulated observations for {resolved_name}")
        now = datetime.utcnow()
        base_aqi = random.randint(80, 180)
        for h in range(24):
            obs_aqi = max(30, base_aqi + random.randint(-15, 15))
            obs = AQIObservation(
                station_id=dynamic_station.id,
                ward_id=dynamic_ward.id,
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
    
    db.refresh(new_city)
    return new_city

@router.post("/{city_id}/sync")
def sync_city_data(city_id: str, db: Session = Depends(get_db)):
    """
    Fetch the latest current weather & air pollution observations from OpenWeatherMap
    for the selected city and insert a new AQIObservation into the database.
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

    # Fetch live weather & air pollution
    weather = get_real_weather(city.latitude, city.longitude, api_key)
    pollution = get_real_air_pollution(city.latitude, city.longitude, api_key)

    if not pollution:
        raise HTTPException(status_code=502, detail="Failed to fetch live air pollution data from OpenWeatherMap.")

    # Fetch/Find the first ward and station belonging to this city
    ward = db.query(Ward).filter(Ward.city_id == city.id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="No ward associated with this city to map observations.")
    
    # Try finding an active station or create one
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

    # Parse weather
    temp = weather.get("main", {}).get("temp", 25.0) if weather else 25.0
    humidity = weather.get("main", {}).get("humidity", 60.0) if weather else 60.0
    w_speed = weather.get("wind", {}).get("speed", 4.0) if weather else 4.0
    w_deg = weather.get("wind", {}).get("deg", 180.0) if weather else 180.0

    # Write new Observation record
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

    return {
        "status": "success",
        "city": city.name,
        "aqi": calculated_aqi,
        "timestamp": new_obs.timestamp
    }
