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
          className="fixed top-4 left-4 z-50 -translate-y-[200%] transition-transform focus:translate-y-0 bg-primary-600 text-white px-4 py-2 rounded-lg shadow-lg font-medium"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  )
}
