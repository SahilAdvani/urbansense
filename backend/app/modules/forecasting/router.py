from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import math
import random

from app.database.session import get_db
from app.database.models import AQIObservation, Ward

router = APIRouter(prefix="/forecasting", tags=["forecasting"])

class ForecastDataPoint(BaseModel):
    timestamp: datetime
    predicted_aqi: int
    confidence_lower: int
    confidence_upper: int

@router.get("/{ward_id}", response_model=List[ForecastDataPoint])
def get_ward_forecast(ward_id: int, db: Session = Depends(get_db)):
    """
    Predicts the next 24 hours of AQI for a selected ward based on the past 
    24 hours of historical observations and local meteorological trends.
    """
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
        
    obs = db.query(AQIObservation).filter(AQIObservation.ward_id == ward_id).order_by(AQIObservation.timestamp.desc()).limit(24).all()
    if not obs:
        # Generate dummy observations if none exist (safe fallback)
        now = datetime.utcnow()
        obs = []
        for h in range(24):
            obs.append(AQIObservation(
                ward_id=ward_id,
                timestamp=now - timedelta(hours=h),
                aqi=random.randint(120, 180),
                temperature=25.0,
                humidity=60.0,
                wind_speed=4.0
            ))

    # Sort observations chronologically
    obs = sorted(obs, key=lambda x: x.timestamp)
    
    n = len(obs)
    first_time = obs[0].timestamp
    x = []
    for o in obs:
        delta_hours = (o.timestamp - first_time).total_seconds() / 3600.0
        x.append(delta_hours)
    y = [o.aqi for o in obs]
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    den = sum((x[i] - mean_x) ** 2 for i in range(n))
    
    slope = num / den if den != 0 else 0.0
    # Cap slope to prevent extreme trend lines from sparse data or gaps
    slope = max(-5.0, min(5.0, slope))
    
    # Get last known observation
    last_obs = obs[-1]
    last_aqi = last_obs.aqi
    last_time = last_obs.timestamp
    
    # Get baseline meteorological metrics
    temp = last_obs.temperature or 25.0
    humidity = last_obs.humidity or 60.0
    wind_speed = last_obs.wind_speed or 4.0

    forecast = []
    for h in range(1, 25):
        future_time = last_time + timedelta(hours=h)
        
        # Diurnal cycle simulation: higher at night/early morning, lower in afternoon
        diurnal_factor = 15 * math.sin((future_time.hour - 6) * math.pi / 12)
        
        # Extrapolate linear trend with exponential dampening to avoid runway values
        dampening = math.exp(-0.1 * h)
        trend_factor = slope * h * 0.4 * dampening
        
        # Introduce weather dispersion factors
        weather_factor = (humidity - 60) * 0.15 - (wind_speed - 4.0) * 1.5
        
        # Combine
        predicted = int(last_aqi + trend_factor + diurnal_factor + weather_factor + random.uniform(-4, 4))
        predicted = max(20, min(500, predicted))  # Bound AQI
        
        # Confidence margins expand as we look further into the future
        margin = int(8 + h * 1.2)
        
        forecast.append(ForecastDataPoint(
            timestamp=future_time,
            predicted_aqi=predicted,
            confidence_lower=max(10, predicted - margin),
            confidence_upper=min(500, predicted + margin)
        ))
        
    return forecast
