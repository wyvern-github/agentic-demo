---
name: advanced-python
description: "Use when architecting, implementing, debugging, or refactoring a typed Python desktop application, utility, or mini game. Covers modular design, state, concurrency, error handling, and verification."
---

# Advanced Python Development

1. Identify a vertical slice and choose the smallest design that supports it. Reuse an existing project layout and supported interpreter range. For a new installable app, prefer a `pyproject.toml` and a package with a documented `python -m <package>` or console entry point.
2. Keep the entry point responsible for configuration and wiring. Separate domain rules from Qt widgets and I/O. For modest apps, plain functions, small classes, dataclasses, and enums are usually enough. Introduce a protocol only when an actual boundary or test double benefits.
3. Represent transitions explicitly for stateful workflows and games. Keep the game update logic independent of painting and keyboard events. Pass a clock, elapsed time, or a seeded random generator through the appropriate boundary so tests do not depend on timing or chance.
4. Make failure semantics deliberate. Validate at the input boundary; preserve useful exception context; let the UI translate expected domain and storage failures into actionable feedback. Log unexpected failures without exposing personal data. Do not mask errors, leave partial writes, or perform I/O at import time.
5. Keep Qt widgets on the GUI thread. Use a timer and elapsed time for a lightweight game loop; avoid blocking that loop with file or database work. Move genuinely slow I/O to an owned worker and return values/errors through signals. Give cancellation, application shutdown, resource ownership, and worker cleanup a clear order. Use processes for sustained CPU work only when warranted.
6. Put settings and user data in an application-specific directory, not the source tree or current directory; use `pathlib` or Qt's standard path API. Avoid global state unless an existing framework requires it. Use context managers for resources and document non-obvious side effects.
7. Verify a representative success case, boundary or invalid inputs, and relevant failure or restart behavior. Run the smallest useful test after each change and the full suite at the final gate. Profile before optimizing, and prefer simpler code when no bottleneck has been demonstrated.
