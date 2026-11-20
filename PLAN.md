# QuickPad Implementation Plan

**Date:** 2026-11-20
**Task timestamp:** 2026-11-20T15:00:40+01:00

## Brief

Build QuickPad as a small, WordPad-like rich-text desktop editor in PyQt6. The application must provide document creation/loading/saving, core character and paragraph formatting, editing/search helpers, document status, and unsaved-change protection. The result is a reconciliation of the existing untracked workspace scaffolding: no implementation sources are currently present in the root project, although untracked environment/package/test artefacts exist.

## Assumptions

- QuickPad is a single-document desktop application on Windows with a normal desktop keyboard and mouse.
- Python 3.12-compatible PyQt6 is the runtime and pytest-qt is the UI test framework.
- A “document” is one `QTextEdit` document. Document-based offsets exposed to application logic are Python Unicode code-point offsets (not Qt UTF-16 cursor offsets).
- Use the document's modified state for prompts. A successful New, Open, or Save establishes a clean baseline; undoing back to that baseline restores the clean state. Caret movement, search, and changing the format for future typing do not dirty existing content.
- Dialog tests will monkeypatch Qt file and message dialogs rather than using unattended native dialogs.

## Practical defaults

- Initial font: Segoe UI at 11 pt when available, otherwise the application default font.
- Window: 960×640, resizable, with menu bar, formatting toolbar, and status bar.
- Default alignment: left; default paragraph bullets: disc.
- Colour: native `QColorDialog`; a missing/invalid selection uses no change.
- Plain text: UTF-8 with BOM-compatible decoding. Save in UTF-8 without BOM unless an existing file already used one.
- HTML: Qt HTML subset, using `QTextDocument.toHtml()`/`setHtml()` at document boundaries, with conservative sanitisation.
- Find: literal, case-insensitive, default whole-document search; match wrap from the next document position, with wrap-around; replacement offers Replace and Replace All. Empty search does nothing and reports 0 matches.
- Find/replace selections and document edits do not alter external unsaved state incorrectly: replacement is one undoable edit block.
- Word count: count contiguous Unicode letter/number/mark runs that contain at least one letter or number. A combining accent stays with its base; punctuation, whitespace, and emoji separate words.

## In scope

- New, open, save, and save-as for `.txt` and `.html`.
- Bold, italic, underline, font family, point size, text colour.
- Left/centre/right/justify alignment and bullets.
- Undo, redo, find, replace, and replace-all.
- Live word count in the status bar.
- Save/Discard/Cancel prompt before replacing or closing a modified document (New, Open, or Close). Save As is a save operation, not a document-replacement action.
- Keyboard shortcuts for major actions and standard editing actions.
- Deliberate plain/error/disabled states and accessible names/tooltips.

## Out of scope

- SQLite or any database.
- Printing.
- Images in documents or UI; external image-resource loading is prohibited.
- `.rtf` and `.docx`.
- Spell checking, collaboration, tabs, autosave, plugins, and format conversion beyond `.txt`/`.html`.

## Acceptance criteria

1. **Shell and editing:** A 960×640 or larger resizable window opens immediately usable, with accessible menus/toolbars/status bar and standard keyboard focus.
2. **File actions:** New/open/save/save-as can target `.txt` and `.html`; no file action is left pending after Cancel or an I/O failure.
3. **Plain text loss:** Saving rich text as `.txt` first asks for explicit confirmation that formatting will be lost. On success, the active document adopts the saved plain-text baseline so a clean document matches what will reopen. On cancel or failure, retain the original content, format, path, and modified state.
4. **HTML safety:** HTML load/save uses a Qt-supported subset and removes scripts, styles, forms, SVG, embedded objects, event attributes, `javascript:` links, and image elements. No external image or resource URL is fetched.
5. **Formatting:** Character and paragraph controls affect the current selection or insertion format and remain synchronized when the cursor moves.
6. **Undo/redo:** Formatting and replacement operations integrate with Qt undo/redo; plain text edits and repeated operations do not corrupt history.
7. **Find/replace:** Literal matching is case-insensitive by default, wrap is supported, zero-length/empty queries do nothing, and replace-all is a single undoable operation.
8. **Unicode:** Public cursor and match offsets are Unicode code-point offsets in the document; emoji and combining-text tests produce correct selections and counts.
9. **Word count:** The status bar updates on edit and reports a punctuation/whitespace-aware count of Unicode letter/number/mark runs.
10. **Unsaved changes:** New, Open, and Close prompt Save/Discard/Cancel when the current document is modified. Cancel or save failure aborts the requested action without replacing or closing the document.
11. **Failure safety:** Open/save failures show an error. Read and prepare the target before replacing the current document; use atomic file writes. Cancel or failure must not change the path to one that was not successfully saved or opened.
12. **Out-of-scope boundaries:** No database, printing, images, `.rtf`, or `.docx` support is exposed.

## Project structure

