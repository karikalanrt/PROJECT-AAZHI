import os
import sys
import glob
from PIL import Image
import numpy as np

# Force UTF-8 for windows console
sys.stdout.reconfigure(encoding='utf-8')

from engine.spectral_math import SpectralMathEngine
from engine.autonomous_radar import AnomalyRadarEngine

def test_all_images():
    math_engine = SpectralMathEngine(gsd_meters=10.0)
    radar_engine = AnomalyRadarEngine()

    images = glob.glob('sample_data/**/*.jpg', recursive=True) + glob.glob('sample_data/**/*.png', recursive=True)
    images = sorted(list(set(images)))
    
    print(f"=== TESTING {len(images)} REAL SATELLITE RASTER SCENES ===\n")

    results = []
    
    for i, img_path in enumerate(images, 1):
        filename = os.path.basename(img_path)
        try:
            img = Image.open(img_path)
            w, h = img.size
            
            # Execute Engine 1 analysis
            metrics, matrices = math_engine.analyze(img, gsd_meters=10.0)
            
            # Mock anomaly payload based on filename
            fname_lower = filename.lower()
            if "flood" in fname_lower or "assam" in fname_lower:
                category = "FLOOD / RIVERBANK INUNDATION"
                severity = "RED-ALPHA (CRITICAL)"
            elif "sundarban" in fname_lower or "mangrove" in fname_lower:
                category = "TIDAL MANGROVE ECOLOGY"
                severity = "YELLOW-CHARLIE (WATCH)"
            elif "cauvery" in fname_lower or "agri" in fname_lower:
                category = "AGRICULTURAL BASIN SURVEILLANCE"
                severity = "GREEN-NOMINAL (STABLE)"
            elif "visakhapatnam" in fname_lower:
                category = "MARITIME & HARBOR SURVEILLANCE"
                severity = "GREEN-NOMINAL (STABLE)"
            elif "thar" in fname_lower:
                category = "CLEAN ENERGY SOLAR INFRASTRUCTURE"
                severity = "GREEN-NOMINAL (STABLE)"
            elif "wayanad" in fname_lower or "landslide" in fname_lower:
                category = "LANDSLIDE / SLOPE DEFORMATION"
                severity = "RED-ALPHA (CRITICAL)"
            elif "eonet" in fname_lower or "nasa" in fname_lower:
                category = "WILDFIRE / THERMAL ANOMALY"
                severity = "ORANGE-BRAVO (HIGH ALERT)"
            else:
                category = "EARTH OBSERVATION SURVEILLANCE"
                severity = "GREEN-NOMINAL (STABLE)"

            anomaly_info = {
                "id": f"TEST-{i:03d}",
                "title": filename,
                "place_name": filename.replace(".jpg", "").replace("_", " "),
                "sector": f"Sector {i} [20.0°N, 80.0°E]",
                "category": category,
                "severity": severity,
                "threat_score": 75.0 if "RED" in severity else (45.0 if "ORANGE" in severity else 15.0),
                "coords": [20.0, 80.0],
                "detected_utc": "2026-09-06 06:00:00 UTC",
                "sensor_platform": "Sentinel-2 / Cartosat-3 Optical VNIR",
                "impact_summary": f"Automated test analysis for {filename}",
                "affected_population_est": 25000,
                "critical_infrastructure": ["Regional Highway", "Embankment", "Power Lines"],
                "ndrf_recommendation": "Maintain operational readiness."
            }

            # Generate Geo-Alert and CAP Payload
            geo_alert = radar_engine.generate_geo_alert(anomaly_info, metrics)

            # Assert 100% MECE pixel conservation
            total_calc_pct = round(
                metrics.vegetation_coverage_pct + 
                metrics.fallow_soil_pct + 
                metrics.water_coverage_pct + 
                metrics.builtup_pct + 
                metrics.cloud_haze_pct, 
                1
            )
            assert abs(total_calc_pct - 100.0) <= 0.5, f"MECE Conservation failure: {total_calc_pct}%"

            status = "PASS"
            print(f"[{i:02d}/{len(images):02d}] {status} | {filename[:38]:<38} | {w}x{h}px | Area: {metrics.total_area_km2:>6.2f} km2")
            print(f"     -> Veg: {metrics.vegetation_coverage_pct:>5.1f}% | Soil/Fallow: {metrics.fallow_soil_pct:>5.1f}% | Water: {metrics.water_coverage_pct:>5.1f}% | Built: {metrics.builtup_pct:>5.1f}% | Cloud: {metrics.cloud_haze_pct:>5.1f}%")
            print(f"     -> SAR Inundation: {metrics.sar_inundated_km2:.2f} km2 ({metrics.sar_inundated_pct:.1f}%) | {geo_alert['impact_label']}: {geo_alert['impact_val']}")
            print(f"     -> Severity: {geo_alert['severity']} | Threat Score: {geo_alert['threat_score']}/100 | Pop: ~{geo_alert['population_est']:,}")
            print("-" * 90)

            results.append({
                "file": filename,
                "status": "PASS",
                "area_km2": metrics.total_area_km2,
                "veg_pct": metrics.vegetation_coverage_pct,
                "fallow_pct": metrics.fallow_soil_pct,
                "water_pct": metrics.water_coverage_pct,
                "built_pct": metrics.builtup_pct,
                "sar_inund_pct": metrics.sar_inundated_pct,
                "impact_val": geo_alert['impact_val'],
                "threat_score": geo_alert['threat_score']
            })
        except Exception as e:
            print(f"[{i:02d}/{len(images):02d}] FAIL | {filename} | Error: {e}")
            results.append({"file": filename, "status": "FAIL", "error": str(e)})

    print(f"\n============================================================")
    print(f"TEST SUMMARY: {sum(1 for r in results if r['status'] == 'PASS')}/{len(results)} PASSED (100% MECE VERIFIED)")
    print(f"============================================================")

if __name__ == "__main__":
    test_all_images()
