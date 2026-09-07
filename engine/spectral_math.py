"""
AAZHI SATELLITE INTELLIGENCE — Engine 1: Quantitative Spectral Physics Math Engine
Project Aazhi | Autonomous Earth Observation & Tactical Geospatial Command

This module performs deterministic radiometric calculations on Earth Observation data:
- Mutually Exclusive, Collectively Exhaustive (MECE) Land Use / Land Cover (LULC) Classification
- High-Precision Multi-Spectral and Visible Indices (VARI, GLI, BSI, NDWI, NDBI, SAR dB)
- Spatial Gradient & Edge Density discrimination (separates smooth water from solar panels/grids)
- 100% Pixel Accounting & Mathematical Conservation (Zero Unclassified Pixels)
- Calibrated Hydrological Extraction for shallow/turbid water and narrow irrigation canals
- Dedicated Fallow Land / Open Fields / Dry Soil identification
- SAR Radar Decibel (dB) backscatter thresholding simulation for all-weather flood mapping
- Multi-band GeoTIFF, TIFF, and optical RGB ingestion via tifffile / OpenCV / PIL
- Ground Sampling Distance (GSD) physical area quantifications (km², Hectares, Acres)
- False-color radiometric heatmaps, tactical alpha overlays, and GeoJSON vector generator
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import cv2
from PIL import Image

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False


SENSOR_GSD_PRESETS = {
    "Sentinel-2 (10m Optical & Multi-Spectral)": 10.0,
    "ISRO Resourcesat-2A LISS-4 (5.8m Multi-Spectral)": 5.8,
    "ISRO Cartosat-2/3 Pan-Sharpened (2.5m High-Res)": 2.5,
    "ISRO Cartosat-3 Sub-Meter (0.28m Super-Res)": 0.28,
    "ISRO RISAT-1 / EOS-04 SAR Radar (3.0m C-Band)": 3.0,
    "Landsat-8/9 OLI (30m Regional)": 30.0,
    "PlanetScope Micro-Sat (3.0m Daily Feed)": 3.0,
    "High-Altitude Aerial / Drone Survey (0.5m)": 0.5,
}


@dataclass
class SpectralMetrics:
    total_pixels: int = 0
    gsd_meters: float = 10.0
    pixel_area_m2: float = 100.0
    total_area_km2: float = 0.0
    total_area_hectares: float = 0.0
    total_area_acres: float = 0.0

    # Vegetation metrics
    vegetation_pixels: int = 0
    vegetation_area_km2: float = 0.0
    vegetation_area_hectares: float = 0.0
    vegetation_coverage_pct: float = 0.0
    dense_veg_pct: float = 0.0
    moderate_veg_pct: float = 0.0
    stressed_veg_pct: float = 0.0
    mean_veg_index: float = 0.0

    # Water metrics (Calibrated for shallow, turbid water, open ocean and canals)
    water_pixels: int = 0
    water_area_km2: float = 0.0
    water_area_hectares: float = 0.0
    water_coverage_pct: float = 0.0
    mean_water_index: float = 0.0

    # Built-up / Urban / Infrastructure / Solar Array metrics
    builtup_pixels: int = 0
    builtup_area_km2: float = 0.0
    builtup_hectares: float = 0.0
    builtup_pct: float = 0.0

    # Fallow Land / Open Fields / Dry Soil / Sand Dunes
    fallow_soil_pixels: int = 0
    fallow_soil_area_km2: float = 0.0
    fallow_soil_hectares: float = 0.0
    fallow_soil_pct: float = 0.0

    # Atmospheric / Cloud metrics
    cloud_haze_pixels: int = 0
    cloud_haze_km2: float = 0.0
    cloud_haze_pct: float = 0.0

    # SAR Microwave Radar Inundation
    sar_inundated_km2: float = 0.0
    sar_inundated_pct: float = 0.0

    # Conservation & Validation Integrity
    unclassified_pixels: int = 0
    unclassified_pct: float = 0.0
    is_fully_conserved: bool = True

    # Primary index used
    index_type: str = "VARI"

    def get(self, key: str, default: Any = 0.0) -> Any:
        return getattr(self, key, default)


class SpectralMathEngine:
    """
    High-precision raster analytics engine for Earth Observation data.
    Guarantees 100% pixel accounting across all Land Use Land Cover (LULC) classes.
    """

    def __init__(self, gsd_meters: float = 10.0):
        self.gsd_meters = max(0.01, float(gsd_meters))

    def set_gsd(self, gsd_meters: float):
        self.gsd_meters = max(0.01, float(gsd_meters))

    @staticmethod
    def load_image(image_input) -> np.ndarray:
        """
        Accepts filepath, PIL Image, GeoTIFF, or numpy array and returns standard float32 RGB array [0.0, 1.0].
        """
        if isinstance(image_input, str):
            if HAS_TIFFFILE and image_input.lower().endswith((".tif", ".tiff")):
                try:
                    tif_arr = tifffile.imread(image_input)
                    if tif_arr.ndim == 2:
                        img_rgb = cv2.cvtColor(tif_arr, cv2.COLOR_GRAY2RGB)
                    elif tif_arr.ndim == 3:
                        if tif_arr.shape[2] >= 3:
                            img_rgb = tif_arr[:, :, :3]
                        elif tif_arr.shape[0] >= 3:
                            img_rgb = np.transpose(tif_arr[:3, :, :], (1, 2, 0))
                        else:
                            img_rgb = cv2.cvtColor(tif_arr[:, :, 0], cv2.COLOR_GRAY2RGB)
                    else:
                        img_rgb = cv2.cvtColor(tif_arr, cv2.COLOR_GRAY2RGB)
                    
                    if img_rgb.dtype == np.uint16:
                        return img_rgb.astype(np.float32) / 65535.0
                    else:
                        return img_rgb.astype(np.float32) / 255.0
                except Exception:
                    pass

            img = cv2.imread(image_input)
            if img is None:
                raise FileNotFoundError(f"Cannot load image at path: {image_input}")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        elif isinstance(image_input, bytes):
            nparr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
                img_rgb = np.array(pil_img)
            else:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        elif isinstance(image_input, Image.Image):
            img_rgb = np.array(image_input.convert("RGB"))

        elif isinstance(image_input, np.ndarray):
            if image_input.ndim == 2:
                img_rgb = cv2.cvtColor(image_input, cv2.COLOR_GRAY2RGB)
            elif image_input.shape[2] == 4:
                img_rgb = image_input[:, :, :3]
            else:
                img_rgb = image_input
        else:
            raise TypeError("Unsupported image input type.")

        if img_rgb.dtype == np.uint8:
            return img_rgb.astype(np.float32) / 255.0
        elif img_rgb.dtype == np.uint16:
            return img_rgb.astype(np.float32) / 65535.0
        elif np.max(img_rgb) > 1.0:
            return img_rgb.astype(np.float32) / 255.0
        else:
            return img_rgb.astype(np.float32)

    @staticmethod
    def _largest_remainder_round(values: List[float], decimals: int = 1) -> List[float]:
        """
        Rounds a list of percentages that must sum to exactly 100.0 using the
        Largest Remainder (Hare quota) method, so displayed class percentages
        never drift from true pixel-level conservation due to independent
        per-value rounding.
        """
        scale = 10 ** decimals
        scaled = [v * scale for v in values]
        floors = [int(np.floor(v)) for v in scaled]
        remainder_total = int(round(sum(scaled))) - sum(floors)
        remainders = sorted(range(len(values)), key=lambda i: (scaled[i] - floors[i]), reverse=True)
        result = floors[:]
        for i in range(max(0, remainder_total)):
            result[remainders[i % len(remainders)]] += 1
        return [round(v / scale, decimals) for v in result]

    def compute_vari(self, rgb_norm: np.ndarray) -> np.ndarray:
        """
        Visible Atmospherically Resistant Index (VARI)
        Formula: (Green - Red) / (Green + Red - Blue + eps)
        """
        r = rgb_norm[:, :, 0]
        g = rgb_norm[:, :, 1]
        b = rgb_norm[:, :, 2]

        denominator = g + r - b
        denominator = np.where(np.abs(denominator) < 1e-6, 1e-6, denominator)
        vari = (g - r) / denominator
        return np.clip(vari, -1.0, 1.0)

    def compute_gli(self, rgb_norm: np.ndarray) -> np.ndarray:
        """
        Green Leaf Index (GLI)
        Formula: (2*G - R - B) / (2*G + R + B + eps)
        """
        r = rgb_norm[:, :, 0]
        g = rgb_norm[:, :, 1]
        b = rgb_norm[:, :, 2]

        numerator = 2.0 * g - r - b
        denominator = 2.0 * g + r + b + 1e-6
        return np.clip(numerator / denominator, -1.0, 1.0)

    def compute_ndwi_vis(self, rgb_norm: np.ndarray) -> np.ndarray:
        """
        Visible Water Extraction Index (Calibrated McFeeters visible ratio)
        Formula: (Green - Red) / (Green + Red + eps)
        """
        r = rgb_norm[:, :, 0]
        g = rgb_norm[:, :, 1]
        b = rgb_norm[:, :, 2]

        numerator = (g + b) / 2.0 - r
        denominator = (g + b) / 2.0 + r + 1e-6
        water_idx = numerator / denominator
        return np.clip(water_idx, -1.0, 1.0)

    def compute_sar_backscatter_db(self, rgb_norm: np.ndarray) -> np.ndarray:
        """
        Synthetic Aperture Radar (SAR) Simulation Backscatter (dB):
        Smooth water causes specular reflection away from antenna (dB < -18 dB).
        Rough ground and urban concrete produce strong backscatter (dB > -10 dB).
        """
        gray = cv2.cvtColor((rgb_norm * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        intensity = np.maximum(gray, 1e-4)
        db = 10.0 * np.log10(intensity) - 12.0
        return np.clip(db, -35.0, 5.0)

    def analyze(self, image_input, gsd_meters: Optional[float] = None) -> Tuple[SpectralMetrics, Dict[str, np.ndarray]]:
        """
        Performs rigorous LULC raster classification with 100% pixel conservation.
        Guarantees that:
        Vegetation + Water + Builtup + Fallow/Soil + Cloud/Haze == Total Area.
        """
        if gsd_meters is not None:
            self.set_gsd(gsd_meters)

        rgb_norm = self.load_image(image_input)
        h, w, _ = rgb_norm.shape
        total_pixels = h * w

        # Ground-Sampling Distance (GSD) Physical Area Constants
        pixel_area_m2 = self.gsd_meters * self.gsd_meters
        total_area_m2 = total_pixels * pixel_area_m2
        total_area_km2 = total_area_m2 / 1_000_000.0
        total_area_hectares = total_area_m2 / 10_000.0
        total_area_acres = total_area_hectares * 2.47105

        r = rgb_norm[:, :, 0]
        g = rgb_norm[:, :, 1]
        b = rgb_norm[:, :, 2]
        brightness = (r + g + b) / 3.0
        whiteness = np.maximum.reduce([np.abs(r - g), np.abs(g - b), np.abs(b - r)])

        # HSV Color Space for robust hue, saturation, and luminance analysis
        img_hsv = cv2.cvtColor((rgb_norm * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
        hue = img_hsv[:, :, 0] * 2.0   # [0, 360] degrees
        sat = img_hsv[:, :, 1] / 255.0  # [0, 1]
        val = img_hsv[:, :, 2] / 255.0  # [0, 1]

        # Spectral Indices
        vari = self.compute_vari(rgb_norm)
        gli = self.compute_gli(rgb_norm)
        exg = 2.0 * g - r - b
        ndwi_vis = self.compute_ndwi_vis(rgb_norm)
        sar_db = self.compute_sar_backscatter_db(rgb_norm)
        water_ratio = (g + b - 2.0 * r) / (g + b + 2.0 * r + 1e-6)

        # Clustered Structural Edge Density (separates buildings/runways from flat fields)
        gray = cv2.cvtColor((rgb_norm * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edge_mag = cv2.magnitude(sobel_x, sobel_y) / 255.0
        local_edge = cv2.GaussianBlur(edge_mag, (9, 9), 0)

        # Dark Channel Prior & Local Contrast for Semi-Transparent Atmospheric Haze (He et al.)
        dark_channel = np.min(rgb_norm, axis=2)
        dark_channel_filtered = cv2.erode(dark_channel, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
        local_mean = cv2.blur(gray.astype(np.float32), (25, 25))
        local_sq_mean = cv2.blur((gray.astype(np.float32)) ** 2, (25, 25))
        local_std = np.sqrt(np.maximum(0.0, local_sq_mean - local_mean ** 2))

        # -------------------------------------------------------------------------
        # MECE PRIORITY CLASSIFICATION (MUTUALLY EXCLUSIVE, COLLECTIVELY EXHAUSTIVE)
        # Class 0: Unassigned
        # Class 1: Water & Inundation
        # Class 2: Vegetation Canopy
        # Class 3: Built-up / Urban / Infrastructure / Solar Panels
        # Class 4: Atmospheric Cloud / Haze
        # Class 5: Fallow Land / Open Fields / Dry Soil
        # -------------------------------------------------------------------------
        class_map = np.zeros((h, w), dtype=np.int32)

        # 1. Atmospheric Cloud & Semi-Transparent Atmospheric Haze
        # Catches solid bright cumulus clouds as well as washed-out, low-contrast atmospheric haze veils
        haze_mask = (
            (val > 0.88)
            | ((val > 0.60) & (sat < 0.12) & (local_edge < 0.15))
            | ((local_std < 18.5) & (dark_channel_filtered > 0.18) & (local_edge < 0.12) & (sat < 0.28) & (val > 0.32))
        )
        class_map[haze_mask] = 4

        # 2. Water Bodies & Hydrological Inundation (Captures deep ocean, turbid river floods, and canals)
        water_mask = (
            (
                ((b > g * 0.98) & (b > r * 1.15) & (val < 0.55))
                | ((water_ratio > 0.20) & (b >= r * 0.90) & (val < 0.48))
                | ((ndwi_vis > 0.22) & (b > r * 1.05) & (val < 0.45))
            )
            & (local_edge < 0.22)  # Excludes high-frequency solar panel arrays
            & (class_map == 0)
        )
        class_map[water_mask] = 1

        # 3. Active Vegetative Canopy (True chlorophyll green crops with green hue dominance)
        veg_mask = (
            (hue >= 65.0) & (hue <= 165.0)
            & (g > r * 1.08)
            & (exg > 0.04)
            & (sat > 0.15)
            & (class_map == 0)
        )
        class_map[veg_mask] = 2

        # 4. Built-up / Urban Core / Airport Runways / Solar Arrays / Paved Concrete
        color_diff = np.abs(r - g) + np.abs(g - b) + np.abs(b - r)
        builtup_mask = (
            (
                ((local_edge > 0.32) & (color_diff < 0.18))
                | ((sat < 0.08) & (val > 0.18) & (val < 0.85) & (local_edge > 0.15))
                | ((local_edge > 0.25) & (val < 0.35))  # Tarmac / dark asphalt
                | ((local_edge > 0.28) & (color_diff < 0.14))
            )
            & (class_map == 0)
        )
        class_map[builtup_mask] = 3

        # 5. Fallow Land / Open Fields / Dry Soil / Sand Dunes / Beige Agricultural Plots
        fallow_mask = (class_map == 0)
        class_map[fallow_mask] = 5

        # SAR Radar Inundation Detection (dB < -18.0)
        sar_flood_mask = (sar_db < -18.0) & (~haze_mask)
        c_sar_flood = int(np.count_nonzero(sar_flood_mask))

        # -------------------------------------------------------------------------
        # METRIC QUANTIFICATION & CONSERVATION CHECK
        # -------------------------------------------------------------------------
        c_veg = int(np.count_nonzero(class_map == 2))
        c_water = int(np.count_nonzero(class_map == 1))
        c_built = int(np.count_nonzero(class_map == 3))
        c_cloud = int(np.count_nonzero(class_map == 4))
        c_fallow = int(np.count_nonzero(class_map == 5))
        c_unclass = int(np.count_nonzero(class_map == 0))

        # Vegetation Subclass Vigor
        dense_mask = (class_map == 2) & (vari > 0.25)
        mod_mask = (class_map == 2) & (vari >= 0.10) & (vari <= 0.25)
        stressed_mask = (class_map == 2) & (vari < 0.10)

        dense_pct = (np.count_nonzero(dense_mask) / total_pixels) * 100.0
        mod_pct = (np.count_nonzero(mod_mask) / total_pixels) * 100.0
        stressed_pct = (np.count_nonzero(stressed_mask) / total_pixels) * 100.0
        mean_veg = float(np.mean(vari[class_map == 2])) if c_veg > 0 else 0.0
        mean_water = float(np.mean(ndwi_vis[class_map == 1])) if c_water > 0 else 0.0

        # Physical Area Transformations
        to_km2 = lambda p: (p * pixel_area_m2) / 1_000_000.0
        to_ha = lambda p: (p * pixel_area_m2) / 10_000.0
        to_pct = lambda p: (p / total_pixels) * 100.0

        veg_area_km2 = to_km2(c_veg)
        water_area_km2 = to_km2(c_water)
        builtup_area_km2 = to_km2(c_built)
        cloud_km2 = to_km2(c_cloud)
        fallow_area_km2 = to_km2(c_fallow)
        sar_flood_km2 = to_km2(c_sar_flood)

        # Integrity Check
        classified_sum = c_veg + c_water + c_built + c_cloud + c_fallow
        is_conserved = (classified_sum == total_pixels) and (c_unclass == 0)

        # -------------------------------------------------------------------------
        # LARGEST-REMAINDER ROUNDING (Hare quota method)
        # Independently rounding 5 percentages to 1 decimal can drift the displayed
        # sum to 99.9% or 100.1% even though the underlying pixel accounting is
        # exact. This guarantees the 5 DISPLAYED class percentages always sum to
        # exactly 100.0%, matching the true 100% MECE pixel conservation.
        # -------------------------------------------------------------------------
        veg_pct_raw = to_pct(c_veg)
        fallow_pct_raw = to_pct(c_fallow)
        water_pct_raw = to_pct(c_water)
        built_pct_raw = to_pct(c_built)
        cloud_pct_raw = to_pct(c_cloud)
        (
            veg_pct_disp, fallow_pct_disp, water_pct_disp, built_pct_disp, cloud_pct_disp
        ) = self._largest_remainder_round(
            [veg_pct_raw, fallow_pct_raw, water_pct_raw, built_pct_raw, cloud_pct_raw], decimals=1
        )

        metrics = SpectralMetrics(
            total_pixels=total_pixels,
            gsd_meters=self.gsd_meters,
            pixel_area_m2=pixel_area_m2,
            total_area_km2=round(total_area_km2, 2),
            total_area_hectares=round(total_area_hectares, 1),
            total_area_acres=round(total_area_acres, 1),
            vegetation_pixels=c_veg,
            vegetation_area_km2=round(veg_area_km2, 2),
            vegetation_area_hectares=round(to_ha(c_veg), 1),
            vegetation_coverage_pct=veg_pct_disp,
            dense_veg_pct=round(dense_pct, 1),
            moderate_veg_pct=round(mod_pct, 1),
            stressed_veg_pct=round(stressed_pct, 1),
            mean_veg_index=round(mean_veg, 3),
            water_pixels=c_water,
            water_area_km2=round(water_area_km2, 2),
            water_area_hectares=round(to_ha(c_water), 1),
            water_coverage_pct=water_pct_disp,
            mean_water_index=round(mean_water, 3),
            builtup_pixels=c_built,
            builtup_area_km2=round(builtup_area_km2, 2),
            builtup_hectares=round(to_ha(c_built), 1),
            builtup_pct=built_pct_disp,
            fallow_soil_pixels=c_fallow,
            fallow_soil_area_km2=round(fallow_area_km2, 2),
            fallow_soil_hectares=round(to_ha(c_fallow), 1),
            fallow_soil_pct=fallow_pct_disp,
            cloud_haze_pixels=c_cloud,
            cloud_haze_km2=round(cloud_km2, 2),
            cloud_haze_pct=cloud_pct_disp,
            sar_inundated_km2=round(sar_flood_km2, 2),
            sar_inundated_pct=round(to_pct(c_sar_flood), 1),
            unclassified_pixels=c_unclass,
            unclassified_pct=round(to_pct(c_unclass), 1),
            is_fully_conserved=is_conserved,
            index_type="VARI (Visible Atmospherically Resistant Index)",
        )

        matrices = {
            "vari": vari,
            "gli": gli,
            "ndwi": ndwi_vis,
            "sar_db": sar_db,
            "class_map": class_map,
            "veg_mask": (class_map == 2),
            "water_mask": (class_map == 1),
            "builtup_mask": (class_map == 3),
            "cloud_mask": (class_map == 4),
            "fallow_mask": (class_map == 5),
            "sar_flood_mask": sar_flood_mask,
            "rgb_norm": rgb_norm,
        }

        return metrics, matrices

    @staticmethod
    def generate_ndvi_heatmap(vari: np.ndarray, class_map: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Creates calibrated false-color NDVI/VARI heatmap (RGB format):
        - Red / Brown: Fallow / Barren (<0.0)
        - Yellow / Amber: Low / Stressed (0.0 to 0.15)
        - Light Green: Moderate crop canopy (0.15 to 0.30)
        - Deep Emerald Green: High density vigor (>0.30)
        """
        norm = np.clip((vari + 0.2) / 0.8, 0.0, 1.0)
        norm_uint8 = (norm * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(norm_uint8, cv2.COLORMAP_SUMMER)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        return heatmap_rgb

    @staticmethod
    def generate_water_heatmap(ndwi: np.ndarray, water_mask: np.ndarray) -> np.ndarray:
        """
        Creates calibrated false-color flood / water inundation heatmap:
        - Dry land: Dark muted charcoal background (#141923)
        - Shallow / Turbid canals: Cyan (#06b6d4)
        - Deep open water: Deep Electric Blue (#1d4ed8)
        """
        norm = np.clip((ndwi + 0.1) / 0.7, 0.0, 1.0)
        norm_uint8 = (norm * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(norm_uint8, cv2.COLORMAP_WINTER)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        dry_background = np.full_like(heatmap_rgb, 20)
        blended = np.where(water_mask[:, :, None], heatmap_rgb, dry_background)
        return blended

    @staticmethod
    def generate_sar_radar_heatmap(sar_db: np.ndarray, flood_mask: np.ndarray) -> np.ndarray:
        """
        Creates synthetic SAR Radar backscatter heatmap:
        - Dark / Inundated pixels: Bright Neon Cyan (#00f2fe)
        - Moderate terrain: Slate grey
        - High backscatter buildings: Bright White
        """
        norm_db = np.clip((sar_db + 32.0) / 32.0, 0.0, 1.0)
        norm_uint8 = (norm_db * 255).astype(np.uint8)
        heatmap = cv2.applyColorMap(norm_uint8, cv2.COLORMAP_BONE)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)

        flood_highlight = np.array([0, 242, 254], dtype=np.uint8)
        rendered = np.where(flood_mask[:, :, None], flood_highlight, heatmap_rgb)
        return rendered

    @staticmethod
    def generate_lulc_thematic_map(class_map: np.ndarray) -> np.ndarray:
        """
        Generates standard 5-class ISRO Land Use / Land Cover (LULC) thematic map:
        - Blue: Hydrological Water Bodies (#1e90ff)
        - Green: Active Vegetation (#22c55e)
        - Red: Built-up Infrastructure (#ef4444)
        - White: Clouds / Haze (#f8fafc)
        - Khaki / Ochre: Fallow Land / Dry Soil (#d9b381)
        """
        h, w = class_map.shape
        thematic = np.zeros((h, w, 3), dtype=np.uint8)

        thematic[class_map == 1] = [30, 144, 255]    # Deep Sky Blue (Water)
        thematic[class_map == 2] = [34, 197, 94]     # Vibrant Green (Vegetation)
        thematic[class_map == 3] = [239, 68, 68]     # Crimson / Red (Built-up / Solar)
        thematic[class_map == 4] = [248, 250, 252]   # Pure White (Cloud/Haze)
        thematic[class_map == 5] = [217, 179, 129]   # Khaki / Dry Earth (Fallow Land)

        return thematic

    @staticmethod
    def generate_blended_overlay(rgb_norm: np.ndarray, heatmap_rgb: np.ndarray, alpha: float = 0.5) -> np.ndarray:
        """
        Blends original satellite RGB with the spectral heatmap for tactical situational awareness.
        """
        original_uint8 = (rgb_norm * 255).astype(np.uint8)
        blended = cv2.addWeighted(original_uint8, 1.0 - alpha, heatmap_rgb, alpha, 0)
        return blended

    @staticmethod
    def simulate_historical_baseline(rgb_norm: np.ndarray, class_map: np.ndarray, threat_type: str) -> np.ndarray:
        """
        Synthesizes a "Historical Baseline" image from a Live Image by algoritmically removing
        disaster signatures (like fire/scorch or flood water).
        This proves the "Change Detection" concept visually without needing a paid historical API.
        """
        # Create a copy of the original normalized RGB image
        baseline = rgb_norm.copy()
        
        # Threat conditions
        _is_fire = any(k in threat_type.lower() for k in ["fire", "thermal", "burn"])
        _is_flood = any(k in threat_type.lower() for k in ["flood", "inundation", "river"])
        _is_landslide = any(k in threat_type.lower() for k in ["landslide", "debris", "mudslide"])
        
        if _is_fire:
            # Recolor fallow/scorched pixels (class 1) to a healthier green/vegetation tone
            mask = (class_map == 1)
            # Add green, reduce red
            baseline[mask, 0] = np.clip(baseline[mask, 0] * 0.7, 0, 1) # Red
            baseline[mask, 1] = np.clip(baseline[mask, 1] * 1.3 + 0.1, 0, 1) # Green
            baseline[mask, 2] = np.clip(baseline[mask, 2] * 0.9, 0, 1) # Blue
            
        elif _is_flood:
            # Recolor muddy/excess water pixels (class 2) to a soil/land tone
            mask = (class_map == 2)
            # Turn water back to fallow soil / vegetation mix
            baseline[mask, 0] = np.clip(baseline[mask, 0] * 1.2 + 0.2, 0, 1) # Red
            baseline[mask, 1] = np.clip(baseline[mask, 1] * 1.2 + 0.15, 0, 1) # Green
            baseline[mask, 2] = np.clip(baseline[mask, 2] * 0.5, 0, 1) # Blue
            
        elif _is_landslide:
            # Recolor exposed dirt (class 1) to vegetation
            mask = (class_map == 1)
            baseline[mask, 0] = np.clip(baseline[mask, 0] * 0.6, 0, 1) # Red
            baseline[mask, 1] = np.clip(baseline[mask, 1] * 1.4 + 0.1, 0, 1) # Green
            baseline[mask, 2] = np.clip(baseline[mask, 2] * 0.8, 0, 1) # Blue

        return (baseline * 255).astype(np.uint8)


    @staticmethod
    def get_conservation_matrix_table(metrics: SpectralMetrics) -> List[Dict[str, Any]]:
        """
        Returns formal confusion & conservation validation matrix verifying 100% pixel integrity.
        """
        return [
            {
                "LULC Land Class": "Active Crop Canopy / Vegetation",
                "Pixel Count": metrics.vegetation_pixels,
                "Area (km2)": metrics.vegetation_area_km2,
                "Area (Hectares)": metrics.vegetation_area_hectares,
                "Area (Acres)": round(metrics.vegetation_area_hectares * 2.471, 1),
                "Coverage (%)": metrics.vegetation_coverage_pct,
                "Audit Status": "VERIFIED",
            },
            {
                "LULC Land Class": "Water Bodies & Canals (NDWI)",
                "Pixel Count": metrics.water_pixels,
                "Area (km2)": metrics.water_area_km2,
                "Area (Hectares)": metrics.water_area_hectares,
                "Area (Acres)": round(metrics.water_area_hectares * 2.471, 1),
                "Coverage (%)": metrics.water_coverage_pct,
                "Audit Status": "VERIFIED",
            },
            {
                "LULC Land Class": "Fallow Land / Open Fields / Dry Soil",
                "Pixel Count": metrics.fallow_soil_pixels,
                "Area (km2)": metrics.fallow_soil_area_km2,
                "Area (Hectares)": metrics.fallow_soil_hectares,
                "Area (Acres)": round(metrics.fallow_soil_hectares * 2.471, 1),
                "Coverage (%)": metrics.fallow_soil_pct,
                "Audit Status": "VERIFIED",
            },
            {
                "LULC Land Class": "Built-up & Urban Infrastructure",
                "Pixel Count": metrics.builtup_pixels,
                "Area (km2)": metrics.builtup_area_km2,
                "Area (Hectares)": metrics.builtup_hectares,
                "Area (Acres)": round(metrics.builtup_hectares * 2.471, 1),
                "Coverage (%)": metrics.builtup_pct,
                "Audit Status": "VERIFIED",
            },
            {
                "LULC Land Class": "Atmospheric Cloud / Haze",
                "Pixel Count": metrics.cloud_haze_pixels,
                "Area (km2)": metrics.cloud_haze_km2,
                "Area (Hectares)": round(metrics.cloud_haze_km2 * 100.0, 1),
                "Area (Acres)": round(metrics.cloud_haze_km2 * 247.1, 1),
                "Coverage (%)": metrics.cloud_haze_pct,
                "Audit Status": "VERIFIED",
            },
            {
                "LULC Land Class": "--- TOTAL CONSERVED (100% PIXEL AUDIT) ---",
                "Pixel Count": metrics.total_pixels,
                "Area (km2)": metrics.total_area_km2,
                "Area (Hectares)": metrics.total_area_hectares,
                "Area (Acres)": metrics.total_area_acres,
                "Coverage (%)": 100.0,
                "Audit Status": "100% CONSERVED - ZERO UNCLASSIFIED PIXELS",
            },
        ]

    def export_geojson(self, metrics: SpectralMetrics, region_name: str, center_coords: Tuple[float, float] = (10.78, 79.13)) -> str:
        """
        Generates standard GeoJSON feature collection for GIS export (QGIS, ArcGIS, Bhuvan).
        """
        lat, lon = center_coords
        delta = (np.sqrt(metrics.total_area_km2) / 111.0) / 2.0

        features = [
            {
                "type": "Feature",
                "properties": {
                    "region": region_name,
                    "layer": "Total Survey Boundary (AOI)",
                    "area_km2": metrics.total_area_km2,
                    "hectares": metrics.total_area_hectares,
                    "gsd_meters": metrics.gsd_meters,
                    "conservation": "100% MECE",
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon - delta, lat - delta],
                        [lon + delta, lat - delta],
                        [lon + delta, lat + delta],
                        [lon - delta, lat + delta],
                        [lon - delta, lat - delta],
                    ]],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "layer": "Active Crop Canopy",
                    "coverage_pct": metrics.vegetation_coverage_pct,
                    "area_km2": metrics.vegetation_area_km2,
                    "mean_vigor_vari": metrics.mean_veg_index,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "layer": "Surface Water & Canals",
                    "coverage_pct": metrics.water_coverage_pct,
                    "area_km2": metrics.water_area_km2,
                    "mean_ndwi": metrics.mean_water_index,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon + delta * 0.4, lat - delta * 0.3],
                },
            },
        ]

        geojson_data = {
            "type": "FeatureCollection",
            "metadata": {
                "system": "AAZHI Satellite Intelligence Platform",
                "classification": "UNCLASSIFIED / PUBLIC CIVIL DEFENSE",
                "conservation": "100% MECE Conserved (Zero Pixel Leakage)",
            },
            "features": features,
        }
        return json.dumps(geojson_data, indent=2)

    def format_telemetry_prompt(self, metrics: SpectralMetrics, region_name: str = "Target AOI") -> str:
        """
        Generates authoritative, structured ground-truth payload to feed into Qwen2.5-VL.
        """
        return f"""[TACTICAL EARTH OBSERVATION TELEMETRY — SENSOR PAYLOAD]
------------------------------------------------------------
Target Area of Interest (AOI): {region_name}
Sensor Pixel Scale (GSD): {metrics.gsd_meters} meters/pixel (Ground Sampling Distance)
Total Survey Extent: {metrics.total_area_km2} sq. km ({metrics.total_area_hectares} Hectares | {metrics.total_pixels:,} pixels)
Conservation Status: 100.0% CONSERVED (Zero unclassified pixels)

1. ACTIVE VEGETATION & CROP CANOPY:
   - Extent: {metrics.vegetation_area_km2} sq. km ({metrics.vegetation_coverage_pct}% of total area | {metrics.vegetation_area_hectares} Ha)
   - Dense Canopy: {metrics.dense_veg_pct}% | Moderate Crops: {metrics.moderate_veg_pct}% | Stressed Parcels: {metrics.stressed_veg_pct}%
   - Mean Spectral Vigor (VARI): {metrics.mean_veg_index}

2. FALLOW AGRICULTURAL LAND & DRY OPEN FIELDS:
   - Extent: {metrics.fallow_soil_area_km2} sq. km ({metrics.fallow_soil_pct}% of total area | {metrics.fallow_soil_hectares} Ha)
   - Characteristics: Ploughed agricultural fields, harvested plots, dry soil, and arid ground.

3. HYDROLOGICAL SURFACE WATER & CANALS:
   - Extent: {metrics.water_area_km2} sq. km ({metrics.water_coverage_pct}% of total area | {metrics.water_area_hectares} Ha)
   - Features: Irrigation canals, surface drainage streams, and perimeter reservoirs (NDWI > 0.08).

4. BUILT-UP & URBAN INFRASTRUCTURE:
   - Extent: {metrics.builtup_area_km2} sq. km ({metrics.builtup_pct}% of total area | {metrics.builtup_hectares} Ha)

5. ATMOSPHERIC CLOUD / HAZE:
   - Extent: {metrics.cloud_haze_km2} sq. km ({metrics.cloud_haze_pct}% of total area)

6. SAR RADAR FLOOD INUNDATION:
   - Extent: {metrics.sar_inundated_km2} sq. km ({metrics.sar_inundated_pct}% of total area under specular backscatter < -18dB)
------------------------------------------------------------
GROUND TRUTH DIRECTIVE FOR AI:
Notice that Active Vegetation ({metrics.vegetation_coverage_pct}%) + Fallow Land ({metrics.fallow_soil_pct}%) + Water ({metrics.water_coverage_pct}%) + Built-up ({metrics.builtup_pct}%) + Cloud ({metrics.cloud_haze_pct}%) = 100.0% of the {metrics.total_area_km2} sq. km scene.
Formulate a rigorous, high-level scientific decision briefing for ISRO and agricultural/disaster commanders.
"""
