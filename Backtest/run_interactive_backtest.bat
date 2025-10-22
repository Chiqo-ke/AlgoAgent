@echo off
REM Interactive Backtest Runner - Windows Batch Script
REM Launches the interactive backtest with user input

echo.
echo ========================================
echo Interactive Backtest Runner
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

REM Run the interactive backtest
echo Starting interactive backtest...
echo.
python "%~dp0interactive_backtest_runner.py"

REM Pause to see results
echo.
pause
