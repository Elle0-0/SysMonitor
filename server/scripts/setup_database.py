import sys
import os

# Add the project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Device, MetricType

# Replace with your actual database URL
DATABASE_URL = f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '../../sysmonitor.db'))}"

def setup_database():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add the 'PC' device if it doesn't exist
    if not session.query(Device).filter(Device.name == 'PC').first():
        device = Device(name='PC', aggregator_id=1, ordinal=1)
        session.add(device)
        print("Device 'PC' added to the database.")

    # Add the 'CPU Usage' metric type if it doesn't exist
    if not session.query(MetricType).filter(MetricType.name == 'CPU Usage').first():
        metric_type_cpu = MetricType(name='CPU Usage')
        session.add(metric_type_cpu)
        print("Metric type 'CPU Usage' added to the database.")

    # Add the 'RAM Usage' metric type if it doesn't exist
    if not session.query(MetricType).filter(MetricType.name == 'RAM Usage').first():
        metric_type_ram = MetricType(name='RAM Usage')
        session.add(metric_type_ram)
        print("Metric type 'RAM Usage' added to the database.")

    session.commit()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()