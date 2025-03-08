import sys
import os
import logging
import socket
import json

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto import MetricsDTO
from lib_database.update_database import update_database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_HOST = 'localhost'
SERVER_PORT = 65433

def receive_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((SERVER_HOST, SERVER_PORT))
        s.listen()
        logging.info(f"Listening on {SERVER_HOST}:{SERVER_PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                logging.info(f"Connected by {addr}")
                data = conn.recv(1024)
                if not data:
                    logging.warning("Received empty data")
                    continue
                logging.info(f"Received data: {data.decode()}")
                try:
                    metrics_dto = MetricsDTO.from_dict(json.loads(data.decode()))
                    update_database(metrics_dto)
                    response = f"Processed: {metrics_dto.to_dict()}"
                    conn.sendall(response.encode())
                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")
                except Exception as e:
                    logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    receive_data()