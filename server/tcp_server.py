import sys
import os
import socket
import threading
import logging
import json
import sqlite3

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dto import MetricsDTO
from lib_database.update_database import update_database

def handle_client(conn, addr):
    logging.info(f"Connected by {addr}")
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                logging.warning("Received empty data")
                break
            logging.info(f"Received data: {data.decode()}")
            try:
                metrics_dto = MetricsDTO.from_dict(json.loads(data.decode()))
                # Process the data and send a response
                response = f"Processed: {metrics_dto.to_dict()}"
                conn.sendall(response.encode())
                # Update the database
                update_database(metrics_dto)
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
                break
            except sqlite3.OperationalError as e:
                logging.error(f"SQLite operational error: {e}")
                break

def start_tcp_server(host='0.0.0.0', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logging.info(f"Server listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    start_tcp_server()