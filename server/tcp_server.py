import sys
import os
import logging
import json
import time
import requests  # For making HTTP requests

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_air_quality_indices
from dto import MetricsDTO

CLIENT_URL = 'https://MichelleVaz.pythonanywhere.com/api/data'  # Replace with your actual PythonAnywhere app URL

# Set the timing intervals (in seconds)
CPU_INTERVAL = 10  # 10 seconds for CPU metrics
THIRD_PARTY_INTERVAL = 1800  # 30 minutes for third-party metrics (weather/air quality)

def collect_and_send_metrics():
    last_third_party_time = time.time()  # Track the last time third-party metrics were collected
    
    while True:
        try:
            # Collect CPU and memory usage metrics every 10 seconds
            cpu_usage = get_cpu_usage()
            memory_usage = get_memory_usage()

            # Send CPU and memory metrics immediately
            metrics_dto = MetricsDTO(
                device_id=5,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                air_quality_index=None,  # CPU and memory metrics don't have air quality data
                latitude=None,
                longitude=None
            )
            data_json = json.dumps(metrics_dto.to_dict())

            # Make an HTTP POST request to send data to the Flask app
            response = requests.post(CLIENT_URL, data=data_json, headers={'Content-Type': 'application/json'})

            if response.status_code == 200:
                logging.info("CPU and memory data successfully sent to PythonAnywhere!")
            else:
                logging.error(f"Failed to send CPU and memory data, status code: {response.status_code}")

            # Collect third-party (weather/air quality) data every 30 minutes
            current_time = time.time()
            if current_time - last_third_party_time >= THIRD_PARTY_INTERVAL:
                air_quality_indices = get_air_quality_indices()
                for location in air_quality_indices:
                    name, lat, lon, air_quality_index = location
                    metrics_dto = MetricsDTO(
                        device_id=5,
                        cpu_usage=None,  # No CPU data for third-party metrics
                        memory_usage=None,  # No memory data for third-party metrics
                        air_quality_index=air_quality_index,
                        latitude=lat,
                        longitude=lon
                    )
                    data_json = json.dumps(metrics_dto.to_dict())

                    # Make an HTTP POST request to send data to the Flask app
                    response = requests.post(CLIENT_URL, data=data_json, headers={'Content-Type': 'application/json'})

                    if response.status_code == 200:
                        logging.info(f"Air quality data for {name} successfully sent to PythonAnywhere!")
                    else:
                        logging.error(f"Failed to send air quality data for {name}, status code: {response.status_code}")

                # Update the last third-party collection time
                last_third_party_time = current_time

        except Exception as e:
            logging.error(f"An error occurred: {e}")

        time.sleep(CPU_INTERVAL)  # Sleep for 10 seconds before collecting CPU data again

def start_http_server():
    logging.info("Starting metric collection and sending to client")
    collect_and_send_metrics()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_http_server()
