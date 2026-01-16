## 2026-01-16 - MemoryManager Optimization
**Learning:** The `MemoryManager` was using O(N) eviction because it iterated over a standard dict to find the minimum access time. `collections.OrderedDict` allows O(1) eviction by maintaining order and using `popitem(last=False)`.
**Action:** When implementing LRU caches in Python, always prefer `OrderedDict` or `functools.lru_cache` over manual list/dict management for O(1) performance.
