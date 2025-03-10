import sys
import os
import uuid

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Device, Metric

# Load database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def setup_database():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add the 'PC' device if it doesn't exist
    if not session.query(Device).filter(Device.name == 'PC').first():
        device = Device(uuid=str(uuid.uuid4()), name='PC')
        session.add(device)
        print("Device 'PC' added to the database.")

    # Add the 'CPU Usage' metric if it doesn't exist
    if not session.query(Metric).filter(Metric.name == 'CPU Usage').first():
        metric_type_cpu = Metric(uuid=str(uuid.uuid4()), name='CPU Usage')
        session.add(metric_type_cpu)
        print("Metric 'CPU Usage' added to the database.")

    # Add the 'RAM Usage' metric if it doesn't exist
    if not session.query(Metric).filter(Metric.name == 'RAM Usage').first():
        metric_type_ram = Metric(uuid=str(uuid.uuid4()), name='RAM Usage')
        session.add(metric_type_ram)
        print("Metric 'RAM Usage' added to the database.")

    session.commit()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
