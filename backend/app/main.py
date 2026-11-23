from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware 
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import models
from app.db.database import engine, get_db
from app.api.v1 import auth, predictions, machines, parts, simulation 
from app.core.middleware import TelemetryMiddleware
from app.core.logging import setup_logging

# Setup application logging
setup_logging()

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Predictive Maintenance API",
    description="Production-grade API for predicting industrial equipment part failures, managing machine fleets, and tracking maintenance work orders.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Custom tracing and telemetry middleware (pure ASGI)
app.add_middleware(TelemetryMiddleware)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include API Routers ---
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(machines.router, prefix="/api/v1/machines", tags=["Machines"])
app.include_router(parts.router, prefix="/api/v1/parts", tags=["Parts"])
app.include_router(simulation.router, prefix="/api/v1/simulation", tags=["Simulation"])

# --- Health & Readiness Probes ---
@app.get("/healthz", tags=["Health"])
def health_check():
    """
    Kubernetes / Container App liveness probe.
    Returns 200 OK if the service process is up.
    """
    return {"status": "healthy", "service": "predictive-maintenance-api"}

@app.get("/readyz", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes / Container App readiness probe.
    Verifies database connectivity before accepting live traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unready", "database": str(e)}
        )

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to the Predictive Maintenance API",
        "version": "2.0.0",
        "docs": "/docs"
    }
