---
description: "Use when adding, modifying, running, or reviewing pytest tests for Python application code, PyQt UI behavior, SQLite persistence, or game logic."
applyTo: "**/test_*.py,**/*_test.py,**/conftest.py"
---

# Pytest Standards

- Put tests under `tests/` unless the project already uses another convention. Name each test for an observable result, such as `test_reopening_preserves_saved_invoice`. Check behavior rather than internal method calls unless the interaction is itself the contract.
- Cover a representative success path, boundary or invalid input, and foreseeable failure. Add a regression test for bug fixes. Use parametrization for equivalent cases, fixtures for shared setup, and simple arrange, act, and assert sections when that improves readability.
- Make tests deterministic. Use `tmp_path` for disposable files and file-backed SQLite behavior, and inject clocks or seed random generators for game logic. Stub external I/O at its boundary. Don't use production data, require external services, or make assertions depend on execution order or arbitrary sleeps.
- Use `pytest-qt` for important PyQt behavior. Use `qtbot.addWidget`, simulated input, and `waitSignal` or `waitUntil`. Assert visible state, signal outcomes, keyboard behavior, and the effect of actions. Test pure logic without creating Qt widgets when possible.
- Use the selected interpreter: `python -m pytest tests/test_example.py -q` for a focused check and `python -m pytest -q` for the final sweep. Configure the Qt binding explicitly if multiple bindings are installed. For headless tests set `QT_QPA_PLATFORM=offscreen` before constructing `QApplication`, for that test process only. Do not count offscreen checks as manual visual verification.
- Report exact commands and pass/fail/skip outcomes. Investigate flakes rather than adding sleeps or blanket retries. If a necessary test or dependency cannot run, explain the blocker and mark that acceptance check unverified.
