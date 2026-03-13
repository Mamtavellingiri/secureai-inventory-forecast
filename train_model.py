#!/usr/bin/env python
# train_model.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import argparse

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.features.feature_engineering import FeatureEngineer
from src.models.forecast_model import InventoryForecastModel

def generate_sample_data():
    """Generate sample sales data for training"""
    print("\n📊 Generating sample sales data...")
    
    # Create date range (2 years of daily data)
    dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
    
    data = []
    
    # Generate for 5 SKUs and 3 locations
    for sku_id in range(1, 6):
        for location_id in range(1, 4):
            
            # Base demand varies by SKU and location
            base = 50 + sku_id * 10 + location_id * 5
            
            for date in dates:
                # Add yearly seasonality
                day_of_year = date.dayofyear
                seasonality = 20 * np.sin(2 * np.pi * day_of_year / 365)
                
                # Add weekly pattern
                weekly = 10 * np.sin(2 * np.pi * date.dayofweek / 7)
                
                # Add trend (slight increase over time)
                days_since_start = (date - dates[0]).days
                trend = 0.02 * days_since_start
                
                # Add random noise
                noise = np.random.normal(0, 5)
                
                # Calculate sales
                sales = base + seasonality + weekly + trend + noise
                sales = max(0, int(sales))
                
                # Random promotions (5% chance)
                is_promotion = np.random.random() < 0.05
                price = 100
                if is_promotion:
                    price = 80  # 20% discount
                
                data.append({
                    'date': date,
                    'sku_id': sku_id,
                    'location_id': location_id,
                    'sales_quantity': sales,
                    'price': price,
                    'base_price': 100,
                    'out_of_stock_flag': 1 if sales == 0 else 0
                })
    
    df = pd.DataFrame(data)
    print(f"✅ Generated {len(df):,} records")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   SKUs: {df['sku_id'].nunique()}, Locations: {df['location_id'].nunique()}")
    return df

def main():
    """Main training function"""
    print("=" * 60)
    print("🔮 INVENTORY FORECASTING MODEL TRAINING")
    print("=" * 60)
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str, help='Path to custom data file')
    args = parser.parse_args()
    
    # 1. Load or generate data
    if args.data_path and os.path.exists(args.data_path):
        print(f"\n📂 Loading data from {args.data_path}...")
        df = pd.read_csv(args.data_path)
        df['date'] = pd.to_datetime(df['date'])
    else:
        # Create data directory if it doesn't exist
        os.makedirs("data/raw", exist_ok=True)
        data_path = "data/raw/sample_sales_data.csv"
        
        if os.path.exists(data_path):
            print(f"\n📂 Loading existing data from {data_path}...")
            df = pd.read_csv(data_path)
            df['date'] = pd.to_datetime(df['date'])
        else:
            df = generate_sample_data()
            df.to_csv(data_path, index=False)
            print(f"✅ Data saved to {data_path}")
    
    # 2. Initialize components
    print("\n⚙️ Initializing feature engineer...")
    fe = FeatureEngineer()
    
    print("⚙️ Initializing model...")
    model = InventoryForecastModel()
    
    # 3. Prepare features
    print("\n🔧 Creating features...")
    X, y, feature_cols = fe.prepare_features_for_training(df)
    
    # 4. Train/test split (time-based)
    print("\n✂️ Splitting data into train/test sets...")
    # Use last 90 days for testing
    unique_dates = df['date'].unique()
    cutoff_date = sorted(unique_dates)[-90]
    
    train_indices = df['date'] < cutoff_date
    test_indices = df['date'] >= cutoff_date
    
    X_train = X[train_indices]
    y_train = y[train_indices]
    X_test = X[test_indices]
    y_test = y[test_indices]
    
    print(f"   Train size: {len(X_train):,} samples")
    print(f"   Test size: {len(X_test):,} samples")
    print(f"   Features: {len(feature_cols)}")
    
    # 5. Train model
    print("\n🎯 Training model...")
    model.train(X_train, y_train, X_test, y_test)
    
    # 6. Evaluate
    print("\n📊 Evaluating model...")
    metrics = model.evaluate(X_test, y_test)
    
    print(f"\n   📈 Performance Metrics:")
    print(f"   • MAPE (Mean Absolute Percentage Error): {metrics['mape']}%")
    print(f"   • RMSE (Root Mean Square Error): {metrics['rmse']}")
    print(f"   • MAE (Mean Absolute Error): {metrics['mae']}")
    print(f"   • R² Score: {metrics['r2']}")
    print(f"   • Bias: {metrics['bias']} ({metrics['bias_percentage']}%)")
    
    # 7. Feature importance
    print("\n🔝 Top 10 Important Features:")
    importance = model.get_feature_importance()
    for i, (feat, imp) in enumerate(list(importance.items())[:10]):
        print(f"   {i+1}. {feat}: {imp:.3f}")
    
    # 8. Save model
    print("\n💾 Saving model...")
    os.makedirs("models", exist_ok=True)
    model.save_model("models/forecast_model.pkl")
    
    # 9. Sample forecast calculation
    print("\n📦 Sample Reorder Point Calculation:")
    sample_reorder = model.calculate_reorder_point(
        forecast_demand=100,
        lead_time_days=7,
        service_level=0.95
    )
    print(f"   • Daily Demand: 100 units")
    print(f"   • Lead Time: 7 days")
    print(f"   • Safety Stock: {sample_reorder['safety_stock']} units")
    print(f"   • Reorder Point: {sample_reorder['reorder_point']} units")
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the API: uvicorn api.main:app --reload")
    print("2. Open browser: http://localhost:8000/docs")
    print("3. Test the forecast endpoint")

if __name__ == "__main__":
    main()