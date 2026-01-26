$env:PYTHONPATH = "C:\Users\nyaga\Documents\AlgoAgent"
Set-Location "C:\Users\nyaga\Documents\AlgoAgent"
& ".\.venv\Scripts\uvicorn.exe" multi_agent.api_server:app --host 0.0.0.0 --port 8000 --reload
