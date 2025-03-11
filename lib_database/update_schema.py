from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, ThirdPartyType


# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

LOCATIONS = [
    ("Dublin", 53.349804, -6.260310),
    ("Cork", 51.898514, -8.475604),
    ("Galway", 53.270668, -9.056791),
    ("Limerick", 52.667999, -8.630000),
    ("Waterford", 52.259319, -7.110070),
    ("Belfast", 54.597301, -5.930100),
    ("Kilkenny", 52.655300, -7.249100),
    ("Sligo", 54.276501, -8.475500),
    ("Wexford", 52.334801, -6.461200),
    ("Drogheda", 53.718300, -6.349700)
]

def update_location_names():
    session = SessionLocal()
    try:
        third_party_types = session.query(ThirdPartyType).all()
        for tpt in third_party_types:
            for location, lat, lon in LOCATIONS:
                if float(tpt.latitude) == lat and float(tpt.longitude) == lon:
                    tpt.location_name = location
                    break
        session.commit()
    except Exception as e:
        logging.error(f"Error updating location names: {str(e)}")
        session.rollback()
    finally:
        session.close()

# Run the update
update_location_names()