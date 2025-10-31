@echo off
REM AI Developer Agent Launcher
REM Easy-to-use launcher for the AI Developer Agent

echo ========================================
echo AI Developer Agent
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again
    pause
    exit /b 1
)

REM Activate virtual environment if exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist ..\.venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call ..\.venv\Scripts\activate.bat
)

REM Parse command
if "%1"=="" goto :interactive
if /I "%1"=="interactive" goto :interactive
if /I "%1"=="-i" goto :interactive
if /I "%1"=="generate" goto :generate
if /I "%1"=="-g" goto :generate
if /I "%1"=="test" goto :test
if /I "%1"=="-t" goto :test
if /I "%1"=="help" goto :help
if /I "%1"=="--help" goto :help
goto :help

:interactive
echo.
echo Starting interactive mode...
echo.
python "%~dp0ai_developer_agent.py" --interactive
goto :end

:generate
if "%2"=="" (
    echo Error: Please provide a strategy description
    echo Example: ai_developer.bat generate "RSI strategy"
    goto :end
)
echo.
echo Generating strategy: %2
echo.
python "%~dp0ai_developer_agent.py" --generate %2
goto :end

:test
if "%2"=="" (
    echo Error: Please provide a strategy file
    echo Example: ai_developer.bat test my_strategy.py
    goto :end
)
echo.
echo Testing strategy: %2
echo.
python "%~dp0ai_developer_agent.py" --test %2
goto :end

:help
echo.
echo Usage:
echo   ai_developer.bat [command] [options]
echo.
echo Commands:
echo   interactive, -i          Start interactive mode (default)
echo   generate, -g "<desc>"    Generate and test strategy
echo   test, -t <file>          Test existing strategy
echo   help, --help             Show this help
echo.
echo Examples:
echo   ai_developer.bat
echo   ai_developer.bat interactive
echo   ai_developer.bat generate "RSI mean reversion"
echo   ai_developer.bat test my_strategy.py
echo.
goto :end

:end
echo.
pause
