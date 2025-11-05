Using the project .venv (Windows PowerShell)

This project follows the repository-level instruction to run Python scripts inside the project's `.venv`.

Quick setup (PowerShell):

1) Create and install core dependencies (from repository root):

```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent
.\scripts\setup_venv.ps1
```

2) Activate the venv for an interactive session:

```powershell
cd c:\Users\nyaga\Documents\AlgoAgent\multi_agent
.\.venv\Scripts\Activate.ps1
# Now your prompt shows the venv; run python commands normally
python -m pip install -r requirements.txt    # optional; see notes
```

3) Run the integration test inside the venv (without activating):

```powershell
# From multi_agent folder
.\.venv\Scripts\python.exe phase3_integration_test.py
```

Notes:
- The `setup_venv.ps1` installs a minimal set of packages required for local testing: `jsonschema`, `redis`, `pydantic`, `python-dateutil`, `google-generativeai`.
- `requirements.txt` contains additional packages (e.g. psycopg2) that may require system packages to build. If you need full requirements, activate the venv and install them manually. On Windows, `psycopg2` often requires PostgreSQL dev tools (pg_config) — if you don't have them, skip or use `psycopg2-binary`.
- When running scripts or tests, prefer `.venv\Scripts\python.exe <script>` to ensure the correct interpreter is used even if the venv is not activated in the shell.

Troubleshooting:
- If PowerShell refuses to run `Activate.ps1` due to execution policy, run as Administrator and set `Set-ExecutionPolicy RemoteSigned` (or run commands using the venv's python/pip executables directly).

