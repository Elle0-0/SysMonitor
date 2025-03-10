from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, Metric, ThirdParty, ThirdPartyType  # Import ThirdParty instead of ThirdPartyMetric
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

            if not (cpu_metric_type and ram_metric_type):
                raise ValueError("One or more device metric types are missing in the database.")

            # Insert Device Metrics
            cpu_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=metrics_dto.device_id,
                metric_id=cpu_metric_type.uuid,  # Corrected field name here
                value=metrics_dto.cpu_usage,
                timestamp=timestamp
            )
            ram_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=metrics_dto.device_id,
                metric_id=ram_metric_type.uuid,  # Corrected field name here
                value=metrics_dto.memory_usage,
                timestamp=timestamp
            )
            session.add_all([cpu_metric, ram_metric])

            # Insert Third-Party Metrics
            for third_party_data in metrics_dto.weather_and_air_quality_data:
                # Get ThirdPartyType ID dynamically (e.g., "Air Quality Index", "Temperature", etc.)
                third_party_type = session.query(ThirdPartyType).filter_by(name=third_party_data['name']).first()

                if not third_party_type:
                    raise ValueError(f"Third-party type '{third_party_data['name']}' is missing in the database.")
                
                # Insert Third-Party Metric
                third_party_metric = ThirdParty(
                    uuid=str(uuid.uuid4()),
                    thirdparty_id=third_party_type.uuid,  # This links to the third-party type
                    name=third_party_data['name'],  # Name of the specific third-party metric (e.g., "Air Quality Index")
                    value=third_party_data['value'],
                    timestamp=timestamp
                )
                session.add(third_party_metric)

            session.commit()  # Commit changes
        except Exception as e:
            session.rollback()
            raise e  # Rethrow for logging/debugging
