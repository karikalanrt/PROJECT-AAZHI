@echo off
title AAZHI SATELLITE INTELLIGENCE - 1-CLICK AUTO-INSTALLER
color 0B

echo ===============================================================================
echo                PROJECT AAZHI : SATELLITE INTELLIGENCE 1-CLICK INSTALLER
echo ===============================================================================
echo.
echo [1/4] Downloading latest AAZHI Satellite Intelligence package...
set "TARGET_DIR=%USERPROFILE%\AAZHI-SAT"
set "ZIP_FILE=%TEMP%\AAZHI-main.zip"

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://github.com/karikalanrt/PROJECT-AAZHI/archive/refs/heads/main.zip', '%ZIP_FILE%')"

echo [2/4] Auto-extracting package into %TARGET_DIR%...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%TEMP%\AAZHI_TMP' -Force; Copy-Item -Path '%TEMP%\AAZHI_TMP\PROJECT-AAZHI-main\*' -Destination '%TARGET_DIR%' -Recurse -Force; Remove-Item -Path '%TEMP%\AAZHI_TMP' -Recurse -Force; Remove-Item -Path '%ZIP_FILE%' -Force"

echo [3/4] Creating 1-Click Desktop Shortcut...
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\AAZHI Satellite Intelligence.lnk"
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%TARGET_DIR%\Launch_AAZHI.bat'; $s.WorkingDirectory = '%TARGET_DIR%'; $s.IconLocation = 'shell32.dll,14'; $s.Description = 'AAZHI Satellite Intelligence Command'; $s.Save()"

echo [4/4] Installation Complete! Launching AAZHI...
echo.
start "" "%TARGET_DIR%\Launch_AAZHI.bat"
exit
