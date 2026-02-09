from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class WeatherQuery(Base):
    __tablename__ = "weather_queries"

    id = Column(Integer, primary_key=True)
    city = Column(String(120), nullable=False)
    sources = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    session_id = Column(String(64), nullable=True)
    summary_json = Column(Text, nullable=True)

    results = relationship(
        "WeatherResult", back_populates="query", cascade="all, delete-orphan"
    )


class WeatherResult(Base):
    __tablename__ = "weather_results"

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("weather_queries.id"), nullable=False)
    source = Column(String(60), nullable=False)
    temperature_c = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_kph = Column(Float, nullable=True)
    wind_gust_kph = Column(Float, nullable=True)
    feels_like_c = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    visibility_km = Column(Float, nullable=True)
    precip_mm = Column(Float, nullable=True)
    cloud_pct = Column(Float, nullable=True)
    condition = Column(String(160), nullable=True)
    raw_json = Column(Text, nullable=True)

    query = relationship("WeatherQuery", back_populates="results")
