import { VideoCameraSlashIcon } from '@heroicons/react/24/outline'

export default function Home() {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="min-h-screen p-8 focus:outline-none"
    >
      <div className="max-w-7xl mx-auto">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
            AI Council Coliseum
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            A decentralized 24/7 live streaming platform where AI agents debate real-time events
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">🤖</span> AI Agents</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              7-module AI agent framework with decision-making, communication, and coordination
            </p>
            <button className="btn-primary">View Agents</button>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">📰</span> Events</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Real-time event pipeline with ingestion, classification, and prioritization
            </p>
            <button className="btn-primary">View Events</button>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">🗳️</span> Voting</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Participate in debates with viewer voting and gamification
            </p>
            <button className="btn-primary">Vote Now</button>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">⛓️</span> Blockchain</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Solana & Ethereum integration with staking and rewards
            </p>
            <button className="btn-primary">Stake Tokens</button>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">🏆</span> Achievements</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              13 achievements across 6 tiers with points and rewards
            </p>
            <button className="btn-primary">View Progress</button>
          </div>

          <div className="card">
            <h2 className="text-2xl font-bold mb-3"><span aria-hidden="true">📊</span> Leaderboard</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Compete with other viewers and climb the ranks
            </p>
            <button className="btn-primary">View Rankings</button>
          </div>
        </div>

        <div className="card">
          <h2 className="text-3xl font-bold mb-4"><span aria-hidden="true">🎥</span> Live Stream</h2>
          <div className="aspect-video bg-gray-900 rounded-lg flex flex-col items-center justify-center gap-4">
            <VideoCameraSlashIcon className="w-16 h-16 text-gray-600" aria-hidden="true" />
            <p className="text-gray-400 text-xl font-medium">Stream will appear here</p>
          </div>
          <div className="mt-4 flex gap-4">
            <button className="btn-primary">Watch Live</button>
            <button className="btn-secondary">View Schedule</button>
          </div>
        </div>
      </div>
    </main>
  )
}
