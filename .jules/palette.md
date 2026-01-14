## 2024-05-22 - Fix broken skip-to-content link
**Learning:** The skip-to-content link in `layout.tsx` targeted `#main-content`, but the ID was missing in `page.tsx`. This renders the accessibility feature useless.
**Action:** Always verify that skip links have a corresponding target ID, and ensure the target is programmatically focusable (`tabIndex={-1}`) for reliable navigation.
