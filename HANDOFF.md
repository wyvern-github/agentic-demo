# QuickPad Planning Handoff

**Task:** Plan QuickPad, a WordPad-like PyQt6 editor
**Task timestamp:** 2026-11-20T15:00:40+01:00
**Artifact paths:**
- `PLAN.md`
- `MILESTONES.md`
- `HANDOFF.md`
- `REVIEW.md` (created later by independent reviewer only)

## Plan-ready state

At planning time, no application code, dependency manifest, tests, Git write,
push, or PR had been authorized or performed. Implementation and four local
milestone commits are now authorized; push, PR, branch switching, and review
remain explicitly out of scope.

## First implementation action

The Python Developer should read `PLAN.md`, `MILESTONES.md`, and this file, verify the existing workspace from disk, then implement M1 only. M1 is the cumulative shell/document-state milestone and must pass before M2 starts.

## Read-only starting state

- **Branch:** `experiment/no-helpers`
- **HEAD:** `60a3f9d3c18f23976b83e5b6ba95359dff09a65e`
- **Tracked changes:** none staged or unstaged
- **Configured remote:** `origin` (unused)
- **Pre-existing untracked paths:**
  - `.venv/`
  - `quickpad.egg-info/`
  - `quickpad/`
  - `tests/`
- **Workspace observation:** the root README describes only the demo repository. PyQt/pytest artefacts exist under untracked `.venv/` and egg metadata references `pyproject.toml`, `quickpad/__init__.py`, `quickpad/__main__.py`, and `quickpad/storage.py`, but no corresponding source/manifest files are currently visible at the root. Existing `tests/` and `quickpad/` contain cache/bytecode/environment content, not application sources in the inspected visible inventory.

This plan reconciles future implementation with existing untracked scaffolding. It does not assume those cache paths are product content or preserve/replace them during Git operations.

## Delivery switches

- **commit:** `milestone`
- **push:** `off`
- **pr:** `off`
- **Feature branch switch:** not authorized
- **Git writes:** not authorized during planning

## Chronological checkpoints

### 2026-11-20T15:00:40+01:00 — Python Planner — Planning artifacts

- **Milestone:** Plan-only gate
- **Changed paths:** root `PLAN.md`, `MILESTONES.md`, `HANDOFF.md`
- **Decisions:** selected PyQt6; four implementation milestones M1–M4; separate FT and IR gates; no database or unsupported formats.
- **Crucial UX decisions:** `.txt` is plain with explicit formatting-loss confirmation; `.html` uses a sanitized Qt subset and never loads external images/resources; cancelled or failed file actions never advance pending destructive state; public offsets use Unicode code-point positions; find is literal/case-insensitive/wrap-enabled by default; replacement is undoable; word count is a live count of Unicode letter/number/mark runs.
- **Check commands/results:** read-only file inventory and artifact inspection. `git --no-pager status --short --branch`, `git --no-pager rev-parse --verify HEAD`, and `git --no-pager remote` returned the baseline above. No tests run and no Git writes performed.
- **Blockers:** none for planning. Source implementation and independent review are future gates.
- **Next executable action:** implementation owner reads these files and reconciles M1 with the actual disk state before editing.

### 2026-11-20T15:18:48+01:00 — Python Developer — M1 verification

- **Milestone:** M1 complete; local commit to follow this checkpoint.
- **Changed paths:** `.gitignore`, `pyproject.toml`, `README.md`, `PLAN.md`,
  `MILESTONES.md`, `HANDOFF.md`, `quickpad\__init__.py`,
  `quickpad\__main__.py`, `quickpad\app.py`, `quickpad\document.py`,
  `quickpad\main_window.py`, `tests\conftest.py`, `tests\test_shell.py`,
  `tests\test_unsaved.py`.
- **Decisions:** Qt's modified/undo state supplies the clean baseline; New and
  Close share a synchronous Save/Discard/Cancel guard. Image-only clipboard
  data is rejected, other clipboard content is pasted as plain text, and
  document resource lookup is blocked. File saving is implemented in M3.
