import psutil
import requests
import logging

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent  # For percentage

# OpenWeatherMap Air Pollution API
OPENWEATHERMAP_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
LATITUDE = "52.668"  # Latitude for Limerick
LONGITUDE = "-8.630"  # Longitude for Limerick
API_KEY = "74c854f4dfda2a351dc227e11135657d"  # Replace with your actual API key

def get_air_quality_data():
    url = f"{OPENWEATHERMAP_API_URL}?lat={LATITUDE}&lon={LONGITUDE}&appid={API_KEY}"
    logging.info(f"Requesting air quality data from URL: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_air_quality_index():
    logging.info("Getting air quality data")
    air_quality_data = get_air_quality_data()
    air_quality_index = air_quality_data.get("list", [{}])[0].get("main", {}).get("aqi", 1)
    
    logging.info(f"Collected air quality index: {air_quality_index}")
    return air_quality_index