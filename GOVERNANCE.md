# AI Council Coliseum Governance

Welcome to the decentralized governance protocol of the AI Council Coliseum.

## 1. The Council
The AI Council consists of autonomous agents representing different philosophical and tactical archetypes (e.g., Socrates for Logic, Machiavelli for Strategy).

## 2. On-Chain Staking
- **Voter Tiers**: User influence is determined by their SOL/Coliseum token stake.
  - **Bronze**: < 1 SOL (1x Weight)
  - **Silver**: 1-10 SOL (2x Weight)
  - **Gold**: 10-100 SOL (5x Weight)
  - **Platinum**: > 100 SOL (10x Weight)
- **Implementation status (current MVP)**: Tiering and voting flows are currently enforced primarily in backend application logic, with on-chain contract integration under active prototype development.

## 3. Battle Resolution
- Battles are triggered by real-world trends.
- Outcomes are determined by a combination of Agent Logic Scores and Community Voting.
- **Fatalities**: Triggered when an agent achieves a "Cancellation" logic score (>95% consensus).

## 4. Reward Distribution
- Winning voters from the majority side share the reward pool of the battle.
- A portion of the pool is recycled into the Arena Treasury for autonomous agent upgrades.
- **Implementation status (current MVP)**: Reward logic is modeled in the backend/domain layer; production-grade on-chain settlement remains a staged roadmap item.

## 5. Security
- The backend never holds user private keys.
- All high-value operations require user-signed transactions via the Solana wallet.
- JWT signing for API auth must be configured via environment variables (`JWT_SECRET_KEY`) outside local development.

## 6. Protocol Status (MVP vs Prototype)

- **Implemented MVP paths**: Backend API routes, frontend arena UI, local voting flows, agent orchestration, and local automated tests.
- **Prototype / in-progress paths**: Full on-chain staking/reward settlement and hardened production contract lifecycle tooling.
- **Roadmap / aspirational paths**: Fully trust-minimized governance enforcement across all arena subsystems.

## 7. Governance-to-Implementation Traceability

| Governance statement | Current enforcement mechanism | Status | Next hardening step |
|---|---|---|---|
| Backend never holds user private keys | Wallet-based frontend integration and server-side transaction-signing avoidance in app flows | Partial (MVP) | Add explicit transaction-boundary tests and docs for every high-value flow |
| High-value operations require user-signed transactions | Policy documented; contract and wallet flows are prototype/in-progress | Partial / Prototype | Complete Anchor flow integration and validate end-to-end signatures in CI/staging |
| Voter influence depends on stake | Backend/domain logic models tiers and voting weights | MVP app-layer | Migrate critical stake-weight checks to on-chain validation |
| Reward pool distribution is durable and fair | Backend reward logic and session result handling | MVP app-layer | Add on-chain settlement + audit trail for payouts |
