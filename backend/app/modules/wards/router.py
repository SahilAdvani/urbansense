from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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
    aqi: Optional[float] = None

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
    
    # Calculate average AQI for all wards in a single group-by query to avoid N+1 queries
    ward_ids = [w.id for w in wards]
    avg_aqis = {}
    if ward_ids:
        averages = (
            db.query(AQIObservation.ward_id, func.avg(AQIObservation.aqi))
            .filter(AQIObservation.ward_id.in_(ward_ids))
            .group_by(AQIObservation.ward_id)
            .all()
        )
        avg_aqis = {r[0]: round(float(r[1]), 2) for r in averages if r[1] is not None}
        
    result = []
    for ward in wards:
        lat, lon = _get_ward_centroid(ward)
        if lat is None or lon is None:
            lat = ward.city.latitude
            lon = ward.city.longitude
        
        result.append(WardResponse(
            id=ward.id, 
            name=ward.name, 
            latitude=lat, 
            longitude=lon,
            geojson_boundary=ward.geojson_boundary,
            aqi=avg_aqis.get(ward.id)
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

    # Use database-level aggregation to prevent Out-Of-Memory (OOM) crashes on large tables
    row = (
        db.query(
            func.avg(AQIObservation.aqi),
            func.avg(AQIObservation.pm25),
            func.avg(AQIObservation.pm10),
            func.avg(AQIObservation.no2),
            func.avg(AQIObservation.co),
            func.avg(AQIObservation.so2),
            func.avg(AQIObservation.o3),
            func.avg(AQIObservation.temperature),
            func.avg(AQIObservation.humidity)
        )
        .filter(AQIObservation.ward_id == ward_id)
        .first()
    )

    if not row or row[0] is None:
        return []

    def clean(val):
        return round(float(val), 2) if val is not None else 0.0

    stats = [
        WardStat(metric="AQI", value=clean(row[0])),
        WardStat(metric="PM2.5", value=clean(row[1])),
        WardStat(metric="PM10", value=clean(row[2])),
        WardStat(metric="NO2", value=clean(row[3])),
        WardStat(metric="CO", value=clean(row[4])),
        WardStat(metric="SO2", value=clean(row[5])),
        WardStat(metric="O3", value=clean(row[6])),
        WardStat(metric="Temp (°C)", value=clean(row[7])),
        WardStat(metric="Humidity (%)", value=clean(row[8])),
    ]
    return stats
