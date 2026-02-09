from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from django.conf import settings

from .sqlalchemy_models import Base


def _build_engine():
    return create_engine(
        settings.SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


ENGINE = _build_engine()
SessionLocal = sessionmaker(bind=ENGINE)

RESULT_EXTRA_COLUMNS = {
    "wind_gust_kph": "FLOAT",
    "feels_like_c": "FLOAT",
    "pressure_hpa": "FLOAT",
    "visibility_km": "FLOAT",
    "precip_mm": "FLOAT",
    "cloud_pct": "FLOAT",
}


def _ensure_result_columns():
    inspector = inspect(ENGINE)
    if "weather_results" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("weather_results")}
    missing = [
        (name, col_type)
        for name, col_type in RESULT_EXTRA_COLUMNS.items()
        if name not in existing
    ]
    if not missing:
        return
    with ENGINE.connect() as conn:
        for name, col_type in missing:
            conn.exec_driver_sql(
                f"ALTER TABLE weather_results ADD COLUMN {name} {col_type}"
            )
        conn.commit()


def init_db():
    inspector = inspect(ENGINE)
    tables = inspector.get_table_names()
    if "weather_queries" not in tables or "weather_results" not in tables:
        Base.metadata.create_all(ENGINE)
    _ensure_result_columns()
