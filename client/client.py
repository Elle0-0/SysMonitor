import time
import logging
import requests
from server.metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_air_quality_index

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_URL = "http://your_pythonanywhere_username.pythonanywhere.com/api/aggregate"

def collect_and_send_metrics():
    try:
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()
        air_quality_index = get_air_quality_index()

        data = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "air_quality_index": air_quality_index
        }

        response = requests.post(SERVER_URL, json=data)
        if response.status_code == 200:
            logging.info("Metrics sent successfully.")
        else:
            logging.error(f"Failed to send metrics: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    while True:
        collect_and_send_metrics()
        time.sleep(30)