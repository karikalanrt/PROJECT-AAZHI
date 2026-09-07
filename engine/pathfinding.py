import numpy as np
import heapq
import time
from typing import List, Tuple, Optional

class PathfindingEngine:
    def __init__(self, gsd_meters: float = 10.0):
        """
        Initializes the A* pathfinding engine.
        """
        self.gsd_meters = gsd_meters
        self.cost_map = None
        self.height = 0
        self.width = 0

    def update_gsd(self, gsd_meters: float):
        self.gsd_meters = gsd_meters

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        # Weighted Euclidean distance heuristic for faster A* convergence
        return np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) * 5.0

    def _get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        r, c = pos
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width:
                    # Allow all valid grid cells, rely on penalty to route around obstacles
                    # If absolutely impassable is needed, we could check for value >= 100
                    if self.cost_map[nr, nc] < 10.0:
                        neighbors.append((nr, nc))
        return neighbors

    def geo_to_pixel(self, lat: float, lon: float, shape: Tuple[int, int], center_lat: float, center_lon: float) -> Tuple[int, int]:
        h, w = shape
        lat_meters_per_deg = 111320.0
        lon_meters_per_deg = 111320.0 * np.cos(np.radians(center_lat))
        
        d_lat = lat - center_lat
        d_lon = lon - center_lon
        
        d_y_meters = d_lat * lat_meters_per_deg
        d_x_meters = d_lon * lon_meters_per_deg
        
        d_row = -d_y_meters / self.gsd_meters
        d_col = d_x_meters / self.gsd_meters
        
        r = int(h / 2.0 + d_row)
        c = int(w / 2.0 + d_col)
        return (np.clip(r, 0, h-1), np.clip(c, 0, w-1))

    def pixel_to_geo(self, r: int, c: int, shape: Tuple[int, int], center_lat: float, center_lon: float) -> Tuple[float, float]:
        h, w = shape
        lat_meters_per_deg = 111320.0
        lon_meters_per_deg = 111320.0 * np.cos(np.radians(center_lat))
        
        d_row = r - h / 2.0
        d_col = c - w / 2.0
        
        d_y_meters = -d_row * self.gsd_meters
        d_x_meters = d_col * self.gsd_meters
        
        d_lat = d_y_meters / lat_meters_per_deg
        d_lon = d_x_meters / lon_meters_per_deg
        
        return (center_lat + d_lat, center_lon + d_lon)

    def find_path(self, class_map: np.ndarray, start_geo: Tuple[float, float], end_geo: Tuple[float, float], center_geo: Tuple[float, float], timeout_sec: float = 10.0) -> Tuple[Optional[List[Tuple[int, int]]], np.ndarray]:
        cost_map = np.zeros(class_map.shape, dtype=np.float32)
        cost_map[class_map == 1] = 1.0
        cost_map[class_map == 3] = 0.3
        cost_map[class_map == 4] = 0.0
        cost_map[class_map == 2] = 0.0
        cost_map[class_map == 5] = 0.0
        
        try:
            import cv2
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            cost_map = cv2.dilate(cost_map, kernel, iterations=1)
        except ImportError:
            pass
            
        self.cost_map = cost_map
        self.height, self.width = cost_map.shape
        
        start_px = self.geo_to_pixel(start_geo[0], start_geo[1], class_map.shape, center_geo[0], center_geo[1])
        goal_px = self.geo_to_pixel(end_geo[0], end_geo[1], class_map.shape, center_geo[0], center_geo[1])
        
        start_time = time.time()
        open_set = []
        heapq.heappush(open_set, (0.0, 0, start_px))
        came_from = {}
        g_score = {start_px: 0.0}
        f_score = {start_px: self._heuristic(start_px, goal_px)}
        count = 0
        
        while open_set:
            if time.time() - start_time > timeout_sec:
                return None, cost_map
                
            current_f, _, current = heapq.heappop(open_set)
            
            if current == goal_px:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_px)
                return path[::-1], cost_map
                
            for neighbor in self._get_neighbors(current):
                dr = current[0] - neighbor[0]
                dc = current[1] - neighbor[1]
                dist = np.sqrt(dr**2 + dc**2)
                
                # Penalty 5.0 encourages routing around obstacles but doesn't get stuck forever
                penalty = self.cost_map[neighbor] * 5.0
                tentative_g_score = g_score[current] + dist + penalty
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal_px)
                    count += 1
                    heapq.heappush(open_set, (f_score[neighbor], count, neighbor))
                    
        return None, cost_map
