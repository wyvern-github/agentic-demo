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

Use File to create, open, and save UTF-8 `.txt` or `.html` documents.
Saving formatted text as `.txt` requires confirmation and converts the active
document to plain text. HTML is restricted to safe text formatting; images,
embedded content, scripts, stylesheets, and external resource loading are not
supported. Clipboard and drag-and-drop insert plain text only.

Use **Edit → Find** (`Ctrl+F`) or **Replace** (`Ctrl+H`) for literal,
case-insensitive search with wrap-around; `F3` finds the next match. Enable
Match case when needed. The find and replacement fields accept line breaks,
and Find Next includes overlapping occurrences. Replace All changes
non-overlapping matches in one undoable operation. The status bar counts
Unicode letter/number words as you edit.
