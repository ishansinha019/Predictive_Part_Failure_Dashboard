from fastapi import FastAPI
# IMPORT THE NEW MIDDLEWARE
from fastapi.middleware.cors import CORSMiddleware 

from app.db import models
from app.db.database import engine
from app.api.v1 import auth, predictions, machines

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Predictive Maintenance API",
    description="API for predicting part failures and managing machine data.",
    version="1.0.0"
)

# --- DEFINE YOUR ALLOWED ORIGINS ---
# This is your frontend's address
origins = [
    "http://localhost:5173",
]

# --- ADD THE MIDDLEWARE TO YOUR APP ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Include API Routers ---
# This organizes the endpoints by functionality.
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(machines.router, prefix="/api/v1/machines", tags=["Machines"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Predictive Maintenance API"}