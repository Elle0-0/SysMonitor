from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, Metric, ThirdParty, ThirdPartyType, Device  # Import Device model
from datetime import datetime
import os
import uuid
import logging

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)  # Use a session factory

# Setup logger
logging.basicConfig(level=logging.INFO)

def update_database(metrics_dto):
    """Inserts device and third-party metrics into the database."""
    timestamp = datetime.utcnow()

    with SessionLocal() as session:
        try:
            # 1. Check if the Device exists by `device_name`
            device = session.query(Device).filter_by(name=metrics_dto.device_name).first()

            if not device:
                # If device does not exist, create and insert it into the 'devices' table
                device = Device(
                    uuid=str(uuid.uuid4()),  # Generate a new UUID for the new device
                    name=metrics_dto.device_name,  # Using the device name passed in the DTO
                    date_registered=timestamp
                )
                session.add(device)
                logging.info(f"New device added: {metrics_dto.device_name} with ID: {device.uuid}")
            else:
                logging.info(f"Device already exists: {metrics_dto.device_name} with ID: {device.uuid}")

            # 2. Get Metric Type IDs dynamically (e.g., "CPU Usage" and "RAM Usage")
            cpu_metric_type = session.query(Metric).filter_by(name="CPU Usage").first()
            ram_metric_type = session.query(Metric).filter_by(name="RAM Usage").first()

            if not (cpu_metric_type and ram_metric_type):
                raise ValueError("One or more device metric types are missing in the database.")

            # 3. Insert Device Metrics
            cpu_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=device.uuid,  # Use the uuid of the found or newly created device
                metric_id=cpu_metric_type.uuid,  # Corrected field name here
                value=metrics_dto.cpu_usage,
                timestamp=timestamp
            )
            ram_metric = DeviceMetric(
                uuid=str(uuid.uuid4()),
                device_id=device.uuid,  # Use the uuid of the found or newly created device
                metric_id=ram_metric_type.uuid,  # Corrected field name here
                value=metrics_dto.ram_usage,
                timestamp=timestamp
            )
            session.add_all([cpu_metric, ram_metric])

            # 4. Prepare Third-Party Metrics in bulk
            third_party_metrics = []
            for third_party_data in metrics_dto.weather_and_air_quality_data:
                location, temp, humidity, wind_speed, pressure, air_quality_index, precipitation, uv_index = third_party_data
                
                # 4.1 Get or Create Third-Party Metric Types for Temperature, Humidity, etc.
                metric_types = {
                    "Temperature": temp,
                    "Humidity": humidity,
                    "Wind Speed": wind_speed,
                    "Pressure": pressure,
                    "Air Quality Index": air_quality_index,
                    "Precipitation": precipitation,
                    "UV Index": uv_index
                }

                for metric_name, value in metric_types.items():
                    # Get the ThirdPartyType ID dynamically for each metric
                    third_party_type = session.query(ThirdPartyType).filter_by(name=metric_name).first()

                    if not third_party_type:
                        # If the type doesn't exist, raise an exception or handle it as needed
                        raise ValueError(f"Third-party type '{metric_name}' is missing in the database.")
                    
                    # Insert Third-Party Metric for each metric, now referencing the third_party_type that contains lat/lon
                    third_party_metrics.append(ThirdParty(
                        uuid=str(uuid.uuid4()),
                        thirdparty_id=third_party_type.uuid,  # This links to the third-party type
                        name=f"{location} {metric_name}",  # Use location and metric as the name
                        value=value,
                        timestamp=timestamp
                    ))

            # Insert all Third-Party Metrics in bulk
            session.bulk_save_objects(third_party_metrics)

            # Commit all changes at once
            session.commit()  # Commit changes
            logging.info("Data successfully updated in the database.")

        except Exception as e:
            session.rollback()
            logging.error(f"Error during database update: {e}")
            raise e  # Rethrow for logging/debugging
