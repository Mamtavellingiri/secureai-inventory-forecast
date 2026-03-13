import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
import joblib
from scipy import stats
import matplotlib.pyplot as plt

class InventoryForecastModel:
    def __init__(self, model_params=None):
        """Initialize XGBoost model with optimal parameters"""
        self.model_params = model_params or {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        self.model = None
        self.feature_columns = None
        
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train the XGBoost model"""
        print("Training XGBoost model...")
        self.model = xgb.XGBRegressor(**self.model_params)
        self.feature_columns = X_train.columns.tolist()
        
        if X_val is not None and y_val is not None:
            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train)
        
        print("Model training completed!")
        return self
    
    def predict(self, X):
        """Generate predictions"""
        if self.model is None:
            raise ValueError("Model not trained yet. Please train the model first.")
        
        # Ensure X has the same columns as training
        X = X[self.feature_columns]
        predictions = self.model.predict(X)
        return predictions
    
    def calculate_reorder_point(self, forecast_demand, lead_time_days=7, service_level=0.95):
        """
        Calculate reorder point and safety stock
        
        Formula:
        Reorder Point = (Daily Demand × Lead Time) + Safety Stock
        Safety Stock = Z-score × Std Dev of Demand × √(Lead Time)
        """
        # Z-score for service level
        z_scores = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
        z_score = z_scores.get(service_level, 1.645)
        
        # Estimate demand standard deviation (20% of demand as rough estimate)
        demand_std = forecast_demand * 0.2
        
        # Calculate safety stock
        safety_stock = z_score * demand_std * np.sqrt(lead_time_days)
        
        # Calculate reorder point
        reorder_point = (forecast_demand * lead_time_days) + safety_stock
        
        return {
            'reorder_point': round(max(0, reorder_point), 2),
            'safety_stock': round(max(0, safety_stock), 2),
            'forecast_daily_demand': round(forecast_demand, 2),
            'lead_time_days': lead_time_days,
            'service_level': service_level
        }
    
    def evaluate(self, X_test, y_test):
        """Evaluate model performance with multiple metrics"""
        predictions = self.predict(X_test)
        
        # Calculate metrics
        mape = mean_absolute_percentage_error(y_test, predictions) * 100
        rmse = np.sqrt(mean_squared_error(y_test, predictions))
        mae = np.mean(np.abs(y_test - predictions))
        r2 = r2_score(y_test, predictions)
        
        # Calculate bias (over/under forecasting)
        bias = np.mean(predictions - y_test)
        bias_percentage = (bias / np.mean(y_test)) * 100
        
        return {
            'mape': round(mape, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2),
            'r2': round(r2, 3),
            'bias': round(bias, 2),
            'bias_percentage': round(bias_percentage, 2)
        }
    
    def get_feature_importance(self):
        """Get feature importance rankings"""
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        importance = dict(zip(
            self.feature_columns,
            self.model.feature_importances_
        ))
        
        # Sort by importance
        sorted_importance = dict(sorted(
            importance.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return sorted_importance
    
    def save_model(self, filepath):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'model_params': self.model_params
        }
        joblib.dump(model_data, filepath)
        print(f"✅ Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load model from disk"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.model_params = model_data['model_params']
        print(f"✅ Model loaded from {filepath}")
        return self
    
    def plot_forecast(self, y_true, y_pred, dates=None, title="Forecast vs Actual"):
        """Plot forecast against actual values"""
        plt.figure(figsize=(12, 6))
        
        if dates is not None:
            plt.plot(dates, y_true, label='Actual', marker='o')
            plt.plot(dates, y_pred, label='Forecast', marker='s')
        else:
            plt.plot(y_true, label='Actual', marker='o')
            plt.plot(y_pred, label='Forecast', marker='s')
        
        plt.title(title)
        plt.xlabel('Time')
        plt.ylabel('Demand')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()