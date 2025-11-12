@echo off
REM Quick Strategy Generator - Windows Batch File
REM Usage: generate.bat "Your strategy description" output_file.py

if "%~1"=="" (
    echo Starting interactive mode...
    python quick_generate.py
) else (
    python quick_generate.py %*
)
