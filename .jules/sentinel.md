## 2025-01-15 - [Critical] Missing Input Validation
**Vulnerability:** Pydantic models in `blockchain.py` and `voting.py` accepted negative amounts and empty lists, allowing potential DoS or logic exploits.
**Learning:** Placeholders and "Draft" code often skip validation, assuming "happy path". Security constraints must be enforced at the API boundary regardless of implementation status.
**Prevention:** Use Pydantic `Field` constraints (`gt=0`, `min_length`, etc.) for all inputs by default.
