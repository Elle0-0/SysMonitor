from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, ThirdPartyType


# Load database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL')

def apply_schema_changes():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Apply the unique constraint on name, latitude, and longitude
    session.execute('ALTER TABLE third_party_types ADD CONSTRAINT uq_third_party_type_name_lat_lon UNIQUE (name, latitude, longitude);')
    session.commit()
    print("Schema changes applied successfully.")

if __name__ == "__main__":
    apply_schema_changes()