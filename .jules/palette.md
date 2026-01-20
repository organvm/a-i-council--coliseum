## 2026-01-20 - Skip Link Target Focus
**Learning:** Implementing a robust "Skip to content" feature requires the target container (e.g., `<main>`) to have `tabIndex={-1}` and `outline-none` attributes to ensure programmatic focus is correctly handled across browsers.
**Action:** Always check that internal anchor targets have `tabIndex={-1}` to ensure focus lands correctly.
