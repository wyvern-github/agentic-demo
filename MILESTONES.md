# QuickPad Milestones

| ID | Deliverable and dependency | Status | Exit check | Observed evidence | Git delivery |
|---|---|---|---|---|---|
| M1 | Shell and document state: create `QMainWindow`, central rich-text editor, menus/toolbars/status bar, dirty tracking, undo/redo actions, window close/new-action guard skeleton. Dependency: existing workspace and PyQt6 environment. | Done | `pytest -q tests/test_shell.py tests/test_unsaved.py` passes the cumulative shell, state, close guard, and basic undo/redo exit checks. | 8 passed offscreen on Python 3.12.10; see M1 handoff. | Commit: `674a3291b1beb6d4c1e4c58525dfbc23b1d8715e`; Push: off |
| M2 | Character and paragraph formatting: bold/italic/underline, font family/size, text colour, alignment, and bullets, with selection/insertion-format synchronization and cumulative undo/redo. Depends on M1. | Done | `pytest -q tests/test_shell.py tests/test_formatting.py tests/test_unsaved.py` passes cumulative M1/M2 behavior. | 20 passed offscreen; selection, insertion, synchronization, lists and undo covered. | Commit: `ada3a114c0709a6a14c74982172b500db1f3ebe1`; Push: off |
| M3 | File workflows and safety: `.txt`/`.html` open/save/save-as, plain-text confirmation, sanitised HTML subset, failure/cancellation state machine, unsaved Save/Discard/Cancel and close/new/open protection. Depends on M2. | Done | `pytest -q tests/test_shell.py tests/test_formatting.py tests/test_files.py tests/test_unsaved.py` passes cumulative M1–M3 behavior, including failure/cancel regression cases. | 67 passed offscreen; real file round trips, rejected resources, atomic failure, and all guard outcomes covered. | Commit: scheduled, receipt at M4; Push: off |
| M4 | Search and status: find/replace/replace-all, Unicode code-point offsets, wrap behavior, and live Unicode-aware word count. Depends on M3. | Pending | `pytest -q tests/test_shell.py tests/test_formatting.py tests/test_files.py tests/test_unsaved.py tests/test_find_replace.py tests/test_unicode.py` passes cumulative M1–M4 behavior. | No implementation run yet; planning only. | Commit: pending milestone; Push: off |
| FT | Final testing gate: complete suite in the chosen PyQt test environment, focused manual smoke of resize/focus/dialog cancellation, and full acceptance traceability. Separate from implementation milestones. | Pending | `python -m pytest -q` passes; `python -m quickpad` opens the smoke window; every acceptance criterion has a test or documented manual check. | Not started. | Commit: no gate-only commit; Push: off |
| IR | Independent review gate: separate reviewer checks branch, cumulative diff, tests, code, UX, and safety findings, then writes `REVIEW.md`. Separate from FT and implementation milestones. | Pending | Reviewer verdict `PASS`; no unresolved P0/P1/P2 finding; required evidence matches the reviewed state. | Explicitly deferred by user; no reviewer or report requested during implementation. | Commit: none; Push: off |

## Milestone test intent

- **M1:** Use `qtbot` to type into the editor; verify Undo/Redo and the modified state, then exercise New/Close with Cancel and Discard. M3 adds the Save branch.
- **M2:** Exercise each formatting control on selected text or paragraphs and check actual character/block formats. Verify that typing picks up the insertion format and moving the caret updates controls without creating an edit.
- **M3:** Reopen real `.txt` and `.html` files under `tmp_path`; verify plain-text and supported-format round trips, Save As path changes, loss confirmation, atomic-write failure, blocked resource loading, and Save/Discard/Cancel across New/Open/Close.
- **M4:** Verify literal case-insensitive search and wrap, matching after emoji, replacement of selected and all matches, one-step undo for Replace All, and status count updates after edits, file open, and undo.

The suite must include:

- Qt widget construction and offscreen smoke checks.
- `tmp_path` tests for `.txt` and `.html`.
- Dialog monkeypatches for Save/Discard/Cancel, open/save cancellation, and file exceptions.
- Rich text to plain-text loss confirmation and `setPlainText`/`toPlainText` behavior.
- Sanitiser tests for `<img>`, external resources, scripts/styles/forms/SVG, event attributes, and unsafe links.
- Selection and insertion formatting tests.
- Undo/redo tests around formatting and replace-all.
- Literal find/replace tests with case-insensitive default and match wrap.
- Emoji and combining-character offsets and word-count tests.
- Close/new/open tests that leave document state intact on Cancel or failure.

## Final verification command

```powershell
$env:QT_QPA_PLATFORM="offscreen"
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m quickpad
```
