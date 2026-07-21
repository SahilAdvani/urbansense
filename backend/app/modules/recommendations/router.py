from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

from app.database.session import get_db
from app.database.models import AIRecommendation, Ward, CitizenAdvisory, Intervention, AQIObservation
from app.shared.ai_service import GroqAIService

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

class CitizenAdvisoryResponse(BaseModel):
    id: int
    ward_id: int
    title: str
    advisory_text: str
    risk_level: str
    target_population: str
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterventionResponse(BaseModel):
    id: int
    ward_id: int
    title: str
    description: Optional[str] = None
    type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterventionDetailResponse(BaseModel):
    id: int
    ward_id: int
    ward_name: Optional[str] = None
    city_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class InterventionCreate(BaseModel):
    ward_id: int
    title: str
    description: Optional[str] = None
    type: str  # construction_halt, water_sprinkling, smog_tower_active, traffic_diversion

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

@router.post("/generate/{ward_id}")
def generate_recommendations_for_ward(ward_id: int, db: Session = Depends(get_db)):
    """
    Triggers Groq API running Llama 3.1 8B Instant to analyze the ward's current 
    measurements, estimate sources, and output recommendations and citizen advisories.
    """
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    # Fetch latest observation
    latest_obs = db.query(AQIObservation).filter(AQIObservation.ward_id == ward_id).order_by(AQIObservation.timestamp.desc()).first()
    if not latest_obs:
        # Fallback if no observations
        latest_obs = AQIObservation(
            ward_id=ward_id,
            timestamp=datetime.utcnow(),
            aqi=150,
            pm25=90.0,
            pm10=180.0,
            no2=40.0,
            co=0.8,
            so2=12.0,
            o3=30.0
        )

    pollutants = {
        "pm25": latest_obs.pm25,
        "pm10": latest_obs.pm10,
        "no2": latest_obs.no2,
        "co": latest_obs.co,
        "so2": latest_obs.so2,
        "o3": latest_obs.o3
    }

    # Call Groq AI service
    ai_data = GroqAIService.analyze_air_quality(ward.name, latest_obs.aqi, pollutants)

    # Compile estimated source percentages
    source_attribution = f"Traffic: {ai_data.get('traffic', 0)}%, Industry: {ai_data.get('industrial', 0)}%, Construction: {ai_data.get('construction', 0)}%, Road Dust: {ai_data.get('road_dust', 0)}%, Biomass: {ai_data.get('biomass_burning', 0)}%"

    # Create AI Recommendation record
    recommendation = AIRecommendation(
        ward_id=ward_id,
        trigger_aqi=latest_obs.aqi,
        primary_pollutant=ai_data.get("primary_pollutant", "PM2.5"),
        estimated_source=source_attribution,
        confidence_score=ai_data.get("confidence_score", 0.8),
        recommendation_text=ai_data.get("recommendation_text", "Limit outdoor activities"),
        action_plan={"steps": ai_data.get("action_plan_steps", [])},
        status="pending"
    )
    db.add(recommendation)

    # Create Citizen Advisory record
    advisory = CitizenAdvisory(
        ward_id=ward_id,
        title=ai_data.get("advisory_title", "AQI Alert"),
        advisory_text=ai_data.get("advisory_text", "Elevated pollution detected."),
        risk_level=ai_data.get("advisory_risk_level", "moderate"),
        target_population=ai_data.get("advisory_target_population", "all"),
        status="draft"
    )
    db.add(advisory)
    db.commit()

    db.refresh(recommendation)
    db.refresh(advisory)

    return {
        "recommendation": AIRecommendationResponse.model_validate(recommendation),
        "advisory": CitizenAdvisoryResponse.model_validate(advisory),
        "source_reasoning": ai_data.get("source_reasoning", "")
    }

@router.post("/interventions", response_model=InterventionResponse)
def create_intervention(intervention_in: InterventionCreate, db: Session = Depends(get_db)):
    """Logs an active municipal intervention execution in the database."""
    ward = db.query(Ward).filter(Ward.id == intervention_in.ward_id).first()
    if not ward:
        raise HTTPException(status_code=404, detail="Ward not found")

    new_intervention = Intervention(
        ward_id=intervention_in.ward_id,
        title=intervention_in.title,
        description=intervention_in.description,
        type=intervention_in.type,
        status="active",
        start_time=datetime.utcnow()
    )
    db.add(new_intervention)

    # If this intervention implements a recommendation, set the latest recommendation to implemented
    rec = db.query(AIRecommendation).filter(
        AIRecommendation.ward_id == intervention_in.ward_id,
        AIRecommendation.status == "pending"
    ).order_by(AIRecommendation.timestamp.desc()).first()
    
    if rec:
        rec.status = "implemented"

    db.commit()
    db.refresh(new_intervention)
    return new_intervention

@router.get("/interventions", response_model=List[InterventionDetailResponse])
def list_interventions(
    city_id: Optional[str] = None,
    ward_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve recorded municipal interventions across wards and cities."""
    query = db.query(Intervention).join(Ward)
    if city_id:
        query = query.filter(Ward.city_id == city_id)
    if ward_id:
        query = query.filter(Intervention.ward_id == ward_id)
    if status:
        query = query.filter(Intervention.status == status)
    
    interventions = query.order_by(Intervention.start_time.desc()).all()
    
    result = []
    for item in interventions:
        det = InterventionDetailResponse.model_validate(item)
        det.ward_name = item.ward.name if item.ward else None
        det.city_id = item.ward.city_id if item.ward else None
        result.append(det)
    return result

@router.get("/advisories", response_model=List[CitizenAdvisoryResponse])
def list_advisories(
    ward_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve citizen advisories, optionally filtered by ward and status."""
    query = db.query(CitizenAdvisory)
    if ward_id:
        query = query.filter(CitizenAdvisory.ward_id == ward_id)
    if status:
        query = query.filter(CitizenAdvisory.status == status)
    return query.order_by(CitizenAdvisory.created_at.desc()).all()

@router.post("/advisories/{advisory_id}/publish", response_model=CitizenAdvisoryResponse)
def publish_advisory(advisory_id: int, db: Session = Depends(get_db)):
    """Approve and publish a citizen advisory warning."""
    advisory = db.query(CitizenAdvisory).filter(CitizenAdvisory.id == advisory_id).first()
    if not advisory:
        raise HTTPException(status_code=404, detail="Advisory not found")
    
    advisory.status = "published"
    advisory.published_at = datetime.utcnow()
    db.commit()
    db.refresh(advisory)
    return advisory

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
