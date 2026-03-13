from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import pandas as pd
import numpy as np
import joblib
import os

# Import your modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models.forecast_model import InventoryForecastModel
from src.features.feature_engineering import FeatureEngineer

# Initialize FastAPI
app = FastAPI(
    title="Inventory Forecasting System",
    description="AI-powered demand forecasting for inventory optimization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
model = None
feature_engineer = FeatureEngineer()

@app.on_event("startup")
async def load_model():
    """Load model at startup"""
    global model
    model_path = "models/forecast_model.pkl"
    if os.path.exists(model_path):
        model = InventoryForecastModel()
        model.load_model(model_path)
        print("✅ Model loaded successfully")
    else:
        print("⚠️ No pre-trained model found. Train the model first using train_model.py")

# Pydantic models for request/response
class ForecastRequest(BaseModel):
    sku_id: int
    location_id: int
    start_date: date
    end_date: date
    lead_time_days: Optional[int] = 7
    service_level: Optional[float] = 0.95

class ForecastResponse(BaseModel):
    sku_id: int
    location_id: int
    forecast_dates: List[str]
    predicted_demand: List[float]
    reorder_point: float
    safety_stock: float
    average_daily_demand: float
    total_forecast_demand: float

class ReorderRequest(BaseModel):
    sku_id: int
    location_id: int
    forecast_daily_demand: float
    lead_time_days: int = 7
    service_level: float = 0.95

class ReorderResponse(BaseModel):
    sku_id: int
    location_id: int
    reorder_point: float
    safety_stock: float
    forecast_daily_demand: float
    lead_time_days: int
    service_level: float

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    timestamp: datetime
    api_version: str

# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="active",
        model_loaded=model is not None,
        timestamp=datetime.now(),
        api_version="1.0.0"
    )

@app.post("/api/v1/forecast", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest):
    """Generate demand forecast for SKU-location pair"""
    try:
        if model is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Please train the model first using train_model.py"
            )
        
        # Generate date range
        date_range = pd.date_range(
            start=request.start_date,
            end=request.end_date,
            freq='D'
        )
        
        # For demo purposes - in production, you'd use actual model prediction
        # This simulates a realistic forecast pattern
        days = len(date_range)
        
        # Create pattern with trend, seasonality, and weekly pattern
        base_demand = 100  # This would come from historical data
        trend = np.linspace(0, 5, days)
        weekly_pattern = 10 * np.sin(2 * np.pi * np.arange(days) / 7)
        random_noise = np.random.normal(0, 5, days)
        
        predicted_demand = base_demand + trend + weekly_pattern + random_noise
        predicted_demand = np.maximum(0, predicted_demand)  # No negative demand
        
        # Calculate reorder point
        avg_daily_demand = np.mean(predicted_demand)
        reorder_calc = model.calculate_reorder_point(
            avg_daily_demand,
            request.lead_time_days,
            request.service_level
        )
        
        return ForecastResponse(
            sku_id=request.sku_id,
            location_id=request.location_id,
            forecast_dates=[d.strftime("%Y-%m-%d") for d in date_range],
            predicted_demand=[round(x, 2) for x in predicted_demand],
            reorder_point=reorder_calc['reorder_point'],
            safety_stock=reorder_calc['safety_stock'],
            average_daily_demand=round(avg_daily_demand, 2),
            total_forecast_demand=round(sum(predicted_demand), 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reorder-point", response_model=ReorderResponse)
async def calculate_reorder_point(request: ReorderRequest):
    """Calculate reorder point based on forecast"""
    try:
        if model is None:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded"
            )
        
        result = model.calculate_reorder_point(
            request.forecast_daily_demand,
            request.lead_time_days,
            request.service_level
        )
        
        return ReorderResponse(
            sku_id=request.sku_id,
            location_id=request.location_id,
            reorder_point=result['reorder_point'],
            safety_stock=result['safety_stock'],
            forecast_daily_demand=result['forecast_daily_demand'],
            lead_time_days=result['lead_time_days'],
            service_level=result['service_level']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/model/info")
async def get_model_info():
    """Get model information and performance metrics"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_type": "XGBoost Regressor",
        "parameters": model.model_params,
        "features": model.feature_columns[:10] if model.feature_columns else [],
        "feature_count": len(model.feature_columns) if model.feature_columns else 0,
        "status": "loaded"
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "model_loaded": model is not None
    }