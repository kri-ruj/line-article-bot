@echo off
echo Creating backup before cleanup...

REM Create backup directory with timestamp
set BACKUP_DIR=backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir %BACKUP_DIR%

echo Backing up Python files to %BACKUP_DIR%...

REM Backup all Python files
xcopy *.py %BACKUP_DIR%\ /Y

REM Backup markdown files
xcopy *.md %BACKUP_DIR%\ /Y

REM Backup important config files
xcopy .env %BACKUP_DIR%\ /Y 2>nul
xcopy requirements.txt %BACKUP_DIR%\ /Y
xcopy Dockerfile %BACKUP_DIR%\ /Y
xcopy deploy.sh %BACKUP_DIR%\ /Y
xcopy *.bat %BACKUP_DIR%\ /Y 2>nul
xcopy *.db %BACKUP_DIR%\ /Y 2>nul

echo.
echo Backup completed to %BACKUP_DIR%
echo You can now safely proceed with cleanup.
pause