import sys
import os
import schedule
import time
import logging
from models import Session, Device, MetricType, DeviceMetric, ThirdPartyMetric
from server.metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_air_quality_index
from flask import Flask, request, jsonify, render_template
from lib_metrics_datamodel.metrics_datamodel import Session, DeviceMetric, ThirdPartyMetric, MetricType, Device

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

@app.route('/api/aggregate', methods=['POST'])
def aggregate():
    session = Session()
    try:
        data = request.json
        cpu_usage = data.get('cpu_usage')
        memory_usage = data.get('memory_usage')
        air_quality_index = data.get('air_quality_index')

        # Insert CPU Usage and Memory Usage into the database
        device = session.query(Device).filter(Device.name == 'PC').first()
        if device is None:
            return jsonify({"error": "Device 'PC' not found in the database."}), 404

        metric_type_cpu = session.query(MetricType).filter(MetricType.name == "CPU Usage").first()
        metric_type_ram = session.query(MetricType).filter(MetricType.name == "RAM Usage").first()

        if metric_type_cpu is None or metric_type_ram is None:
            return jsonify({"error": "Metric types 'CPU Usage' or 'RAM Usage' not found in the database."}), 404

        device_metric_cpu = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_cpu.metric_type_id, value=cpu_usage)
        device_metric_ram = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_ram.metric_type_id, value=memory_usage)

        session.add(device_metric_cpu)
        session.add(device_metric_ram)

        # Insert Air Quality Index into the database
        third_party_metric_air_quality = ThirdPartyMetric(name="Air Quality Index", value=air_quality_index, source="OpenWeatherMap")
        session.add(third_party_metric_air_quality)

        session.commit()
        return jsonify({"message": "Metrics collected and stored successfully."}), 200
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/report', methods=['GET'])
def report():
    session = Session()
    try:
        # Query the latest CPU and Memory usage metrics
        cpu_metric = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 1).order_by(DeviceMetric.device_metric_id.desc()).first()
        ram_metric = session.query(DeviceMetric).filter(DeviceMetric.metric_type_id == 2).order_by(DeviceMetric.device_metric_id.desc()).first()

        # Query the latest Air Quality Index
        air_quality_metric = session.query(ThirdPartyMetric).filter(ThirdPartyMetric.name == "Air Quality Index").order_by(ThirdPartyMetric.third_party_metric_id.desc()).first()

        return render_template('index.html', cpu_metric=cpu_metric, ram_metric=ram_metric, air_quality_metric=air_quality_metric)
    finally:
        session.close()

class Application:
    def __init__(self):
        # Initialize your application here
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def collect_and_store_metrics(self):
        session = Session()
        try:
            logging.info("Starting to collect metrics.")
            
            # Collect PC metrics
            cpu_usage = get_cpu_usage()
            memory_usage = get_memory_usage()
            logging.info(f"Collected CPU usage: {cpu_usage}%, Memory usage: {memory_usage}%")

            # Insert CPU Usage and Memory Usage into the database
            device = session.query(Device).filter(Device.name == 'PC').first()
            if device is None:
                logging.error("Device 'PC' not found in the database.")
                return

            metric_type_cpu = session.query(MetricType).filter(MetricType.name == "CPU Usage").first()
            metric_type_ram = session.query(MetricType).filter(MetricType.name == "RAM Usage").first()

            if metric_type_cpu is None or metric_type_ram is None:
                logging.error("Metric types 'CPU Usage' or 'RAM Usage' not found in the database.")
                return

            device_metric_cpu = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_cpu.metric_type_id, value=cpu_usage)
            device_metric_ram = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_ram.metric_type_id, value=memory_usage)

            session.add(device_metric_cpu)
            session.add(device_metric_ram)
            logging.info("Inserted CPU and Memory usage metrics into the database.")

            # Collect and Insert Air Quality Index
            air_quality_index = get_air_quality_index()
            third_party_metric_air_quality = ThirdPartyMetric(name="Air Quality Index", value=air_quality_index, source="OpenWeatherMap")
            
            session.add(third_party_metric_air_quality)
            logging.info(f"Collected Air Quality Index: {air_quality_index} and inserted into the database.")

            session.commit()
            logging.info("Metrics collected and stored successfully.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            session.rollback()
        finally:
            session.close()

    def run(self):
        # Main logic of your application
        logging.info("Application is running")
        
        # Schedule the task to run every minute for testing purposes
        schedule.every(1).minute.do(self.collect_and_store_metrics)

        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    app = Application()
    app.run()
    app.run(debug=True)