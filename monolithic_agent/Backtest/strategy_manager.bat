@echo off
REM Strategy Manager Batch Runner
REM Easy-to-use commands for managing trading strategies

echo ========================================
echo Strategy Manager
echo ========================================
echo.

REM Check if virtual environment is activated
python -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>nul
if errorlevel 1 (
    echo Activating virtual environment...
    if exist .venv\Scripts\activate.bat (
        call .venv\Scripts\activate.bat
    ) else if exist venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
    ) else (
        echo Warning: Virtual environment not found
    )
)

REM Parse command
if "%1"=="" goto :show_menu
if /I "%1"=="status" goto :status
if /I "%1"=="generate" goto :generate
if /I "%1"=="run" goto :run
if /I "%1"=="run-all" goto :run_all
if /I "%1"=="help" goto :help
goto :invalid

:show_menu
echo Available commands:
echo   status     - Show status of all strategies
echo   generate   - Generate missing Python code
echo   run NAME   - Run specific strategy backtest
echo   run-all    - Run all strategy backtests
echo   help       - Show detailed help
echo.
echo Example: strategy_manager.bat generate
goto :end

:status
echo Checking strategy status...
echo.
python strategy_manager.py --status
goto :end

:generate
echo Generating missing strategies...
echo.
if /I "%2"=="force" (
    python strategy_manager.py --generate --force
) else (
    python strategy_manager.py --generate
)
goto :end

:run
if "%2"=="" (
    echo Error: Please specify strategy name
    echo Example: strategy_manager.bat run test_strategy
    exit /b 1
)
echo Running backtest for: %2
echo.
python strategy_manager.py --run %2
goto :end

:run_all
echo Running all strategy backtests...
echo.
python strategy_manager.py --run-all
goto :end

:help
python strategy_manager.py --help
goto :end

:invalid
echo Invalid command: %1
echo Run without arguments to see available commands
exit /b 1

:end
