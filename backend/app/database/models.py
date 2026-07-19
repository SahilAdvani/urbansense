from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text, UUID, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="municipal_admin")  # super_admin, municipal_admin, pollution_officer
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class City(Base):
    __tablename__ = "cities"
    
    id = Column(String(100), primary_key=True, index=True)  # e.g., "delhi", "mumbai"
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    has_wards = Column(Boolean, default=False)
    is_syncing = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wards = relationship("Ward", back_populates="city", cascade="all, delete-orphan")

class Ward(Base):
    __tablename__ = "wards"
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(String(100), ForeignKey("cities.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    geojson_boundary = Column(JSON, nullable=True)  # Store Polygon coordinates or full GeoJSON Feature
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    city = relationship("City", back_populates="wards")
    stations = relationship("AQIStation", back_populates="ward", cascade="all, delete-orphan")
    observations = relationship("AQIObservation", back_populates="ward", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="ward", cascade="all, delete-orphan")
    advisories = relationship("CitizenAdvisory", back_populates="ward", cascade="all, delete-orphan")
    recommendations = relationship("AIRecommendation", back_populates="ward", cascade="all, delete-orphan")

class AQIStation(Base):
    __tablename__ = "aqi_stations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ward = relationship("Ward", back_populates="stations")
    observations = relationship("AQIObservation", back_populates="station", cascade="all, delete-orphan")

class AQIObservation(Base):
    __tablename__ = "aqi_observations"
    
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("aqi_stations.id", ondelete="SET NULL"), nullable=True)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    aqi = Column(Integer, nullable=False)
    pm25 = Column(Float, nullable=True)
    pm10 = Column(Float, nullable=True)
    no2 = Column(Float, nullable=True)
    co = Column(Float, nullable=True)
    so2 = Column(Float, nullable=True)
    o3 = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    
    ward = relationship("Ward", back_populates="observations")
    station = relationship("AQIStation", back_populates="observations")

class Intervention(Base):
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=False)  # construction_halt, water_sprinkling, smog_tower_active, traffic_diversion
    status = Column(String(50), default="active")  # planned, active, completed, cancelled
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    ward = relationship("Ward", back_populates="interventions")

class CitizenAdvisory(Base):
    __tablename__ = "citizen_advisories"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    advisory_text = Column(Text, nullable=False)
    risk_level = Column(String(50), nullable=False)  # low, moderate, high, critical
    target_population = Column(String(255), default="all")  # all, sensitive_groups
    status = Column(String(50), default="draft")  # draft, approved, published
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    ward = relationship("Ward", back_populates="advisories")

class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    ward_id = Column(Integer, ForeignKey("wards.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    trigger_aqi = Column(Integer, nullable=False)
    primary_pollutant = Column(String(50), nullable=False)
    estimated_source = Column(String(255), nullable=True)
    confidence_score = Column(Float, nullable=True)
    recommendation_text = Column(Text, nullable=False)
    action_plan = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")  # pending, implemented, dismissed
    
    ward = relationship("Ward", back_populates="recommendations")
