import sys

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_block = """geo_alert_data = None
        # ── FLOOD / SEVERE INUNDATION ────────────────────────────────────────"""

good_block = """geo_alert_data = None
is_alert_triggered = False

if active_anomaly_info is not None:
    is_alert_triggered = True
    geo_alert_data = radar_engine.generate_geo_alert(active_anomaly_info, metrics)
elif input_source == "📁 Upload Custom Satellite Scene (GeoTIFF / JPG / PNG)" or active_anomaly_info is None:
    is_alert_triggered = True

    # ── LAYER 1: Filename-based ecology context ──────────────────────────────
    # Identifies known geographic / ecological types from the uploaded filename
    # so that the same image gives the same result regardless of path taken.
    _fname_ctx = (uploaded_file.name.lower() if uploaded_file else "") if 'uploaded_file' in dir() else ""

    _is_mangrove_coastal = any(k in _fname_ctx for k in ["sundarban", "mangrove", "coastal", "tidal", "delta", "estuary"])
    _is_flood_river     = any(k in _fname_ctx for k in ["assam", "brahmaputra", "flood", "inundation", "riverbank", "ganga"])
    _is_desert_arid     = any(k in _fname_ctx for k in ["thar", "rajasthan", "arid", "desert", "barren", "dry"])
    _is_harbor_port     = any(k in _fname_ctx for k in ["visakhapatnam", "vizag", "harbor", "port", "seaport", "naval"])
    _is_solar_energy    = any(k in _fname_ctx for k in ["solar", "photovoltaic", "pv_array", "energy_farm"])
    _is_agricultural    = any(k in _fname_ctx for k in ["cauvery", "thanjavur", "paddy", "crop", "agri", "farm", "field"])
    _is_urban           = any(k in _fname_ctx for k in ["city", "urban", "metro", "chennai", "mumbai", "delhi", "hyderabad"])
    _is_forest          = any(k in _fname_ctx for k in ["forest", "jungle", "reserve", "wildlife", "biosphere"])

    # ── LAYER 2: Pixel-metric combination logic ──────────────────────────────
    # Uses ACTUAL spectral measurements (water_pct, veg_pct, built_pct, fallow_pct)
    # combined with ecology context for correct classification.
    # Priority order: Flood > Coastal-Wetland > Urban > Arid > Forest > Agricultural > Mixed

    if _is_flood_river or (water_pct >= 30.0 and not _is_mangrove_coastal and not _is_harbor_port):
        # ── FLOOD / SEVERE INUNDATION ────────────────────────────────────────"""

if bad_block in content:
    content = content.replace(bad_block, good_block)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed app.py successfully")
else:
    print("Could not find bad block in app.py")
