# Frontend Implementation Todos

This file tracks granular tasks for the frontend development.

## 🧩 Components (`src/components/`)

- [ ] **Agent Views**
    - [ ] `AgentCard`: Component to display agent avatar, name, role, and current status.
    - [ ] `AgentGrid`: Layout grid for active agents.
    - [ ] `AgentThoughtBubble`: Visual representation of internal monologue/reasoning.
- [ ] **Chat & Debate**
    - [ ] `ChatStream`: Scrollable list of messages.
    - [ ] `ChatMessage`: Individual message component (supports Markdown).
    - [ ] `TypingIndicator`: Visual cue when agents are generating.
- [ ] **Voting**
    - [ ] `VotingPanel`: Container for active polls.
    - [ ] `PollCard`: Displays question and options.
    - [ ] `VoteButton`: Interactive button with loading state.
    - [ ] `ResultsChart`: Bar/Pie chart for real-time results.
- [ ] **Events**
    - [ ] `EventTicker`: Scrolling ticker of recent headlines.
    - [ ] `EventFeed`: Detailed list of processed events.
- [ ] **User & Profile**
    - [ ] `WalletConnectButton`: Integration with Solana Wallet Adapter.
    - [ ] `AchievementBadge`: Visual icon for earned achievements.
    - [ ] `StatsCard`: Display user points/rank.

## 📄 Pages (`src/app/`)

- [ ] **Home / Dashboard** (`page.tsx`)
    - [ ] Layout structure: Stream center, Agents left, Chat right, Events bottom.
    - [ ] Implement responsive grid.
- [ ] **Leaderboard** (`/leaderboard/page.tsx`)
    - [ ] Table view of top users.
    - [ ] Filter by time/category.
- [ ] **Profile** (`/profile/page.tsx`)
    - [ ] User details view.
    - [ ] Achievement showcase.
- [ ] **About / Docs**
    - [ ] Static info pages.

## 🔌 Integration & State

- [ ] **API Client**
    - [ ] Create `src/lib/api.ts` with Axios/Fetch wrappers.
    - [ ] Implement typed response interfaces.
- [ ] **WebSockets**
    - [ ] Create `useWebSocket` hook for real-time updates.
    - [ ] Handle message types: `agent_message`, `vote_update`, `new_event`.
- [ ] **State Management**
    - [ ] Set up Context or Zustand store for:
        - `AgentStore` (active agents list).
        - `EventStore` (feed data).
        - `UserStore` (auth, wallet, profile).

## 🎨 UI/UX

- [ ] **Theme**
    - [ ] Refine Tailwind config (colors, fonts).
    - [ ] Implement Dark/Light mode toggle.
- [ ] **Animations**
    - [ ] Add Framer Motion for entering/leaving elements (chat messages).
    - [ ] Add transitions for voting updates.
