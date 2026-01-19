## 2026-01-19 - [Hoisting System Calls out of Loops]
**Learning:** System calls like `datetime.utcnow()` are surprisingly expensive inside tight loops (like sort keys). Hoisting them out can yield significant speedups (e.g., >50% in benchmarks).
**Action:** Always verify if loop invariants or time-dependent variables (current time) can be calculated once before the loop.
