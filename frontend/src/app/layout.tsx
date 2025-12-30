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
          className="fixed -top-96 left-0 z-50 w-full bg-primary-600 p-4 text-center font-bold text-white shadow-lg transition-all focus:top-0"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  )
}
