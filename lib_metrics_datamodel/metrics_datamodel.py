from sqlalchemy import create_engine, Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class Aggregator(Base):
    __tablename__ = 'aggregators'
    aggregator_id = Column(Integer, primary_key=True)
    guid = Column(String, nullable=False)
    name = Column(String, nullable=False)

class Device(Base):
    __tablename__ = 'devices'
    device_id = Column(Integer, primary_key=True)
    aggregator_id = Column(ForeignKey('aggregators.aggregator_id'), nullable=False)
    name = Column(String, nullable=False)
    ordinal = Column(Integer, nullable=False)
    aggregator = relationship('Aggregator')

class MetricSnapshot(Base):
    __tablename__ = 'metric_snapshots'
    metric_snapshot_id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.device_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    device = relationship('Device')

class MetricType(Base):
    __tablename__ = 'metric_types'
    metric_type_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class DeviceMetric(Base):
    __tablename__ = 'device_metrics'
    device_metric_id = Column(Integer, primary_key=True)
    device_id = Column(ForeignKey('devices.device_id'), nullable=False)
    metric_type_id = Column(ForeignKey('metric_types.metric_type_id'), nullable=False)
    value = Column(Float, nullable=False)
    device = relationship('Device')
    metric_type = relationship('MetricType')

class ThirdPartyMetric(Base):
    __tablename__ = 'third_party_metrics'
    third_party_metric_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Replace with your actual database URL
DATABASE_URL = 'sqlite:///system_metrics.db'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)