import sys
import os
import hashlib
from datetime import datetime, timedelta
import random

# Add parent directory to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal, Base, engine
from app.database.models import User, Ward, AQIStation, AQIObservation, Intervention, CitizenAdvisory, AIRecommendation

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Mock Wards with simple bounding box GeoJSONs
MOCK_WARDS = [
    {
        "name": "Ward 1 - Central Market",
        "geojson_boundary": {
            "type": "Feature",
            "properties": {"name": "Central Market"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.2, 28.6], [77.22, 28.6], [77.22, 28.62], [77.2, 28.62], [77.2, 28.6]]]
            }
        }
    },
    {
        "name": "Ward 2 - Industrial Zone",
        "geojson_boundary": {
            "type": "Feature",
            "properties": {"name": "Industrial Zone"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.24, 28.62], [77.26, 28.62], [77.26, 28.64], [77.24, 28.64], [77.24, 28.62]]]
            }
        }
    },
    {
        "name": "Ward 3 - Green Park",
        "geojson_boundary": {
            "type": "Feature",
            "properties": {"name": "Green Park"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.18, 28.58], [77.2, 28.58], [77.2, 28.6], [77.18, 28.6], [77.18, 28.58]]]
            }
        }
    },
    {
        "name": "Ward 4 - Riverside Residential",
        "geojson_boundary": {
            "type": "Feature",
            "properties": {"name": "Riverside Residential"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[77.22, 28.56], [77.24, 28.56], [77.24, 28.58], [77.22, 28.58], [77.22, 28.56]]]
            }
        }
    }
]

def seed():
    db = SessionLocal()
    try:
        print("Starting Database Seeding...")

        # 1. Create Tables
        Base.metadata.create_all(bind=engine)
        print("Database tables verified/created.")

        # 2. Seed Default User
        admin_email = "admin@urbansense.gov"
        existing_user = db.query(User).filter(User.email == admin_email).first()
        admin_user_id = None
        if not existing_user:
            admin = User(
                email=admin_email,
                hashed_password=hash_password("admin123"),
                role="municipal_admin"
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            admin_user_id = admin.id
            print(f"Created default user: {admin_email}")
        else:
            admin_user_id = existing_user.id
            print(f"Default user {admin_email} already exists.")

        # 3. Seed Wards
        inserted_wards = []
        for ward_data in MOCK_WARDS:
            existing_ward = db.query(Ward).filter(Ward.name == ward_data["name"]).first()
            if not existing_ward:
                ward = Ward(
                    name=ward_data["name"],
                    geojson_boundary=ward_data["geojson_boundary"]
                )
                db.add(ward)
                db.commit()
                db.refresh(ward)
                inserted_wards.append(ward)
                print(f"Created ward: {ward.name}")
            else:
                inserted_wards.append(existing_ward)
                print(f"Ward {existing_ward.name} already exists.")

        # 4. Seed AQI Stations
        stations = []
        for i, ward in enumerate(inserted_wards):
            # Centroid approximation
            coords = ward.geojson_boundary["geometry"]["coordinates"][0][0]
            lat, lon = coords[1], coords[0]
            
            existing_station = db.query(AQIStation).filter(AQIStation.ward_id == ward.id).first()
            if not existing_station:
                station = AQIStation(
                    name=f"Monitoring Station - {ward.name.split(' - ')[1]}",
                    ward_id=ward.id,
                    latitude=lat + 0.005,
                    longitude=lon + 0.005
                )
                db.add(station)
                db.commit()
                db.refresh(station)
                stations.append(station)
                print(f"Created station: {station.name}")
            else:
                stations.append(existing_station)
                print(f"Station for ward {ward.name} already exists.")

        # 5. Seed Historical Observations (past 24 hours)
        now = datetime.utcnow()
        for station in stations:
            existing_obs = db.query(AQIObservation).filter(AQIObservation.station_id == station.id).first()
            if not existing_obs:
                print(f"Generating 24 hours of observations for station: {station.name}")
                base_aqi = 100 if "Green Park" in station.name else (220 if "Industrial" in station.name else 140)
                
                for h in range(24):
                    timestamp = now - timedelta(hours=h)
                    # Add some random variance
                    aqi_var = random.randint(-20, 20)
                    aqi = max(30, base_aqi + aqi_var)
                    
                    obs = AQIObservation(
                        station_id=station.id,
                        ward_id=station.ward_id,
                        timestamp=timestamp,
                        aqi=aqi,
                        pm25=aqi * 0.6 + random.uniform(-5, 5),
                        pm10=aqi * 1.2 + random.uniform(-10, 10),
                        no2=random.uniform(20, 80),
                        co=random.uniform(0.1, 2.0),
                        so2=random.uniform(5, 25),
                        o3=random.uniform(10, 50),
                        temperature=25.0 + random.uniform(-3, 3),
                        humidity=60.0 + random.uniform(-10, 10),
                        wind_speed=random.uniform(2.0, 12.0),
                        wind_direction=random.uniform(0, 360)
                    )
                    db.add(obs)
                db.commit()

        # 6. Seed AI Recommendations and Interventions for high AQI Wards
        for ward in inserted_wards:
            if "Industrial" in ward.name or "Central" in ward.name:
                existing_rec = db.query(AIRecommendation).filter(AIRecommendation.ward_id == ward.id).first()
                if not existing_rec:
                    rec = AIRecommendation(
                        ward_id=ward.id,
                        trigger_aqi=245,
                        primary_pollutant="PM2.5",
                        estimated_source="Industrial Emissions & Traffic Congestion",
                        confidence_score=0.88,
                        recommendation_text="Halt all major construction activities, deploy road water sprinklers, and restrict diesel vehicle entry in the area.",
                        action_plan={
                            "steps": [
                                "Deploy 4 mechanical sweepers and water sprinklers",
                                "Temporary ban on construction operations within 1km",
                                "Issue medical advisories for high-risk citizens"
                            ]
                        },
                        status="pending"
                    )
                    db.add(rec)
                    db.commit()
                    print(f"Created pending AI recommendation for ward: {ward.name}")

        print("Database Seeding Completed Successfully!")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
