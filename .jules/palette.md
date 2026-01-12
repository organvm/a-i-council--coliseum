## 2024-03-24 - Broken Skip Link
**Learning:** A "Skip to content" link is useless if the target ID doesn't exist. This is a common "invisible" bug because mouse users never see it. Always verify the `id` matches the `href`.
**Action:** When auditing accessibility, always click the skip link to ensure it actually moves focus to the main content container (which needs `tabIndex="-1"` and `outline: none` for programmatic focus).
