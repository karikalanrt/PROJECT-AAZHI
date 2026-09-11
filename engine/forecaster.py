"""
AAZHI SATELLITE INTELLIGENCE — Engine 6: Predictive Disaster Spread Forecasting
Project Aazhi | Autonomous Earth Observation & Tactical Geospatial Command

This module performs Cellular Automata (CA) simulations to predict the spread
of natural disasters (Floods, Wildfires) across the terrain over time, based on
Land Use / Land Cover (LULC) classifications.
"""

from typing import Optional, Tuple
import numpy as np
import cv2


class DisasterForecaster:
    """
    Cellular Automata terrain-coupled disaster spread simulation engine.
    Calculates spatial expansion vectors across LULC classes.
    """

    def __init__(self, class_map: np.ndarray):
        """
        Initializes the forecaster with the base LULC class map.
        class_map: 2D numpy array of uint8 where classes are:
            1: Water / Inundation
            2: Active Vegetation Canopy
            3: Built-up Infrastructure
            4: Cloud / Haze (Neutral)
            5: Fallow / Dry Bare Soil
        """
        self.base_map = class_map
        self.height, self.width = class_map.shape

    def simulate_flood(self, time_steps: int) -> np.ndarray:
        """
        Simulates flood spread starting from existing water (class 1).
        Water expands easily into Fallow Soil (5), moderately into Vegetation (2),
        and is blocked by Built-up barriers (3).
        """
        # 0 = safe, 1 = inundated
        inundation_map = np.where(self.base_map == 1, 1, 0).astype(np.uint8)
        current_map = inundation_map.copy()

        # Each time_step (hour) performs iterative morphological cellular dilation
        for _ in range(max(1, time_steps * 2)):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated = cv2.dilate(current_map, kernel, iterations=1)

            # Find newly flooded candidates
            new_flood = dilated - current_map

            # Apply terrain resistance rules
            allowable = np.zeros_like(new_flood)
            allowable[self.base_map == 5] = 1  # Unimpeded spread on bare / fallow soil
            allowable[self.base_map == 1] = 1  # Water surface

            # Vegetation resistance (50% permeability)
            veg_mask = (self.base_map == 2)
            rand_mask = np.random.rand(self.height, self.width) > 0.5
            allowable[veg_mask & rand_mask] = 1

            actual_new_flood = new_flood * allowable
            current_map = current_map | actual_new_flood

        return current_map

    def simulate_wildfire(self, time_steps: int, origin: Optional[Tuple[int, int]] = None) -> np.ndarray:
        """
        Simulates wildfire spread across combustible fuel types.
        Fire propagates rapidly through dry Fallow (5) and Vegetation (2),
        and is blocked by Water (1) and Built-up concrete (3).
        """
        fire_map = np.zeros_like(self.base_map, dtype=np.uint8)

        if origin is None:
            # Seed fire cluster in vegetation zone
            veg_y, veg_x = np.where(self.base_map == 2)
            if len(veg_y) > 100:
                idx = np.random.randint(len(veg_y))
                cy, cx = veg_y[idx], veg_x[idx]
                y1, y2 = max(0, cy - 2), min(self.height, cy + 3)
                x1, x2 = max(0, cx - 2), min(self.width, cx + 3)
                fire_map[y1:y2, x1:x2] = 1
        else:
            y, x = origin
            if 0 <= y < self.height and 0 <= x < self.width:
                y1, y2 = max(0, y - 2), min(self.height, y + 3)
                x1, x2 = max(0, x - 2), min(self.width, x + 3)
                fire_map[y1:y2, x1:x2] = 1

        current_map = fire_map.copy()

        for _ in range(max(1, time_steps * 2)):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            dilated = cv2.dilate(current_map, kernel, iterations=1)
            new_fire = dilated - current_map

            allowable = np.zeros_like(new_fire)
            allowable[self.base_map == 5] = 1  # Spreads on dry fallow soil
            allowable[self.base_map == 2] = 1  # Spreads through vegetation fuel

            # Low ember jumping chance over built-up areas (5%)
            builtup_mask = (self.base_map == 3)
            rand_mask = np.random.rand(self.height, self.width) > 0.95
            allowable[builtup_mask & rand_mask] = 1

            actual_new_fire = new_fire * allowable
            current_map = current_map | actual_new_fire

        return current_map

    def generate_heatmap_overlay(self, spread_mask: np.ndarray, disaster_type: str) -> np.ndarray:
        """
        Converts the binary spread mask into an RGBA tactical map overlay for Leaflet / Folium.
        disaster_type: 'flood' or 'fire'
        """
        overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)

        if disaster_type.lower() == 'flood':
            color = [0, 242, 254]  # Cyan / Electric Blue
        else:
            color = [255, 69, 0]   # Fire Orange-Red

        overlay[spread_mask == 1] = [*color, 180]  # 70% Alpha channel
        return overlay

