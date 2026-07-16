from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json

from app.database.session import get_db
from app.database.models import Ward, AQIStation, AQIObservation

router = APIRouter(prefix="/wards", tags=["wards"])


class WardResponse(BaseModel):
    id: int
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geojson_boundary: Optional[dict] = None
    aqi: Optional[int] = None

    class Config:
        from_attributes = True



class WardDetailResponse(BaseModel):
    id: int
    name: str
    geojson_boundary: Optional[dict] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class WardStat(BaseModel):
    metric: str
    value: float


def _get_ward_centroid(ward: Ward) -> tuple[Optional[float], Optional[float]]:
    """Extract approximate centroid (lat, lon) from a ward's GeoJSON boundary."""
    try:
        if ward.geojson_boundary:
            coords = ward.geojson_boundary["geometry"]["coordinates"][0]
            lons = [p[0] for p in coords]
            lats = [p[1] for p in coords]
            return sum(lats) / len(lats), sum(lons) / len(lons)
    except Exception:
        pass
    return None, None


@router.get("/", response_model=List[WardResponse])
def list_wards(city_id: Optional[str] = None, db: Session = Depends(get_db)):
    """Return all wards with approximate centroid coordinates and average AQI."""
    query = db.query(Ward)
    if city_id:
        query = query.filter(Ward.city_id == city_id)
    wards = query.all()
    result = []
    for ward in wards:
        lat, lon = _get_ward_centroid(ward)
        if lat is None or lon is None:
            lat = ward.city.latitude
            lon = ward.city.longitude
        
        # Calculate current average AQI for the ward
        obs_vals = db.query(AQIObservation.aqi).filter(AQIObservation.ward_id == ward.id).all()
        aqi_val = int(sum(o[0] for o in obs_vals) / len(obs_vals)) if obs_vals else None
        
        result.append(WardResponse(
            id=ward.id, 
            name=ward.name, 
            latitude=lat, 
            longitude=lon,
            geojson_boundary=ward.geojson_boundary,
            aqi=aqi_val
        ))
    return result





@router.get("/{ward_id}", response_model=WardDetailResponse)
def get_ward(ward_id: int, db: Session = Depends(get_db)):
    """Return a single ward with GeoJSON boundary and centroid."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")
    lat, lon = _get_ward_centroid(ward)
    return WardDetailResponse(
        id=ward.id,
        name=ward.name,
        geojson_boundary=ward.geojson_boundary,
        latitude=lat,
        longitude=lon,
    )


@router.get("/{ward_id}/stats", response_model=List[WardStat])
def get_ward_stats(ward_id: int, db: Session = Depends(get_db)):
    """Return average pollutant values for a ward as chart-ready stats."""
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    observations = (
        db.query(AQIObservation)
        .filter(AQIObservation.ward_id == ward_id)
        .all()
    )

    if not observations:
        return []

    def avg(field: str) -> float:
        vals = [getattr(o, field) for o in observations if getattr(o, field) is not None]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    stats = [
        WardStat(metric="AQI", value=avg("aqi")),
        WardStat(metric="PM2.5", value=avg("pm25")),
        WardStat(metric="PM10", value=avg("pm10")),
        WardStat(metric="NO2", value=avg("no2")),
        WardStat(metric="CO", value=avg("co")),
        WardStat(metric="SO2", value=avg("so2")),
        WardStat(metric="O3", value=avg("o3")),
        WardStat(metric="Temp (°C)", value=avg("temperature")),
        WardStat(metric="Humidity (%)", value=avg("humidity")),
    ]
    return stats
