from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, ThirdPartyMetric, Metric, ThirdPartyType
from datetime import datetime
import os
import uuid


DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)  # Use a session factory


def update_database(metrics_dto):
    """Inserts device and third-party metrics into the database."""
    timestamp = datetime.utcnow()
    
    with SessionLocal() as session:
        try:
            # Get Metric Type IDs dynamically
            cpu_metric_type = session.query(Metric).filter_by(name="CPU Usage").first()
            ram_metric_type = session.query(Metric).filter_by(name="Memory Usage").first()
            air_quality_type = session.query(ThirdPartyType).filter_by(name="Air Quality Index").first()

            if not (cpu_metric_type and ram_metric_type and air_quality_type):
                raise ValueError("One or more metric types are missing in the database.")

            # Insert Device Metrics
            cpu_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=metrics_dto.device_id,
                metrics_id=cpu_metric_type.uuid,
                value=metrics_dto.cpu_usage,
                timestamp=timestamp
            )
            ram_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=metrics_dto.device_id,
                metrics_id=ram_metric_type.uuid,
                value=metrics_dto.memory_usage,
                timestamp=timestamp
            )
            session.add_all([cpu_metric, ram_metric])

            # Insert Third-Party Metric (Air Quality)
            air_quality_metric = ThirdPartyMetric(
                uuid=str(uuid.uuid4()),
                thirdparty_id=air_quality_type.uuid,
                name="Air Quality Index",
                value=metrics_dto.air_quality_index,
                timestamp=timestamp
            )
            session.add(air_quality_metric)

            session.commit()  # Commit changes
        except Exception as e:
            session.rollback()
            raise e  # Rethrow for logging/debugging
