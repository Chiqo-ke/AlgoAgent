# -*- coding: utf-8 -*-
"""
CLI Launcher with proper Windows encoding handling
"""
import sys
import os

# Set environment variable to force UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# For Windows, set console to UTF-8 mode
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

# Now run the CLI by executing it as a script
if __name__ == "__main__":
    with open('cli.py', 'r', encoding='utf-8') as f:
        exec(f.read())
