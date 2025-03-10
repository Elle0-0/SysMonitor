import time
import logging
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_weather_and_air_quality_data
import requests

# Replace with your server's endpoint URL
SERVER_URL = "https://michellevaz.pythonanywhere.com/api/update_metrics"

def send_metrics_to_server(cpu_usage, memory_usage, weather_and_air_quality_data):
    """Sends collected metrics to the server via HTTP POST request."""
    payload = {
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "weather_and_air_quality_data": [
            {
                "name": name,
                "value": value
            }
            for name, value in weather_and_air_quality_data
        ]
    }

    try:
        response = requests.post(SERVER_URL, json=payload)
        response.raise_for_status()
        logging.info("Metrics successfully sent to server.")
    except requests.RequestException as e:
        logging.error(f"Error sending metrics to server: {e}")

def main():
    while True:
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()
        # Retrieve the weather and air quality data as a list of tuples (name, value)
        weather_and_air_quality_data = get_weather_and_air_quality_data()

        send_metrics_to_server(cpu_usage, memory_usage, weather_and_air_quality_data)

        # Sleep before collecting the data again (adjust interval as needed)
        time.sleep(10)  # Sleep for 10 minutes

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
