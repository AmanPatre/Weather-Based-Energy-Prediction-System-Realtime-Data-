import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import json

def load_and_prepare_data(file_path):
    """Load the merged CSV file and prepare it for training"""
    df = pd.read_csv("C:/Users/HP/OneDrive/Desktop/Sem/SEM 6/EPICS/EPICS_PROJECT/Weather-Based-Energy-Prediction-System-Realtime-Data-/data/merged.csv")
    
    # Convert date/time column to datetime format
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])
    
    # Extract hour if not already present
    if 'Hour' not in df.columns:
        df['Hour'] = df['Date/Time'].dt.hour
    
    # Create cyclical time features
    df['hour_sin'] = np.sin(2 * np.pi * df['Hour']/24)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour']/24)
    
    # Check if energy columns exist, if not create synthetic ones
    if 'solar_energy_kwh' not in df.columns:
        print("Creating synthetic solar energy targets...")
        df['solar_energy_kwh'] = ((100 - df['Cloud_Cover']) * 0.05 + df['Ambient_Temperature'] * 0.03)
        df['solar_energy_kwh'] = df['solar_energy_kwh'] * (df['Hour'].between(6, 18).astype(int) * 0.9 + 0.1)
    
    if 'wind_energy_kwh' not in df.columns:
        print("Creating synthetic wind energy targets...")
        df['wind_energy_kwh'] = df['Wind_Speed'] ** 3 * 0.01
    
    return df

def prepare_features(df):
    """Prepare features for training"""
    features = [
        'Ambient_Temperature', 'Wind_Speed', 'Cloud_Cover', 'Humidity',
        'hour_sin', 'hour_cos'
    ]
    
    # Check if all features exist in the dataframe
    available_features = [f for f in features if f in df.columns]
    print(f"Using features: {available_features}")
    
    return available_features

def train_energy_model(df, target_column, features):
    """Train and evaluate an energy prediction model"""
    X = df[features]
    y = df[target_column]
    
    # Split data (maintaining temporal order)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Predict and evaluate
    y_pred = model.predict(X_test_scaled)
    
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"{target_column} Prediction:")
    print(f"MAE: {mae:.3f} kWh")
    print(f"R² Score: {r2:.3f}")
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    print("-" * 50)
    
    return model, scaler

def generate_hourly_forecast(model, scaler, weather_data, features, date_to_forecast):
    """Generate 24-hour forecast for a specific date"""
    forecast = []
    
    # Filter weather data for the specific date (use most recent available data)
    forecast_data = weather_data[weather_data['Date/Time'].dt.date == pd.to_datetime(date_to_forecast).date()]
    
    if len(forecast_data) == 0:
        print(f"No weather data found for {date_to_forecast}, using average values")
        # Use average values for each hour
        for hour in range(24):
            avg_data = weather_data[weather_data['Hour'] == hour].mean(numeric_only=True)
            hour_data = pd.DataFrame({
                'Ambient_Temperature': [avg_data.get('Ambient_Temperature', 25.0)],
                'Wind_Speed': [avg_data.get('Wind_Speed', 4.0)],
                'Cloud_Cover': [avg_data.get('Cloud_Cover', 50)],
                'Humidity': [avg_data.get('Humidity', 70)],
                'Hour': [hour]
            })
            hour_data['hour_sin'] = np.sin(2 * np.pi * hour_data['Hour']/24)
            hour_data['hour_cos'] = np.cos(2 * np.pi * hour_data['Hour']/24)
            
            # Ensure all features are present
            for feature in features:
                if feature not in hour_data.columns:
                    hour_data[feature] = 0  # Default value
            
            # Scale and predict
            hour_scaled = scaler.transform(hour_data[features])
            prediction = model.predict(hour_scaled)[0]
            prediction = max(0, round(prediction, 1))
            forecast.append(prediction)
    else:
        # Use actual weather forecast data
        for hour in range(24):
            hour_data = forecast_data[forecast_data['Hour'] == hour].copy()
            if len(hour_data) == 0:
                # Use average values for this hour if no specific data
                avg_data = weather_data[weather_data['Hour'] == hour].mean(numeric_only=True)
                hour_data = pd.DataFrame({
                    'Ambient_Temperature': [avg_data.get('Ambient_Temperature', 25.0)],
                    'Wind_Speed': [avg_data.get('Wind_Speed', 4.0)],
                    'Cloud_Cover': [avg_data.get('Cloud_Cover', 50)],
                    'Humidity': [avg_data.get('Humidity', 70)],
                    'Hour': [hour]
                })
            
            # Prepare features
            hour_data = hour_data.iloc[0:1].copy()  # Take first row if multiple
            hour_data['hour_sin'] = np.sin(2 * np.pi * hour_data['Hour']/24)
            hour_data['hour_cos'] = np.cos(2 * np.pi * hour_data['Hour']/24)
            
            # Ensure all features are present
            for feature in features:
                if feature not in hour_data.columns:
                    hour_data[feature] = 0  # Default value
            
            # Scale and predict
            hour_scaled = scaler.transform(hour_data[features])
            prediction = model.predict(hour_scaled)[0]
            prediction = max(0, round(prediction, 1))
            forecast.append(prediction)
    
    return forecast

