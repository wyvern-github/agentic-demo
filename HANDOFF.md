# QuickPad handoff

**State:** M4 committed; final verification is in progress.

**Artifacts:** [Plan](./PLAN.md), [Milestones](./MILESTONES.md), [Handoff](./HANDOFF.md).

**Delivery:** `commit=milestone`, `push=off`, `pr=off`. No remote or PR target required.

## Checkpoints

### 2026-11-20 14:03:08 +01:00 | Python Planner | Planning

- Changed paths: `PLAN.md`, `MILESTONES.md`, `HANDOFF.md`.
- Decisions: One local document at a time; Qt owns formatting and undo; HTML keeps supported formatting; TXT conversion requires confirmation if styles would be lost. Four pytest-qt milestones, then a full test run, native smoke check, and independent review.
- Verification: No commands or runtime tests run during planning. No Git actions taken. No planning blockers.
- Starting branch, `HEAD` (or unborn state), and pre-existing changes: not inspected during planning; record before editing application files.
- Next action when implementation is requested: re-read the artifacts, run `git status --short --branch`, `git rev-parse --verify HEAD`, and `git remote -v` locally, then record the baseline and begin M1. Preserve existing changes and omit sensitive remote details from the handoff.

### 2026-11-20 14:07:14 +01:00 | Python Developer | Preflight

- Changed paths: `PLAN.md`, `MILESTONES.md`, `HANDOFF.md` (baseline and M1 status).
- Starting branch: `main`; starting `HEAD`: `1594f1548d05e692fed4f9e6a17502b9dbc7284a`. Before implementation, `PLAN.md`, `MILESTONES.md`, and `HANDOFF.md` were untracked planning artifacts; there were no staged or other worktree changes. They belong to this task and will be included with M1.
- Decisions: The approved delivery choices are `commit=milestone`, `push=off`, `pr=off`. An `origin` remote exists but will not be used. The user requested implementation only; independent review remains pending.
- Checks: `git status --short --branch`, `git status --porcelain=v1 -uall`, `git diff --cached --name-status`, `git diff --name-status`, `git branch --show-current`, `git rev-parse --verify HEAD`, and `git remote -v` confirmed the baseline. `python --version` reported Python 3.12.10; no project-local `.venv` existed.
- Blockers: None.
- Next action: create the project-local environment and implement M1, then run its exit check before the first local commit.

### 2026-11-20 14:11:59 +01:00 | Python Developer | M1

- Changed paths: `.gitignore`, `pyproject.toml`, `quickpad/__init__.py`, `quickpad/__main__.py`, `quickpad/storage.py`, `quickpad/window.py`, `tests/conftest.py`, `tests/test_files.py`, `MILESTONES.md`, and `HANDOFF.md`; the task's existing `PLAN.md` is also included in delivery.
- Decisions: Installed PyQt6, pytest, and pytest-qt in the ignored project-local `.venv`; HTML resources are blocked and images removed. QSaveFile uses no direct-write fallback, so failed writes leave an existing destination intact.
- Checks: `python -m venv .venv` and `.\.venv\Scripts\python.exe -m pip install -e ".[test]"` succeeded. With `QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q tests\test_files.py` passed: **13 passed**. `git check-ignore .venv\Scripts\python.exe` confirmed the environment is ignored.
- Blockers: None. Push and PR remain off.
- Next action: commit M1 locally, record its receipt, and implement M2 formatting and conversion.

### 2026-11-20 14:12:53 +01:00 | Python Developer | M1 delivery

- Changed paths: `MILESTONES.md`, `HANDOFF.md` (receipt and M2 status).
- Decision and result: committed M1 locally as `d601cd0b32f0b67ed951be4c0720ba73a1365313`; no push or PR. The staged diff was checked for unrelated files, secrets, and whitespace before committing.
- Checks: `git diff --cached --check` passed; `git status --short` was clean immediately after the commit.
- Blockers: None.
- Next action: implement M2, verify its exit check, update the artifacts, and commit.

### 2026-11-20 14:19:13 +01:00 | Python Developer | M2

- Changed paths: `quickpad/window.py`, `tests/test_formatting.py`, `MILESTONES.md`, and `HANDOFF.md`.
- Decisions: Formatting operates on Qt selections or subsequent typing; plain documents disable its controls. Lossy TXT conversion requires confirmation before the atomic write, resets formatting and history only after success, and leaves rich state intact on cancellation or failure. Non-lossy text saves keep undo history.
- Checks: With `QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q tests\test_formatting.py` passed: **21 passed**. The combined M1/M2 regression run, `.\.venv\Scripts\python.exe -m pytest -q tests\test_formatting.py tests\test_files.py -x`, passed: **34 passed**. The offscreen Qt plugin did not enumerate native Windows fonts, so font-choice appearance remains a native smoke-check item.
- Blockers: None. Push and PR remain off.
- Next action: commit M2 locally, record its receipt, and implement M3 Find & Replace.

### 2026-11-20 14:19:46 +01:00 | Python Developer | M2 delivery