- **Checks:** with `$env:QT_QPA_PLATFORM = 'offscreen'`,
  `& .\.venv\Scripts\python.exe -m pytest -q tests\test_shell.py tests\test_unsaved.py`
  passed **8 tests**. An earlier run exposed a pytest-qt teardown prompt; its
  `before_close_func` now clears the modified flag before fixture cleanup.
- **Workspace reconciliation:** an independently authorized identity rewrite
  in another session temporarily stashed and restored the task files and changed
  HEAD from `60a3f9d3c18f23976b83e5b6ba95359dff09a65e` to
  `76bf88ff4a7fcced45731792b7f00038608a06d8`. Both commits have identical
  tree `e583ad462e207ad914231b5ac06f2ad3392c122d`; the branch remained
  `experiment/no-helpers`. The other session confirmed restoration and no
  remaining temporary stash; M1 was retested afterward.
- **Git choices/outcome:** `commit=milestone`, `push=off`, `pr=off`; M1 commit
  is next. Independent review is expressly pending, not requested.
- **Blockers:** none.
- **Next executable action:** stage only M1 paths, inspect the staged diff,
  commit M1, then implement and test M2.

### 2026-11-20T15:23:30+01:00 — Python Developer — M2 verification

- **Milestone:** M2 complete; local commit to follow this checkpoint.
- **Changed paths:** `quickpad\formatting.py`, `quickpad\main_window.py`,
  `tests\test_formatting.py`, `MILESTONES.md`, `HANDOFF.md`.
- **Decisions:** shared menu/toolbar actions apply selection or insertion
  formatting, with signal-blocked cursor synchronization. Bullet removal
  preserves paragraph indentation and groups changes for undo. Font-family
  entry remains usable when offscreen Qt has an empty font database.
- **Checks:** with `$env:QT_QPA_PLATFORM = 'offscreen'`,
  `& .\.venv\Scripts\python.exe -m pytest -q tests\test_shell.py tests\test_formatting.py tests\test_unsaved.py`
  passed **20 tests**. The first run exposed the empty offscreen font database;
  the control and test now handle it. Editor diagnostics reported no errors in
  the changed Python files.
- **Git choices/outcome:** M1 commit
  `674a3291b1beb6d4c1e4c58525dfbc23b1d8715e` was created locally after its
  staged diff was inspected. M2 is next; push and PR remain off.
- **Blockers:** none.
- **Next executable action:** stage only M2 paths, inspect the staged diff,
  commit M2, then implement and test M3.

### 2026-11-20T15:38:39+01:00 — Python Developer — M3 verification

- **Milestone:** M3 complete; local commit to follow this checkpoint.
- **Changed paths:** `quickpad\html_safety.py`, `quickpad\storage.py`,
  `quickpad\document.py`, `quickpad\main_window.py`, `tests\test_files.py`,
  `tests\test_unsaved.py`, `tests\test_shell.py`, `README.md`, `MILESTONES.md`,
  `HANDOFF.md`.
- **Decisions:** stage and sanitise Open before prompting; if the guard saves
  over that target, open the newly saved bytes. `QSaveFile` uses no direct-write
  fallback. Explicit document formatting, including default-looking formatting,
  warns before `.txt` conversion and is flattened only after a successful
  write. HTML preserves safe inline font, colour, alignment, heading, whitespace
  and list formatting while rejecting resource-bearing content. Two compact
  toolbars keep font controls visible at the 600×400 minimum window size.
- **Checks:** with `$env:QT_QPA_PLATFORM = 'offscreen'` and `PYTEST_ADDOPTS`
  setting a unique project-local `--basetemp`,
  `& .\.venv\Scripts\python.exe -m pytest -q tests\test_shell.py tests\test_formatting.py tests\test_files.py tests\test_unsaved.py`
  passed **67 tests**. Tests use actual UTF-8/HTML files, a real cancelled
  `QSaveFile` transaction, an actual OS write error, and clipboard/drop events;
  the owned test scratch was removed. Editor diagnostics reported no errors.
- **Git choices/outcome:** M2 commit
  `ada3a114c0709a6a14c74982172b500db1f3ebe1` was created locally after staged
  inspection. M3 is next; push and PR remain off.
- **Blockers:** none.
- **Next executable action:** stage only M3 paths, inspect the staged diff,
  commit M3, then implement and test M4.
