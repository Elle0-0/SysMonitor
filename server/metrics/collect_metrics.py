import psutil
import requests
import os
import logging

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent  # For percentage

# OpenWeatherMap Air Pollution API (no registration required for limited access)
OPENWEATHERMAP_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
LATITUDE = "52.668"  # Example latitude for Berlin
LONGITUDE = "-8.630"  # Example longitude for Berlin
API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "dc0b9ad7c4e6b96eb2d4b9f87f2fa4d1")  # Use environment variable for API key

def get_air_quality_data():
    url = f"{OPENWEATHERMAP_API_URL}?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching air quality data: {e}")
        return None

def get_air_quality_index():
    logging.info("Getting air quality data")
    air_quality_data = get_air_quality_data()
    if air_quality_data:
        air_quality_index = air_quality_data.get("list", [{}])[0].get("main", {}).get("aqi", 1)
        logging.info(f"Collected air quality index: {air_quality_index}")
        return air_quality_index
    else:
        logging.warning("Failed to collect air quality data, returning default value")
        return 1  # Default value if data collection fails

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

