'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import SiteHeader from './SiteHeader'
import { me, type User } from '@/lib/api'
import { clearToken, getToken } from '@/lib/session'

/**
 * Wraps a signed-in page: confirms there is a session, then renders the chrome
 * around it.
 *
 * The guard is a convenience, not a security boundary. This app is exported as
 * static HTML, so every page is downloadable by anyone and this check runs on
 * the user's own machine. What actually protects data is the backend rejecting
 * any request without a valid token — which is why the session is confirmed
 * with the server (`GET /api/auth/me`) rather than trusted from localStorage:
 * the database is recreated on every restart, so a token surviving in a
 * browser tab routinely refers to a session that no longer exists.
 */
type State =
  | { status: 'checking' }
  | { status: 'signedIn'; user: User }
  | { status: 'signedOut' }

export default function AppShell({
  subtitle,
  children,
}: {
  subtitle?: string
  children: React.ReactNode
}) {
  const router = useRouter()
  const [state, setState] = useState<State>({ status: 'checking' })

  useEffect(() => {
    if (!getToken()) {
      setState({ status: 'signedOut' })
      return
    }

    let cancelled = false
    me()
      .then((user) => {
        if (!cancelled) setState({ status: 'signedIn', user })
      })
      .catch(() => {
        // Any failure here — expired session, backend down — means we cannot
        // show this page, and the sign-in screen is the only useful next step.
        clearToken()
        if (!cancelled) setState({ status: 'signedOut' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    // `replace`, not `push`: a signed-out visit should not leave a history
    // entry that the back button bounces straight off again.
    if (state.status === 'signedOut') router.replace('/')
  }, [state.status, router])

  if (state.status !== 'signedIn') {
    return (
      <p className="shellStatus" role="status">
        {state.status === 'checking' ? 'Loading…' : 'Redirecting to sign in…'}
      </p>
    )
  }

  return (
    <>
      <SiteHeader
        subtitle={subtitle}
        user={state.user}
        onSignOut={() => setState({ status: 'signedOut' })}
      />
      {children}
    </>
  )
}
