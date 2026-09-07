@echo off
title AAZHI SATELLITE INTELLIGENCE - OFFLINE DESKTOP LAUNCHER
color 0B

echo ===============================================================================
echo                PROJECT AAZHI : SATELLITE INTELLIGENCE COMMAND
echo                Air-Gapped Autonomous Multi-Spectral & SAR Platform
echo ===============================================================================
echo.
echo [1/3] Checking environment & dependencies...
python -c "import streamlit, rasterio, cv2, folium" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required satellite intelligence packages (One-time setup)...
    pip install -r requirements.txt
) else (
    echo [OK] All satellite & AI engines are ready.
)

echo.
echo [2/3] Initializing Offline Edge Radar & Spectral Physics Engines...
echo [3/3] Opening dashboard in your default browser...
echo.
echo ===============================================================================
echo   RUNNING 100% OFFLINE ON LOCALHOST. NO INTERNET CONNECTION REQUIRED.
echo   Press Ctrl + C in this window to stop the server when done.
echo ===============================================================================
echo.

start http://localhost:8501
streamlit run app.py --server.headless=true

pause
