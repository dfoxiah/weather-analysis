import requests


def fetch(city, timeout=6):
    url = f"https://wttr.in/{city}"
    resp = requests.get(
        url,
        params={"format": "j1"},
        headers={"User-Agent": "weather-coursework"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    current_list = data.get("current_condition") or []
    if not current_list:
        return {"error": "Нет данных от wttr.in"}

    current = current_list[0]
    desc_list = current.get("weatherDesc") or []
    condition = desc_list[0].get("value") if desc_list else None

    return {
        "source": "wttr",
        "city": city,
        "temperature_c": current.get("temp_C"),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("windspeedKmph"),
        "wind_gust_kph": current.get("WindGustKmph") or current.get("windgustKmph"),
        "feels_like_c": current.get("FeelsLikeC"),
        "pressure_hpa": current.get("pressure"),
        "visibility_km": current.get("visibility"),
        "precip_mm": current.get("precipMM"),
        "cloud_pct": current.get("cloudcover"),
        "condition": condition,
        "raw": data,
    }
