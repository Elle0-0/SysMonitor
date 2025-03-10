from sqlalchemy import (
    create_engine, Column, Integer, Float, String, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index, DECIMAL
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
import uuid
import os
import pymysql

pymysql.install_as_MySQLdb()

Base = declarative_base()

class Device(Base):
    __tablename__ = 'devices'
    
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    date_registered = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    metrics = relationship('DeviceMetric', back_populates='device')

class Metric(Base):
    __tablename__ = 'metrics'
    
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    
    metrics = relationship('DeviceMetric', back_populates='metric')

class DeviceMetric(Base):
    __tablename__ = 'device_metrics'
    
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey('devices.uuid'), nullable=False)
    metric_id = Column(String(36), ForeignKey('metrics.uuid'), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    device = relationship('Device', back_populates='metrics')
    metric = relationship('Metric', back_populates='metrics')
    
    __table_args__ = (Index('ix_device_metrics_device_id', 'device_id'),)

class ThirdPartyType(Base):
    __tablename__ = 'third_party_types'
    
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    latitude = Column(DECIMAL(9, 6), nullable=False)  # Change to DECIMAL
    longitude = Column(DECIMAL(9, 6), nullable=False)  # Change to DECIMAL
    
    third_parties = relationship('ThirdParty', back_populates='third_party_type')
    
    __table_args__ = (
        UniqueConstraint('name', 'latitude', 'longitude', name='uq_third_party_type_name_lat_lon'),
    )

class ThirdParty(Base):
    __tablename__ = 'third_parties'
    
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thirdparty_id = Column(String(36), ForeignKey('third_party_types.uuid'), nullable=False)
    name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    third_party_type = relationship('ThirdPartyType', back_populates='third_parties')
    
    __table_args__ = (Index('ix_third_party_timestamp', 'timestamp'),)

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(engine)
