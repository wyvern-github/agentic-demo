# QuickPad: PyQt6 desktop editor

Date: 2026-11-20

## Brief and scope

Build a small, single-document WordPad-style editor for people who want to open a local note, edit it, and save it without learning a new interface. Ship New, Open, Save, Save As, character and paragraph formatting, undo/redo, find and replace, a live word count, and protection against accidental loss of unsaved changes.

Out of scope: databases, printing, images and other embedded media, RTF/DOCX, and browser-quality HTML rendering. Only the user's local document files are persisted; no autosave, session recovery, or preferences store in the first release.

## Acceptance criteria

| ID | Observable behavior | Verification |
| --- | --- | --- |
| AC1 | Launch into a blank, focused editor with an Untitled title and `Words: 0`. New resets document identity and history. Open, Save, and Save As work for UTF-8 `.txt` and `.html`; Save on Untitled opens Save As. A missing suffix uses the selected filter; a supported explicit suffix wins. Unsupported suffixes, decoding failures, and I/O errors show actionable feedback and leave the active document, path, and dirty state intact. | M1: pytest-qt File actions, temporary-file round trips, cancellation, and injected failures. |
| AC2 | Bold, italic, underline, font family, size, and text colour apply to the selection or subsequent typing. Left, center, right, and justified alignment and toggled unordered bullets apply to the current or selected paragraphs. Supported styles survive saving and reopening HTML. Formatting controls are disabled for plain-text documents. Saving rich content as TXT requires explicit confirmation before dropping styles; cancellation leaves the content and file untouched. | M2: pytest-qt formatting actions, cursor and selection state, semantic HTML round trip, and TXT conversion/cancellation. |
| AC3 | Standard Undo and Redo shortcuts and menu actions restore supported text and formatting edits; availability follows the current document. Replacing all matches is one undoable edit. | M2: pytest-qt text/format undo and redo. M3: pytest-qt Replace All undo. |
| AC4 | A keyboard-accessible Find & Replace panel supports case-insensitive, literal, single-line Find Next with wrap, Replace on the selected match, and Replace All. It reports no matches or the number replaced, disables operations for an empty query, and allows an empty replacement to delete matches. | M3: pytest-qt keyboard, match, replacement, wrap, no-match, and empty-query cases. |
| AC5 | The status bar shows a live word count of the whole visible document: one word per nonempty whitespace-delimited token, with list markers excluded. It updates on typing, New/Open, replacement, and undo/redo. | M1 and M3: pytest-qt status label checks including empty content, multiline text, and replacement. |
| AC6 | New, Open, and Close on a modified document offer Save, Discard, and Cancel. Save continues only after writing successfully; canceled dialogs and failed saves do not abandon the document. Clean documents proceed without prompting. | M4: parametrized pytest-qt lifecycle matrix, including format-only edits and return to the saved state via undo. |

## Design and workflow

- **Platform:** Windows first, Python 3.12 as the initial test baseline, PyQt6 at runtime, `pytest` and `pytest-qt` in a `test` extra. Set `qt_api = "pyqt6"` in `pyproject.toml`.
- **Shape:** A `QMainWindow` with a central `QTextEdit`. Reuse `QAction`s across menus, toolbar, and standard shortcuts. Let Qt own text, cursor positions, formatting, and undo history. Use `QTextDocument`'s modified state and an optional current `Path` for document identity. Keep file I/O separate from widgets; use synchronous local I/O for small documents and commit writes atomically with `QSaveFile` rather than truncating a destination before a successful write.
- **File behavior:** Untitled documents start in rich mode with HTML as the default save filter. TXT opens in plain mode; paste plain text in either mode in the first release. After a successful lossy Save As to TXT, switch the editor to the saved plain representation, with a clean flag and reset history for that conversion. A successful Save As to HTML enables formatting. HTML is Qt rich text, not a web page; ignore embedded images and block external resource loads. Compare reopened content and formats, not HTML bytes.
- **Window sketch:** `[File | Edit | Format]` above `[New Open Save | Undo Redo | B I U | Font Size Colour | Alignment Bullets]`, then an optional labeled Find & Replace strip, a large editor, and a persistent `Words: n` status label. Show the filename and modified marker in the title. Keep keyboard focus in the editor initially and restore it when the search strip closes. Use native controls, a quiet neutral palette, visible focus, and text feedback for search and failure states. Let the toolbar overflow and the search strip reflow at narrow widths. Test keyboard navigation and Windows display scaling manually.
- **Workflow:** Open or type immediately, select and format text, find or replace terms, then save. Use inline feedback for search results, a status message for a successful save, and dialogs only when a decision or error needs attention. On failed open or save, keep the current content editable and explain what failed.

## Planned project structure

```text
pyproject.toml
quickpad\
  __init__.py
  __main__.py            # QApplication and window setup
  window.py              # editor, menus, actions, and document lifecycle
  storage.py             # format choice, UTF-8 reads, atomic writes
  find_replace.py        # find/replace panel and cursor operations
tests\
  test_files.py
  test_formatting.py
  test_find_replace.py
  test_unsaved.py
```

## Run and verify after implementation

1. In a Python 3.12 virtual environment, run `python -m pip install -e ".[test]"`, then `python -m quickpad`.
2. Run the milestone selectors from [MILESTONES.md](./MILESTONES.md), then `python -m pytest -q`. Use `QT_QPA_PLATFORM=offscreen` only in the headless test process when needed. Use `qtbot`, disposable files, and deterministic dialog or failure stubs at the UI/I/O boundary.
3. Perform the native Windows smoke check and request independent review. Offscreen tests do not verify toolbar overflow, look and feel, or high-DPI behavior.

Main risks are silent formatting loss, replacing or closing a document after a canceled or failed save, and undo grouping. Test those paths explicitly. Use Qt cursor positions for search and replacement rather than indexing Python strings into a Qt document; include non-BMP text in a regression case. For local I/O, assert that a failed write preserves an existing destination as well as editor state.

## Git delivery

`commit=milestone`, `push=off`, `pr=off`. Make one local commit per verified milestone with changes; skip empty commits. Final verification and independent review are gates, not extra milestones or automatic commits. The implementation starts on `main` at `1594f1548d05e692fed4f9e6a17502b9dbc7284a`; remote and PR targets are not applicable.
