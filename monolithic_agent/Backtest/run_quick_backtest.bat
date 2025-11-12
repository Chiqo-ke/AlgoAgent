@echo off
REM Quick Interactive Backtest - Windows Batch Script
REM Launches quick backtest with minimal configuration

echo.
echo ========================================
echo Quick Interactive Backtest
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Run the quick backtest
echo Starting quick backtest...
echo.
python "%~dp0quick_interactive_backtest.py"

REM Pause to see results
echo.
pause
