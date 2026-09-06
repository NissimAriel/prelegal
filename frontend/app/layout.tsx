import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Prelegal',
  description:
    'Draft common legal agreements from curated templates, in your browser.',
}

/**
 * The document shell, and nothing else.
 *
 * App chrome lives in `components/AppShell` rather than here, because the
 * sign-in screen has no session and so has no header, user or sign-out control
 * to show.
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
