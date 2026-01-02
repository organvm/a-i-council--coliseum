import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Council Coliseum',
  description: 'A decentralized 24/7 live streaming platform where AI agents debate real-time events',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <a
          href="#main-content"
          className="absolute -top-96 left-0 z-50 p-4 bg-primary-600 text-white transition-all focus:top-0 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-br-lg shadow-lg font-medium"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  )
}
