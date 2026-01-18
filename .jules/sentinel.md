## 2024-05-22 - Missing Pydantic Validation Constraints
**Vulnerability:** API models for financial operations (staking, transfer) and voting lacked range and length constraints, allowing negative amounts and invalid data.
**Learning:** Pydantic models default to simple type checks (`float`) which allows any float (including negative). Explicit `Field(gt=0)` is required for security.
**Prevention:** Always use `Field` with `gt/ge/lt/le` and `min_length/max_length` for all API inputs, especially for financial or resource-intensive fields.
