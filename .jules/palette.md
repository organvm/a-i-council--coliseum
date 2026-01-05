## 2024-05-23 - Skip to Content Disconnect
**Learning:** A "Skip to content" link in the layout is useless if the target element (ID) doesn't exist on the page. Next.js App Router separates layout and page, making this easy to miss.
**Action:** Always verify the target ID exists in the main page component when seeing a skip link in the layout. Use `tabIndex={-1}` on the target container to ensure focus lands correctly.
