from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# If DATABASE_URL is not set, we can use an in-memory SQLite for testing/bootstrap
db_url = settings.DATABASE_URL
if not db_url:
    db_url = "sqlite:///./urbansense.db"
elif db_url.startswith("postgres://"):
    # SQLAlchemy requires postgresql:// instead of postgres://
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
