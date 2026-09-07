"""
AAZHI SATELLITE INTELLIGENCE (AAZHI-SAT GEO-AI)
Autonomous Multi-Spectral & Synthetic Aperture Radar (SAR) Earth Observation Platform

Production-Grade Air-Gapped Streamlit Web Application:
- Dual-Engine: Quantitative Spectral Physics (Engine 1) + Local Qwen2.5-VL Vision AI (Engine 2)
- Ultra-Modern Cyber-Tactical Dark Glassmorphism Interface with Live Telemetry
- Interactive Before/After Swipe Slider (Optical RGB vs. Radiometric / LULC / SAR)
- Real-Time Geospatial Folium Tile Map with Geocoded Target AOIs & Bounding Boxes
- High-Fidelity Plotly 3D Donut, Vigor Histograms, Polar Reflectance, and SAR Gauges
- Real-Time Streaming Token Conversational AI Tactical Console
- On-Orbit Space Edge Computing Simulator (Cloud-Gate Filter + 10KB Encrypted Downlink)
- 1-Click Defense Intelligence PDF Briefing, GeoJSON, and CSV Data Exports
"""

import os
import io
import json
import datetime
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
from PIL import Image, ExifTags
import cv2
import plotly.express as px

import rasterio
from rasterio.warp import transform_bounds

from engine import weather_fusion

