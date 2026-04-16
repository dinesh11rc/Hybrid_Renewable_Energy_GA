import sqlite3
import datetime
import math
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

class PredictiveModel:
    def __init__(self, db_file='hybrid_energy.db'):
        self.db_file = db_file
        self.models_trained = False
        
        # Scikit-Learn Models
        self.solar_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        self.wind_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        self.demand_model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42)
        
        # Metrics
        self.metrics = {
            "solar": {"mae": 0.0, "rmse": 0.0},
            "wind": {"mae": 0.0, "rmse": 0.0},
            "demand": {"mae": 0.0, "rmse": 0.0}
        }
        
    def _fetch_data(self):
        """Fetch all historical sensor readings into a Pandas DataFrame."""
        conn = sqlite3.connect(self.db_file)
        # Attempt to load newly added schema columns; fallback gracefully if absent
        try:
            query = "SELECT timestamp, solar_generation, wind_generation, total_demand, temperature, weather_condition FROM sensor_readings"
            df = pd.read_sql_query(query, conn)
        except sqlite3.OperationalError:
            # Fallback for old schema
            query = "SELECT timestamp, solar_generation, wind_generation, total_demand FROM sensor_readings"
            df = pd.read_sql_query(query, conn)
            df['temperature'] = 25.0
            df['weather_condition'] = 'clear'
            
        conn.close()
        return df

    def _engineer_features(self, df):
        """Convert timestamps to actionable ML features."""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # Simple encoding for weather if exists
        df['is_cloudy'] = (df['weather_condition'] == 'cloudy').astype(int)
        
        return df

    def train_models(self):
        """Train the Random Forest models on historical data and compute accuracy metrics."""
        df = self._fetch_data()
        if len(df) < 50:
            print("[PredictiveModel] Insufficient data to train ML models. Falling back to simple heuristics.")
            return False
            
        df = self._engineer_features(df)
        
        # Define Features (X) and Targets (y)
        features = ['hour', 'day_of_week', 'day_of_year', 'temperature', 'is_cloudy']
        X = df[features]
        
        y_solar = df['solar_generation']
        y_wind = df['wind_generation']
        y_demand = df['total_demand']
        
        # Train Models
        self.solar_model.fit(X, y_solar)
        self.wind_model.fit(X, y_wind)
        self.demand_model.fit(X, y_demand)
        
        self.models_trained = True
        
        # Calculate Model Accuracy (Predicting on training set for simplicity of demonstration, 
        # in production this would be a proper train/test split)
        pred_solar = self.solar_model.predict(X)
        self.metrics["solar"]["mae"] = round(mean_absolute_error(y_solar, pred_solar), 2)
        self.metrics["solar"]["rmse"] = round(math.sqrt(mean_squared_error(y_solar, pred_solar)), 2)
        
        pred_wind = self.wind_model.predict(X)
        self.metrics["wind"]["mae"] = round(mean_absolute_error(y_wind, pred_wind), 2)
        self.metrics["wind"]["rmse"] = round(math.sqrt(mean_squared_error(y_wind, pred_wind)), 2)
        
        pred_demand = self.demand_model.predict(X)
        self.metrics["demand"]["mae"] = round(mean_absolute_error(y_demand, pred_demand), 2)
        self.metrics["demand"]["rmse"] = round(math.sqrt(mean_squared_error(y_demand, pred_demand)), 2)
        
        print(f"[PredictiveModel] ML Models Trained successfully on {len(df)} records.")
        return True
        
    def get_metrics(self):
        """Return the calculated MAE and RMSE metrics."""
        if not self.models_trained:
            self.train_models()
        return self.metrics

    def generate_forecast(self, hours_ahead=24, scenario="normal", region_type="Individual House"):
        """
        Generate a forecast using the trained ML models.
        scenario: "normal", "cloudy", "windy", "peak_demand"
        """
        if not self.models_trained:
            success = self.train_models()
            if not success:
                return None # Fallback to heuristic
        
        forecast = []
        now = datetime.datetime.now()
        
        # Create future feature dataframe
        future_data = []
        for h in range(hours_ahead):
            forecast_time = now + datetime.timedelta(hours=h)
            is_cloudy = 1 if scenario == "cloudy" else 0
            
            # Simple temp heuristic for future
            base_temp = 20 + 10 * math.sin(math.pi * (forecast_time.hour - 6) / 12) if 6 <= forecast_time.hour <= 18 else 15
            
            future_data.append({
                'hour': forecast_time.hour,
                'day_of_week': forecast_time.weekday(),
                'day_of_year': forecast_time.timetuple().tm_yday,
                'temperature': base_temp,
                'is_cloudy': is_cloudy,
                'timestamp_obj': forecast_time
            })
            
        future_df = pd.DataFrame(future_data)
        X_future = future_df[['hour', 'day_of_week', 'day_of_year', 'temperature', 'is_cloudy']]
        
        # Predict
        solar_preds = self.solar_model.predict(X_future)
        wind_preds = self.wind_model.predict(X_future)
        demand_preds = self.demand_model.predict(X_future)
        
        # Apply Scenario Modifiers mapping to Digital Twin requirements
        if scenario == "cloudy":
            solar_preds = solar_preds * 0.6  # Reduce by 40%
        elif scenario == "windy":
            wind_preds = wind_preds * 1.5    # Increase by 50%
        elif scenario == "peak_demand":
            demand_preds = demand_preds * 1.25 # Increase by 25%
        
        # Apply Region Modifiers
        for i in range(hours_ahead):
            hour = future_data[i]['hour']
            is_weekend = future_data[i]['day_of_week'] >= 5
            
            # Modify demand pattern by region over the ML baseline
            if region_type == 'Hospital':
                demand_preds[i] *= 1.5
            elif region_type == 'Apartment Complex':
                if 17 <= hour <= 22:
                    demand_preds[i] *= 1.3
            elif region_type == 'Smart Campus':
                if is_weekend:
                    demand_preds[i] *= 0.3
                elif 9 <= hour <= 16:
                    demand_preds[i] *= 1.4
        
        for i in range(hours_ahead):
            s = max(0, solar_preds[i])
            w = max(0, wind_preds[i])
            d = max(0, demand_preds[i])
            
            forecast.append({
                "hour": future_data[i]['hour'],
                "timestamp": future_data[i]['timestamp_obj'].isoformat(),
                "solar_forecast": round(s, 2),
                "wind_forecast": round(w, 2),
                "renewable_total": round(s + w, 2),
                "demand_forecast": round(d, 2),
                "surplus_deficit": round(s + w - d, 2)
            })
            
        return forecast
