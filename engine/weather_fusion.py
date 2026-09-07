import requests
import logging

def fuse_weather_data(geo_alert_data):
    """
    Takes a geo_alert_data dictionary, extracts coordinates, fetches live weather,
    and returns a modified geo_alert_data with validated or downgraded severity.
    """
    if not geo_alert_data or "coords" not in geo_alert_data:
        return geo_alert_data
        
    lat, lon = geo_alert_data["coords"]
    
    try:
        # Fetch current temp and 7-day precipitation sum
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation&daily=precipitation_sum&timezone=auto"
        response = requests.get(url, timeout=3.0)
        
        if response.status_code == 200:
            data = response.json()
            current_temp = data.get("current", {}).get("temperature_2m", 0)
            daily_precip_list = data.get("daily", {}).get("precipitation_sum", [])
            # Sum up whatever precipitation data is available for the 7 days
            total_precip = sum([p for p in daily_precip_list if p is not None])
            
            cat = geo_alert_data.get("category", "").lower()
            threat_type = geo_alert_data.get("threat_type", "").lower()
            
            # Helper to check if string relates to flood
            is_flood = any(k in cat or k in threat_type for k in ["flood", "inundation", "cyclone"])
            # Helper to check if string relates to thermal/fire
            is_thermal = any(k in cat or k in threat_type for k in ["thermal", "wildfire", "drought", "fire"])
            
            if is_flood:
                if total_precip < 5.0:
                    geo_alert_data["severity"] = "YELLOW-CHARLIE (WATCH)"
                    geo_alert_data["weather_fusion_note"] = f"Low confidence of active flooding. Area has received only {total_precip:.1f}mm of rain recently. Likely a permanent water body or false positive."
                    geo_alert_data["impact_summary"] = geo_alert_data.get("impact_summary", "") + f" [WEATHER API FUSION: {geo_alert_data['weather_fusion_note']}]"
                else:
                    geo_alert_data["weather_fusion_note"] = f"High confidence. Area has received heavy rainfall ({total_precip:.1f}mm)."
                    geo_alert_data["impact_summary"] = geo_alert_data.get("impact_summary", "") + f" [WEATHER API FUSION: {geo_alert_data['weather_fusion_note']}]"
                    
            elif is_thermal:
                if current_temp < 15.0 or total_precip > 5.0:
                    geo_alert_data["severity"] = "YELLOW-CHARLIE (WATCH)"
                    geo_alert_data["weather_fusion_note"] = f"Likely Contained / Stale Satellite Data. Current ambient temp is {current_temp:.1f}°C with {total_precip:.1f}mm recent rain."
                    geo_alert_data["impact_summary"] = geo_alert_data.get("impact_summary", "") + f" [WEATHER API FUSION: {geo_alert_data['weather_fusion_note']}]"
                else:
                    geo_alert_data["weather_fusion_note"] = f"High confidence. Current ambient temp is {current_temp:.1f}°C, supporting thermal anomaly signatures."
                    geo_alert_data["impact_summary"] = geo_alert_data.get("impact_summary", "") + f" [WEATHER API FUSION: {geo_alert_data['weather_fusion_note']}]"
                    
    except Exception as e:
        logging.error(f"Weather API Fusion failed: {e}")
        # If API fails, just return the original alert data untouched
        pass
        
    return geo_alert_data
