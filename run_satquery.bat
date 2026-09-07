@echo off
title AAZHI-SAT AI - Satellite Intelligence Command Center
color 0B
cls
echo ====================================================================
echo         PROJECT AAZHI -- AAZHI-SAT GEO-AI COMMAND
echo   Autonomous Earth Observation Conversational Intelligence Platform
echo   Dual-Engine: Quantitative Spectral Math + Qwen2.5-VL Local VLM
echo   Hardware: NVIDIA RTX 3050 (6GB VRAM) ^| 100%% Air-Gapped Offline
echo ====================================================================
echo.

echo [1/2] Verifying local Ollama server status...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 2 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Ollama server is offline. Starting background Ollama daemon...
    start /B ollama serve >nul 2>&1
    timeout /t 3 >nul
) else (
    echo [OK] Ollama server is active and responsive!
)

echo.
echo [2/2] Launching Ultra-Modern SatQuery AI Command Dashboard...
echo [*] Browser will open automatically at: http://localhost:8501
echo [*] Press Ctrl+C in this terminal window to stop the server.
echo.
streamlit run app.py
pause
