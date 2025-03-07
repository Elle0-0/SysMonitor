import schedule
import time
import logging
from models import Session, Device, MetricType, DeviceMetric, ThirdPartyMetric
from metrics.collect_metrics import get_cpu_usage, get_memory_usage, get_traffic_congestion
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from environment variables
CITY = os.getenv('CITY', 'your_city_name')

def collect_and_store_metrics():
    session = Session()
    try:
        # Collect PC metrics
        cpu_usage = get_cpu_usage()
        memory_usage = get_memory_usage()

        # Insert CPU Usage and Memory Usage into the database
        device = session.query(Device).filter(Device.name == 'PC').first()
        metric_type_cpu = session.query(MetricType).filter(MetricType.name == "CPU Usage").first()
        metric_type_ram = session.query(MetricType).filter(MetricType.name == "RAM Usage").first()

        device_metric_cpu = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_cpu.metric_type_id, value=cpu_usage)
        device_metric_ram = DeviceMetric(device_id=device.device_id, metric_type_id=metric_type_ram.metric_type_id, value=memory_usage)

        session.add(device_metric_cpu)
        session.add(device_metric_ram)

        # Collect and Insert Traffic Congestion metrics
        congestion_level = get_traffic_congestion(CITY)
        third_party_metric_traffic = ThirdPartyMetric(name=f"Traffic Congestion in {CITY}", value=congestion_level, source="Traffic")
        
        session.add(third_party_metric_traffic)

        session.commit()
        logging.info("Metrics collected and stored successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

# Schedule the task to run every 10 minutes
schedule.every(10).minutes.do(collect_and_store_metrics)

while True:
    schedule.run_pending()
    time.sleep(1)
