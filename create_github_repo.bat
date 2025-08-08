@echo off
echo ========================================
echo Creating GitHub Repository
echo ========================================

REM Check if gh is authenticated
"C:\Program Files\GitHub CLI\gh.exe" auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Not authenticated with GitHub
    echo Please run: gh auth login
    pause
    exit /b 1
)

echo Authenticated with GitHub!
echo.

REM Create the repository
echo Creating repository...
"C:\Program Files\GitHub CLI\gh.exe" repo create line-article-bot --public --description "LINE bot that saves articles to Google Sheets" --source=. --remote=origin --push

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS! Repository created
    echo ========================================
    echo.
    echo Opening repository in browser...
    "C:\Program Files\GitHub CLI\gh.exe" repo view --web
) else (
    echo.
    echo ERROR: Failed to create repository
    echo Try running manually:
    echo gh repo create line-article-bot --public --source=. --remote=origin --push
)

pause