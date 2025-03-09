import sys
import os
import threading
from flask import Flask, jsonify, render_template
import logging
import requests  # Import the requests module
import time

# Add the parent directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Session, DeviceMetric, ThirdPartyMetric, MetricType, Device

app = Flask(__name__)

@app.route('/api/report', methods=['GET'])
def report():
    session = Session()
    try:
        # Query the latest CPU and Memory usage metrics
        cpu_metrics = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 1).order_by(DeviceMetric.device_metric_id.desc()).limit(100).all()
        ram_metrics = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 2).order_by(DeviceMetric.device_metric_id.desc()).limit(100).all()

        # Query the latest Air Quality Index for all locations
        air_quality_metrics = session.query(ThirdPartyMetric).filter(ThirdPartyMetric.name == "Air Quality Index").order_by(ThirdPartyMetric.third_party_metric_id.desc()).all()

        air_quality_data = [
            {
                "latitude": metric.latitude,
                "longitude": metric.longitude,
                "air_quality_index": metric.value
            }
            for metric in air_quality_metrics
        ]

        return jsonify({
            "cpu_metrics": [metric.value for metric in cpu_metrics],
            "ram_metrics": [metric.value for metric in ram_metrics],
            "air_quality_data": air_quality_data
        })
    finally:
        session.close()

@app.route('/')
def index():
    return render_template('index.html')

# Function to run client_main.py in a background thread
def run_client_script():
    time.sleep(2)  # Simulate some delay before running the script
    exec(open("client_main.py").read())  # Execute the client_main.py script

if __name__ == '__main__':
    # Start the client_main.py script in a background thread
    thread = threading.Thread(target=run_client_script)
    thread.start()

    # Start the Flask app
    app.run(debug=True)
