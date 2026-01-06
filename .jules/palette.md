# Palette's Journal - Critical UX/A11y Learnings

## 2024-05-22 - [Phantom Skip Links]
**Learning:** Skip-to-content links often rot because the target ID (`#main-content`) is missing from the main container. This makes the feature completely broken for keyboard users despite visually appearing to work (it just scrolls up or does nothing).
**Action:** Always verify the `id` attribute exists on the target element when seeing a skip link in `layout.tsx`.
