'use client'

import Link from 'next/link'
import { logout } from '@/lib/api'
import { clearToken } from '@/lib/session'
import type { User } from '@/lib/api'

/**
 * The app chrome above every signed-in page: branding on the left, who you are
 * and a way out on the right.
 *
 * Branding, not a document heading — the agreement's own title is the page's
 * `<h1>`, so nothing here may compete with it in the outline.
 */
export default function SiteHeader({
  subtitle,
  user,
  onSignOut,
}: {
  /** What the current page is, e.g. the name of the agreement being drafted. */
  subtitle?: string
  user: User
  onSignOut: () => void
}) {
  const signOut = async () => {
    // Revoke server-side first: the request identifies the session by the very
    // token being discarded, so clearing it first would send an unauthenticated
    // logout that silently revokes nothing.
    try {
      await logout()
    } catch {
      // Sign out locally regardless. The user asked to leave, and a session we
      // could not revoke is no longer reachable once the token is gone.
    } finally {
      clearToken()
      onSignOut()
    }
  }

  return (
    <header className="siteHeader">
      <p className="brand">Prelegal</p>
      {subtitle && <p>{subtitle}</p>}
      <nav className="siteHeaderSession">
        <Link href="/documents/">Your agreements</Link>
        <Link href="/draft/">New agreement</Link>
        <p className="sessionEmail">{user.email}</p>
        <button type="button" className="linkButton" onClick={signOut}>
          Sign out
        </button>
      </nav>
    </header>
  )
}
