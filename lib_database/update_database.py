from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import DeviceMetric, Metric, ThirdParty, ThirdPartyType, Device  # Import Device model
from datetime import datetime
import os
import uuid
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 60})
SessionLocal = sessionmaker(bind=engine)  # Use a session factory

# Setup logger
logging.basicConfig(level=logging.INFO)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
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
                location = third_party_data["name"]
                temp = third_party_data["temperature"]
                humidity = third_party_data["humidity"]
                wind_speed = third_party_data["wind_speed"]
                pressure = third_party_data["pressure"]
                air_quality_index = third_party_data["air_quality_index"]
                precipitation = third_party_data["precipitation"]
                uv_index = third_party_data["uv_index"]
                latitude = third_party_data.get("latitude")  # Use get to avoid KeyError
                longitude = third_party_data.get("longitude")  # Use get to avoid KeyError

                # 4.1 Get Third-Party Metric Types for Temperature, Humidity, etc.
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
                    third_party_type = session.query(ThirdPartyType).filter_by(name=metric_name, latitude=latitude, longitude=longitude).first()

                    if not third_party_type:
                        raise ValueError(f"Third-party type {metric_name} ({latitude}, {longitude}) not found in the database.")

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
            logging.error(f"Error during database update: {e}", exc_info=True)
            raise e