def main():
    # Load data from merged.csv
    csv_file_path = "C:/Users/HP/OneDrive/Desktop/Sem/SEM 6/EPICS/EPICS_PROJECT/Weather-Based-Energy-Prediction-System-Realtime-Data-/data/merged.csv"
    
    try:
        df = load_and_prepare_data(csv_file_path)
        print(f"Data loaded successfully. Shape: {df.shape}")
        print(f"Date range: {df['Date/Time'].min()} to {df['Date/Time'].max()}")
        print(f"Columns available: {list(df.columns)}")
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Prepare features
    features = prepare_features(df)
    
    # Train models
    print("\nTraining Solar Energy Model...")
    solar_model, solar_scaler = train_energy_model(df, 'solar_energy_kwh', features)
    
    print("Training Wind Energy Model...")
    wind_model, wind_scaler = train_energy_model(df, 'wind_energy_kwh', features)
    
    # Generate forecast for the last available date
    last_date = df['Date/Time'].max()
    forecast_date = last_date.strftime('%Y-%m-%d')
    
    print(f"\nGenerating forecast for {forecast_date}...")
    
    # Generate solar energy forecast
    solar_forecast = generate_hourly_forecast(solar_model, solar_scaler, df, features, forecast_date)
    total_solar = round(sum(solar_forecast), 1)
    
    # Generate wind energy forecast
    wind_forecast = generate_hourly_forecast(wind_model, wind_scaler, df, features, forecast_date)
    total_wind = round(sum(wind_forecast), 1)
    
    # Create output in specified JSON format
    solar_output = {
        "date": forecast_date,
        "granularity": "hourly",
        "forecast_series_kwh": solar_forecast,
        "total_generation_kwh": total_solar
    }
    
    wind_output = {
        "date": forecast_date,
        "granularity": "hourly",
        "forecast_series_kwh": wind_forecast,
        "total_generation_kwh": total_wind
    }
    
    print("\n=== SOLAR ENERGY FORECAST ===")
    print(json.dumps(solar_output, indent=2))
    
    print("\n=== WIND ENERGY FORECAST ===")
    print(json.dumps(wind_output, indent=2))
    
    # Save to files
    with open('solar_energy_forecast.json', 'w') as f:
        json.dump(solar_output, f, indent=2)
    
    with open('wind_energy_forecast.json', 'w') as f:
        json.dump(wind_output, f, indent=2)
    
    print("\nForecasts saved to 'solar_energy_forecast.json' and 'wind_energy_forecast.json'")

if __name__ == "__main__":
    main()