import requests


def _geocode(city, timeout):
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
        return None, None, None
    loc = results[0]
    return loc.get("latitude"), loc.get("longitude"), loc.get("name")


def fetch(city, timeout=6):
    lat, lon, name = _geocode(city, timeout)
    if lat is None or lon is None:
        return {"error": "Город не найден"}

    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
    headers = {"User-Agent": "WeatherLab/1.0 (coursework)"}
    resp = requests.get(
        url,
        params={"lat": lat, "lon": lon},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    timeseries = data.get("properties", {}).get("timeseries") or []
    if not timeseries:
        return {"error": "Нет данных от met.no"}

    entry = timeseries[0]
    details = entry.get("data", {}).get("instant", {}).get("details", {})
    next_1 = entry.get("data", {}).get("next_1_hours", {})
    precip = next_1.get("details", {}).get("precipitation_amount")
    symbol = next_1.get("summary", {}).get("symbol_code")

    wind_speed = details.get("wind_speed")
    wind_gust = details.get("wind_speed_of_gust")

    return {
        "source": "met_no",
        "city": name or city,
        "temperature_c": details.get("air_temperature"),
        "humidity": details.get("relative_humidity"),
        "wind_kph": wind_speed * 3.6 if wind_speed is not None else None,
        "wind_gust_kph": wind_gust * 3.6 if wind_gust is not None else None,
        "feels_like_c": None,
        "pressure_hpa": details.get("air_pressure_at_sea_level"),
        "visibility_km": None,
        "precip_mm": precip,
        "cloud_pct": details.get("cloud_area_fraction"),
        "condition": symbol,
        "raw": data,
    }
