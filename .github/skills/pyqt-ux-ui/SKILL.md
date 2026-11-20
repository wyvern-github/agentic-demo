---
name: pyqt-ux-ui
description: "Use when designing or polishing a PyQt6 desktop office application, utility, or mini game. Covers art direction, accessible color, typography, layout, interaction, and game presentation."
---

# Advanced PyQt UX/UI Design

## Establish a Visual Direction

1. Identify the audience, the first useful action, and the most repeated interaction. Sketch the main window and its empty, populated, loading, and error states before styling.
2. Consider different treatments when the brief leaves room for invention. Pick one and record why it fits the audience. Give the app one recognizable visual idea through typography, iconography, a domain-specific illustration, or game art. Keep conventional controls predictable.
3. Use a spacing scale, for example 4, 8, 12, 16, and 24 logical pixels. Define type roles, icon sizes, and minimum content sizes. Favor native Qt widgets, layout managers, scalable icons, and system font fallback. Use assets you can legally ship and record their sources.

## Choose Colors for People

- Define semantic tokens for window, surface, text, muted text, border, accent, selection, focus, success, warning, and error. Centralize them in a palette or a small style module. Apply QSS selectively so native keyboard, hover, checked, and disabled states survive.
- For an office app, start with quiet neutrals and one decision color: `#F6F8FB` window, `#FFFFFF` surface, `#172033` text, `#475569` secondary text, `#075E54` action with white text. Reserve status colors for status. Adjust the starting palette to the domain rather than reusing it blindly.
- For a mini game, a stronger contrast of materials and colors can support the action: `#191921` backdrop, `#292930` panels, `#F5F5EF` text, `#B8ED62` player or primary action, and `#FFD166` rewards. Use silhouettes, symbols, and spatial cues so game objects remain distinct without color.
- Verify actual foreground/background pairs, including selection and focus. Target WCAG AA as a desktop design baseline: 4.5:1 for normal text, 3:1 for large text and meaningful control boundaries or graphics. Never communicate a state by hue alone. Check grayscale, color-vision simulation when available, and system contrast behavior.

## Fit the Interaction to the App

- Office: put the working view in the center, optimize scanning and keyboard navigation, and place commands near their targets. Offer non-destructive recovery or undo where practical. Preserve selection during refresh and show no-results, validation, and save states inline where appropriate.
- Games: show the playable surface immediately. Make score, time, or lives readable without competing with gameplay. Define controls, pause, restart, and end states. Pause when focus is lost if continuing would penalize the player. Keep animation bounded and avoid rapid flashes or mandatory sound cues.
- Resize from a defined minimum to a wide window without clipping. Test font scaling, long labels, and Windows display scaling. Give icon-only actions accessible names, sensible tooltips, and visible keyboard focus. Verify tab order and use native modal behavior only when a decision genuinely blocks progress.

## Verify the Result

Exercise the main task and failure recovery with mouse and keyboard. Inspect an empty and populated or active state, a narrow and normal window, and display scaling where available. For a game, exercise start, play, pause, loss/win, and restart without resetting unrelated preferences. Record visual evidence or explicitly note when only headless tests were possible.
