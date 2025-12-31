# Virtual Environment Setup Guide

## Windows Setup

### Step 1: Create Virtual Environment

```cmd
# Navigate to project directory
cd C:\Users\Yashvi\Desktop\PMC\multi_agent_rag

# Create virtual environment
python -m venv venv

# Alternative if python3 is your command:
python3 -m venv venv
```

### Step 2: Activate Virtual Environment

```cmd
# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

**You should see `(venv)` at the start of your command line.**

### Step 3: Upgrade pip

```cmd
python -m pip install --upgrade pip
```

### Step 4: Install Dependencies

```cmd
pip install -r requirements.txt
```

This will install all required packages (~2-3 minutes).

### Step 5: Verify Installation

```cmd
# Check installations
pip list

# Should see:
# - openai
# - weaviate-client
# - streamlit
# - langchain
# etc.
```

---

## Troubleshooting

### Issue: "python not found"

**Solution**:
```cmd
# Check Python installation
where python
python --version

# If not found, install Python from:
# https://www.python.org/downloads/
```

### Issue: PowerShell script execution error

**Error**: "cannot be loaded because running scripts is disabled"

**Solution**:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate again
venv\Scripts\Activate.ps1
```

### Issue: pip install fails

**Solution**:
```cmd
# Upgrade pip first
python -m pip install --upgrade pip

# Install wheel
pip install wheel

# Try again
pip install -r requirements.txt
```

---

## Deactivating Virtual Environment

When you're done:

```cmd
deactivate
```

---

## Quick Reference

```cmd
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install packages
pip install -r requirements.txt

# Deactivate
deactivate
```
