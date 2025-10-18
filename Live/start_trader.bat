@echo off
REM AlgoAgent Live Trader Startup Script
REM Quick launcher for Windows

echo ================================================
echo   AlgoAgent Live Trader
echo ================================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create .env from .env.template:
    echo   1. Copy .env.template to .env
    echo   2. Edit .env with your MT5 credentials
    echo.
    pause
    exit /b 1
)

REM Check if strategy file is provided
if "%1"=="" (
    echo ERROR: No strategy file specified!
    echo.
    echo Usage:
    echo   start_trader.bat path\to\strategy.py [--dry-run]
    echo.
    echo Example:
    echo   start_trader.bat ..\Backtest\codes\my_strategy.py --dry-run
    echo.
    pause
    exit /b 1
)

REM Check if strategy file exists
if not exist "%1" (
    echo ERROR: Strategy file not found: %1
    echo.
    pause
    exit /b 1
)

REM Extract dry-run flag
set DRY_RUN_FLAG=
if "%2"=="--dry-run" set DRY_RUN_FLAG=--dry-run

echo Strategy: %1
if defined DRY_RUN_FLAG (
    echo Mode: DRY RUN
) else (
    echo Mode: LIVE TRADING
    echo WARNING: This will execute real trades!
    echo Press Ctrl+C to cancel, or
    pause
)
echo.
echo Starting trader...
echo ================================================
echo.

REM Run the trader
python live_trader.py --strategy "%1" %DRY_RUN_FLAG%

echo.
echo ================================================
echo Trader stopped.
echo ================================================
pause
