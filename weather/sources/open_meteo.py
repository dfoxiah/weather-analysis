import requests


def fetch(city, timeout=6):
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_resp = requests.get(
        geo_url,
        params={"name": city, "count": 1, "language": "ru", "format": "json"},
        timeout=timeout,
    )
    geo_resp.raise_for_status()
    geo_data = geo_resp.json()

    results = geo_data.get("results") or []
    if not results:
        return {"error": "Город не найден"}

    loc = results[0]
    lat = loc.get("latitude")
    lon = loc.get("longitude")

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_resp = requests.get(
        weather_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "wind_speed_10m",
                    "wind_gusts_10m",
                    "apparent_temperature",
                    "pressure_msl",
                    "visibility",
                    "precipitation",
                    "cloud_cover",
                    "weather_code",
                ]
            ),
            "wind_speed_unit": "kmh",
            "timezone": "auto",
        },
        timeout=timeout,
    )
    weather_resp.raise_for_status()
    weather_data = weather_resp.json()
    current = weather_data.get("current") or {}

    code = current.get("weather_code")
    condition = f"code {code}" if code is not None else None

    visibility = current.get("visibility")
    visibility_km = visibility / 1000 if visibility is not None else None

    return {
        "source": "open_meteo",
        "city": f"{loc.get('name')}, {loc.get('country_code')}",
        "temperature_c": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_kph": current.get("wind_speed_10m"),
        "wind_gust_kph": current.get("wind_gusts_10m"),
        "feels_like_c": current.get("apparent_temperature"),
        "pressure_hpa": current.get("pressure_msl"),
        "visibility_km": visibility_km,
        "precip_mm": current.get("precipitation"),
        "cloud_pct": current.get("cloud_cover"),
        "condition": condition,
        "raw": weather_data,
    }
