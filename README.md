# Weather-Based Energy Prediction System


A comprehensive machine learning system that predicts solar and wind energy generation based on real-time weather data, following the flowchart process outlined in the project requirements


## 🌟 System Overview
This system implements a complete weather-based energy prediction pipeline that:


1. **Fetches real-time weather data** from Open-Meteo API
2. **Cleans and processes historical CSV data** for model training
3. **Trains machine learning models** for solar and wind energy prediction
4. **Generates hourly energy predictions** using real-time weather inputs
5. **Provides comprehensive model evaluation** and performance analysis


## 🏗️ System Architecture


The system follows the exact process flow from the flowchart:


```
API (Real-time Weather Data) → CSV Update → Data Cleaning → Model Training → Energy Prediction
     ↓
Weather Parameters: Temperature, Wind Speed, Solar Irradiance, Humidity, Cloud Cover
     ↓
Hourly Energy Predictions: Solar (kW/h) + Total Energy (kW/h)
```

## 📁 Project Structure

```
weather-prediction-model/
├── Data/
│   ├── weather_last_year_data .csv          # Historical training data
│   ├── cleaned_weather_data.csv             # Processed historical data
│   └── weather.csv                          # Additional weather data
├── weather_forecast.py                      # Original weather data fetcher
├── weather_energy_prediction_model.py       # Main prediction model
├── data_preprocessing.py                    # Data cleaning and preprocessing
├── model_evaluation.py                      # Model performance evaluation
├── requirements.txt                         # Python dependencies
└── README.md                               # This file


## 🚀 Quick Start


### 1. Install Dependencies


```bash

