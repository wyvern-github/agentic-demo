---
description: "Use when writing, modifying, or reviewing Python source. Defines style, typing, docstrings, error handling, resource safety, and project setup."
applyTo: "**/*.py"
---

# Python Programming Standards

- Use the project's supported Python version, tooling, and conventions. Otherwise follow PEP 8, use meaningful names, and prefer the standard library or an established, declared dependency over an unnecessary framework. Keep imports side-effect free.
- Write a concise module docstring in each maintained source file. Document public classes, functions, and methods with PEP 257-style docstrings. Describe intent and non-obvious inputs, return values, raised errors, invariants, units, and side effects where applicable. Explain why tricky code exists; do not repeat the signature or narrate obvious statements.
- Type public parameters and return values, important data models, and cross-component boundaries. Use explicit `None` checks where it has meaning. Resolve types using the actual API or local type checker rather than hiding errors behind `Any` or broad ignores.
- Keep functions focused. Separate domain logic from Qt widgets, database code, and other side effects. Keep resource ownership clear with context managers or explicit lifecycle methods. Catch expected exceptions at an appropriate boundary and propagate unexpected failures with context.
- Do not hard-code machine-specific paths, credentials, or personal data. Use a project-local environment for dependencies, and keep it, caches, and runtime databases out of version control. Document supported versions, dependencies, and the run/test commands for a runnable app.
- Make the smallest behavior change that satisfies the acceptance criteria. Run configured formatting, linting, and typing checks for changed code, and follow the pytest instructions for behavioral verification.
