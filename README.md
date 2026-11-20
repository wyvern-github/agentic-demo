# agentic-demo
Demo project for learning agentic AI based coding

## QuickPad

QuickPad is a small, single-document PyQt6 editor. It runs on Python 3.12 or
newer. From PowerShell in the project directory, set up and launch it with:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e '.[test]'
& .\.venv\Scripts\python.exe -m quickpad
```

For headless tests, use:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
& .\.venv\Scripts\python.exe -m pytest -q
```
