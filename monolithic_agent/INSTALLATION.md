# Installation Guide - Conversation Memory Feature

## Quick Install (Recommended)

```powershell
# Make sure .venv is activated
.venv\Scripts\activate

# Run the automated installer
python install_langchain.py
```

## Manual Installation

### Option 1: Install Main Requirements
```powershell
pip install -r requirements.txt
```

### Option 2: Install Strategy Requirements Only
```powershell
pip install -r strategy_requirements.txt
```

### Option 3: Install Individual Packages
```powershell
pip install langchain
pip install langchain-google-genai
pip install langchain-community
```

## Verify Installation

```powershell
python verify_setup.py
```

## After Installation

1. **Create migrations**
   ```powershell
   python manage.py makemigrations strategy_api
   python manage.py migrate
   ```

2. **Restart Django server**
   ```powershell
   python manage.py runserver
   ```

3. **Test the feature**
   ```powershell
   python test_conversation_memory.py
   ```

## Troubleshooting

### "No module named 'langchain'" error
- Make sure .venv is activated: `.venv\Scripts\activate`
- Reinstall packages: `python install_langchain.py`

### "Module not found" after installation
- Restart your Django server (Ctrl+C, then `python manage.py runserver`)
- Verify with: `python -c "import langchain; print(langchain.__version__)"`

### Virtual Environment Issues
```powershell
# Create new venv if needed
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## Files Updated

- ✅ `requirements.txt` - Main project dependencies (NEW)
- ✅ `strategy_requirements.txt` - Strategy module dependencies (UPDATED)
- ✅ `Strategy/requirements.txt` - Strategy folder dependencies (UPDATED)

## What Gets Installed

### Core Dependencies
- `langchain>=0.1.0` - LangChain framework for AI memory
- `langchain-google-genai>=0.0.5` - Google Gemini integration
- `langchain-community>=0.0.10` - Community tools

### Already Installed (Django Project)
- Django, DRF, CORS headers, JWT auth
- pandas, numpy, requests
- google-generativeai

All packages are compatible with Python 3.8+
