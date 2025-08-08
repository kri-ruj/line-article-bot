@echo off
echo.
echo ========================================
echo    LINE Article Intelligence System
echo ========================================
echo.
echo Choose which app to run:
echo.
echo 1. Ultimate App (NO DEPENDENCIES - Recommended)
echo 2. LINE Bot (Requires dependencies + .env)
echo 3. Production App (Requires dependencies + .env)
echo 4. Demo (Shows AI features)
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Starting Ultimate App...
    echo Open browser at: http://localhost:5001
    echo.
    python app_ultimate.py
) else if "%choice%"=="2" (
    echo.
    echo Starting LINE Bot...
    echo Make sure .env file is configured
    echo.
    python app_line_fixed.py
) else if "%choice%"=="3" (
    echo.
    echo Starting Production App...
    echo Make sure .env file is configured
    echo.
    python app_production.py
) else if "%choice%"=="4" (
    echo.
    echo Running AI Features Demo...
    echo.
    python simple_10x_demo.py
) else (
    echo Invalid choice!
    pause
    exit
)

pause