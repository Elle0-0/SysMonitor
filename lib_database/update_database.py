from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, ThirdPartyMetric
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)

def update_database(metrics_dto):
    Session = sessionmaker(bind=engine)  # Create a session maker tied to the engine
    session = Session()  # Each request gets a fresh session
    try:
        # Insert metrics into the database
        timestamp = datetime.utcnow()
        
        # Add CPU Usage and Memory Usage data
        cpu_metric = DeviceMetric(
            device_id=metrics_dto.device_id,
            metric_type_id=1,
            value=metrics_dto.cpu_usage,
            timestamp=timestamp
        )
        ram_metric = DeviceMetric(
            device_id=metrics_dto.device_id,
            metric_type_id=2,
            value=metrics_dto.memory_usage,
            timestamp=timestamp
        )
        session.add(cpu_metric)
        session.add(ram_metric)
        
        # Add Air Quality Index data
        air_quality_metric = ThirdPartyMetric(
            name="Air Quality Index",
            value=metrics_dto.air_quality_index,
            source="OpenWeatherMap",
            latitude=metrics_dto.latitude,
            longitude=metrics_dto.longitude,
            timestamp=timestamp
        )
        session.add(air_quality_metric)
        
        session.commit()  # Commit the changes to the database
    except Exception as e:
        session.rollback()  # Rollback the session if there is an error
        raise e
    finally:
        session.close()  # Always close the session to release the connection
