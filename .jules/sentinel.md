## 2024-05-22 - Missing Pydantic Validation Constraints
**Vulnerability:** Several API models (StakeRequest, TransferRequest, VotingSession) allowed negative or invalid values (e.g., negative stake amounts) because they used plain types like `float` or `int` without Pydantic constraints.
**Learning:** In this codebase, Pydantic models are used for request bodies but often lack `Field` constraints (`gt`, `min_length`, etc.), relying on placeholder logic that doesn't validate. This suggests a pattern where API definitions were prioritized over robust validation.
**Prevention:** Always use `pydantic.Field` with explicit constraints (e.g., `gt=0`, `min_length=1`) for numeric and string fields in request models, rather than relying on downstream logic or type hints alone.