- Changed paths: `MILESTONES.md`, `HANDOFF.md` (receipt and M3 status).
- Decision and result: committed M2 locally as `ba1d7f83a045f59c046f5ee66c66149f3176040b`; no push or PR. The staged diff was checked for unrelated files, secrets, and whitespace.
- Checks: `git diff --cached --check` passed; `git status --short` was clean immediately after the commit.
- Blockers: None.
- Next action: implement M3, verify its exit check, update the artifacts, and commit.

### 2026-11-20 14:22:59 +01:00 | Python Developer | M3

- Changed paths: `quickpad/find_replace.py`, `quickpad/window.py`, `tests/test_find_replace.py`, `MILESTONES.md`, and `HANDOFF.md`.
- Decisions: Find & Replace uses Qt document cursors for literal, case-insensitive matches and non-BMP-safe positions. Each replacement inherits the first matched character's format; Replace All is one undoable edit. Empty replacement deletes; invalid multiline input is disabled with feedback.
- Checks: With `QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q tests\test_find_replace.py` passed: **13 passed**. The combined M1–M3 run, `.\.venv\Scripts\python.exe -m pytest -q tests\test_find_replace.py tests\test_formatting.py tests\test_files.py`, passed: **47 passed**.
- Blockers: None. Offscreen resize and focus checks passed; native visual and display-scaling checks remain pending.
- Next action: commit M3 locally, record its receipt, and implement M4 unsaved-change protection.

### 2026-11-20 14:23:25 +01:00 | Python Developer | M3 delivery

- Changed paths: `MILESTONES.md`, `HANDOFF.md` (receipt and M4 status).
- Decision and result: committed M3 locally as `1f42c99eaae576495efb64a02788736d6b9e3b7b`; no push or PR. The staged diff was checked for unrelated files, secrets, and whitespace.
- Checks: `git diff --cached --check` passed; `git status --short` was clean immediately after the commit.
- Blockers: None.
- Next action: implement M4, verify its exit check, update the artifacts, and commit.

### 2026-11-20 14:28:06 +01:00 | Python Developer | M4

- Changed paths: `quickpad/window.py`, `tests/conftest.py`, `tests/test_files.py`, `tests/test_formatting.py`, `tests/test_unsaved.py`, `README.md`, `MILESTONES.md`, and `HANDOFF.md`.
- Decisions: New, Open, and Close offer Save, Discard, or Cancel for modified documents; failed or canceled saves stop the action. Discard followed by canceled or failed Open preserves the active document. Added launch and usage instructions.
- Checks: With `QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q tests\test_unsaved.py` passed: **28 passed**. The M1–M3 regression run, `.\.venv\Scripts\python.exe -m pytest -q tests\test_files.py tests\test_formatting.py tests\test_find_replace.py`, passed: **47 passed**.
- Investigation: The first regression run stalled in pytest-qt cleanup because it closes registered widgets before fixture teardown. The fixture now clears the modified flag in pytest-qt's `before_close_func`; the repeated checks above passed.
- Blockers: None. Push and PR remain off.
- Next action: commit M4 locally, then run the full suite and the documented launch command. Leave independent review pending as requested.

### 2026-11-20 14:28:32 +01:00 | Python Developer | M4 delivery

- Changed paths: `MILESTONES.md`, `HANDOFF.md` (receipt and final-gate status).
- Decision and result: committed M4 locally as `48b8bcc6b1764e5afacbfe649927cd631e5f3212`; no push or PR. The staged diff was checked for unrelated files, secrets, and whitespace.
- Checks: `git diff --cached --check` passed; `git status --short` was clean immediately after the commit.
- Blockers: None.
- Next action: run the full suite and documented launch command; record the results and any unavailable manual checks. Do not request independent review in this implementation-only stage.

### 2026-11-20 14:41:10 +01:00 | Python Developer | M2 toolbar correction

- Changed paths: `quickpad/window.py`, `tests/test_formatting.py`, `MILESTONES.md`, and `HANDOFF.md`.
- Investigation and decision: Native Windows smoke testing at the 640-pixel minimum showed font family and size hidden in the toolbar overflow; synthetic expansion was unreliable with an active selection. Compact control widths keep them visible in that scenario. A long-font-name regression reproduced the issue without the width constraints. The size field was also checked at 512 pt to avoid clipping its suffix.
- Checks: With `QT_QPA_PLATFORM=offscreen`, `.\.venv\Scripts\python.exe -m pytest -q tests\test_formatting.py` passed: **22 passed**. A native Windows Qt smoke check at 640×400 verified both controls visible, applied a font and 512 pt size to a selection, and confirmed the full size label fits. The earlier complete suite passed **75 tests** and the native launch closed with exit 0 before this correction; both final gates must be rerun against the corrected state.
- Blockers: None. This in-scope correction needs an additional local commit because it was discovered after the four milestone commits; no push or PR.
- Next action: commit the verified toolbar correction, then rerun the complete suite and native launch. Leave independent review pending.
