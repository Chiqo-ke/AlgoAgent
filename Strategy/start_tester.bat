@echo off
REM Quick launcher for Interactive Strategy Tester
REM Double-click this file to start testing

echo.
echo ================================================================================
echo   AlgoAgent Strategy Validator - Interactive Tester
echo ================================================================================
echo.

REM Try virtual environment Python first
if exist "C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe" (
    echo Using virtual environment Python...
    "C:\Users\nyaga\Documents\AlgoAgent\.venv\Scripts\python.exe" interactive_strategy_tester.py
) else (
    echo Using system Python...
    python interactive_strategy_tester.py
)

echo.
pause
