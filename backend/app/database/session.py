import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import URL
from app.core.config import settings

from sqlalchemy.pool import NullPool

# If DATABASE_URL is not set, we can use an in-memory SQLite for testing/bootstrap
db_url = settings.DATABASE_URL
if not db_url:
    db_url = "sqlite:///./urbansense.db"
elif "sqlite" not in db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    try:
        scheme, rest = db_url.split("://", 1)
        if "/" in rest:
            netloc, database = rest.split("/", 1)
        else:
            netloc, database = rest, ""
            
        if "@" in netloc:
            userpass, hostport = netloc.rsplit("@", 1)
        else:
            userpass, hostport = "", netloc
            
        if ":" in userpass:
            username, password = userpass.split(":", 1)
            password = urllib.parse.unquote(password)
        else:
            username, password = userpass, ""
            
        if ":" in hostport:
            host, port = hostport.split(":", 1)
            port = int(port)
        else:
            host, port = hostport, 5432
            
        db_url = URL.create(
            drivername=scheme,
            username=username,
            password=password,
            host=host,
            port=port,
            database=database
        )
    except Exception as e:
        print(f"Error parsing database URL: {e}")

connect_args = {}
# Since db_url could be a URL object, we check type or str representation
db_url_str = str(db_url)
if db_url_str.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
else:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        poolclass=NullPool
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

