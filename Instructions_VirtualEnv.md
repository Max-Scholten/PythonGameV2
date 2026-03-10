# Setup `.\.venv` (Option A — keep Python 3.13 and use prebuilt `pygame` wheel)

Starting point: you do **not** have `.\.venv` in your project root.

## Steps

### 1). Create the virtual environment
```powershell
python -m venv .venv
```
### 2). Activate the virtual environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 3). Verify Python inside the virtual environment.
```powershell
python -V
.\.venv\Scripts\python.exe -V
```
### 4). Upgrade pip tooling.
```powershell
python -m pip install --upgrade pip setuptools wheel
```
### 5). Install dependencies from requirements.txt (if present).
```powershell
if (Test-Path .\requirements.txt) {
  python -m pip install -r .\requirements.txt
} else {
  Write-Host "No `requirements.txt` found — install packages manually, then run `python -m pip freeze > .\requirements.txt`"
}
```
### 5.5). (Only when pygame fails to build).
```powershell
python -m pip install --upgrade pygame --pre
```
### 6). Install pyserial (if not already installed).
```powershell
python -m pip install pyserial
```

### 7). Pip installed packages (recommended).
```powershell
python -m pip freeze > .\requirements.txt
```

### 8). Quick verification.
```powershell
.\.venv\Scripts\python.exe -V
python -m pip show pygame
python -m pip list
```
