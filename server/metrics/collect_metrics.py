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
# OpenWeatherMap Air Pollution API (no registration required for limited access)
OPENWEATHERMAP_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")  # Use environment variable for API key

# List of locations in Ireland (latitude, longitude)
LOCATIONS = [
    ("Dublin", 53.349805, -6.26031),
    ("Cork", 51.898514, -8.475604),
    ("Galway", 53.270668, -9.056791),
    ("Limerick", 52.668, -8.630),
    ("Waterford", 52.259319, -7.11007)
]

def get_air_quality_data(lat, lon):
    url = f"{OPENWEATHERMAP_API_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching air quality data for ({lat}, {lon}): {e}")
        return None

def get_air_quality_indices():
    air_quality_indices = []
    for location in LOCATIONS:
        name, lat, lon = location
        logging.info(f"Getting air quality data for {name}")
        air_quality_data = get_air_quality_data(lat, lon)
        if air_quality_data:
            air_quality_index = air_quality_data.get("list", [{}])[0].get("main", {}).get("aqi", 1)
            logging.info(f"Collected air quality index for {name}: {air_quality_index}")
            air_quality_indices.append((name, lat, lon, air_quality_index))
        else:
            logging.warning(f"Failed to collect air quality data for {name}, returning default value")
            air_quality_indices.append((name, lat, lon, 1))  # Default value if data collection fails
    return air_quality_indices

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

