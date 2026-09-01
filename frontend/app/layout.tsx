import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Mutual NDA creator — Prelegal',
  description:
    'Fill in a few key details and download a completed Common Paper Mutual Non-Disclosure Agreement.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {/* Branding, not a document heading — the agreement's own title is the
            page's <h1>, so this must not compete with it in the outline. */}
        <header className="siteHeader">
          <p className="brand">Prelegal</p>
          <p>Mutual Non-Disclosure Agreement</p>
        </header>
        {children}
      </body>
    </html>
  )
}
