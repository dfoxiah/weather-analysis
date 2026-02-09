from .sources import SOURCES


def coerce_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def analyze(results):
    temps = [r.get("temperature_c") for r in results]
    temps = [t for t in temps if t is not None]
    humid = [r.get("humidity") for r in results]
    humid = [h for h in humid if h is not None]
    winds = [r.get("wind_kph") for r in results]
    winds = [w for w in winds if w is not None]
    feels = [r.get("feels_like_c") for r in results]
    feels = [f for f in feels if f is not None]
    pressure = [r.get("pressure_hpa") for r in results]
    pressure = [p for p in pressure if p is not None]
    visibility = [r.get("visibility_km") for r in results]
    visibility = [v for v in visibility if v is not None]
    precip = [r.get("precip_mm") for r in results]
    precip = [p for p in precip if p is not None]
    gusts = [r.get("wind_gust_kph") for r in results]
    gusts = [g for g in gusts if g is not None]
    clouds = [r.get("cloud_pct") for r in results]
    clouds = [c for c in clouds if c is not None]

    summary = {
        "avg_temp": round(sum(temps) / len(temps), 1) if temps else None,
        "min_temp": min(temps) if temps else None,
        "max_temp": max(temps) if temps else None,
        "temp_spread": round(max(temps) - min(temps), 1) if len(temps) > 1 else None,
        "avg_humidity": round(sum(humid) / len(humid), 1) if humid else None,
        "avg_wind": round(sum(winds) / len(winds), 1) if winds else None,
        "avg_feels_like": round(sum(feels) / len(feels), 1) if feels else None,
        "avg_pressure": round(sum(pressure) / len(pressure), 1) if pressure else None,
        "avg_visibility": round(sum(visibility) / len(visibility), 1)
        if visibility
        else None,
        "avg_precip": round(sum(precip) / len(precip), 1) if precip else None,
        "avg_gust": round(sum(gusts) / len(gusts), 1) if gusts else None,
        "avg_cloud": round(sum(clouds) / len(clouds), 1) if clouds else None,
    }
    return summary
