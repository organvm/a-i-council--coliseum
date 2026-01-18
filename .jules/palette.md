# Palette's Journal

## 2025-05-18 - Broken Skip-to-Content Links
**Learning:** Adding a "Skip to content" link is useless if the target ID doesn't exist. Furthermore, to ensure programmatic focus works reliably across all browsers after navigation, the target container must have `tabIndex={-1}` and `outline-none`.
**Action:** Always verify that internal anchor links have a matching `id` in the DOM and that the target is focusable if it's not a native interactive element.
