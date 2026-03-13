import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FeatureEngineer:
    def __init__(self):
        """Initialize Feature Engineer with holiday calendar"""
        self.holiday_dates = self._get_holiday_dates()
    
    def _get_holiday_dates(self):
        """Define major holidays (add more as needed)"""
        holidays = {
            '2023-01-01': 'New Year',
            '2023-12-25': 'Christmas',
            '2024-01-01': 'New Year',
            '2024-12-25': 'Christmas',
        }
        return holidays
    
    def create_features(self, df):
        """
        Create all features for model training
        """
        # Make a copy to avoid modifying original
        data = df.copy()
        
        # Ensure date is datetime
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values(['sku_id', 'location_id', 'date'])
        
        print("Creating date-based features...")
        # 1. Date-based features
        data['day_of_week'] = data['date'].dt.dayofweek
        data['month'] = data['date'].dt.month
        data['quarter'] = data['date'].dt.quarter
        data['day_of_month'] = data['date'].dt.day
        data['week_of_year'] = data['date'].dt.isocalendar().week
        data['is_weekend'] = (data['day_of_week'] >= 5).astype(int)
        data['is_month_start'] = data['date'].dt.is_month_start.astype(int)
        data['is_month_end'] = data['date'].dt.is_month_end.astype(int)
        
        # Holiday feature
        date_str = data['date'].dt.strftime('%Y-%m-%d')
        data['is_holiday'] = date_str.isin(self.holiday_dates).astype(int)
        
        print("Creating lag features...")
        # 2. Lag features (past sales)
        for lag in [1, 7, 14, 30]:
            data[f'lag_{lag}'] = data.groupby(['sku_id', 'location_id'])['sales_quantity'].shift(lag)
        
        print("Creating rolling statistics...")
        # 3. Rolling statistics
        for window in [7, 14, 30]:
            # Mean
            data[f'rolling_mean_{window}'] = data.groupby(['sku_id', 'location_id'])['sales_quantity'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).mean()
            )
            # Std deviation
            data[f'rolling_std_{window}'] = data.groupby(['sku_id', 'location_id'])['sales_quantity'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).std()
            )
            # Max
            data[f'rolling_max_{window}'] = data.groupby(['sku_id', 'location_id'])['sales_quantity'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).max()
            )
        
        # 4. Price features (if available)
        if 'price' in data.columns and 'base_price' in data.columns:
            data['price_discount_pct'] = (data['base_price'] - data['price']) / data['base_price']
            data['price_discount_pct'] = data['price_discount_pct'].clip(0, 1)
        
        # 5. Out of stock features
        if 'out_of_stock_flag' in data.columns:
            data['oos_last_7_days'] = data.groupby(['sku_id', 'location_id'])['out_of_stock_flag'].transform(
                lambda x: x.shift(1).rolling(7, min_periods=1).sum()
            )
        
        print(f"Created {len(data.columns)} features")
        return data
    
    def prepare_features_for_training(self, df, target_col='sales_quantity'):
        """Prepare feature matrix X and target vector y"""
        # Create all features
        df_feat = self.create_features(df)
        
        # Define feature columns (exclude IDs and dates)
        exclude_cols = ['id', 'date', 'sales_quantity', 'returns_quantity', 
                       'sku_id', 'location_id', 'out_of_stock_flag']
        
        feature_cols = [col for col in df_feat.columns if col not in exclude_cols]
        
        # Handle missing values
        X = df_feat[feature_cols].fillna(0)
        y = df_feat[target_col]
        
        print(f"Prepared {len(feature_cols)} features for training")
        return X, y, feature_cols