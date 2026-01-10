## 2024-05-23 - Robust Skip-to-Content Implementation
**Learning:** Simply adding an ID to a target element isn't always enough for consistent "Skip to Content" behavior across all browsers and screen readers. The target must also be programmatically focusable.
**Action:** Always add `tabIndex={-1}` and `outline-none` (to prevent focus styles on the container itself) to the `<main>` element or skip target. This ensures focus actually lands and stays on the content container, allowing the next Tab press to correctly navigate to the first interactive element inside.
