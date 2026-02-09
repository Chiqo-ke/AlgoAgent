@echo off
REM Verify Timeout Settings
REM ========================

echo Running timeout verification...
C:\Users\nyaga\Documents\.venv\Scripts\python.exe verify_timeouts.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: Timeout settings verified!
    exit /b 0
) else (
    echo.
    echo FAILED: Timeout verification failed!
    exit /b 1
)
