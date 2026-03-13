import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///inventory.db')
    
    # Model parameters
    MODEL_PARAMS = {
        'n_estimators': 200,
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42
    }
    
    # Training parameters
    TEST_DAYS = 90
    LEAD_TIME_DAYS = 7
    SERVICE_LEVEL = 0.95
    
    # Paths
    MODEL_PATH = "models/forecast_model.pkl"
    DATA_PATH = "data/raw/sales_data.csv"
    
    # API
    API_TITLE = "Inventory Forecasting System"
    API_VERSION = "1.0.0"
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    # Environment
    ENV = os.getenv('ENV', 'development')
    DEBUG = ENV == 'development'