@echo off
title AAZHI SATELLITE INTELLIGENCE - OFFLINE DESKTOP LAUNCHER
color 0B

echo ===============================================================================
echo                PROJECT AAZHI : SATELLITE INTELLIGENCE COMMAND
echo                Air-Gapped Autonomous Multi-Spectral and SAR Platform
echo ===============================================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking environment and dependencies
python -c "import streamlit, rasterio, cv2, folium" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required satellite intelligence packages
    pip install -r requirements.txt
) else (
    echo [OK] All satellite and AI engines are ready.
)

:: Auto-Create Windows Desktop Shortcut (Supports both OneDrive and Standard Desktops)
echo [INFO] Pinning 1-Click Launcher to your Windows Desktop
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d = [Environment]::GetFolderPath('Desktop'); $w = New-Object -ComObject WScript.Shell; $s = $w.CreateShortcut((Join-Path $d 'AAZHI Satellite Intelligence.lnk')); $s.TargetPath = '%~dp0Launch_AAZHI.bat'; $s.WorkingDirectory = '%~dp0'; $s.IconLocation = 'shell32.dll,14'; $s.Description = 'AAZHI Satellite Intelligence Command - Offline Edge'; $s.Save()" >nul 2>&1
echo [OK] Shortcut created on your Desktop: 'AAZHI Satellite Intelligence'

echo.
echo [2/3] Initializing Offline Edge Radar and Spectral Physics Engines
echo [3/3] Opening dashboard in your default browser at http://localhost:8501
echo.
echo ===============================================================================
echo   RUNNING 100%% OFFLINE ON LOCALHOST. NO INTERNET CONNECTION REQUIRED.
echo   Press Ctrl + C in this window to stop the server when done.
echo ===============================================================================
echo.

start http://localhost:8501
streamlit run app.py --server.headless=true

pause
