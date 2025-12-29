## 2024-05-23 - Heapq vs Timsort on Sorted Data
**Learning:** `heapq.nlargest` (O(N log K)) is SLOWER than `sorted` (O(N) best case) when data is already nearly sorted.
**Action:** Only use `heapq` for "top K" when data is likely unsorted (like random access counts). If data is time-series or append-only, `sorted` (Timsort) detects the run and is faster.
