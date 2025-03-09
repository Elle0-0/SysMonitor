import sys
import os
import logging
import json
from flask import Flask, jsonify, request, render_template
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from models import Session, DeviceMetric, ThirdPartyMetric, MetricType, Device
from dto import MetricsDTO
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Flask app setup
app = Flask(__name__)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, pool_recycle=280)
Session = scoped_session(sessionmaker(bind=engine))

@app.before_first_request
def ensure_metric_types():
    session = Session()
    try:
        # Check if the metric types exist
        existing_metric_types = session.query(MetricType).all()
        if not existing_metric_types:
            # Insert default metric types if not found
            cpu_metric_type = MetricType(name="CPU Usage")
            ram_metric_type = MetricType(name="RAM Usage")
            session.add(cpu_metric_type)
            session.add(ram_metric_type)
            session.commit()
    except Exception as e:
        logging.error(f"Error ensuring metric types: {e}")
    finally:
        session.close()

@app.route('/api/data', methods=['POST'])
def report():
    session = Session()  # Creating the scoped session
    try:
        # Get the incoming JSON data from the TCP server
        data = request.get_json()
        metrics_dto = MetricsDTO.from_dict(data)

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
        return jsonify({"message": "Data successfully received and stored!"}), 200

    except Exception as e:
        session.rollback()
        logging.error(f"Error processing the data: {e}")
        return jsonify({"error": "Failed to process the data"}), 500

    finally:
        session.close()  # Use close() instead of remove()

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    session = Session()  # Creating the scoped session
    try:
        # Query the most recent metrics
        device_metrics = session.query(DeviceMetric).order_by(DeviceMetric.timestamp.desc()).limit(5).all()
        third_party_metrics = session.query(ThirdPartyMetric).order_by(ThirdPartyMetric.timestamp.desc()).limit(5).all()

        # Format the results into a dictionary
        device_metrics_data = [
            {"device_id": metric.device_id, "metric_type_id": metric.metric_type_id, "value": metric.value, "timestamp": metric.timestamp}
            for metric in device_metrics
        ]

        third_party_metrics_data = [
            {"name": metric.name, "value": metric.value, "latitude": metric.latitude, "longitude": metric.longitude, "timestamp": metric.timestamp}
            for metric in third_party_metrics
        ]

        return jsonify({
            "device_metrics": device_metrics_data,
            "third_party_metrics": third_party_metrics_data
        })

    except Exception as e:
        logging.error(f"Error fetching the data: {e}")
        return jsonify({"error": "Failed to fetch the data"}), 500

    finally:
        session.close()  # Use close() instead of remove()

@app.route('/')
def index():
    return render_template('index.html')  # Render the index.html template

if __name__ == '__main__':
    # Start the Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)
