@echo off
REM =================================================================
REM Set Streaming Mode for Strategy Generation
REM =================================================================
REM This script switches the strategy generation mode to STREAMING
REM (sequential row-by-row data processing)
REM
REM Created: 2025-11-03
REM =================================================================

echo.
echo ====================================================================
echo Setting Data Processing Mode to STREAMING (Sequential)
echo ====================================================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: Virtual environment not found, using system Python
)

echo.
echo Updating configuration...
python set_mode.py streaming

echo.
pause