```text
quickpad/
  __init__.py
  __main__.py
  app.py
  main_window.py
  document.py
  text_service.py
  storage.py
  dialogs.py
tests/
  conftest.py
  test_shell.py
  test_files.py
  test_formatting.py
  test_find_replace.py
  test_unsaved.py
  test_unicode.py
pyproject.toml
```

The exact structure may be refined during implementation, but test modules should remain behavior-focused.

## UX and workflow

- **Primary view:** a central `QTextEdit` with a compact toolbar above it and status bar below. Menus: File, Edit, Format, Help.
- **File flow:** File → New/Open/Save/Save As. Native filter labels show only `Text files (*.txt)` and `HTML files (*.html)`.
- **Save flow:** Save with no path behaves as Save As. Use the chosen filter if the name lacks an extension; reject unsupported extensions. Warn before writing rich content to `.txt`; flatten the editor only after a successful write.
- **Unsaved flow:** Save/Discard/Cancel. Save continues only after a successful write. Discard permits the requested operation but does not clear or reset the current document before the operation succeeds.
- **Open/new flow:** For Open, select and prepare the target before prompting; cancellation or read failure is then a no-op on the current document. Apply the staged content only after the guard permits replacement. If the guard saves over the selected target, use the newly saved content, not the stale staged copy.
- **HTML flow:** loading is sanitised before `setHtml`; save emits only the approved subset and no resource URLs. `.html` opening is rich; `.txt` opening is plain.
- **Formatting flow:** formatting controls act on selection or current insertion position. Font/size/colour use native Qt controls; alignment/bullets operate on paragraphs.
- **Find bar:** non-modal dialog/panel with Find, Replace, Replace All, Match Case checkbox, and status text. Find Next and Replace preserve document-based offsets.

## State transition rules

Keep the requested New, Open, or Close operation local to its handler. On Save failure or Cancel, return immediately and drop the request; it must not fire later. On Save success or Discard, execute the original operation once. Use a single shared guard for menu and window-close paths.

## Persistence

No database or settings persistence is required for this plan. Window geometry may use `QSettings` only if the implementation adds it without changing acceptance behavior.

## Risks

- **Data loss:** Write through `QSaveFile` with direct-write fallback disabled. Test failed writes against an existing file and assert that the original bytes and editor state survive.
- **HTML fidelity and resources:** Preserve supported formatting semantically, not byte-for-byte. Test a format round trip and block resource lookup as a second line of defense.
- **Unicode and Qt cursor positions:** Convert offsets against the same normalized document text used for matching; test matches after emoji and across paragraph boundaries.

## Qt HTML subset

Allowed formatting elements: `p`, `div`, `br`, `span`, `b`, `strong`, `i`, `em`, `u`, `s`, `font`, `h1`–`h6`, `ul`, `ol`, `li`, `blockquote`, `pre`, and `a` without external resource loading. Allowed attributes are conservative: alignment, basic text/font/color/background values, list style, and plain `href` only for safe schemes. Strip `<img>`, `<script>`, `<style>`, `<link>`, `<iframe>`, `<object>`, `<embed>`, `<svg>`, `<video>`, `<audio>`, `<form>`, event attributes, `src`/`srcset`, CSS URLs, and `javascript:`/other unsafe links.

## Verification strategy

| Acceptance | Milestone/check |
|---|---|
| 1, 5, 6 | M1 shell + editing/undo; M2 formatting |
| 2, 3, 4, 10, 11 | M1 state skeleton; M3 file and safety flows |
| 7 | M4 find/replace |
| 8, 9 | M4 Unicode/count |
| 12 | Final pytest collection/import review |

Test command for implementation:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m pytest -q tests/test_shell.py tests/test_formatting.py
& .\.venv\Scripts\python.exe -m pytest -q tests/test_files.py tests/test_unsaved.py
& .\.venv\Scripts\python.exe -m pytest -q tests/test_find_replace.py tests/test_unicode.py
& .\.venv\Scripts\python.exe -m quickpad
```

Set `QT_QPA_PLATFORM=offscreen` in headless test environments. Tests must use `pytestqt` and `tmp_path`.

The requested final gate runs the suite and launch offscreen. Resize, focus,
and dialog cancellation are exercised programmatically in that environment;
native on-screen appearance and high-DPI behavior remain unverified.

## Git Delivery

- `commit`: `milestone`
- `push`: `off`
- `pr`: `off`
- Base/current branch: `experiment/no-helpers`
- Start HEAD: `60a3f9d3c18f23976b83e5b6ba95359dff09a65e`
- Before the first milestone commit, a separately authorized Git identity
  rewrite changed HEAD to `76bf88ff4a7fcced45731792b7f00038608a06d8`. Both
  commits have the same tree (`e583ad462e207ad914231b5ac06f2ad3392c122d`);
  the branch and implementation scope are unchanged.
- Remote: configured (`origin`) but unused by this plan
- Implementation is authorized: make one local commit per verified milestone
  with changes; do not switch branches, push, open a PR, or request review.
