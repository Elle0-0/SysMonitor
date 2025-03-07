import sys
import os
import time
import logging
import socket
import json

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib_metrics_datamodel.metrics_client_datamodel import get_cpu_usage, get_memory_usage, get_air_quality_index
from lib_config.config import load_config
from dto import MetricsDTO

# Load configuration
config = load_config()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_HOST = 'localhost'
SERVER_PORT = 65432
INTERVAL = config['interval']
DEVICE_ID = 1  # Set the device ID

def collect_and_send_metrics():
    try:
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()
        air_quality_index = get_air_quality_index()

        metrics_dto = MetricsDTO(DEVICE_ID, cpu_usage, memory_usage, air_quality_index)
        data = json.dumps(metrics_dto.to_dict())

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.sendall(data.encode())
            response = s.recv(1024)
            logging.info(f"Received response: {response.decode()}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    while True:
        collect_and_send_metrics()
        time.sleep(INTERVAL)