import psutil
import requests
import logging

# OpenWeatherMap API URLs
OPENWEATHERMAP_API_URL = "http://api.openweathermap.org/data/2.5/weather"
OPENWEATHERMAP_AIR_API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
API_KEY = "dc0b9ad7c4e6b96eb2d4b9f87f2fa4d1"  # Use your actual API key

LOCATIONS = [
    ("Dublin", 53.349804, -6.260310),
    ("Cork", 51.898514, -8.475604),
    ("Galway", 53.270668, -9.056791),
    ("Limerick", 52.667999, -8.630000),
    ("Waterford", 52.259319, -7.110070),
    ("Belfast", 54.597301, -5.930100),
    ("Kilkenny", 52.655300, -7.249100),
    ("Sligo", 54.276501, -8.475500),
    ("Wexford", 52.334801, -6.461200),
    ("Drogheda", 53.718300, -6.349700)
]

def get_cpu_usage():
    """Returns the current CPU usage as a percentage."""
    return psutil.cpu_percent(interval=1)

def get_ram_usage():
    """Returns the current RAM usage as a percentage."""
    ram = psutil.virtual_memory()
    return ram.percent  # Returns percentage of RAM usage

def get_weather_data(lat, lon):
    """Fetches weather data from OpenWeatherMap API."""
    url = f"{OPENWEATHERMAP_API_URL}?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching weather data for ({lat}, {lon}): {e}")
        return None

def get_air_quality_data(lat, lon):
    """Fetches air quality data from OpenWeatherMap API."""
    url = f"{OPENWEATHERMAP_AIR_API_URL}?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching air quality data for ({lat}, {lon}): {e}")
        return None

def get_weather_and_air_quality_data():
    """Fetches and processes weather and air quality data for multiple locations."""
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

            # Append the collected data for the location
            logging.info(f"Collected weather and air quality data for {name}: Temp={temp}°C, Humidity={humidity}%, Wind Speed={wind_speed}m/s, Pressure={pressure}hPa, Air Quality={air_quality_index}, Precipitation={precipitation}mm, UV Index={uv_index}")
            weather_and_air_quality_data.append((name, temp, humidity, wind_speed, pressure, air_quality_index, precipitation, uv_index, lat, lon))
        else:
            logging.warning(f"Failed to collect data for {name}")
            # Append default values when data is missing
            weather_and_air_quality_data.append((name, None, None, None, None, 1, 0, 0, lat, lon))  # Default values for missing data
    
    return weather_and_air_quality_data
