import time
import logging
import os
import sys
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib_utils.blocktimer import BlockTimer  # Import BlockTimer
from metrics.collect_metrics import get_cpu_usage, get_ram_usage, get_weather_and_air_quality_data

# Replace with your server's endpoint URL
SERVER_URL = "https://michellevaz.pythonanywhere.com/api/update_metrics"

app = Flask(__name__)
CORS(app)  # Enable CORS

device_metrics_thread = None
weather_data_thread = None
stop_event = threading.Event()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def send_metrics_to_server(device_name, cpu_usage, ram_usage, weather_and_air_quality_data):
    """Sends collected metrics to the server via HTTP POST request."""
    payload = {
        "device_name": device_name,  # Add the device_name to the payload
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "weather_and_air_quality_data": [
            {
                "name": name,
                "temperature": temp,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "pressure": pressure,
                "air_quality_index": air_quality_index,
                "precipitation": precipitation,
                "uv_index": uv_index,
                "latitude": lat,  # Include latitude
                "longitude": lon  # Include longitude
            }
            for name, temp, humidity, wind_speed, pressure, air_quality_index, precipitation, uv_index, lat, lon in weather_and_air_quality_data
        ]
    }

    logging.info(f"Payload to be sent: {payload}")
    try:
        with BlockTimer("Sending metrics to server", logging.getLogger(__name__)):
            response = requests.post(SERVER_URL, json=payload, timeout=120)  # Increase timeout to 120 seconds
            response.raise_for_status()
            logging.info("Metrics successfully sent to server.")
            logging.info(f"Server response: {response.text}")  # Log the server response
    except requests.RequestException as e:
        logging.error(f"Error sending metrics to server: {e}")
        logging.error(f"Response content: {e.response.content if e.response else 'No response'}")  # Log response content if available
        raise

def collect_device_metrics():
    device_name = "MichelleLaptop"  
    
    while not stop_event.is_set():
        with BlockTimer("Collecting device metrics", logging.getLogger(__name__)):
            cpu_usage = get_cpu_usage()
            ram_usage = get_ram_usage()
            weather_and_air_quality_data = []  # No weather data for device metrics

        send_metrics_to_server(device_name, cpu_usage, ram_usage, weather_and_air_quality_data)
        stop_event.wait(5)  # Sleep for 5 seconds

def collect_weather_data():
    device_name = "MichelleLaptop"  
    
    while not stop_event.is_set():
        with BlockTimer("Collecting weather data", logging.getLogger(__name__)):
            weather_and_air_quality_data = get_weather_and_air_quality_data()
            cpu_usage = None  # No CPU data for weather metrics
            ram_usage = None  # No RAM data for weather metrics

        send_metrics_to_server(device_name, cpu_usage, ram_usage, weather_and_air_quality_data)
        stop_event.wait(600)  # Sleep for 10 minutes

@app.route('/start_data_collection', methods=['POST'])
def start_data_collection():
    global device_metrics_thread, weather_data_thread, stop_event
    try:
        if (device_metrics_thread is None or not device_metrics_thread.is_alive()) and (weather_data_thread is None or not weather_data_thread.is_alive()):
            stop_event.clear()
            device_metrics_thread = threading.Thread(target=collect_device_metrics)
            weather_data_thread = threading.Thread(target=collect_weather_data)
            device_metrics_thread.start()
            weather_data_thread.start()
            return jsonify({"message": "Data collection started successfully."}), 200
        else:
            return jsonify({"message": "Data collection is already running."}), 200
    except Exception as e:
        logging.error(f"Error starting data collection: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stop_data_collection', methods=['POST'])
def stop_data_collection():
    global stop_event
    try:
        stop_event.set()
        return jsonify({"message": "Data collection stopped successfully."}), 200
    except Exception as e:
        logging.error(f"Error stopping data collection: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=65433)