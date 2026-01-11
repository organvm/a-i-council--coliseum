# Palette's Journal

## 2024-05-22 - Broken Skip Links
**Learning:** Adding a "Skip to content" link is useless if the target ID doesn't exist. Often developers add the link in the layout but forget to tag the main content area in the page templates.
**Action:** Always verify that `#main-content` (or equivalent) actually exists in the DOM when seeing a skip link in the code. Ensure the target has `tabIndex={-1}` to reliably receive focus.
