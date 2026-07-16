from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from app.database.session import get_db
from app.database.models import AIRecommendation, Ward

router = APIRouter(prefix="/recommendations", tags=["ai-recommendations"])


class AIRecommendationResponse(BaseModel):
    id: int
    ward_id: int
    timestamp: datetime
    trigger_aqi: int
    primary_pollutant: str
    estimated_source: Optional[str] = None
    confidence_score: Optional[float] = None
    recommendation_text: str
    action_plan: Optional[Any] = None
    status: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AIRecommendationResponse])
def list_recommendations(
    status: Optional[str] = None,
    ward_id: Optional[int] = None,
    city_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List AI recommendations, optionally filtered by status, ward, or city."""
    query = db.query(AIRecommendation)
    if status:
        query = query.filter(AIRecommendation.status == status)
    if ward_id:
        query = query.filter(AIRecommendation.ward_id == ward_id)
    if city_id:
        query = query.join(Ward).filter(Ward.city_id == city_id)
    return query.order_by(AIRecommendation.timestamp.desc()).all()



@router.get("/{rec_id}", response_model=AIRecommendationResponse)
def get_recommendation(rec_id: int, db: Session = Depends(get_db)):
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.patch("/{rec_id}/status")
def update_recommendation_status(
    rec_id: int,
    new_status: str,
    db: Session = Depends(get_db),
):
    """Update the status of an AI recommendation (pending → implemented / dismissed)."""
    valid = {"pending", "implemented", "dismissed"}
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid}")
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.status = new_status
    db.commit()
    db.refresh(rec)
    return rec
