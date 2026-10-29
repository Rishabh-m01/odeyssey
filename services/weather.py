"""
services/weather.py
Weather retrieval service for ODEYSSEY using Open-Meteo API.
Open-Meteo is an open-source, free weather service that does not require an API key.
Handles timeouts, connection errors, and response formatting gracefully with fallback.
"""

import time
import requests

# In-memory cache: key=(lat, lon), value=(timestamp, data)
_WEATHER_CACHE = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes

# WMO Weather interpretation codes (WMO code -> human description & icon)
WMO_WEATHER_MAP = {
    0: {"desc": "Clear sky", "icon": "☀️"},
    1: {"desc": "Mainly clear", "icon": "🌤️"},
    2: {"desc": "Partly cloudy", "icon": "⛅"},
    3: {"desc": "Overcast", "icon": "☁️"},
    45: {"desc": "Foggy", "icon": "🌫️"},
    48: {"desc": "Depositing rime fog", "icon": "🌫️"},
    51: {"desc": "Light drizzle", "icon": "🌦️"},
    53: {"desc": "Moderate drizzle", "icon": "🌦️"},
    55: {"desc": "Dense drizzle", "icon": "🌧️"},
    61: {"desc": "Slight rain", "icon": "🌧️"},
    63: {"desc": "Moderate rain", "icon": "🌧️"},
    65: {"desc": "Heavy rain", "icon": "⛈️"},
    71: {"desc": "Slight snow fall", "icon": "🌨️"},
    73: {"desc": "Moderate snow fall", "icon": "❄️"},
    75: {"desc": "Heavy snow fall", "icon": "❄️"},
    80: {"desc": "Slight rain showers", "icon": "🌦️"},
    81: {"desc": "Moderate rain showers", "icon": "🌧️"},
    82: {"desc": "Violent rain showers", "icon": "⛈️"},
    95: {"desc": "Thunderstorm", "icon": "⚡"},
    96: {"desc": "Thunderstorm with slight hail", "icon": "⛈️"},
    99: {"desc": "Thunderstorm with heavy hail", "icon": "⛈️"},
}


def get_weather_forecast(lat: float, lon: float, days: int = 5, timeout: int = 4) -> dict:
    """
    Fetch weather forecast from Open-Meteo for given coordinates.
    Returns structured forecast with daily high/low temperatures, precipitation chance, and conditions.
    Gracefully handles network timeouts, missing fields, and rate limits.
    """
    cache_key = (round(lat, 3), round(lon, 3))
    now = time.time()

    # Check cache
    if cache_key in _WEATHER_CACHE:
        cached_time, cached_data = _WEATHER_CACHE[cache_key]
        if now - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    # Cap days between 1 and 7 (Open-Meteo free tier standard forecast window)
    forecast_days = max(1, min(days, 7))

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "weathercode",
        ],
        "timezone": "auto",
        "forecast_days": forecast_days,
    }

    try:
        response = requests.get(url, params=params, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            max_temps = daily.get("temperature_2m_max", [])
            min_temps = daily.get("temperature_2m_min", [])
            precip = daily.get("precipitation_probability_max", [])
            codes = daily.get("weathercode", [])

            daily_forecast = []
            for i in range(len(dates)):
                code = codes[i] if i < len(codes) else 0
                wmo_info = WMO_WEATHER_MAP.get(code, {"desc": "Fair", "icon": "🌤️"})
                daily_forecast.append({
                    "date": dates[i],
                    "day_index": i + 1,
                    "max_temp_c": max_temps[i] if i < len(max_temps) else None,
                    "min_temp_c": min_temps[i] if i < len(min_temps) else None,
                    "precipitation_probability": precip[i] if i < len(precip) else 0,
                    "condition": wmo_info["desc"],
                    "icon": wmo_info["icon"],
                })

            result = {
                "available": True,
                "source": "Open-Meteo API",
                "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)",
                "coordinates": {"lat": lat, "lon": lon},
                "forecast": daily_forecast,
                "summary": (
                    f"Temperatures ranging from {min_temps[0]}°C to {max_temps[0]}°C. "
                    f"Condition: {daily_forecast[0]['condition']}."
                    if daily_forecast and max_temps and min_temps
                    else "Forecast available."
                ),
            }
            _WEATHER_CACHE[cache_key] = (now, result)
            return result
        else:
            return _fallback_weather_response(
                lat, lon, reason=f"Open-Meteo returned status {response.status_code}."
            )
    except requests.exceptions.Timeout:
        return _fallback_weather_response(
            lat, lon, reason="Open-Meteo weather request timed out (service temporarily unreachable)."
        )
    except requests.exceptions.RequestException as e:
        return _fallback_weather_response(
            lat, lon, reason=f"Network error accessing weather service: {str(e)}"
        )
    except Exception as e:
        return _fallback_weather_response(
            lat, lon, reason=f"Unexpected error parsing weather data: {str(e)}"
        )


def _fallback_weather_response(lat: float, lon: float, reason: str) -> dict:
    """Provides a clear, honest fallback when external weather data cannot be fetched."""
    return {
        "available": False,
        "source": "Fallback (No live connection)",
        "reason": reason,
        "coordinates": {"lat": lat, "lon": lon},
        "forecast": [],
        "note": "Live weather forecast is currently unavailable. Please check local conditions closer to your travel date.",
    }