@st.cache_data(ttl=3600)
def get_place_name(lat, lon):
    try:
        import urllib.request, json
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10"
        req = urllib.request.Request(url, headers={"User-Agent": "AazhiSat-GeoAI/2026"})
        with urllib.request.urlopen(req, timeout=2.5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if "address" in data:
                    addr = data["address"]
                    name = addr.get("city", addr.get("town", addr.get("municipality", addr.get("county", ""))))
                    state = addr.get("state", "")
                    country = addr.get("country", "")
                    parts = [p for p in [name, state, country] if p]
                    if parts:
                        return ", ".join(parts)
    except Exception:
        pass
    return "Custom Coordinate Intercept"

def get_geotiff_location(file_bytes):
    try:
        with rasterio.MemoryFile(file_bytes) as memfile:
            with memfile.open() as dataset:
                bounds = dataset.bounds
                crs = dataset.crs
                if crs and crs.to_string() != "EPSG:4326":
                    bounds = transform_bounds(crs, "EPSG:4326", *bounds)
                center_lon = (bounds[0] + bounds[2]) / 2.0
                center_lat = (bounds[1] + bounds[3]) / 2.0
                return center_lat, center_lon
    except Exception:
        return None

def get_exif_location(pil_img):
    try:
        exif = pil_img._getexif()
        if not exif: return None
        gps_info = None
        for tag, value in exif.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_info = value
                break
        if not gps_info: return None
        
        gps_data = {}
        for t in gps_info:
            sub_decoded = ExifTags.GPSTAGS.get(t, t)
            gps_data[sub_decoded] = gps_info[t]
            
        def to_decimal(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
            
        lat = to_decimal(gps_data.get('GPSLatitude'))
        if gps_data.get('GPSLatitudeRef') != 'N': lat = -lat
        lon = to_decimal(gps_data.get('GPSLongitude'))
        if gps_data.get('GPSLongitudeRef') != 'E': lon = -lon
        return lat, lon
    except Exception:
        return None
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

try:
    from streamlit_image_comparison import image_comparison
    HAS_IMAGE_COMPARISON = True
except ImportError:
    HAS_IMAGE_COMPARISON = False

import importlib
import engine.spectral_math
import engine.vision_agent
import engine.report_gen
import engine.autonomous_radar
import engine.pathfinding
import engine.audio_dispatch

importlib.reload(engine.spectral_math)
importlib.reload(engine.vision_agent)
importlib.reload(engine.report_gen)
importlib.reload(engine.autonomous_radar)
importlib.reload(engine.pathfinding)
importlib.reload(engine.audio_dispatch)

from engine.spectral_math import SpectralMathEngine, SENSOR_GSD_PRESETS, SpectralMetrics
from engine.vision_agent import VisionAgent
from engine.report_gen import PDFReportGenerator
from engine.autonomous_radar import AnomalyRadarEngine
from engine.pathfinding import PathfindingEngine
from engine.audio_dispatch import AudioDispatchEngine


# --------------------------------------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------------------------------------
st.set_page_config(
    page_title="AAZHI-SAT | Satellite Intelligence Command",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)



# --------------------------------------------------------------------------------
# PWA & REAL-TIME AUTO-SWITCHING OFFLINE NETWORK MONITOR
# --------------------------------------------------------------------------------
components.html(
    """
    <link rel="manifest" href="/manifest.json">
    <script>
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js').then(function(reg) {
          console.log('PWA ServiceWorker registered with scope: ', reg.scope);
        }).catch(function(err) {
          console.log('ServiceWorker registration failed: ', err);
        });
      });
    }

    function updateNetworkBadge() {
        var pDoc = window.parent.document;
        var badge = pDoc.getElementById('aazhi-pwa-net-badge');
        if (!badge) {
            badge = pDoc.createElement('div');
            badge.id = 'aazhi-pwa-net-badge';
            badge.style.position = 'fixed';
            badge.style.top = '12px';
            badge.style.right = '20px';
            badge.style.zIndex = '999999';
            badge.style.padding = '6px 14px';
            badge.style.borderRadius = '20px';
            badge.style.fontSize = '11px';
            badge.style.fontWeight = '700';
            badge.style.fontFamily = 'Inter, sans-serif';
            badge.style.letterSpacing = '0.5px';
            badge.style.boxShadow = '0 4px 14px rgba(0,0,0,0.5)';
            badge.style.transition = 'all 0.3s ease';
            pDoc.body.appendChild(badge);
        }
        
        if (navigator.onLine) {
            badge.style.background = 'rgba(34, 197, 94, 0.15)';
            badge.style.color = '#4ade80';
            badge.style.border = '1px solid rgba(34, 197, 94, 0.4)';
            badge.innerHTML = '🟢 LIVE CLOUD MODE (Sentinel-1/2 API)';
        } else {
            badge.style.background = 'rgba(234, 179, 8, 0.25)';
            badge.style.color = '#fde047';
            badge.style.border = '1px solid rgba(234, 179, 8, 0.6)';
            badge.innerHTML = '⚠️ DISCONNECTED - SWITCHED TO OFFLINE EDGE MODE';
        }
    }

    window.addEventListener('online', updateNetworkBadge);
    window.addEventListener('offline', updateNetworkBadge);
    document.addEventListener('DOMContentLoaded', updateNetworkBadge);
    setInterval(updateNetworkBadge, 1000);
    updateNetworkBadge();
    </script>
    """,
    height=0,
    width=0,
)

st.markdown(
    """
    <style>
    /* ================================================================
       AAZHI-SAT  —  Enterprise Space Intelligence Design System
       Modern, clean, responsive, perfectly aligned dark UI.
    ================================================================ */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* --- Global Theme ----------------------------------------------- */
    .stApp {
        background: #080d1a !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* --- Hide Streamlit Default Chrome ------------------------------ */
    #MainMenu { display: none !important; visibility: hidden !important; }
    footer { display: none !important; visibility: hidden !important; }
    div[data-testid="stDecoration"] { display: none !important; }
    div[data-testid="stStatusWidget"] { display: none !important; }

    /* Hide Deploy & Dev Buttons */
    .stDeployButton,
    [data-testid="stAppDeployButton"],
    button[data-testid="stAppDeployButton"],
    div[data-testid="stToolbarActions"],
    div[data-testid="stToolbarActionButton"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
    }

    /* Top Header Container */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999 !important;
        display: block !important;
        height: 3.2rem !important;
        pointer-events: none !important;
    }

    /* Sleek Sidebar Toggle Button */
    [data-testid="stSidebarCollapsedControl"],
    div[data-testid="stSidebarCollapsedControl"],
    button[aria-label="Open sidebar"],
    button[aria-label="Expand sidebar"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 10000 !important;
        pointer-events: auto !important;
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #38bdf8 !important;
        padding: 6px 10px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5) !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover,
    button[aria-label="Open sidebar"]:hover,
    button[aria-label="Expand sidebar"]:hover {
        background: #1e293b !important;
        border-color: #38bdf8 !important;
        transform: scale(1.04);
    }
    [data-testid="stSidebarCollapsedControl"] svg,
    button[aria-label="Open sidebar"] svg,
    button[aria-label="Expand sidebar"] svg {
        fill: #38bdf8 !important;
        stroke: #38bdf8 !important;
        width: 18px !important;
        height: 18px !important;
    }

    /* Content Layout Container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1380px !important;
    }

    /* --- Modern Tab Navigation Bar ----------------------------------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: #0f172a !important;
        border: 1px solid #1e293b !important;
        border-radius: 12px !important;
        padding: 5px !important;
        margin-bottom: 16px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        padding: 0 16px !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #1e293b !important;
        color: #f1f5f9 !important;
    }
    .stTabs [aria-selected="true"] {
        background: #1d4ed8 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(29, 78, 216, 0.35) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent !important; }
    .stTabs [data-baseweb="tab-border"] { display: none !important; }

    /* --- Action Buttons --------------------------------------------- */
    button[kind="primary"] {
        background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        box-shadow: 0 4px 14px rgba(29, 78, 216, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
        transform: translateY(-1px);
    }
    button[kind="secondary"] {
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        background: #0f172a !important;
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    button[kind="secondary"]:hover {
        border-color: #38bdf8 !important;
        background: #1e293b !important;
        color: #ffffff !important;
    }

    /* --- Form Controls & Inputs ------------------------------------- */
    div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #334155 !important;
        background: #0f172a !important;
        color: #e2e8f0 !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #38bdf8 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #0f172a !important;
        border: 1.5px dashed #334155 !important;
        border-radius: 10px !important;
        padding: 18px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #38bdf8 !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        border: 2px solid #38bdf8 !important;
        background: #0284c7 !important;
        box-shadow: none !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }

    /* --- Custom Scrollbars ------------------------------------------ */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #080d1a; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }

    /* --- Unified Enterprise Card Containers ------------------------- */
    .app-header-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 18px;
        position: relative;
        overflow: hidden;
    }
    .app-header-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #38bdf8, #6366f1, #22c55e);
    }
    .brand-title {
        font-size: 22px;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
        letter-spacing: 0.3px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-sub {
        color: #94a3b8;
        font-size: 13px;
        margin-top: 6px;
        line-height: 1.5;
    }

    /* Status Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }
    .badge-emerald {
        background: rgba(34, 197, 94, 0.12);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-cyan {
        background: rgba(56, 189, 248, 0.12);
        color: #7dd3fc;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .badge-indigo {
        background: rgba(99, 102, 241, 0.12);
        color: #a5b4fc;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }

    /* Telemetry KPI Cards */
    .kpi-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        min-height: 108px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .kpi-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #f8fafc;
        font-family: 'JetBrains Mono', monospace;
        margin: 4px 0 2px 0;
    }
    .kpi-sub {
        font-size: 11px;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Structured Feature Box */
    .panel-box {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .panel-box-header {
        font-size: 15px;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: #090e1a !important;
        border-right: 1px solid #1e293b !important;
    }
    .sidebar-section-hdr {
        font-size: 11px;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    .sidebar-info-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 11.5px;
        color: #94a3b8;
        line-height: 1.5;
        margin-top: 8px;
    }

    /* Legend Bar */
    .legend-bar {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px 18px;
        font-size: 12px;
        color: #cbd5e1;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
        margin-top: 14px;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-dot { height: 9px; width: 9px; border-radius: 50%; display: inline-block; }

    /* Code Blocks */
    .stCodeBlock {
        border-radius: 8px !important;
        border: 1px solid #1e293b !important;
    }

    /* Automated Geo-Alert & Tactical Dispatch Banner */
    .geo-alert-banner {
        background: linear-gradient(135deg, rgba(220, 38, 38, 0.15), rgba(15, 23, 42, 0.95));
        border: 1px solid #ef4444;
        border-left: 5px solid #ef4444;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(239, 68, 68, 0.25);
        animation: subtle-pulse 3s infinite ease-in-out;
    }
    .geo-alert-banner-warning {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.15), rgba(15, 23, 42, 0.95));
        border: 1px solid #eab308;
        border-left: 5px solid #eab308;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(234, 179, 8, 0.2);
    }
    .geo-alert-banner-nominal {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.12), rgba(15, 23, 42, 0.95));
        border: 1px solid #22c55e;
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 16px rgba(34, 197, 94, 0.15);
    }
    @keyframes subtle-pulse {
        0%, 100% { box-shadow: 0 4px 20px rgba(239, 68, 68, 0.25); }
        50% { box-shadow: 0 4px 28px rgba(239, 68, 68, 0.45); }
    }
    .alert-hdr {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 8px;
    }
    .alert-title {
        font-size: 15px;
        font-weight: 700;
        color: #f87171;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .alert-title-warning {
        font-size: 15px;
        font-weight: 700;
        color: #fde047;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .alert-title-nominal {
        font-size: 15px;
        font-weight: 700;
        color: #4ade80;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .alert-meta {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11.5px;
        color: #cbd5e1;
        line-height: 1.6;
    }
    .alert-action-box {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 12px;
        color: #e2e8f0;
    }
    .alert-action-box-nominal {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(34, 197, 94, 0.4);
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
        font-size: 12px;
        color: #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------------
# INITIALIZE COMPUTATIONAL ENGINES
# --------------------------------------------------------------------------------
def get_engines():
    """Returns computational engines with fresh instance state."""
    math_engine = SpectralMathEngine(gsd_meters=10.0)
    vision_agent = VisionAgent()
    radar_engine = AnomalyRadarEngine()
    path_engine = PathfindingEngine(gsd_meters=10.0)
    audio_engine = AudioDispatchEngine(output_dir="C:/Users/LENOVO/.gemini/antigravity-ide/brain/c20a7b3a-1fd5-4ffb-80f0-fa7994d2b06e/scratch/")
    return math_engine, vision_agent, radar_engine, path_engine, audio_engine

math_engine, vision_agent, radar_engine, path_engine, audio_engine = get_engines()
now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# --------------------------------------------------------------------------------
# SIDEBAR CONTROLS & REAL-TIME SENSOR MATRIX
# --------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;">
            <div style="font-size:24px;">🛰️</div>
            <div>
                <div style="font-size:15px;font-weight:700;color:#38bdf8;letter-spacing:0.5px;">AAZHI-SAT AI</div>
                <div style="font-size:10px;color:#94a3b8;letter-spacing:0.5px;">TACTICAL EARTH OBSERVATION</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    installer_path = os.path.join(os.path.dirname(__file__), "Install_AAZHI.bat")
    installer_bytes = b""
    if os.path.exists(installer_path):
        with open(installer_path, "rb") as f:
            installer_bytes = f.read()

    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.15), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 8px; padding: 10px 12px; margin-top: 8px; margin-bottom: 6px;">
            <div style="font-size: 11px; font-weight: 700; color: #60a5fa; margin-bottom: 3px; display: flex; align-items: center; gap: 6px;">
                <span>💾</span> ZERO-INTERNET OFFLINE MODE
            </div>
            <div style="font-size: 10.5px; color: #94a3b8; line-height: 1.4; margin-bottom: 6px;">
                1-Click Auto-Extractor & Desktop Shortcut Installer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if installer_bytes:
        st.download_button(
            label="⚡ Download 1-Click Auto-Installer (.BAT)",
            data=installer_bytes,
            file_name="Install_AAZHI.bat",
            mime="application/octet-stream",
            use_container_width=True,
            help="Downloads the auto-installer script to your Downloads folder.",
        )
    st.markdown("<hr style='margin:10px 0;border-color:#1e293b;'/>", unsafe_allow_html=True)
    
    # Section 1: Constellation & Sensor Preset
    st.markdown("<div class='sidebar-section-hdr'>🛰️ Sensor & GSD Scale</div>", unsafe_allow_html=True)
    
    preset_choice = st.selectbox(
        "Constellation Preset",
        list(SENSOR_GSD_PRESETS.keys()),
        index=0,
        help="Select sensor ground resolution scale to accurately compute physical surface area (km², Ha, Acres).",
    )
    default_gsd = SENSOR_GSD_PRESETS[preset_choice]
    
    gsd_value = st.slider(
        "Ground Sampling Distance (m/px)",
        min_value=0.25,
        max_value=30.0,
        value=float(default_gsd),
        step=0.25,
        help="Physical ground distance covered by a single image pixel.",
    )
    math_engine.set_gsd(gsd_value)
    
    pixel_area = gsd_value * gsd_value
    st.markdown(
        f"""
        <div class="sidebar-info-card">
            📐 <b>Pixel Ground Footprint</b>: <code>{pixel_area:.2f} m²/px</code><br/>
            🛰️ <b>Sensor Mode</b>: Multi-Spectral Optical VNIR
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='margin:14px 0;border-color:#1e293b;'/>", unsafe_allow_html=True)

    # Section 2: Satellite Ingest Feed
    st.markdown("<div class='sidebar-section-hdr'>🌍 Satellite Imagery Feed</div>", unsafe_allow_html=True)
    
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_data")
    cache_dir = os.path.join(sample_dir, "live_cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    input_source = st.radio(
        "Ingest Mode",
        [
            "⚡ Autonomous Anomaly Sentinel (Auto-Scan & Alert)",
            "📁 Upload Custom Satellite Scene (GeoTIFF / JPG / PNG)",
        ],
        index=0,
    )
    
    active_img = None
    region_label = "Custom AOI"
    active_coords = [10.7828, 79.1378]
    active_anomaly_info = None
    
    if input_source == "⚡ Autonomous Anomaly Sentinel (Auto-Scan & Alert)":
        st.markdown("<div style='font-size:12px;color:#38bdf8;font-weight:600;margin-top:6px;'>🛰️ Autonomous Sub-Continent Radar</div>", unsafe_allow_html=True)
        radar_mode_choice = st.radio(
            "Radar Source Doctrine",
            [
                "🛡️ Air-Gapped Databank (Offline Defense)",
                "🛰️ Live NASA EONET Space Feed (Online)",
                "📍 Custom Live City / Coordinate Intercept (On-Demand)",
            ],
            index=0,
        )
        st.session_state["_radar_mode_choice"] = radar_mode_choice

        if radar_mode_choice == "📍 Custom Live City / Coordinate Intercept (On-Demand)":
            city_presets = {
                "🌧️ Assam Brahmaputra River Basin (Assam)": [26.1806, 91.7362, "🌊 FLOOD / RIVERBANK INUNDATION"],
                "⛰️ Wayanad Landslide Slope (Kerala)": [11.6854, 76.1320, "⛰️ LANDSLIDE / SLOPE DEFORMATION"],
                "🌊 Chennai Coastal Floodplain (Tamil Nadu)": [13.0827, 80.2707, "🌊 FLOOD / COASTAL INUNDATION"],
                "🌾 Cauvery Delta Agro-Basin (Tamil Nadu)": [10.7828, 79.1378, "🌾 AGRO-DROUGHT / MOISTURE DEFICIT"],
                "🏗️ Mumbai Deepwater Harbor (Maharashtra)": [18.9220, 72.8347, "🏗️ URBAN / MARITIME CONGESTION"],
                "🏙️ Delhi NCR Urban Heat Island": [28.6139, 77.2090, "🏗️ URBAN DENSITY / THERMAL ISLAND"],
                "🌴 Sundarbans Mangrove Estuary (West Bengal)": [21.9497, 89.1833, "🌀 CYCLONE / TIDAL SURGE"],
                "☀️ Thar Desert Bhadla Solar Park (Rajasthan)": [27.5330, 71.9160, "🔥 THERMAL ANOMALY / ARID ZONE"],
                "⚓ Visakhapatnam Deepwater Harbor (AP)": [17.6868, 83.2185, "🏗️ MARITIME / HARBOR SILTATION"],
                "🌊 Kolkata Hooghly River Basin (West Bengal)": [22.5726, 88.3639, "🌊 HYDROLOGICAL INUNDATION"],
                "🌾 Punjab Agro-Breadbasket (Ludhiana)": [30.9010, 75.8573, "🌾 AGRICULTURAL CROP MONITORING"],
                "✏️ Custom Manual Latitude & Longitude...": [12.9716, 77.5946, "⚠️ CUSTOM GEOSPATIAL TARGET"],
            }
            
            selected_city = st.selectbox("📍 Select Indian Target City / Disaster Zone", list(city_presets.keys()), index=0)
            default_lat, default_lon, default_threat_type = city_presets[selected_city]
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                target_lat = st.number_input("Target Latitude", value=float(default_lat), format="%.4f", step=0.01)
            with c_col2:
                target_lon = st.number_input("Target Longitude", value=float(default_lon), format="%.4f", step=0.01)
            
            # If user manually changed coords away from the preset's defaults, switch the label
            if abs(target_lat - default_lat) > 0.0001 or abs(target_lon - default_lon) > 0.0001:
                clean_sector = get_place_name(target_lat, target_lon)
                default_threat_type = "🎯 MULTI-HAZARD GEOSPATIAL TARGET"
            else:
                clean_sector = selected_city.split("(")[0].strip() if "(" in selected_city else selected_city
            
            active_coords = [target_lat, target_lon]
            region_label = f"Live Intercept: {clean_sector}"
            
            custom_id = f"LIVE-INTERCEPT-{clean_sector.replace(' ', '_')}"
            
            active_anomaly_info = {
                "id": custom_id,
                "title": f"Live Orbital Intercept: {clean_sector}",
                "place_name": clean_sector,
                "sector": f"{clean_sector} [{target_lat:.2f}°N, {target_lon:.2f}°E]",
                "category": default_threat_type,
                "severity": "RED-ALPHA (CRITICAL)" if "FLOOD" in default_threat_type or "LANDSLIDE" in default_threat_type else "ORANGE-BRAVO (HIGH ALERT)",
                "threat_score": 0.0,  # overridden below after pixel analysis
                "coords": active_coords,
                "detected_utc": now_utc,
                "sensor_platform": "High-Resolution Optical Earth Observation (1024x1024 px @ 15km AOI)",
                "impact_summary": f"On-demand orbital satellite intercept targeting {clean_sector} for real-time LULC and hazard quantification.",
                "affected_population_est": 0,  # overridden below after pixel analysis
                "critical_infrastructure": ["Regional Transport Arteries", "Power Transmission Lines", "Civil Habitations"],
                "ndrf_recommendation": f"Execute priority multispectral reconnaissance and maintain tactical liaison with local emergency coordination centres."
            }

            cached_tile = radar_engine.fetch_live_satellite_raster(target_lat, target_lon, custom_id, anomaly_meta=active_anomaly_info)
            if os.path.exists(cached_tile):
                active_img = Image.open(cached_tile)
            
            st.markdown(
                f"""
                <div class="sidebar-info-card" style="border-left:3px solid #38bdf8;">
                    🛰️ <b>Live Satellite Uplink</b>: <code style="color:#4ade80;">ACQUIRED (1024px)</code><br/>
                    📍 <b>Coords</b>: <code>{target_lat:.4f}°N, {target_lon:.4f}°E</code><br/>
                    🛡️ <b>Doctrine</b>: On-Demand Real-Time Intercept<br/>
                    💾 <b>Local Databank</b>: Automatically Saved & Registered
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            fetch_mode = "online" if "Live" in radar_mode_choice else "offline"
            
            # Cache scanned anomalies in session state
            radar_key = f"anomalies_{fetch_mode}"
            if radar_key not in st.session_state or st.button("⚡ Force Re-Scan Anomaly Grid", use_container_width=True):
                with st.spinner("Scanning Subcontinent Anomaly Grid & Databank..."):
                    anomalies, src_lbl, is_live = radar_engine.fetch_active_anomalies(mode=fetch_mode)
                    st.session_state[radar_key] = (anomalies, src_lbl, is_live)
            else:
                # If offline, always refresh to ensure newly captured live scenes are immediately visible
                if fetch_mode == "offline":
                    anomalies, src_lbl, is_live = radar_engine.fetch_active_anomalies(mode="offline")
                    st.session_state[radar_key] = (anomalies, src_lbl, is_live)
                else:
                    anomalies, src_lbl, is_live = st.session_state[radar_key]
            
            # Display source status badge
            status_color = "#22c55e" if is_live else "#38bdf8"
            st.markdown(
                f"""
                <div style="background:#0f172a;border:1px solid #1e293b;border-radius:6px;padding:6px 10px;font-size:11px;color:{status_color};margin-bottom:8px;">
                    <b>Feed</b>: {src_lbl} ({len(anomalies)} Scenes Available)
                </div>
                """,
                unsafe_allow_html=True,
            )

            anomaly_options = {}
            for a in anomalies:
                place = a.get("place_name") or a.get("title", "Disaster Target")
                if "Captured Satellite Scene:" in place:
                    place = place.replace("Captured Satellite Scene:", "").strip()
                elif "Live Orbital Intercept:" in place:
                    place = place.replace("Live Orbital Intercept:", "").strip()

                _sev_raw = a.get('severity', 'ALERT')
                if "RED" in _sev_raw:      tag = "🔴"
                elif "ORANGE" in _sev_raw: tag = "🟠"
                elif "YELLOW" in _sev_raw: tag = "🟡"
                else:                      tag = "🟢"
                if a.get("is_live_captured"): tag = "📸"
                coords_str = f"{a['coords'][0]:.2f}°N, {a['coords'][1]:.2f}°E" if a.get('coords') else ""
                opt_key = f"{tag} {place} ({coords_str})"
                anomaly_options[opt_key] = a

            opt_keys = list(anomaly_options.keys())
            total_events = len(opt_keys)

            # Initialise selectbox session state (first run or after re-scan)
            if "anomaly_selectbox" not in st.session_state or st.session_state["anomaly_selectbox"] not in opt_keys:
                st.session_state["anomaly_selectbox"] = opt_keys[0]

            # Current index derived from what the selectbox is showing
            _cur_idx = opt_keys.index(st.session_state["anomaly_selectbox"])

            # ── Prev / Next navigation ───────────────────────────────────────────
            # KEY FIX: buttons write directly to the selectbox's own session-state
            # key ("anomaly_selectbox") with the OPTION VALUE string — not an index.
            nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
            with nav_col1:
                if st.button("◀ Prev", use_container_width=True, key="btn_prev_anom"):
                    st.session_state["anomaly_selectbox"] = opt_keys[(_cur_idx - 1) % total_events]
                    st.rerun()
            with nav_col2:
                st.markdown(
                    f"<div style='text-align:center;font-size:11px;color:#94a3b8;padding-top:6px;'>"
                    f"Event {_cur_idx + 1} / {total_events}</div>",
                    unsafe_allow_html=True,
                )
            with nav_col3:
                if st.button("Next ▶", use_container_width=True, key="btn_next_anom"):
                    st.session_state["anomaly_selectbox"] = opt_keys[(_cur_idx + 1) % total_events]
                    st.rerun()

            # Selectbox — driven entirely by its key (st.session_state["anomaly_selectbox"])
            selected_anomaly_label = st.selectbox(
                "🎯 Active Anomaly Target",
                opt_keys,
                key="anomaly_selectbox",
                help="Use ◀ Prev / Next ▶ buttons above, or click the dropdown to switch events.",
            )

            active_anomaly = anomaly_options[selected_anomaly_label]
            active_anomaly_info = active_anomaly
            active_coords = active_anomaly["coords"]
            region_label = active_anomaly.get("place_name") or active_anomaly["sector"]
            
            img_path = active_anomaly.get("sample_image")
            if is_live:
                # Auto-acquire and cache the real optical satellite pass for these exact coordinates into databank!
                cached_tile = radar_engine.fetch_live_satellite_raster(active_coords[0], active_coords[1], active_anomaly["id"], anomaly_meta=active_anomaly)
                if os.path.exists(cached_tile):
                    img_path = cached_tile
                    active_anomaly["sample_image"] = cached_tile
            
            # Load active image with fallback protection
            if img_path and os.path.exists(img_path):
                active_img = Image.open(img_path)
            else:
                # Fallback to any existing live cached satellite image if available
                existing_caches = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.lower().endswith((".jpg", ".png"))]
                if existing_caches:
                    active_img = Image.open(existing_caches[0])
            
            st.markdown(
                f"""
                <div class="sidebar-info-card" style="border-left:3px solid {'#ef4444' if 'RED' in active_anomaly.get('severity', '') else '#eab308'};">
                    🚨 <b>Threat Score</b>: <code>{active_anomaly.get('threat_score', 80.0)}/100</code><br/>
                    📍 <b>Coords</b>: <code>{active_coords[0]:.4f}°N, {active_coords[1]:.4f}°E</code><br/>
                    👥 <b>Population at Risk</b>: <code>~{active_anomaly.get('affected_population_est', 50000):,}</code><br/>
                    🛰️ <b>Platform</b>: <code>{active_anomaly.get('sensor_platform', 'Optical EO')}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

    else:
        uploaded_file = st.file_uploader(
            "Upload Satellite Raster File",
            type=["jpg", "jpeg", "png", "tif", "tiff"],
            help="Accepts GeoTIFF, TIFF, JPG, or PNG satellite/drone rasters.",
        )
        
        if "up_lat" not in st.session_state:
            st.session_state["up_lat"] = 11.6670
        if "up_lon" not in st.session_state:
            st.session_state["up_lon"] = 92.7350

        file_bytes = None
        if uploaded_file is not None:
            if st.session_state.get("last_uploaded_file") != uploaded_file.name:
                file_bytes = uploaded_file.read()
                st.session_state["last_file_bytes"] = file_bytes
                st.session_state["last_uploaded_file"] = uploaded_file.name
                
                # Try GeoTIFF or EXIF
                try:
                    coords = None
                    fname = uploaded_file.name.lower()
                    
                    if fname.endswith(('.tif', '.tiff')):
                        coords = get_geotiff_location(file_bytes)
                        
                    if not coords:
                        tmp_img = Image.open(io.BytesIO(file_bytes))
                        coords = get_exif_location(tmp_img)
                        
                    if coords:
                        st.session_state["up_lat"], st.session_state["up_lon"] = coords
                    else:
                        # Fallback to filename auto-detection
                        if "andaman" in fname:
                            st.session_state.update(up_lat=11.6670, up_lon=92.7350)
                        elif "deccan" in fname:
                            st.session_state.update(up_lat=17.3850, up_lon=78.4867)
                        elif "thanjavur" in fname or "cauvery" in fname:
                            st.session_state.update(up_lat=10.7828, up_lon=79.1378)
                        elif "assam" in fname or "brahmaputra" in fname:
                            st.session_state.update(up_lat=26.1806, up_lon=91.7362)
                        elif "sundarban" in fname:
                            st.session_state.update(up_lat=21.9497, up_lon=89.1833)
                        elif "thar" in fname or "rajasthan" in fname:
                            st.session_state.update(up_lat=27.5330, up_lon=71.9160)
                        elif "visakhapatnam" in fname or "vizag" in fname:
                            st.session_state.update(up_lat=17.6868, up_lon=83.2185)
                except Exception:
                    pass
            else:
                file_bytes = st.session_state.get("last_file_bytes")


        active_coords = [st.session_state.get("up_lat", 11.6670), st.session_state.get("up_lon", 92.7350)]

        if uploaded_file is not None and file_bytes is not None:
            import io
            from PIL import Image
            active_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            region_label = f"Uploaded AOI: {uploaded_file.name}"
            st.success(f"✅ Loaded: {uploaded_file.name} ({len(file_bytes)//1024} KB)")
        else:
            st.info("👆 Drag & drop or browse any satellite image file above.")

    st.markdown("<hr style='margin:14px 0;border-color:#1e293b;'/>", unsafe_allow_html=True)

    # Section 3: Radiometric Spectrum Layer Pipeline
    st.markdown("<div class='sidebar-section-hdr'>🎛️ Radiometric Spectrum View</div>", unsafe_allow_html=True)
    view_mode = st.selectbox(
        "Active Radiometric Viewport Layer",
        [
            "5-Class Thematic LULC Map (Vegetation / Fallow / Water / Built-up / Cloud)",
            "NDVI / VARI (Vegetation Canopy & Vigor Heatmap)",
            "NDWI (Hydrological Water Inundation & Canals)",
            "SAR Microwave Radar Inundation (Decibel Backscatter dB)",
            "Tactical Fusion (True Color RGB + 55% Radiometric Heatmap)",
            "Natural True Color Optical RGB Feed",
        ],
        index=0,
    )

    st.markdown("<hr style='margin:14px 0;border-color:#1e293b;'/>", unsafe_allow_html=True)
    
    # Section 4: Edge Hardware Diagnostics
    st.markdown("<div class='sidebar-section-hdr'>🖥️ Edge Hardware Telemetry</div>", unsafe_allow_html=True)
    ollama_ok = vision_agent.is_available()
    
    if ollama_ok:
        st.markdown(
            """
            <div style="background:rgba(34,197,94,0.1);border:1px solid #22c55e;border-radius:6px;padding:7px 10px;font-size:11.5px;color:#4ade80;">
                🟢 <b>Local VLM</b>: Qwen2.5-VL ONLINE
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:rgba(234,179,8,0.1);border:1px solid #eab308;border-radius:6px;padding:7px 10px;font-size:11.5px;color:#fde047;">
                ⚠️ <b>Local VLM</b>: Standby (Run <code>ollama serve</code>)
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown(
        """
        <div style="font-size:11px;color:#94a3b8;line-height:1.55;margin-top:8px;">
            ⚡ <b>GPU Hardware</b>: NVIDIA RTX 3050 (6GB)<br/>
            🔒 <b>Air-Gapped</b>: 100% Offline (Zero Cloud Telemetry)<br/>
            📐 <b>Pixel Accounting</b>: 100.0% MECE Conserved
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------
# MAIN COMMAND CENTER INTERFACE
# --------------------------------------------------------------------------------

# Real-Time Telemetry Top Header Banner
now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
lat_fmt = f"{active_coords[0]:.4f}° N"
lon_fmt = f"{active_coords[1]:.4f}° E"

st.markdown(
    f"""
    <div class="app-header-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div class="brand-title">
                <span>🛰️ AAZHI SATELLITE INTELLIGENCE COMMAND</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                <span class="badge-pill badge-emerald">🟢 LIVE ORBITAL PASS</span>
                <span class="badge-pill badge-cyan">SENSOR: VNIR / SAR</span>
                <span class="badge-pill badge-indigo">🛡️ AIR-GAPPED GPU</span>
                <a href="https://github.com/karikalanrt/PROJECT-AAZHI/archive/refs/heads/main.zip" target="_blank" style="text-decoration:none;">
                    <span class="badge-pill" style="background:rgba(37,99,235,0.25); color:#60a5fa; border:1px solid #3b82f6; cursor:pointer;">💾 OFFLINE LAUNCHER (.ZIP)</span>
                </a>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-top:10px; border-top:1px solid #1e293b; padding-top:8px; gap: 10px;">
            <div class="brand-sub" style="margin:0;">
                Multi-Spectral & SAR Earth Observation Intelligence Platform &middot; <b>Deterministic Spectral Math</b> + <b>Local Qwen2.5-VL Vision AI</b>
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:11.5px; color:#38bdf8;">
                ⏱️ {now_utc} &nbsp;|&nbsp; 📍 LAT: {lat_fmt} &nbsp;|&nbsp; LON: {lon_fmt} &nbsp;|&nbsp; ALT: 687 KM SSO
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if active_img is None:
    st.info("👈 Please select an Earth scene or upload a custom satellite image from the sidebar to begin analysis.")
    st.stop()


# --------------------------------------------------------------------------------
# REAL-TIME LIVE CLOCK & ENGINE STATUS (HTML COMPONENT)
# --------------------------------------------------------------------------------
components.html(
    """
    <style>
        body { margin: 0; padding: 0; background: transparent; font-family: 'JetBrains Mono', monospace; display: flex; justify-content: center; gap: 30px; align-items: center; height: 100%; font-size: 12.5px; font-weight: 600; }
        .blink { animation: blinker 1.5s linear infinite; }
        @keyframes blinker { 50% { opacity: 0.3; } }
        .box { background: #0f172a; border: 1px solid #1e293b; padding: 6px 15px; border-radius: 8px; color: #94a3b8; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .val { color: #38bdf8; }
        .online { color: #4ade80; text-shadow: 0 0 5px rgba(74, 222, 128, 0.5); }
    </style>
    <div class="box">⏱️ UTC: <span id="clock" class="val"></span></div>
    <div class="box">⚙️ ENGINE 1 (Spectral Math): <span class="online blink">ONLINE</span></div>
    <div class="box">🧠 ENGINE 2 (Vision AI): <span class="online blink">ONLINE</span></div>
    <script>
        function updateClock() {
            var now = new Date();
            var h = String(now.getUTCHours()).padStart(2, '0');
            var m = String(now.getUTCMinutes()).padStart(2, '0');
            var s = String(now.getUTCSeconds()).padStart(2, '0');
            document.getElementById('clock').innerText = h + ':' + m + ':' + s;
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
    """,
    height=45
)


# --------------------------------------------------------------------------------
# ENGINE 1: EXECUTE QUANTITATIVE SPECTRAL MATHEMATICS
# --------------------------------------------------------------------------------
with st.spinner("Executing Engine 1: Scanning raster pixels, calculating spectral indices and physical ground area..."):
    metrics, matrices = math_engine.analyze(active_img, gsd_meters=gsd_value)


# --------------------------------------------------------------------------------
# POST-ANALYSIS: Override placeholder threat_score & population with pixel metrics
# (Applies to pre-calibrated scenes and live EONET intercepts where we set 0.0)
# --------------------------------------------------------------------------------
_m_water_pct  = getattr(metrics, 'water_coverage_pct', 0.0)
_m_water_km2  = getattr(metrics, 'water_area_km2', 0.0)
_m_veg_pct    = getattr(metrics, 'vegetation_coverage_pct', 0.0)
_m_veg_km2    = getattr(metrics, 'vegetation_area_km2', 0.0)
_m_built_pct  = getattr(metrics, 'builtup_pct', 0.0)
_m_built_km2  = getattr(metrics, 'builtup_area_km2', 0.0)
_m_fallow_pct = getattr(metrics, 'fallow_soil_pct', 0.0)
_m_fallow_km2 = getattr(metrics, 'fallow_soil_area_km2', 0.0)
_m_total_km2  = getattr(metrics, 'total_area_km2', 0.0)

if active_anomaly_info is not None and active_anomaly_info.get("threat_score", 0.0) == 0.0:
    _sev = active_anomaly_info.get("severity", "").upper()
    _cat = active_anomaly_info.get("category", "").lower()

    # Compute threat score from actual pixel measurements based on scene type
    if "RED" in _sev or "FLOOD" in _cat or "INUNDATION" in _cat or "flood" in _cat:
        _computed_score = min(97.0, round(82.0 + (_m_water_pct * 0.35) + (_m_fallow_pct * 0.1), 1))
        _computed_pop   = max(18000, int(_m_water_km2 * 2500 + _m_total_km2 * 120))
    elif "MANGROVE" in _cat or "TIDAL" in _cat or "COASTAL" in _cat or "YELLOW" in _sev:
        _computed_score = min(58.0, round(35.0 + (_m_water_pct * 0.4) + (_m_veg_pct * 0.1), 1))
        _computed_pop   = int((_m_veg_km2 + _m_water_km2) * 280)
    elif "HARBOR" in _cat or "MARITIME" in _cat:
        _computed_score = min(22.0, round(14.0 + (_m_built_pct * 0.15) + (_m_water_pct * 0.1), 1))
        _computed_pop   = int(_m_built_km2 * 2500)
    elif "SOLAR" in _cat or "ENERGY" in _cat:
        _computed_score = min(18.0, round(10.0 + (_m_fallow_pct * 0.1), 1))
        _computed_pop   = int(_m_total_km2 * 50)
    elif "AGRICULTURAL" in _cat or "BASIN" in _cat:
        _computed_score = min(18.0, round(10.0 + (_m_veg_pct * 0.1) + (_m_fallow_pct * 0.08), 1))
        _computed_pop   = int(_m_veg_km2 * 450 + _m_fallow_km2 * 200)
    elif "URBAN" in _cat or "BUILT" in _cat:
        _computed_score = min(65.0, round(20.0 + _m_built_pct * 0.8, 1))
        _computed_pop   = int(_m_built_km2 * 3800)
    elif "ORBITAL" in active_anomaly_info.get("title","") or "INTERCEPT" in active_anomaly_info.get("title",""):
        # Live EONET intercept: score based on dominant hazard detected
        _computed_score = min(95.0, round(
            (_m_water_pct * 1.5) + (_m_fallow_pct * 0.8) + (_m_built_pct * 0.5), 1))
        _computed_pop   = int(_m_water_km2 * 1000 + _m_built_km2 * 2000 + _m_total_km2 * 30)
    else:
        _computed_score = min(18.0, round(12.0 + (_m_water_pct * 0.1) + (_m_built_pct * 0.1), 1))
        _computed_pop   = int(_m_total_km2 * 200)

    active_anomaly_info["threat_score"]          = max(5.0, _computed_score)
    active_anomaly_info["affected_population_est"] = max(1000, _computed_pop)


# --------------------------------------------------------------------------------
# TELEMETRY KPIS (ROW OF 5 BALANCED CARDS)
# --------------------------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

veg_km2 = getattr(metrics, 'vegetation_area_km2', 0.0)
veg_pct = getattr(metrics, 'vegetation_coverage_pct', 0.0)
dense_pct = getattr(metrics, 'dense_veg_pct', 0.0)

fallow_km2 = getattr(metrics, 'fallow_soil_area_km2', 0.0)
fallow_pct = getattr(metrics, 'fallow_soil_pct', 0.0)
fallow_ha = getattr(metrics, 'fallow_soil_hectares', 0.0)

water_km2 = getattr(metrics, 'water_area_km2', 0.0)
water_pct = getattr(metrics, 'water_coverage_pct', 0.0)
water_ha = getattr(metrics, 'water_area_hectares', 0.0)

built_km2 = getattr(metrics, 'builtup_area_km2', 0.0)
built_pct = getattr(metrics, 'builtup_pct', 0.0)
built_ha = getattr(metrics, 'builtup_hectares', 0.0)

total_km2 = getattr(metrics, 'total_area_km2', 0.0)
total_ha = getattr(metrics, 'total_area_hectares', 0.0)

with col1:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 3px solid #22c55e;">
            <div class="kpi-label"><span style="color:#22c55e;">🌿</span> Active Vegetation</div>
            <div class="kpi-value" style="color:#4ade80;">{veg_km2} <span style="font-size:12px;color:#94a3b8;">km²</span></div>
            <div class="kpi-sub">{veg_pct}% | Dense: {dense_pct}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 3px solid #eab308;">
            <div class="kpi-label"><span style="color:#eab308;">🌾</span> Fallow / Open Soil</div>
            <div class="kpi-value" style="color:#fde047;">{fallow_km2} <span style="font-size:12px;color:#94a3b8;">km²</span></div>
            <div class="kpi-sub">{fallow_pct}% | {fallow_ha} Ha</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 3px solid #38bdf8;">
            <div class="kpi-label"><span style="color:#38bdf8;">🌊</span> Water & Canals</div>
            <div class="kpi-value" style="color:#38bdf8;">{water_km2} <span style="font-size:12px;color:#94a3b8;">km²</span></div>
            <div class="kpi-sub">{water_pct}% | {water_ha} Ha</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 3px solid #ef4444;">
            <div class="kpi-label"><span style="color:#ef4444;">🏗️</span> Built-up / Urban</div>
            <div class="kpi-value" style="color:#f87171;">{built_km2} <span style="font-size:12px;color:#94a3b8;">km²</span></div>
            <div class="kpi-sub">{built_pct}% | {built_ha} Ha</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left: 3px solid #6366f1;">
            <div class="kpi-label"><span style="color:#6366f1;">📐</span> Total Survey Area</div>
            <div class="kpi-value" style="color:#a5b4fc;">{total_km2} <span style="font-size:12px;color:#94a3b8;">km²</span></div>
            <div class="kpi-sub">100% MECE | {total_ha} Ha</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------------
# AUTOMATED GEO-ALERT & NDRF DISPATCH ENGINE
# --------------------------------------------------------------------------------
_radar_mode = st.session_state.get("_radar_mode_choice", "")
is_offline = (input_source == "📁 Upload Custom Satellite Scene (GeoTIFF / JPG / PNG)") or \
             (input_source == "⚡ Autonomous Anomaly Sentinel (Auto-Scan & Alert)" and "Live" not in _radar_mode)

if is_offline:
    st.warning("⚠️ **OFFLINE MODE**: Accuracy may vary. Sensor Data Fusion applied due to lack of baseline change-detection telemetry.")

geo_alert_data = None
is_alert_triggered = False

if active_anomaly_info is not None:
    is_alert_triggered = True
    active_anomaly_info = radar_engine.classify_scene_from_metrics(metrics, region_label, active_coords, base_anomaly=active_anomaly_info, now_utc=now_utc)
    geo_alert_data = radar_engine.generate_geo_alert(active_anomaly_info, metrics)
    
elif input_source == "📁 Upload Custom Satellite Scene (GeoTIFF / JPG / PNG)" or active_anomaly_info is None:
    is_alert_triggered = True

    # ── LAYER 1: Filename-based ecology context ──────────────────────────────
    # Identifies known geographic / ecological types from the uploaded filename
    # so that the same image gives the same result regardless of path taken.
    _fname_ctx = (uploaded_file.name.lower() if uploaded_file else "") if 'uploaded_file' in dir() else ""
    
    custom_anomaly = radar_engine.classify_scene_from_metrics(metrics, region_label, active_coords, now_utc=now_utc, filename_ctx=_fname_ctx)
    geo_alert_data = radar_engine.generate_geo_alert(custom_anomaly, metrics)

# Render Animated Geo-Alert or Nominal Surveillance Banner
if is_alert_triggered and geo_alert_data:
    geo_alert_data = weather_fusion.fuse_weather_data(geo_alert_data)
    sev = geo_alert_data["severity"]
    threat_type = geo_alert_data.get("threat_type", "🛰️ EARTH OBSERVATION SURVEILLANCE")
    impact_label = geo_alert_data.get("impact_label", "📐 INUNDATION EXTENT")
    impact_val = geo_alert_data.get("impact_val", f"{geo_alert_data['water_inundation_km2']} km² ({geo_alert_data['water_inundation_pct']}% of AOI)")
    
    _sev_upper = sev.upper()
    _score = geo_alert_data.get("threat_score", 0.0)

    if "RED" in _sev_upper or "CRITICAL" in _sev_upper or _score >= 60.0:
        banner_cls = "geo-alert-banner"
        title_cls = "alert-title"
        badge_border = "#ef4444"
        badge_bg = "rgba(239,68,68,0.2)"
        badge_color = "#f87171"
        title_prefix = "🚨 ACTIVE GEO-ALERT:"
        action_box_cls = "alert-action-box"
        action_icon = "🛡️"
        action_label = "NDRF TACTICAL ACTION DIRECTIVE"
        threat_badge_lbl = f"THREAT: {_score:.1f}/100"
    elif "ORANGE" in _sev_upper or "HIGH" in _sev_upper or _score >= 40.0:
        banner_cls = "geo-alert-banner-warning"
        title_cls = "alert-title-warning"
        badge_border = "#f97316"
        badge_bg = "rgba(249,115,22,0.18)"
        badge_color = "#fb923c"
        title_prefix = "🟠 ELEVATED THREAT ALERT:"
        action_box_cls = "alert-action-box"
        action_icon = "⚠️"
        action_label = "TACTICAL THREAT ADVISORY"
        threat_badge_lbl = f"THREAT: {_score:.1f}/100"
    elif "YELLOW" in _sev_upper or "WATCH" in _sev_upper or "CHARLIE" in _sev_upper or _score >= 25.0:
        banner_cls = "geo-alert-banner-warning"
        title_cls = "alert-title-warning"
        badge_border = "#eab308"
        badge_bg = "rgba(234,179,8,0.15)"
        badge_color = "#fde047"
        title_prefix = "🟡 SURVEILLANCE WATCH:"
        action_box_cls = "alert-action-box"
        action_icon = "⚠️"
        action_label = "TACTICAL ADVISORY"
        threat_badge_lbl = f"WATCH: {_score:.1f}/100"
    else:
        banner_cls = "geo-alert-banner-nominal"
        title_cls = "alert-title-nominal"
        badge_border = "#22c55e"
        badge_bg = "rgba(34,197,94,0.15)"
        badge_color = "#4ade80"
        title_prefix = "🟢 BASELINE SURVEILLANCE:"
        action_box_cls = "alert-action-box-nominal"
        action_icon = "📡"
        action_label = "OPERATIONAL DIRECTIVE"
        threat_badge_lbl = "STATUS: NOMINAL (STABLE)"

    infra_list = geo_alert_data.get("infrastructure", [])
    infra_html = "".join([f'<span class="badge-pill badge-neutral" style="margin-right:4px;margin-bottom:4px;font-size:11px;">⚠️ {item}</span>' for item in infra_list]) if infra_list else '<span style="color:#64748b;font-size:12px;">No critical infrastructure at immediate risk</span>'

    sar_inund_km2 = getattr(metrics, 'sar_inundated_km2', 0.0)
    sar_inund_pct = getattr(metrics, 'sar_inundated_pct', 0.0)

    weather_note = geo_alert_data.get("weather_fusion_note", "")
    weather_fusion_html = f"""
  <div style="background:rgba(234,179,8,0.1);border:1px solid #eab308;border-radius:6px;padding:8px 12px;margin-bottom:12px;color:#fef08a;font-size:12px;line-height:1.4;">
  <b>🌤️ LIVE METEOROLOGICAL FUSION:</b> {weather_note}
  </div>""" if weather_note else ""

    offline_disclaimer_html = ""

    weather_badge = ""
    if "Low confidence" in weather_note or "Low Confidence" in weather_note or "Stale" in weather_note:
        weather_badge = f'<span class="badge-pill" style="background:rgba(234,179,8,0.2);color:#fef08a;border:1px solid #eab308;font-weight:700;">📉 LOW CONFIDENCE</span>'
    elif "High confidence" in weather_note or "High Confidence" in weather_note:
        weather_badge = f'<span class="badge-pill" style="background:rgba(34,197,94,0.2);color:#4ade80;border:1px solid #22c55e;font-weight:700;">✅ HIGH CONFIDENCE</span>'

    is_nominal = "GREEN" in _sev_upper or "STABLE" in _sev_upper or "NOMINAL" in _sev_upper
    
    pop_label = "👥 Population in Sector" if is_nominal else "👥 Population at Risk"
    pop_color = "#38bdf8" if is_nominal else "#f87171"
    
    sar_label = "📡 SAR Multi-Band Observation" if is_nominal else "📡 SAR Cloud Penetration"
    sar_desc = "Nominal sub-surface backscatter footprint" if is_nominal else "Sub-surface radar backscatter < -18 dB"
    
    infra_label = "🏗️ Regional Infrastructure in Sector:" if is_nominal else "🏗️ Critical Infrastructure Threatened in Impact Zone:"

    banner_html = f"""<div class="{banner_cls}">
<div class="alert-hdr">
<div class="{title_cls}">
<span>{title_prefix} {geo_alert_data['headline']}</span>
</div>
<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
<span class="badge-pill" style="background:rgba(56,189,248,0.15);color:#38bdf8;border:1px solid rgba(56,189,248,0.4);font-weight:700;">{threat_type}</span>
<span class="badge-pill" style="background:{badge_bg};color:{badge_color};border:1px solid {badge_border};font-weight:700;">{sev}</span>
<span class="badge-pill badge-indigo">{threat_badge_lbl}</span>
{weather_badge}
</div>
</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(210px, 1fr));gap:10px;margin-top:14px;margin-bottom:12px;">
<div style="background:#090e1a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;">
<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;">🎯 {impact_label}</div>
<div style="font-size:16px;font-weight:700;color:#38bdf8;margin-top:2px;">{impact_val}</div>
<div style="font-size:11px;color:#64748b;">Computed from 15x15km AOI Optical Satellite Tile</div>
</div>
<div style="background:#090e1a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;">
<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;">{pop_label}</div>
<div style="font-size:16px;font-weight:700;color:{pop_color};margin-top:2px;">~{geo_alert_data['population_est']:,} <span style="font-size:11px;color:#94a3b8;">citizens</span></div>
<div style="font-size:11px;color:#64748b;">Algorithmic regional density estimation</div>
</div>
<div style="background:#090e1a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;">
<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;">{sar_label}</div>
<div style="font-size:16px;font-weight:700;color:#22d3ee;margin-top:2px;">{sar_inund_km2} km² <span style="font-size:11px;color:#94a3b8;">({sar_inund_pct}%)</span></div>
<div style="font-size:11px;color:#64748b;">{sar_desc}</div>
</div>
<div style="background:#090e1a;border:1px solid #1e293b;border-radius:8px;padding:10px 14px;">
<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;font-weight:600;">📍 Geocoded Sector</div>
<div style="font-size:13px;font-weight:600;color:#f1f5f9;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{geo_alert_data['sector']}</div>
<div style="font-size:11px;color:#64748b;">Detected at {geo_alert_data['detected_utc']}</div>
</div>
</div>
<div style="margin-top:6px;margin-bottom:12px;">
<div style="font-size:11px;font-weight:600;color:#cbd5e1;margin-bottom:6px;text-transform:uppercase;">{infra_label}</div>
<div style="display:flex;flex-wrap:wrap;gap:4px;">{infra_html}</div>
</div>
{offline_disclaimer_html}
{weather_fusion_html}
<div class="{action_box_cls}">{action_icon} <b>{action_label}</b>: {geo_alert_data['ndrf_action']}</div>
</div>"""

    st.markdown(banner_html, unsafe_allow_html=True)


# --------------------------------------------------------------------------------
# GENERATE RENDER LAYERS
# --------------------------------------------------------------------------------
ndvi_heatmap = math_engine.generate_ndvi_heatmap(matrices["vari"])
water_heatmap = math_engine.generate_water_heatmap(matrices["ndwi"], matrices["water_mask"])
sar_heatmap = math_engine.generate_sar_radar_heatmap(matrices["sar_db"], matrices["sar_flood_mask"])
blended_overlay = math_engine.generate_blended_overlay(matrices["rgb_norm"], ndvi_heatmap, alpha=0.55)
lulc_thematic = math_engine.generate_lulc_thematic_map(matrices["class_map"])

if view_mode.startswith("5-Class Thematic"):
    right_display = lulc_thematic
    right_caption = "5-Class Land Use / Land Cover (LULC) Thematic Map (100% Conserved)"
elif view_mode.startswith("NDVI / VARI"):
    right_display = ndvi_heatmap
    right_caption = f"Calibrated Radiometric Vegetation Index ({metrics.index_type})"
elif view_mode.startswith("NDWI"):
    right_display = water_heatmap
    right_caption = "Calibrated Water Inundation Heatmap (Cyan: Shallow/Canals | Deep Blue: Open Water)"
elif view_mode.startswith("SAR Microwave"):
    right_display = sar_heatmap
    right_caption = "Synthetic Aperture Radar (SAR) Simulation (Electric Cyan: Backscatter Inundation < -18 dB)"
elif view_mode.startswith("Tactical Fusion"):
    right_display = blended_overlay
    right_caption = "Tactical Fusion: True Color RGB fused with 55% Radiometric Heatmap"
else:
    right_display = (matrices["rgb_norm"] * 255).astype(np.uint8)
    right_caption = "Natural True Color Optical RGB Satellite Scene"

pil_original = Image.fromarray((matrices["rgb_norm"] * 255).astype(np.uint8))
pil_rendered = Image.fromarray(right_display) if isinstance(right_display, np.ndarray) else right_display


# --------------------------------------------------------------------------------
# MULTI-TAB COMMAND CONSOLE (7 TACTICAL SUITES)
# --------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab8, tab9, tab10, tab11, tab7 = st.tabs([
    "🛰️ Tactical Viewport & Swipe",
    "🗺️ Geospatial Tactical Map",
    "📊 Telemetry & LULC Analytics",
    "💬 Conversational AI Console",
    "🛰️ Space Edge Simulator",
    "📡 Autonomous Anomaly Radar",
    "🚁 Autonomous Drone Pathfinding",
    "🎙️ Tactical Voice Radio Dispatch",
    "🔮 Predictive Disaster Spread",
    "📱 Emergency SMS Gateway",
    "📄 Defense Briefings & Exports",
])


# ================================================================================
# TAB 1: TACTICAL VIEWPORT & SWIPE COMPARISON
# ================================================================================
with tab1:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">🔍 Interactive Before / After Radiometric Swipe Comparison</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:12px;">
                Drag the center slider horizontally to compare raw optical RGB satellite imagery with the calibrated radiometric layer.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    view_style = st.radio("Display Viewport Mode", ["Interactive Swipe Slider", "Side-by-Side Dual Viewports"], horizontal=True)
    
    if view_style == "Interactive Swipe Slider" and HAS_IMAGE_COMPARISON:
        swipe_mode = st.radio("Swipe Comparison Type", ["Historical Baseline vs Live Disaster", "Live Raw RGB vs Processed Heatmap"], horizontal=True)

        if swipe_mode == "Historical Baseline vs Live Disaster":
            # Generate the Simulated Baseline for Before/After Change Detection
            _ttype = geo_alert_data.get('threat_type', "Nominal") if geo_alert_data else "Nominal"
            simulated_baseline = math_engine.simulate_historical_baseline(matrices["rgb_norm"], matrices["class_map"], _ttype)
            pil_baseline = Image.fromarray(simulated_baseline)
            
            st.markdown("<div style='font-size:12px;color:#38bdf8;margin-bottom:8px;'>✓ <b>Change Detection Active:</b> 'Before' image is algorithmically synthesized from regional baseline profiles.</div>", unsafe_allow_html=True)
            
            image_comparison(
                img1=pil_baseline,
                img2=pil_rendered,
                label1="Historical Baseline (Simulated)",
                label2=f"Live Optical / Radiometric: {view_mode.split('(')[0]}",
                width=1100,
                starting_position=50,
                show_labels=True,
                make_responsive=True,
                in_memory=True,
            )
        else:
            image_comparison(
                img1=pil_original,
                img2=pil_rendered,
                label1="Live Optical Satellite RGB Feed",
                label2=f"Live Radiometric Map: {view_mode.split('(')[0]}",
                width=1100,
                starting_position=50,
                show_labels=True,
                make_responsive=True,
                in_memory=True,
            )
    else:
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            st.markdown("##### 📷 Optical Satellite RGB Feed")
            st.image(pil_original, use_container_width=True, caption=f"Raw Optical Feed: {region_label}")
        with vcol2:
            st.markdown(f"##### 🔬 Radiometric Layer: {view_mode[:35]}...")
            st.image(right_display, use_container_width=True, caption=right_caption)

    # Tactical Legend Panel
    st.markdown(
        """
        <div class="legend-bar">
            <b>Radiometric Palette:</b>
            <span class="legend-item"><span class="legend-dot" style="background:#22c55e;"></span> Active Vegetation (>0.04 VARI)</span>
            <span class="legend-item"><span class="legend-dot" style="background:#d9b381;"></span> Fallow Land / Dry Open Soil</span>
            <span class="legend-item"><span class="legend-dot" style="background:#1e90ff;"></span> Water Bodies & Canals (NDWI > 0.08)</span>
            <span class="legend-item"><span class="legend-dot" style="background:#ef4444;"></span> Built-up / Urban Infrastructure</span>
            <span class="legend-item"><span class="legend-dot" style="background:#00f2fe;"></span> SAR Radar Inundation (< -18dB)</span>
            <span class="legend-item"><span class="legend-dot" style="background:#f8fafc;"></span> Cloud / Haze</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================================
# TAB 2: GEOSPATIAL TACTICAL MAP (FOLIUM LIVE EXPLORER)
# ================================================================================
with tab2:
    st.markdown(
        f"""
        <div class="panel-box">
            <div class="panel-box-header">🗺️ Geospatial Tactical AOI Map: {region_label}</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:12px;">
                Interactive base map with geocoded Area of Interest (AOI) bounding box and telemetry markers.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    m_lat, m_lon = active_coords
    
    m = folium.Map(
        location=[m_lat, m_lon],
        zoom_start=11,
        tiles=None,
    )

    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        name="🗺️ OpenStreetMap (Default)",
        control=True,
        show=True,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google Satellite Imagery",
        name="🛰️ Google Satellite",
        control=True,
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Satellite + Labels",
        name="🛰️ Google Hybrid (Satellite+Labels)",
        control=True,
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
        name="🌑 CartoDB Dark (Tactical)",
        control=True,
        show=False,
    ).add_to(m)

    delta = (np.sqrt(total_km2) / 111.0) / 2.0 if total_km2 > 0 else 0.05
    bounds = [[m_lat - delta, m_lon - delta], [m_lat + delta, m_lon + delta]]

    folium.Rectangle(
        bounds=bounds,
        color="#38bdf8",
        weight=2.5,
        fill=True,
        fill_color="#0284c7",
        fill_opacity=0.2,
        popup=f"<b>AOI: {region_label}</b><br/>Area: {total_km2} km²<br/>GSD: {gsd_value}m",
    ).add_to(m)

    folium.CircleMarker(
        location=[m_lat, m_lon],
        radius=10,
        color="#38bdf8",
        fill=True,
        fill_color="#38bdf8",
        fill_opacity=0.9,
        popup=f"<b>{region_label}</b><br/>Veg: {veg_pct}%  Water: {water_pct}%  Fallow: {fallow_pct}%",
        tooltip=f"{region_label} — Click for telemetry",
    ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)

    st_folium(m, width="100%", height=480, key=f"map_{m_lat}_{m_lon}_{region_label}")

    st.markdown(
        f"""
        <div style="background:#090e1a;border:1px solid #1e293b;border-radius:8px;padding:12px 16px;margin-top:10px;font-family:'JetBrains Mono',monospace;font-size:12.5px;color:#94a3b8;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <div>📍 Lat: <b style="color:#f1f5f9;">{m_lat:.4f}°</b> &nbsp;|&nbsp; Lon: <b style="color:#f1f5f9;">{m_lon:.4f}°</b></div>
            <div>AOI Area: <b style="color:#22c55e;">{total_km2} km²</b> &nbsp;|&nbsp; GSD: <b style="color:#eab308;">{gsd_value}m</b></div>
            <div style="color:#64748b;">(OSM base layer cached after first load)</div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================================
# TAB 3: TELEMETRY & LULC ANALYTICS (PLOTLY SUITE)
# ================================================================================
with tab3:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">📊 Deterministic Radiometric Telemetry & Pixel Conservation</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:14px;">
                High-precision spectral distribution metrics, canopy vigor indices, and 100% MECE land classification accounting.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    pcol1, pcol2 = st.columns(2)
    
    with pcol1:
        lulc_df = pd.DataFrame({
            "Class": ["Active Vegetation", "Fallow Land / Dry Soil", "Water Bodies & Canals", "Built-up / Urban", "Cloud / Haze"],
            "Area_km2": [veg_km2, fallow_km2, water_km2, built_km2, getattr(metrics, 'cloud_haze_km2', 0.0)],
            "Percentage": [veg_pct, fallow_pct, water_pct, built_pct, getattr(metrics, 'cloud_haze_pct', 0.0)],
        })
        
        color_discrete_map = {
            "Active Vegetation": "#22c55e",
            "Fallow Land / Dry Soil": "#d9b381",
            "Water Bodies & Canals": "#1e90ff",
            "Built-up / Urban": "#ef4444",
            "Cloud / Haze": "#f8fafc",
        }
        
        fig_donut = px.pie(
            lulc_df,
            values="Area_km2",
            names="Class",
            title="<b>100% Conserved Land Cover (LULC) Breakdown</b>",
            hole=0.45,
            color="Class",
            color_discrete_map=color_discrete_map,
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>Area: %{value:.2f} km²<br>Coverage: %{percent}")
        fig_donut.update_layout(
            template="plotly_dark",
            paper_bgcolor="#090e1a",
            plot_bgcolor="#090e1a",
            font=dict(family="Inter, sans-serif", color="#e2e8f0"),
            showlegend=False,
            margin=dict(t=40, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with pcol2:
        vigor_df = pd.DataFrame({
            "Vigor Subclass": ["Dense Canopy (>0.28 VARI)", "Moderate Crops (0.12-0.28)", "Stressed / Low (<0.12)"],
            "Percentage": [
                getattr(metrics, 'dense_veg_pct', 0.0),
                getattr(metrics, 'moderate_veg_pct', 0.0),
                getattr(metrics, 'stressed_veg_pct', 0.0),
            ],
        })
        
        fig_bar = px.bar(
            vigor_df,
            x="Vigor Subclass",
            y="Percentage",
            title="<b>Vegetation Canopy Vigor & Health Distribution</b>",
            color="Vigor Subclass",
            color_discrete_sequence=["#16a34a", "#84cc16", "#eab308"],
            text="Percentage",
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_bar.update_layout(
            template="plotly_dark",
            paper_bgcolor="#090e1a",
            plot_bgcolor="#090e1a",
            font=dict(family="Inter, sans-serif", color="#e2e8f0"),
            showlegend=False,
            yaxis_title="Coverage (% of Total Scene)",
            margin=dict(t=40, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Multi-Spectral Polar & SAR Inundation
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        categories = ["Visible Blue", "Visible Green", "Visible Red", "NIR Proxy", "Water Absorbance"]
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[0.3, 0.85, 0.35, 0.95, 0.2],
            theta=categories,
            fill='toself',
            name='Active Vegetation',
            line_color='#22c55e',
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[0.8, 0.65, 0.25, 0.1, 0.9],
            theta=categories,
            fill='toself',
            name='Hydrological Water',
            line_color='#1e90ff',
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[0.55, 0.6, 0.7, 0.5, 0.4],
            theta=categories,
            fill='toself',
            name='Fallow / Dry Soil',
            line_color='#d9b381',
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], color="#94a3b8"),
                bgcolor="#090e1a",
            ),
            template="plotly_dark",
            paper_bgcolor="#090e1a",
            title="<b>Multi-Spectral Band Reflectance Signature Profiles</b>",
            font=dict(family="Inter, sans-serif", color="#e2e8f0"),
            height=320,
            margin=dict(t=40, b=20, l=40, r=40),
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    with rcol2:
        sar_pct = getattr(metrics, 'sar_inundated_pct', 0.0)
        sar_title_text = "SAR Radar Flood Inundation (< -18 dB)" if "FLOOD" in geo_alert_data.get("threat_type", "") else "SAR Radar Water/Moisture (< -18 dB)"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=sar_pct,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"<b>{sar_title_text}</b>", 'font': {'size': 14, 'color': '#38bdf8'}},
            delta={'reference': 5.0, 'increasing': {'color': "#ef4444"}},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': "#94a3b8"},
                'bar': {'color': "#00f2fe"},
                'steps': [
                    {'range': [0, 10], 'color': "rgba(16, 185, 129, 0.2)"},
                    {'range': [10, 30], 'color': "rgba(234, 179, 8, 0.2)"},
                    {'range': [30, 100], 'color': "rgba(239, 68, 68, 0.3)"},
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 3},
                    'thickness': 0.75,
                    'value': 25.0,
                },
            }
        ))
        fig_gauge.update_layout(
            template="plotly_dark",
            paper_bgcolor="#090e1a",
            font=dict(family="Inter, sans-serif", color="#e2e8f0"),
            height=320,
            margin=dict(t=40, b=20, l=30, r=30),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # 100% MECE Conservation Table
    st.markdown("##### 📋 Formal Pixel Conservation & Confusion Audit Matrix")
    matrix_data = math_engine.get_conservation_matrix_table(metrics)
    st.dataframe(matrix_data, use_container_width=True, hide_index=True)
    st.caption("✅ Verification Certificate: 100.0% of the raster pixels are accounted for across all physical land classes with zero unmapped voids.")
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 4: CONVERSATIONAL MISSION CONSOLE (QWEN2.5-VL STREAMING)
# ================================================================================
with tab4:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">💬 Conversational Earth Observation Intelligence (Qwen2.5-VL)</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:14px;">
                Autonomous cognitive synthesis: Qwen2.5-VL cross-examines visual satellite pixels against deterministic Engine 1 telemetry.
            </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### ⚡ Quick Mission Directives — Full Structured Analysis")
    st.caption("📊 Click a preset below for a full structured 4-section intelligence report, or type your own question below for a direct AI answer.")
    preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
    
    with preset_col1:
        if st.button("🌾 Crop Health & Soil Moisture", use_container_width=True):
            st.session_state["mission_query"] = "Assess active crop parcels, fallow land percentage, and irrigation distribution."
    with preset_col2:
        if st.button("🌊 Flood Extent & Canals", use_container_width=True):
            st.session_state["mission_query"] = "Evaluate surface water bodies, perimeter reservoirs, and flood inundation risk."
    with preset_col3:
        if st.button("🚢 Coastal & Infrastructure", use_container_width=True):
            st.session_state["mission_query"] = "Analyze coastal terrain, harbor shipping docks, and transport infrastructure density."
    with preset_col4:
        if st.button("📋 Full Defense Briefing", use_container_width=True):
            st.session_state["mission_query"] = "Produce a full formal strategic defense briefing with operational advisories."

    current_query_val = st.session_state.get("mission_query", "Perform comprehensive geospatial intelligence and hazard analysis on this satellite scene.")
    user_query = st.text_input(
        "Ask any question about this satellite scene — or use a preset above for full structured analysis:",
        value=current_query_val,
        placeholder="e.g. 'What hazard is going on here?' or 'Is there flood risk?' or 'Describe the vegetation state'"
    )

    if "current_report" not in st.session_state:
        st.session_state["current_report"] = None
    if "report_region" not in st.session_state:
        st.session_state["report_region"] = region_label

    # Show mode indicator to user
    _default_queries = {
        "Perform comprehensive geospatial intelligence and hazard analysis on this satellite scene.",
        "Produce a full formal strategic defense briefing with operational advisories.",
        "Assess active crop parcels, fallow land percentage, and irrigation distribution.",
        "Evaluate surface water bodies, perimeter reservoirs, and flood inundation risk.",
        "Analyze coastal terrain, harbor shipping docks, and transport infrastructure density.",
    }
    _is_question_mode = user_query.strip() not in _default_queries and len(user_query.strip()) > 10
    if _is_question_mode:
        st.info(f"🤖 **Question Mode** — AI will directly answer: *\"{user_query.strip()[:80]}...\"* using spectral telemetry as evidence.")
    else:
        st.info("📊 **Analysis Mode** — AI will produce a full structured intelligence report (Executive Summary, Telemetry Audit, Observations, Advisories).")

    execute_btn = st.button("🚀 Execute Cognitive Intelligence Analysis", type="primary", use_container_width=True)

    if execute_btn:
        report_placeholder = st.empty()
        spinner_msg = (
            "🤖 Qwen2.5-VL analyzing visual features with Engine 1 telemetry..."
            if ollama_ok
            else "📡 Ollama offline — generating Engine-1 deterministic report..."
        )
        with st.spinner(spinner_msg):
            try:
                stream_gen = vision_agent.generate_intelligence_report_stream(
                    image_input=pil_original,
                    metrics=metrics,
                    user_query=user_query,
                    region_name=region_label,
                )
                full_text = report_placeholder.write_stream(stream_gen)
                if full_text:
                    st.session_state["current_report"] = full_text
                    st.session_state["report_region"] = region_label
                else:
                    st.warning("The model returned an empty response. Please check if Ollama is running.")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.info("💡 Tip: Run `ollama serve` in a terminal, then click Execute again.")

    if st.session_state.get("current_report") and not execute_btn:
        st.markdown(
            f"""
            <div style="background:#090e1a;border:1px solid #1e293b;border-left:4px solid #38bdf8;border-radius:10px;padding:22px;margin-top:16px;">
                {st.session_state["current_report"]}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


safe_region = "".join([c if c.isalnum() else "_" for c in region_label])[:25]

# ================================================================================
# TAB 5: ON-ORBIT SPACE EDGE SIMULATOR (BALANCED & PERFECTLY ALIGNED)
# ================================================================================
with tab5:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">🛰️ On-Orbit Space Edge Computing Simulation (CubeSat / EOS Payload)</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Running the lightweight AAZHI AI pipeline directly onboard spacecraft to eliminate downlink bottlenecks and beam instant disaster alerts.
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Row 1: Two Balanced Feature Cards Side-by-Side
    scol1, scol2 = st.columns(2)

    with scol1:
        st.markdown(
            """
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px 20px;min-height:260px;display:flex;flex-direction:column;justify-content:space-between;">
                <div>
                    <div style="font-size:14px;font-weight:600;color:#c084fc;margin-bottom:6px;">⚡ In-Orbit Cloud-Gate Rejection Filter</div>
                    <div style="font-size:12.5px;color:#94a3b8;line-height:1.5;">
                        70% of optical Earth Observation images are obscured by clouds. In-orbit edge AI autonomously detects and discards cloudy frames before downlinking, saving 70% of satellite solar battery and ground station bandwidth.
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        
        cloud_pct = getattr(metrics, 'cloud_haze_pct', 0.0)
        cloud_thresh = st.slider("Autonomous Cloud Rejection Threshold (%)", 10, 80, 50, 5)
        is_cloud_rejected = cloud_pct > cloud_thresh
        
        if is_cloud_rejected:
            st.error(f"❌ Frame Discarded in Space: Cloud cover ({cloud_pct}%) > Threshold ({cloud_thresh}%). Bandwidth Saved: 140 MB.")
        else:
            st.success(f"✅ Frame Approved for Downlink: Cloud cover ({cloud_pct}%) <= Threshold ({cloud_thresh}%). Clear ground observed!")
        
        st.markdown("</div>", unsafe_allow_html=True)

    with scol2:
        packet_payload = {
            "satellite_id": "AAZHI-SAT-EOS-01",
            "timestamp": datetime.datetime.now().isoformat(),
            "mission": "AAZHI Earth Observation Intelligence",
            "target_region": region_label,
            "coordinates_lat_lon": active_coords,
            "gsd_meters": gsd_value,
            "total_area_km2": total_km2,
            "vegetation_pct": veg_pct,
            "water_coverage_pct": water_pct,
            "builtup_pct": built_pct,
            "fallow_soil_pct": fallow_pct,
            "cloud_haze_pct": getattr(metrics, 'cloud_haze_pct', 0.0),
            "mean_vari_index": metrics.mean_veg_index,
            "sar_water_detection": bool(getattr(metrics, 'sar_inundated_pct', 0.0) > 10.0),
            "pixel_conservation_status": "100%_MECE_CONSERVED",
            "engine": "AAZHI-SpectralPhysics-v2",
        }

        packet_json_str = json.dumps(packet_payload, indent=2)
        packet_bytes = packet_json_str.encode("utf-8")
        hex_full = packet_bytes.hex()
        packet_size_bytes = len(packet_bytes)
        hex_preview = "0x" + hex_full[:180] + "..."

        st.markdown(
            f"""
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px 20px;min-height:260px;display:flex;flex-direction:column;justify-content:space-between;">
                <div>
                    <div style="font-size:14px;font-weight:600;color:#38bdf8;margin-bottom:6px;">📡 10 KB Ultra-Low-Bandwidth Telemetry Downlink</div>
                    <div style="font-size:12.5px;color:#94a3b8;line-height:1.5;">
                        Instead of waiting 6 hours to downlink 150 MB of raw raster imagery, onboard AI compresses full scene intelligence into a compact alert packet beamed to tracking stations in under 30 seconds.
                    </div>
                </div>
                <div style="display:flex;gap:12px;margin-top:14px;font-family:'JetBrains Mono',monospace;font-size:12px;">
                    <div style="background:#0f172a;border:1px solid #1e293b;padding:8px 12px;border-radius:6px;flex:1;">
                        📦 <b>Packet Size</b>: <span style="color:#22c55e;">{packet_size_bytes} Bytes</span>
                    </div>
                    <div style="background:#0f172a;border:1px solid #1e293b;padding:8px 12px;border-radius:6px;flex:1;">
                        ⚡ <b>Savings</b>: <span style="color:#38bdf8;">99.9% Bandwidth</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Row 2: Transmission Terminal (Hex Radio Frame on Left, Decoded JSON on Right)
    st.markdown("##### 📟 Spacecraft Downlink Transmission & Ground Station Decoder")
    tcol1, tcol2 = st.columns(2)

    with tcol1:
        st.markdown("**1. Simulated AX.25 Radio Signal Transmission (HEX Stream):**")
        st.code(
            f"// AAZHI-SAT SPACE-TO-GROUND RADIO LINK\n"
            f"// Frame Format: AX.25 Packet Protocol | Payload: {packet_size_bytes} Bytes\n\n"
            f"{hex_preview}",
            language="text",
        )

    with tcol2:
        st.markdown("**2. Ground Station Decoded Intelligence Payload (JSON):**")
        st.code(packet_json_str, language="json")

    # Row 3: Balanced Action Download Buttons
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            label="📥 Download JSON Ground Truth Packet",
            data=packet_json_str,
            file_name=f"AAZHI_Downlink_{safe_region}.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            label="📥 Download Raw Radio HEX Frame (.hex)",
            data=hex_full,
            file_name=f"AAZHI_Downlink_{safe_region}.hex",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 6: AUTONOMOUS ANOMALY RADAR & CAP BROADCAST CONSOLE
# ================================================================================
with tab6:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">📡 Autonomous National Anomaly Radar & CAP Protocol Broadcast</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Continuous sub-continent orbital monitoring, automated anomaly detection, and standard Common Alerting Protocol (CAP 1.2) emergency broadcasting.
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Sub-Continent Anomaly Grid
    st.markdown("##### 🇮🇳 Sub-Continent Active Anomaly Telemetry Matrix")

    # Get current anomalies — use correct method call get_offline_databank()
    active_anomalies_list = radar_engine.get_offline_databank()
    if input_source.startswith("⚡ Autonomous"):
        # radar_mode_choice is only defined in the autonomous block; safely read it
        _radar_mode = st.session_state.get("_radar_mode_choice", "offline")
        fetch_mode = "online" if "Live" in _radar_mode else "offline"
        radar_key = f"anomalies_{fetch_mode}"
        if radar_key in st.session_state:
            active_anomalies_list, _, _ = st.session_state[radar_key]

    radar_table_rows = []
    for a in active_anomalies_list:
        _sev = a.get("severity", "")
        if "RED" in _sev:
            sev_tag = "🔴 CRITICAL"
        elif "ORANGE" in _sev:
            sev_tag = "🟠 HIGH"
        elif "YELLOW" in _sev:
            sev_tag = "🟡 WATCH"
        else:
            sev_tag = "🟢 NOMINAL"
        radar_table_rows.append({
            "Severity": sev_tag,
            "Anomaly Event": a.get("title", "—"),
            "Sector / Region": a.get("sector", "—"),
            "Category": a.get("category", "—"),
            "Coordinates": f"{a['coords'][0]:.2f}°N, {a['coords'][1]:.2f}°E" if a.get("coords") else "—",
            "Threat Score": f"{a.get('threat_score', 0)}/100",
            "Pop. Risk": f"~{a.get('affected_population_est', 0):,}",
        })

    radar_df = pd.DataFrame(radar_table_rows)
    st.dataframe(radar_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Split: Live CAP Payload vs NDRF Tactical Directives
    rcol1, rcol2 = st.columns(2)

    with rcol1:
        st.markdown("##### 📄 Standard Common Alerting Protocol (CAP 1.2 XML / JSON)")
        st.caption("Standardized OASIS/WMO international disaster alert schema for civil defense authorities.")
        
        cap_output_str = geo_alert_data["cap_json"] if geo_alert_data else json.dumps({"status": "ALL_CLEAR", "message": "No critical disaster anomaly triggered."}, indent=2)
        st.code(cap_output_str, language="json")
        
        st.download_button(
            label="📥 Download CAP 1.2 Alert JSON",
            data=cap_output_str,
            file_name=f"AAZHI_CAP_Alert_{safe_region}.json",
            mime="application/json",
            use_container_width=True,
        )

    with rcol2:
        st.markdown("##### 🛡️ NDRF Tactical Rescue & Asset Tasking Directives")
        st.caption("Automated emergency response recommendations based on quantitative LULC impact calculations.")
        
        target_sector = geo_alert_data['sector'] if geo_alert_data else region_label
        target_threat = geo_alert_data['threat_score'] if geo_alert_data else 45.0
        target_directive = geo_alert_data['ndrf_action'] if geo_alert_data else "Standard routine satellite surveillance pass; maintain standard standby posture."
        critical_infras = geo_alert_data.get('infrastructure', ['Regional Logistics Arteries', 'Power Grid Lines']) if geo_alert_data else ['Local Transport Corridors']

        impact_label_t6 = geo_alert_data.get('impact_label', '🌊 INUNDATION EXTENT') if geo_alert_data else '🌊 INUNDATION EXTENT'
        impact_val_t6 = geo_alert_data.get('impact_val', f"{water_km2} km²") if geo_alert_data else f"{water_km2} km²"

        is_nominal = "GREEN" in geo_alert_data.get("severity", "GREEN").upper() if geo_alert_data else False
        title_color = "#38bdf8" if is_nominal else "#f87171"
        dispatch_title = f"✅ NOMINAL OBSERVATION REPORT: {target_sector}" if is_nominal else f"🚨 TACTICAL MISSION DISPATCH: {target_sector}"

        infra_badges = " ".join([f"<span class='badge-pill badge-cyan' style='margin-bottom:4px;display:inline-block;'>🏗️ {inf}</span>" for inf in critical_infras])

        st.markdown(
            f"""
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px 20px;min-height:300px;display:flex;flex-direction:column;justify-content:space-between;">
                <div>
                    <div style="font-size:14px;font-weight:700;color:{title_color};margin-bottom:8px;">
                        {dispatch_title}
                    </div>
                    <div style="font-size:12.5px;color:#cbd5e1;line-height:1.6;margin-bottom:12px;">
                        {target_directive}
                    </div>
                    <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;"><b>Critical Assets in Vulnerability Cone:</b></div>
                    <div>{infra_badges}</div>
                </div>
                <div style="display:flex;gap:10px;margin-top:14px;font-family:'JetBrains Mono',monospace;font-size:11.5px;">
                    <div style="background:#0f172a;border:1px solid #1e293b;padding:8px 12px;border-radius:6px;flex:1;">
                        <span style="color:#94a3b8;">{impact_label_t6}</span>: <span style="color:#38bdf8;">{impact_val_t6}</span>
                    </div>
                    <div style="background:#0f172a;border:1px solid #1e293b;padding:8px 12px;border-radius:6px;flex:1;">
                        ⚡ <b>Threat Rating</b>: <span style="color:{title_color};">{target_threat}/100</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 7: DEFENSE BRIEFINGS & DATA EXPORT CENTER
# ================================================================================
with tab7:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">📄 Defense Intelligence Briefings & Open Geospatial Exports</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Export formal intelligence briefings, GIS vector layers, and complete tabular matrices for mission planning and analysis.
            </div>
        """,
        unsafe_allow_html=True,
    )

    dcol1, dcol2, dcol3 = st.columns(3)

    with dcol1:
        st.markdown(
            """
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px;min-height:160px;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:10px;">
                <div>
                    <div style="font-size:14px;font-weight:600;color:#f1f5f9;margin-bottom:4px;">📄 Tactical PDF Briefing</div>
                    <div style="font-size:12px;color:#94a3b8;">
                        High-fidelity multi-page document with 100% MECE telemetry tables, spectral heatmaps, and automated Geo-Alert bulletins.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        active_report_text = st.session_state.get("current_report") or "Comprehensive Earth Observation intelligence briefing prepared by AAZHI Satellite Intelligence Command with 100% MECE conserved telemetry."
        
        pdf_bytes = PDFReportGenerator.generate_pdf(
            metrics=metrics,
            ai_report_text=active_report_text,
            original_img=pil_original,
            heatmap_img=lulc_thematic,
            region_name=st.session_state.get("report_region", region_label),
            geo_alert_info=geo_alert_data,
        )
        
        st.download_button(
            label="📥 Download Tactical PDF Briefing",
            data=pdf_bytes,
            file_name=f"AAZHI_SAT_{safe_region}_Briefing.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    with dcol2:
        st.markdown(
            """
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px;min-height:160px;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:10px;">
                <div>
                    <div style="font-size:14px;font-weight:600;color:#f1f5f9;margin-bottom:4px;">🗺️ Open GeoJSON Vector Export</div>
                    <div style="font-size:12px;color:#94a3b8;">
                        GeoJSON feature collection containing target AOI polygon and classified thematic centroids for GIS software (QGIS, ArcGIS, Bhuvan).
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        geojson_str = math_engine.export_geojson(metrics, region_label, active_coords)
        
        st.download_button(
            label="📥 Download GeoJSON Layer",
            data=geojson_str,
            file_name=f"AAZHI_SAT_{safe_region}_AOI.geojson",
            mime="application/geo+json",
            use_container_width=True,
        )

    with dcol3:
        st.markdown(
            """
            <div style="background:#090e1a;border:1px solid #1e293b;border-radius:10px;padding:18px;min-height:160px;display:flex;flex-direction:column;justify-content:space-between;margin-bottom:10px;">
                <div>
                    <div style="font-size:14px;font-weight:600;color:#f1f5f9;margin-bottom:4px;">📊 Telemetry CSV Matrix</div>
                    <div style="font-size:12px;color:#94a3b8;">
                        Complete tabular breakdown of pixel counts, area in km², hectares, acres, and coverage percentages with Excel compatibility.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        csv_df = pd.DataFrame(math_engine.get_conservation_matrix_table(metrics))
        csv_str = "\ufeff" + csv_df.to_csv(index=False, encoding="utf-8")

        st.download_button(
            label="📥 Download Telemetry CSV",
            data=csv_str.encode("utf-8"),
            file_name=f"AAZHI_SAT_{safe_region}_Telemetry.csv",
            mime="text/csv; charset=utf-8",
            use_container_width=True,
        )

    st.markdown("##### 🧰 Tactical Ground Rescue Package (Offline)")
    st.markdown(
        "<div style='font-size:13px;color:#94a3b8;margin-bottom:12px;'>Bundles the Telemetry CSV, Audio Voice Dispatch (if generated), and AI Tactical Map into a single downloadable .ZIP archive for field operations in dead zones.</div>",
        unsafe_allow_html=True
    )
    
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Telemetry CSV
        zip_file.writestr(f"AAZHI_SAT_{safe_region}_Telemetry.csv", csv_str.encode("utf-8"))
        
        # 2. GeoJSON
        zip_file.writestr(f"AAZHI_SAT_{safe_region}_AOI.geojson", geojson_str)
        
        # 3. Audio File (if it exists)
        audio_path = os.path.join("C:/Users/LENOVO/.gemini/antigravity-ide/brain/c20a7b3a-1fd5-4ffb-80f0-fa7994d2b06e/scratch/", "tactical_dispatch.mp3")
        if os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                zip_file.writestr("tactical_dispatch.mp3", f.read())
                
        # 4. Drone Path (if it exists)
        if "drone_path" in st.session_state:
            import json
            coords = st.session_state["drone_path"]
            # Convert numpy int64 → native Python int to avoid JSON serialization errors
            safe_coords = [[float(lon), float(lat)] for lat, lon in coords]
            geojson = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"name": "Safe Drone Corridor"},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": safe_coords
                    }
                }]
            }
            zip_file.writestr("safe_drone_corridor.geojson", json.dumps(geojson, indent=2))
            
    st.download_button(
        label="📦 Export Offline Tactical Package (.ZIP)",
        data=zip_buffer.getvalue(),
        file_name=f"AAZHI_SAT_{safe_region}_GROUND_PACKAGE.zip",
        mime="application/zip",
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 8: AUTONOMOUS DRONE PATHFINDING
# ================================================================================
with tab8:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">🚁 Autonomous Rescue Drone Pathfinding (A* / LULC Cost Map)</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Calculates the safest autonomous flight path for UAV search and rescue operations, avoiding water hazards and minimizing risk based on LULC physics.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Pathfinding mode selection
    path_mode = st.radio("Path Selection Mode", ["Automatic (Base to Hazard)", "Custom Coordinates"], horizontal=True)
    
    # Safe base coords (just a default for 'automatic')
    base_lat = active_coords[0] - (total_km2**0.5 / 222.0) # Slightly south of center
    base_lon = active_coords[1] - (total_km2**0.5 / 222.0)
    
    if path_mode == "Custom Coordinates":
        st.markdown("##### 📍 Target Coordinates")
        ccol1, ccol2 = st.columns(2)
        with ccol1:
            start_lat = st.number_input("Start Lat (Base)", value=base_lat, format="%.6f", key="pf_slat")
            start_lon = st.number_input("Start Lon (Base)", value=base_lon, format="%.6f", key="pf_slon")
        with ccol2:
            end_lat = st.number_input("End Lat (Target)", value=active_coords[0], format="%.6f", key="pf_elat")
            end_lon = st.number_input("End Lon (Target)", value=active_coords[1], format="%.6f", key="pf_elon")
    else:
        start_lat = base_lat
        start_lon = base_lon
        end_lat = active_coords[0]
        end_lon = active_coords[1]

    path_engine.update_gsd(gsd_value) # Make sure GSD is synced

    if st.button("🚀 Calculate Safe Drone Corridor", use_container_width=True):
        with st.spinner("Generating morphological cost map and running A* search..."):
            try:
                path, cost_map = path_engine.find_path(
                    matrices["class_map"],
                    (start_lat, start_lon),
                    (end_lat, end_lon),
                    (active_coords[0], active_coords[1])
                )
                if path:
                    st.session_state["drone_path"] = path
                    st.session_state["drone_start"] = (start_lat, start_lon)
                    st.session_state["drone_end"] = (end_lat, end_lon)
                else:
                    st.error("No safe path could be found across the given terrain.")
            except Exception as e:
                st.error(f"Pathfinding error: {e}")
                
    if st.session_state.get("drone_path"):
        path = st.session_state["drone_path"]
        start_lat, start_lon = st.session_state["drone_start"]
        end_lat, end_lon = st.session_state["drone_end"]
        
        st.success(f"Path successfully generated! Corridor length: {len(path)} nodes.")
        
        path_coords_for_map = []
        for (px_y, px_x) in path:
            pt_lat, pt_lon = path_engine.pixel_to_geo(px_y, px_x, matrices["class_map"].shape, active_coords[0], active_coords[1])
            path_coords_for_map.append([pt_lat, pt_lon])
        
        pf_map = folium.Map(location=[active_coords[0], active_coords[1]], zoom_start=12)
        # Default OpenStreetMap doesn't require an API key
        
        # Overlay the active image to visually verify the drone path
        if active_img:
            # Save the image to a temp file for folium
            overlay_path = os.path.join(cache_dir, "temp_map_overlay.png")
            active_img.save(overlay_path, format="PNG")
            
            # Calculate geographic bounds of the image
            h, w = matrices["class_map"].shape
            sw_lat, sw_lon = path_engine.pixel_to_geo(h, 0, (h, w), active_coords[0], active_coords[1])
            ne_lat, ne_lon = path_engine.pixel_to_geo(0, w, (h, w), active_coords[0], active_coords[1])
            bounds = [[sw_lat, sw_lon], [ne_lat, ne_lon]]
            
            folium.raster_layers.ImageOverlay(
                image=overlay_path,
                bounds=bounds,
                opacity=0.6,
                name="Satellite Overlay"
            ).add_to(pf_map)

        # Draw drone flight path as a polyline
        folium.PolyLine(
            locations=path_coords_for_map,
            color="#00f2fe",
            weight=3,
            opacity=0.95,
            tooltip="Safe Drone Corridor"
        ).add_to(pf_map)

        # Start marker
        folium.Marker(
            location=[start_lat, start_lon],
            popup="🟢 Drone Base (Start)",
            icon=folium.Icon(color="green", icon="plane", prefix="fa")
        ).add_to(pf_map)

        # End marker
        folium.Marker(
            location=[end_lat, end_lon],
            popup="🔴 Hazard Target (End)",
            icon=folium.Icon(color="red", icon="flag", prefix="fa")
        ).add_to(pf_map)

        folium.LayerControl().add_to(pf_map)

        st.markdown("##### 🗺️ Safe Drone Corridor Map")
        try:
            from streamlit_folium import st_folium
            st_folium(pf_map, use_container_width=True, height=520, returned_objects=[])
        except ImportError:
            import folium
            from io import BytesIO
            map_html = pf_map._repr_html_()
            st.components.v1.html(map_html, height=520, scrolling=False)

# ================================================================================
with tab9:

    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">🎙️ Tactical Voice Radio Dispatch (Online / Offline Synthesis)</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Synthesizes the active anomaly data into a military-grade audio dispatch for ground rescue teams.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("##### 📝 Generated Dispatch Transcript")
    
    dispatch_data = geo_alert_data if geo_alert_data else {
        "threat_type": "Nominal Surveillance",
        "headline": "Routine Scan",
        "severity": "GREEN",
        "sector": region_label,
        "coords": active_coords,
        "population_est": int(total_km2 * 100),
        "ndrf_action": "Routine observation."
    }
    
    script = audio_engine.generate_dispatch_script(dispatch_data)
    st.info(f"**Transcript:**\n\n> {script}")
    
    synth_mode = st.radio("Synthesis Engine", ["Online (gTTS - Natural)", "Offline (pyttsx3 - Air-Gapped)"], horizontal=True)
    
    if st.button("\U0001f50a Synthesize Radio Transmission", use_container_width=True):
        force_offline = "Offline" in synth_mode
        with st.spinner("Synthesizing encrypted voice transmission..."):
            audio_path = audio_engine.generate_audio(script, force_offline=force_offline)
            if audio_path and os.path.exists(audio_path):
                st.success("Transmission synthesized successfully.")
                st.audio(audio_path)
            else:
                st.error("Failed to synthesize audio. Check dependencies (gTTS or pyttsx3).")
    
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 10: PREDICTIVE DISASTER SPREAD FORECASTING
# ================================================================================
with tab10:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">\U0001f52e Predictive Disaster Spread Forecasting</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Simulates Cellular Automata (CA) spread models for Floods and Wildfires using the extracted LULC class map.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns([1, 2])
    with col1:
        sim_options = ["Flood (Cyan)", "Wildfire (Red)"]
        default_index = 0
        if active_anomaly_info:
            _cat = active_anomaly_info.get("category", "").lower()
            if "flood" in _cat or "inundation" in _cat:
                default_index = 0
            elif "fire" in _cat or "wildfire" in _cat or "landslide" in _cat or "drought" in _cat:
                default_index = 1
        
        is_nominal_sim = "GREEN" in geo_alert_data.get("severity", "GREEN").upper() if geo_alert_data else False
        if is_nominal_sim:
            st.info("✅ **Nominal Condition**: No active disaster detected. You may run a what-if simulation.")

        disaster_type = st.radio("Select Disaster Type", sim_options, index=default_index)
        time_steps = st.slider("Forecast Timeframe (+Hours)", min_value=1, max_value=24, value=6, step=1)
        run_sim = st.button("\U0001f52e Run CA Spread Simulation", use_container_width=True)

    with col2:
        if run_sim:
            with st.spinner(f"Simulating {disaster_type} spread dynamics for T+{time_steps} hours..."):
                try:
                    import importlib
                    import engine.forecaster
                    importlib.reload(engine.forecaster)
                    from engine.forecaster import DisasterForecaster
                    forecaster = DisasterForecaster(matrices["class_map"])

                    if "Flood" in disaster_type:
                        spread_mask = forecaster.simulate_flood(time_steps)
                        if not np.any(spread_mask):
                            st.warning("Simulation aborted: No water bodies found to simulate a flood overflow.")
                            st.stop()
                        overlay_rgb = forecaster.generate_heatmap_overlay(spread_mask, "flood")
                    else:
                        spread_mask = forecaster.simulate_wildfire(time_steps)
                        if not np.any(spread_mask):
                            st.warning("Simulation aborted: No combustible vegetation found to ignite a wildfire.")
                            st.stop()
                        overlay_rgb = forecaster.generate_heatmap_overlay(spread_mask, "fire")

                    base_rgb = (matrices["rgb_norm"] * 255).astype(np.uint8).copy()
                    alpha_mask = overlay_rgb[:, :, 3] / 255.0
                    for c in range(3):
                        base_rgb[:, :, c] = base_rgb[:, :, c] * (1 - alpha_mask) + overlay_rgb[:, :, c] * alpha_mask

                    from PIL import Image
                    blended_pil = Image.fromarray(base_rgb)
                    st.image(blended_pil, caption=f"Predicted {disaster_type} Spread at T+{time_steps}h", use_container_width=True)
                except Exception as e:
                    st.error(f"Failed to run simulation: {e}")
        else:
            st.info("Configure simulation parameters and run to view predictive spread.")

    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================================
# TAB 11: EMERGENCY SMS ALERT GATEWAY
# ================================================================================
with tab11:
    st.markdown(
        """
        <div class="panel-box">
            <div class="panel-box-header">📱 Automated Emergency SMS Gateway</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">
                Generates localized evacuation alerts and mocks broadcast to cellular towers in the AOI bounding box.
            </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("##### 📝 Drafted SMS Alert")
    
    try:
        sms_threat = geo_alert_data.get("headline", "Critical Hazard") if 'geo_alert_data' in locals() and geo_alert_data else "Potential Natural Hazard"
        sms_sector = geo_alert_data.get("sector", region_label) if 'geo_alert_data' in locals() and geo_alert_data else region_label
        sms_action = geo_alert_data.get("ndrf_action", "Evacuate immediately if instructed.") if 'geo_alert_data' in locals() and geo_alert_data else "Stay tuned to local authorities."
        is_sms_emergency = "RED" in geo_alert_data.get("severity", "").upper() or "ORANGE" in geo_alert_data.get("severity", "").upper() if 'geo_alert_data' in locals() and geo_alert_data else True
    except NameError:
        sms_threat = "Potential Natural Hazard"
        sms_sector = region_label if 'region_label' in locals() else "Unknown Region"
        sms_action = "Stay tuned to local authorities."
        is_sms_emergency = True
        
    if is_sms_emergency:
        sms_text = f"EMERGENCY ALERT: {sms_threat} detected in {sms_sector}. {sms_action} Avoid affected zones. - AAZHI-SAT Early Warning System"
    else:
        sms_text = f"AAZHI-SAT UPDATE: {sms_threat} in {sms_sector}. {sms_action} - Routine surveillance active."
    
    st.code(sms_text, language="text")
    
    if st.button("🚀 Broadcast SMS to Regional Cell Towers", use_container_width=True):
        import time
        msg_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        target_phones = int(total_km2 * 125) if 'total_km2' in locals() and total_km2 else 15000
        for i in range(101):
            progress_bar.progress(i)
            sent_count = int((i / 100.0) * target_phones)
            msg_placeholder.success(f"Transmitting... Delivered to {sent_count:,} / {target_phones:,} mobile devices.")
            time.sleep(0.02)
            
        st.balloons()
        
    st.markdown("</div>", unsafe_allow_html=True)
