# Palette's Journal

## 2024-05-22 - Skip Link Implementation
**Learning:** Even in single-page layouts like this one, providing a "Skip to content" link is critical for keyboard users to bypass any future repetitive navigation (or even just to quickly get to the main content).
**Action:** Always include a skip link in `RootLayout` and ensure the main content container has a corresponding ID. Using `focus:not-sr-only` (or equivalent absolute positioning overrides) keeps it invisible until needed.
