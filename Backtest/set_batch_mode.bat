@echo off
REM =================================================================
REM Set Batch Mode for Strategy Generation
REM =================================================================
REM This script switches the strategy generation mode to BATCH
REM (bulk data processing)
REM
REM Created: 2025-11-03
REM =================================================================

echo.
echo ====================================================================
echo Setting Data Processing Mode to BATCH (Bulk)
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
python set_mode.py batch

echo.
pause
