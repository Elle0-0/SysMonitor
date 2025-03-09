from sqlalchemy import (
    create_engine, Column, Integer, Float, String, ForeignKey, DateTime, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
import uuid
import os

Base = declarative_base()

class Aggregator(Base):
    __tablename__ = 'aggregators'
    
    aggregator_id = Column(Integer, primary_key=True)
    guid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)

    # Relationship: One Aggregator → Many Devices
    devices = relationship('Device', back_populates='aggregator')

class Device(Base):
    __tablename__ = 'devices'
    
    device_id = Column(Integer, primary_key=True)
    aggregator_id = Column(Integer, ForeignKey('aggregators.aggregator_id'), nullable=False)
    name = Column(String(255), nullable=False)
    ordinal = Column(Integer, nullable=False)

    # Ensure `ordinal` is unique per aggregator
    __table_args__ = (UniqueConstraint('aggregator_id', 'ordinal', name='uq_device_ordinal'),)

    # Relationships
    aggregator = relationship('Aggregator', back_populates='devices')
    metrics = relationship('DeviceMetric', back_populates='device')

class DeviceMetric(Base):
    __tablename__ = 'device_metrics'
    
    device_metric_id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.device_id'), nullable=False)
    metric_type_id = Column(Integer, ForeignKey('metric_types.metric_type_id'), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    device = relationship('Device', back_populates='metrics')
    metric_type = relationship('MetricType', back_populates='metrics')

    # Indexes
    __table_args__ = (Index('ix_device_metrics_device_id', 'device_id'),)

class MetricType(Base):
    __tablename__ = 'metric_types'
    
    metric_type_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)

    # Relationship: One MetricType → Many DeviceMetrics
    metrics = relationship('DeviceMetric', back_populates='metric_type')

class ThirdPartyMetric(Base):
    __tablename__ = 'third_party_metrics'
    
    third_party_metric_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Enforce latitude and longitude constraints (only works in PostgreSQL/MySQL)
    __table_args__ = (
        CheckConstraint('latitude BETWEEN -90 AND 90', name='chk_latitude_range'),
        CheckConstraint('longitude BETWEEN -180 AND 180', name='chk_longitude_range'),
        Index('ix_third_party_metrics_name', 'name'),
    )

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(engine)
