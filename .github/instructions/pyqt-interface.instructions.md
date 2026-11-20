---
description: "Use when building, changing, or reviewing PyQt desktop interfaces, including QMainWindow, toolbars, ribbons, docks, panels, and game controls."
---

# PyQt Interface Basics

- Default to PyQt6 for new GUI work unless the project or brief requires another binding. Use `QMainWindow` for a desktop shell, a central widget for the primary task, and layouts instead of absolute geometry. Keep the first view usable immediately. Give empty, error, and disabled states deliberate treatments.
- **Toolbar:** Use `QToolBar` and share `QAction` instances with menus or shortcuts so enabled and checked state stays synchronized. Put frequent, contextual actions in small groups with separators. Use recognizable icons, a label for ambiguous commands, and an accessible name and tooltip for icon-only actions. Verify overflow, focus, and hit areas at the smallest supported window.
- **Ribbon:** Use only for an action-rich office workflow or when requested. A `QTabWidget` or equivalent can hold task tabs such as Home and Data, with clearly labeled command groups. Give the most important actions visual priority, use compact secondary controls, and keep overflow or a collapse option discoverable. Don't force a ribbon onto a simple utility or a game.
- **Panels:** Prefer a `QSplitter` for adjacent views or `QDockWidget` for optional tools. Preserve useful minimum widths and keep the primary view larger than auxiliary panels. Give each optional dock a meaningful title and a menu action to show it again. Persist layout preferences via `QSettings` when useful and offer a reset if layouts are customizable.
- Prefer native controls for editing, selection, and menus; keep styling in shared tokens. Show destructive actions deliberately, separate transient status from decisions, and don't obscure the main task with ornamental containers. Set keyboard focus order and standard shortcuts, use clear labels for fields, and don't rely on color alone.
- For games, prioritize the play area and a stable HUD. Use a compact menu or overlay for pause and restart instead of application chrome that takes space from play.
- Check resized layouts, long labels, interaction states, keyboard-only use, and high-DPI scaling where available.