pip install -r requirements.txt
```


### 2. Run the Complete Pipeline


```bash
python weather_energy_prediction_model.py
```
This will:
- Fetch real-time weather data from API
- Clean historical CSV data
- Train solar and wind energy models
- Generate hourly energy predictions
- Save the trained model

### 3. Run Data Preprocessing (Optional)

```bash
python data_preprocessing.py
```

This will:
- Clean and analyze historical data
- Create additional features
- Generate data distribution visualizations
- Save cleaned data for model training

### 4. Evaluate Model Performance (After Training)

```bash
python model_evaluation.py
```

This will:
- Load the trained model
- Evaluate performance metrics
- Generate performance visualizations
- Create a comprehensive performance report

## 🔧 System Components

### 1. Main Prediction Model (`weather_energy_prediction_model.py`)

**Class: `WeatherEnergyPredictionModel`**

**Key Methods:**
- `fetch_realtime_weather_data()`: Fetches weather data from Open-Meteo API
- `clean_csv_data()`: Cleans historical CSV data
- `train_model()`: Trains Random Forest models for solar and wind energy
- `predict_energy()`: Makes energy predictions using real-time weather data
- `run_complete_pipeline()`: Executes the complete workflow

**Features:**
- Dual model approach (solar + wind energy)
- Real-time weather data integration
- Automatic feature engineering
- Model persistence and loading

### 2. Data Preprocessing (`data_preprocessing.py`)

**Key Functions:**
- `load_and_explore_data()`: Loads and explores historical data
- `clean_data()`: Removes missing values, duplicates, and outliers
- `create_features()`: Creates interaction and efficiency features
- `encode_categorical_variables()`: Encodes categorical variables
- `analyze_data_distribution()`: Creates data distribution visualizations
- `analyze_correlations()`: Creates correlation heatmaps

### 3. Model Evaluation (`model_evaluation.py`)

**Class: `ModelEvaluator`**

**Key Methods:**
- `evaluate_model_performance()`: Calculates performance metrics
- `create_performance_visualizations()`: Creates prediction vs actual plots
- `create_feature_importance_plot()`: Shows feature importance analysis
- `generate_performance_report()`: Creates comprehensive performance report

## 📊 Data Requirements

### Input Data Format

The system expects historical data with the following columns:

| Column | Description | Type |
|--------|-------------|------|
| Source_Type | Energy source (Solar/Wind) | Categorical |
| Solar_Irradiance | Solar radiation intensity (W/m²) | Numerical |
| Wind_Speed | Wind speed (m/s) | Numerical |
| Ambient_Temperature | Air temperature (°C) | Numerical |
| Humidity | Relative humidity (%) | Numerical |
| Cloud_Cover | Cloud coverage (%) | Numerical |
| Panel_Area | Solar panel area (m²) | Numerical |
| Blade_Length | Wind turbine blade length (m) | Numerical |
| Storage_Capacity | Energy storage capacity | Numerical |
| Maintenance_Schedule | Maintenance schedule | Numerical |
| Energy_Output_Class | Energy output classification | Categorical |

### Real-time Weather Data

The system fetches real-time weather data including:
- Temperature (°C)
- Wind Speed (m/s)
- Solar Irradiance (W/m²)
- Humidity (%)
- Cloud Cover (%)

## 🎯 Model Architecture

### Algorithm
- **Random Forest Regressor** for both solar and wind energy prediction
- Separate models for solar and wind energy generation
- Feature scaling using StandardScaler
- Categorical encoding using LabelEncoder

### Features
- **Base Features**: Solar_Irradiance, Wind_Speed, Ambient_Temperature, Humidity, Cloud_Cover, Panel_Area, Blade_Length
- **Engineered Features**: Temperature_Squared, Humidity_Temperature_Interaction, Solar_Wind_Interaction
- **Categorical Features**: Source_Type_Encoded

### Target Variables
- **Solar Energy**: Solar_Irradiance × Panel_Area × Efficiency_Factor
- **Wind Energy**: Wind_Speed³ × Blade_Length × Power_Coefficient

## 📈 Output and Results

### Energy Predictions

The system generates hourly predictions in the format:

| Datetime | Predicted_Solar_kWh | Predicted_Energy_kWh |
|----------|---------------------|----------------------|
| 2024-01-15 09:00 | 25.0 | 35.0 |
| 2024-01-15 10:00 | 40.0 | 50.0 |
| ... | ... | ... |

### Generated Files

1. **Real-time weather data**: `weather_forecast_YYYY-MM-DD.csv`
2. **Energy predictions**: `energy_predictions_YYYYMMDD_HHMMSS.csv`
3. **Trained model**: `weather_energy_model.pkl`
4. **Cleaned data**: `Data/cleaned_weather_data.csv`
5. **Visualizations**: 
   - `data_distribution_analysis.png`
   - `correlation_heatmap.png`
   - `model_performance_analysis.png`
   - `feature_importance_analysis.png`
6. **Reports**: `model_performance_report.txt`

## 🔄 Workflow Process

### Step 1: Data Ingestion
- Fetch real-time weather data from Open-Meteo API
- Update CSV with latest weather information

### Step 2: Data Cleaning
- Remove missing values and duplicates
- Handle outliers using IQR method
- Create additional engineered features
- Encode categorical variables

### Step 3: Model Training
- Split data into training and testing sets
- Scale features using StandardScaler
- Train Random Forest models for solar and wind energy
- Evaluate model performance

### Step 4: Real-time Prediction
- Use trained models with real-time weather data
- Generate hourly energy predictions
- Save predictions to CSV file

## 🎛️ Configuration

### Location Settings
```python
# In weather_energy_prediction_model.py
latitude = 23.077080    # Your location latitude
longitude = 76.85131    # Your location longitude
```

### Model Parameters
```python
# Random Forest parameters
n_estimators = 100      # Number of trees
random_state = 42       # Random seed for reproducibility
test_size = 0.2         # Test set size (20%)
```

### Feature Engineering
```python
# Efficiency factors
solar_efficiency = 0.15     # Solar panel efficiency
wind_power_coefficient = 0.4  # Wind turbine power coefficient
```

## 📊 Performance Metrics

The system evaluates models using:
- **R² Score**: Coefficient of determination
- **RMSE**: Root Mean Square Error
- **MAE**: Mean Absolute Error
- **MAPE**: Mean Absolute Percentage Error

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Check internet connection
   - Verify API endpoint availability
   - Check latitude/longitude coordinates

2. **Data Loading Error**
   - Ensure CSV file exists in Data/ folder
   - Check file permissions
   - Verify CSV format matches expected structure

3. **Model Training Error**
   - Ensure sufficient training data
   - Check for missing values in features
   - Verify feature column names match

4. **Memory Issues**
   - Reduce dataset size for testing
   - Use smaller Random Forest parameters
   - Process data in chunks

### Error Messages

- `❌ Failed to fetch weather data`: API connection issue
- `❌ Error cleaning data`: Data preprocessing problem
- `❌ Error training model`: Model training failure
- `❌ Error making predictions`: Prediction generation issue

## 🔮 Future Enhancements

### Planned Features
- **Real-time Dashboard**: Web interface for live monitoring
- **Multiple Weather APIs**: Fallback and redundancy
- **Advanced ML Models**: Deep learning and ensemble methods
- **Weather Forecasting**: Multi-day predictions
- **Energy Optimization**: Load balancing and storage optimization

### Model Improvements
- **Hyperparameter Tuning**: Grid search and optimization
- **Feature Selection**: Automated feature importance analysis
- **Cross-validation**: K-fold cross-validation for robust evaluation
- **Model Ensembling**: Combine multiple algorithms

## 📚 Technical Details

### Dependencies
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **scikit-learn**: Machine learning algorithms
- **requests**: HTTP library for API calls
- **joblib**: Model persistence
- **matplotlib**: Data visualization
- **seaborn**: Statistical data visualization

### System Requirements
- **Python**: 3.7 or higher
- **Memory**: Minimum 4GB RAM
- **Storage**: 1GB free space
- **Internet**: Required for API calls

### Performance
- **Training Time**: 1-5 minutes (depending on data size)
- **Prediction Time**: <1 second per hour
- **Memory Usage**: 100-500MB during training
- **Storage**: ~50MB for trained models

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings for all functions
- Include type hints where possible
- Write clear commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support:
- Create an issue in the repository
- Check the troubleshooting section
- Review the error logs
- Verify system requirements

## 🎉 Acknowledgments

- Open-Meteo API for weather data
- Scikit-learn for machine learning algorithms
- Python community for excellent libraries
- Contributors and users of this system

---

**Note**: This system is designed for educational and research purposes. For production use, please ensure proper testing, validation, and compliance with local regulations.
