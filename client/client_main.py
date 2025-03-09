import sys
import os
import logging
import socket
import json
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from datetime import datetime
from dto import MetricsDTO
from models import DeviceMetric, ThirdPartyMetric
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 65433
DATABASE_URL = os.getenv('DATABASE_URL')

# Create a database engine with connection pooling disabled
engine = create_engine(DATABASE_URL, poolclass=None)

# Scoped session to ensure thread-local session management
Session = scoped_session(sessionmaker(bind=engine))

def update_database(metrics_dto):
    session = Session()  # This gets the current session for this thread
    try:
        timestamp = datetime.utcnow()
        
        # Insert CPU Usage and Memory Usage into the database
        cpu_metric = DeviceMetric(
            device_id=metrics_dto.device_id,
            metric_type_id=1,  # Assuming 1 is the ID for CPU Usage
            value=metrics_dto.cpu_usage,
            timestamp=timestamp
        )
        ram_metric = DeviceMetric(
            device_id=metrics_dto.device_id,
            metric_type_id=2,  # Assuming 2 is the ID for RAM Usage
            value=metrics_dto.memory_usage,
            timestamp=timestamp
        )
        session.add(cpu_metric)
        session.add(ram_metric)
        
        # Insert Air Quality Index into the database
        air_quality_metric = ThirdPartyMetric(
            name="Air Quality Index",
            value=metrics_dto.air_quality_index,
            source="OpenWeatherMap",
            latitude=metrics_dto.latitude,
            longitude=metrics_dto.longitude,
            timestamp=timestamp
        )
        session.add(air_quality_metric)
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.remove()  # Ensure the session is removed when done

def handle_connection(conn, addr):
    with conn:
        logging.info(f"Connected by {addr}")
        data = conn.recv(1024)
        if not data:
            logging.warning("Received empty data")
            return
        logging.info(f"Received data: {data.decode()}")
        try:
            metrics_dto = MetricsDTO.from_dict(json.loads(data.decode()))
            update_database(metrics_dto)  # Update the database
            response = f"Processed: {metrics_dto.to_dict()}"
            conn.sendall(response.encode())
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

def receive_data():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((SERVER_HOST, SERVER_PORT))
        s.listen()
        logging.info(f"Listening on {SERVER_HOST}:{SERVER_PORT}")
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_connection, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    receive_data()
