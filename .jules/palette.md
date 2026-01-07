## 2024-05-22 - Broken Skip Link Targets
**Learning:** Skip links must point to valid IDs (`#main-content`) that exist on the page. A missing ID makes the accessibility feature worse than useless as it disorients users.
**Action:** Always verify `id="main-content"` exists on the `<main>` tag when using standard layout templates. Use `tabIndex={-1}` to ensure programmatically focusable.
