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
