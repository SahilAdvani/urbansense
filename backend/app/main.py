from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.core.config import settings
from app.database.session import Base, engine
import app.database.models as models
from app.modules.auth.router import router as auth_router
from app.modules.wards.router import router as wards_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.cities.router import router as cities_router
from app.modules.forecasting.router import router as forecasting_router
from app.shared.background_tasks import start_background_tasks

# Create database tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="UrbanSense - AI-Powered Urban Air Quality Intelligence Platform",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

@app.on_event("startup")
async def startup_event():
    # Spawn the background sync loop task asynchronously
    asyncio.create_task(start_background_tasks())


# CORS middleware — allow all origins for production compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(wards_router, prefix=settings.API_V1_STR)
app.include_router(recommendations_router, prefix=settings.API_V1_STR)
app.include_router(cities_router, prefix=settings.API_V1_STR)
app.include_router(forecasting_router, prefix=settings.API_V1_STR)



@app.get("/")
def read_root():
    return {
        "message": "Welcome to the UrbanSense API",
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    """Health check endpoint — verifies the API is up and database URL is configured."""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "database_connected": bool(settings.DATABASE_URL),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
