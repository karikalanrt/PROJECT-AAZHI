"""
AAZHI SATELLITE INTELLIGENCE — Live Meteorological Data Fusion Engine
Project Aazhi | Autonomous Earth Observation & Tactical Geospatial Command

Cross-validates satellite-observed anomaly signatures against live ambient temperature
and 7-day cumulative precipitation from the Open-Meteo Global Forecast API.
"""

import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


def fuse_weather_data(geo_alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates or calibrates anomaly severity using real-time meteorological observations.
    - Floods: Verified against 7-day cumulative precipitation (>= 5.0mm = High Confidence).
    - Thermal/Wildfires: Verified against ambient temperature (>= 15.0°C and dry = High Confidence).
    """
    if not geo_alert_data or "coords" not in geo_alert_data:
        return geo_alert_data

    lat, lon = geo_alert_data["coords"]

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,precipitation"
            f"&daily=precipitation_sum&timezone=auto"
        )
        response = requests.get(url, timeout=3.0)

        if response.status_code == 200:
            data = response.json()
            current_temp = data.get("current", {}).get("temperature_2m", 0.0)
            daily_precip_list = data.get("daily", {}).get("precipitation_sum", [])
            total_precip = sum(p for p in daily_precip_list if p is not None)

            cat = geo_alert_data.get("category", "").lower()
            threat_type = geo_alert_data.get("threat_type", "").lower()

            is_flood = any(k in cat or k in threat_type for k in ["flood", "inundation", "cyclone"])
            is_thermal = any(k in cat or k in threat_type for k in ["thermal", "wildfire", "drought", "fire"])

            if is_flood:
                if total_precip < 5.0:
                    geo_alert_data["severity"] = "YELLOW-CHARLIE (WATCH)"
                    note = f"Low confidence of active flooding. Area has received only {total_precip:.1f}mm of rain recently. Likely permanent water body or low-lying basin."
                else:
                    note = f"High confidence. Area has received heavy rainfall ({total_precip:.1f}mm)."
                
                geo_alert_data["weather_fusion_note"] = note
                geo_alert_data["impact_summary"] = f"{geo_alert_data.get('impact_summary', '')} [WEATHER FUSION: {note}]"

            elif is_thermal:
                if current_temp < 15.0 or total_precip > 5.0:
                    geo_alert_data["severity"] = "YELLOW-CHARLIE (WATCH)"
                    note = f"Likely Contained / Stale Satellite Data. Current ambient temp is {current_temp:.1f}°C with {total_precip:.1f}mm recent rain."
                else:
                    note = f"High confidence. Current ambient temp is {current_temp:.1f}°C, supporting thermal anomaly signatures."

                geo_alert_data["weather_fusion_note"] = note
                geo_alert_data["impact_summary"] = f"{geo_alert_data.get('impact_summary', '')} [WEATHER FUSION: {note}]"

    except Exception as e:
        logger.debug("Weather API Fusion fallback: %s", e)

    return geo_alert_data

