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
        # Fallback to random coordinates near Central India if API call fails
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
    
    # Initialize 1 dynamic Ward for the city to hold observations
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

    # Initialize dynamic observations (last 24 hours) with standard AQI values
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
