## 2024-05-23 - Keyword Extraction Optimization
**Learning:** `sorted(list, reverse=True)[:k]` is O(N log N) which is inefficient for finding top K elements when N is large. `heapq.nlargest(k, list)` is O(N log K) and significantly faster for small K.
**Action:** Use `heapq.nlargest` or `heapq.nsmallest` when only the top/bottom K elements are needed from a collection.
