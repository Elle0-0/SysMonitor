import sys
import os
import socket
import logging
import json
import time

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_air_quality_indices
from dto import MetricsDTO

CLIENT_HOST = 'localhost'
CLIENT_PORT = 65433

def collect_and_send_metrics():
    while True:
        try:
            cpu_usage = get_cpu_usage()
            memory_usage = get_memory_usage()
            air_quality_indices = get_air_quality_indices()
            for location in air_quality_indices:
                name, lat, lon, air_quality_index = location
                metrics_dto = MetricsDTO(
                    device_id=1,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    air_quality_index=air_quality_index,
                    latitude=lat,
                    longitude=lon
                )
                data_json = json.dumps(metrics_dto.to_dict())
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((CLIENT_HOST, CLIENT_PORT))
                    s.sendall(data_json.encode())
                    response = s.recv(1024)
                    logging.info(f"Received response: {response.decode()}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        time.sleep(5)  # Collect and send metrics every 5 seconds

def start_tcp_server():
    logging.info("Starting metric collection and sending to client")
    collect_and_send_metrics()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_tcp_server()