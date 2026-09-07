'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ApiError, login } from '@/lib/api'
import { getToken, setToken } from '@/lib/session'

/** Where a successful sign-in lands. The only page in the product so far. */
const HOME = '/draft/'

/**
 * The sign-in screen.
 *
 * There is no password field, because there is no authentication yet: any
 * valid email address identifies a user and creates one on first sight. This
 * is the V1 foundation's stub (see backend/app/auth.py) — it exists so the
 * session plumbing, the users table and the route guard are all real and
 * exercised, leaving a later ticket to add a credential rather than a login.
 */
export default function LoginScreen() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Someone arriving with a session already in hand does not need to sign in
  // again. The token is not verified here; `AppShell` does that on arrival, and
  // sends them back if it turns out to be stale.
  useEffect(() => {
    if (getToken()) router.replace(HOME)
  }, [router])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const { token } = await login(email.trim())
      setToken(token)
      router.replace(HOME)
    } catch (cause) {
      setError(
        cause instanceof ApiError && cause.status === 422
          ? 'That does not look like an email address.'
          : 'Could not sign in. Is the backend running?',
      )
      setSubmitting(false)
    }
    // Deliberately not clearing `submitting` on success: the navigation that
    // follows unmounts this screen, and re-enabling the button first would let
    // an impatient second click start a second sign-in.
  }

  return (
    <main className="loginScreen">
      <form className="loginCard" onSubmit={onSubmit}>
        <p className="brand loginBrand">Prelegal</p>
        <h1>Draft legal agreements</h1>
        <p className="loginIntro">
          Sign in with your email to get started. No password needed yet.
        </p>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          autoFocus
          placeholder="you@company.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        {error && (
          <p className="loginError" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="submitButton" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Continue'}
        </button>
      </form>
    </main>
  )
}
