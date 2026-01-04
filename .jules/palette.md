## 2024-05-23 - Robust Skip Links
**Learning:** Standard "skip to content" links often fail because the target container lacks `tabIndex={-1}`, preventing programmatic focus transfer in many browsers.
**Action:** Always add `id="target"`, `tabIndex={-1}`, and `outline-none` to the main content container when implementing skip links.
