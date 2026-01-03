## 2025-02-18 - Broken Skip-to-Content Pattern
**Learning:** The "Skip to content" link was implemented in `layout.tsx`, but the target `<main>` element in `page.tsx` lacked the corresponding `id` and `tabIndex`, rendering the accessibility feature non-functional.
**Action:** When auditing "Skip to content" links, always verify both the source (the link) and the destination (the target ID + `tabIndex="-1"` for focusability).
