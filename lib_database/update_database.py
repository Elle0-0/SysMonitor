import sqlalchemy
from sqlalchemy.orm import sessionmaker
from dto import MetricsDTO
from datetime import datetime
from models import Session, DeviceMetric, ThirdPartyMetric
import os

DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sysmonitor.db'))

def update_database(metrics_dto):
    session = Session()
    try:
        # Insert a new metric snapshot
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
        session.close()