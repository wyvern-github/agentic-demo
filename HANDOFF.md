# QuickPad handoff

**State:** M1 verified; M2 is next.

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
