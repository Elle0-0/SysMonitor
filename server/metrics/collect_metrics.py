import psutil
import requests
import os
import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, ThirdPartyMetric, Metric, ThirdPartyType

# OpenWeatherMap API URLs (for weather and air pollution data)
OPENWEATHERMAP_API_URL = "http://api.openweathermap.org/data/2.5/weather"
OPENWEATHERMAP_AIR_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
API_KEY = "dc0b9ad7c4e6b96eb2d4b9f87f2fa4d1"  # Use environment variable for API key

# List of 10 locations in Ireland (latitude, longitude)
LOCATIONS = [
    ("Dublin", 53.349805, -6.26031),
    ("Cork", 51.898514, -8.475604),
    ("Galway", 53.270668, -9.056791),
    ("Limerick", 52.668, -8.630),
    ("Waterford", 52.259319, -7.11007),
    ("Belfast", 54.5973, -5.9301),
    ("Kilkenny", 52.6553, -7.2491),
    ("Sligo", 54.2765, -8.4755),
    ("Wexford", 52.3348, -6.4612),
    ("Drogheda", 53.7183, -6.3497)
]

# SQLAlchemy setup for inserting into the database
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)  # Use a session factory

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent  # For percentage

def get_weather_data(lat, lon):
    url = f"{OPENWEATHERMAP_API_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching weather data for ({lat}, {lon}): {e}")
        return None

def get_air_quality_data(lat, lon):
    url = f"{OPENWEATHERMAP_AIR_API_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching air quality data for ({lat}, {lon}): {e}")
        return None

def get_weather_and_air_quality_data():
    weather_and_air_quality_data = []
    for location in LOCATIONS:
        name, lat, lon = location
        logging.info(f"Getting data for {name}")
        weather_data = get_weather_data(lat, lon)
        air_quality_data = get_air_quality_data(lat, lon)
        
        if weather_data and air_quality_data:
            temp = weather_data.get("main", {}).get("temp", None)
            humidity = weather_data.get("main", {}).get("humidity", None)
            wind_speed = weather_data.get("wind", {}).get("speed", None)
            pressure = weather_data.get("main", {}).get("pressure", None)
            air_quality_index = air_quality_data.get("list", [{}])[0].get("main", {}).get("aqi", 1)
            precipitation = weather_data.get("rain", {}).get("1h", 0)  # Precipitation in the last hour
            uv_index = weather_data.get("current", {}).get("uvi", 0)  # UV index

            logging.info(f"Collected weather and air quality data for {name}: Temp={temp}°C, Humidity={humidity}%, Wind Speed={wind_speed}m/s, Pressure={pressure}hPa, Air Quality={air_quality_index}, Precipitation={precipitation}mm, UV Index={uv_index}")
            weather_and_air_quality_data.append((name, lat, lon, temp, humidity, wind_speed, pressure, air_quality_index, precipitation, uv_index))
        else:
            logging.warning(f"Failed to collect data for {name}")
            weather_and_air_quality_data.append((name, lat, lon, None, None, None, None, 1, 0, 0))  # Default values for missing data
    
    return weather_and_air_quality_data

def update_database(metrics_dto):
    """Inserts device and third-party metrics into the database."""
    timestamp = datetime.utcnow()
    
    with SessionLocal() as session:
        try:
            # Get Metric Type IDs dynamically
            cpu_metric_type = session.query(Metric).filter_by(name="CPU Usage").first()
            ram_metric_type = session.query(Metric).filter_by(name="Memory Usage").first()
            air_quality_type = session.query(ThirdPartyType).filter_by(name="Air Quality Index").first()
            weather_metric_type = session.query(ThirdPartyType).filter_by(name="Weather Data").first()

            if not (cpu_metric_type and ram_metric_type and air_quality_type and weather_metric_type):
                raise ValueError("One or more metric types are missing in the database.")

            # Insert Device Metrics
            cpu_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),  # Generate a new UUID
                device_id=metrics_dto.device_id,
                metrics_id=cpu_metric_type.uuid,
                value=metrics_dto.cpu_usage,
                timestamp=timestamp
            )
            ram_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),  # Generate a new UUID
                device_id=metrics_dto.device_id,
                metrics_id=ram_metric_type.uuid,
                value=metrics_dto.memory_usage,
                timestamp=timestamp
            )
            session.add_all([cpu_metric, ram_metric])

            # Insert Third-Party Metrics (Weather and Air Quality for multiple counties)
            weather_and_air_quality_data = get_weather_and_air_quality_data()
            for name, lat, lon, temp, humidity, wind_speed, pressure, air_quality_index, precipitation, uv_index in weather_and_air_quality_data:
                # Insert Weather Data
                weather_metric = ThirdPartyMetric(
                    uuid=str(uuid.uuid4()),  # Generate a new UUID
                    thirdparty_id=weather_metric_type.uuid,
                    name=f"Weather Data for {name}",
                    value=temp,  # Example: temperature in Celsius
                    timestamp=timestamp
                )
                session.add(weather_metric)

                # Insert Air Quality Data
                air_quality_metric = ThirdPartyMetric(
                    uuid=str(uuid.uuid4()),  # Generate a new UUID
                    thirdparty_id=air_quality_type.uuid,
                    name=f"Air Quality Index for {name}",
                    value=air_quality_index,
                    timestamp=timestamp
                )
                session.add(air_quality_metric)

            session.commit()  # Commit changes
        except Exception as e:
            session.rollback()
            raise e  # Rethrow for logging/debugging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
