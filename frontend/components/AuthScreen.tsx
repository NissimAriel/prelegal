'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ApiError, login, signup } from '@/lib/api'
import { getToken, setToken } from '@/lib/session'

/** Where a successful sign-in lands. */
const HOME = '/draft/'

type Mode = 'signIn' | 'signUp'

const COPY: Record<Mode, { heading: string; action: string; switchTo: string }> = {
  signIn: {
    heading: 'Sign in',
    action: 'Sign in',
    switchTo: 'New here? Create an account',
  },
  signUp: {
    heading: 'Create an account',
    action: 'Create account',
    switchTo: 'Already have an account? Sign in',
  },
}

/**
 * Signing in and registering, in one screen.
 *
 * One screen rather than two routes because the fields are identical and the
 * difference is one word on a button — sending someone to a different page to
 * type the same two things is a detour, and it is where "I don't have an
 * account yet" usually goes wrong.
 */
export default function AuthScreen() {
  const router = useRouter()
  const [mode, setMode] = useState<Mode>('signIn')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Someone arriving with a session already in hand does not need to sign in
  // again. The token is not verified here; `AppShell` does that on arrival,
  // and sends them back if it turns out to be stale.
  useEffect(() => {
    if (getToken()) router.replace(HOME)
  }, [router])

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const { token } = await (mode === 'signUp'
        ? signup(email.trim(), password)
        : login(email.trim(), password))
      setToken(token)
      router.replace(HOME)
    } catch (cause) {
      setError(describe(cause, mode))
      setSubmitting(false)
    }
    // Deliberately not clearing `submitting` on success: the navigation that
    // follows unmounts this screen, and re-enabling the button first would let
    // an impatient second click start a second request.
  }

  const switchMode = () => {
    setMode(mode === 'signIn' ? 'signUp' : 'signIn')
    setError(null)
  }

  const copy = COPY[mode]

  return (
    <main className="authScreen">
      <div className="authIntro">
        <p className="brand authBrand">Prelegal</p>
        <h1>Agreements, drafted in conversation</h1>
        <p className="authLede">
          Describe what you need and an assistant fills in a Common Paper
          template as you talk. Eleven agreements, from NDAs to data processing.
        </p>
        <SamplePage />
      </div>

      <form className="authForm" onSubmit={onSubmit}>
        <h2>{copy.heading}</h2>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          required
          minLength={8}
          autoComplete={mode === 'signUp' ? 'new-password' : 'current-password'}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        {mode === 'signUp' && (
          <p className="authHint">At least 8 characters.</p>
        )}

        {error && (
          <p className="authError" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="submitButton" disabled={submitting}>
          {submitting ? 'Just a moment…' : copy.action}
        </button>

        <button type="button" className="linkButton authSwitch" onClick={switchMode}>
          {copy.switchTo}
        </button>
      </form>
    </main>
  )
}

/**
 * A fragment of a cover page, as the hero.
 *
 * The product's whole idea is fixed legal boilerplate with the negotiated
 * terms marked in — which is what a Common Paper template looks like, and what
 * the highlight on a filled value means throughout the app. Showing that is a
 * truer picture of what you get than any illustration would be.
 */
function SamplePage() {
  return (
    <div className="samplePage" aria-hidden="true">
      <p className="samplePageTitle">Mutual Non-Disclosure Agreement</p>
      <dl>
        <dt>Purpose</dt>
        <dd>
          <mark>Evaluating a potential partnership</mark>
        </dd>
        <dt>Effective Date</dt>
        <dd>
          <mark>4 March 2026</mark>
        </dd>
        <dt>Term of Confidentiality</dt>
        <dd>
          <mark>3 years</mark> from the Effective Date
        </dd>
        <dt>Governing Law</dt>
        <dd>
          <mark>Delaware</mark>
        </dd>
      </dl>
    </div>
  )
}

/** What went wrong, said in terms of what to do about it. */
function describe(cause: unknown, mode: Mode): string {
  if (!(cause instanceof ApiError)) {
    return 'Could not reach the server. Check it is running and try again.'
  }
  if (cause.status === 409) {
    return 'That email already has an account. Sign in instead.'
  }
  if (cause.status === 401) {
    return 'That email and password do not match.'
  }
  if (cause.status === 422) {
    return mode === 'signUp'
      ? 'Check the email address, and use at least 8 characters for the password.'
      : 'Check the email address and password.'
  }
  return cause.message
}
