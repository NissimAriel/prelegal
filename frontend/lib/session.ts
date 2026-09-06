/**
 * Where the session token lives in the browser.
 *
 * `localStorage` rather than a cookie because the token is read by client-side
 * code to decide what to render, and because it survives a reload — the app is
 * statically exported, so every navigation that misses the client-side router
 * starts a fresh page with no server-rendered notion of who is signed in.
 *
 * This is a stub login (see backend/app/auth.py) and the guard around it is
 * cosmetic: nothing here is a security boundary, and the real one is the
 * backend rejecting requests without a valid token.
 */

const TOKEN_KEY = 'prelegal.token'

/**
 * Reads the stored token, or null if there is none.
 *
 * Returns null rather than throwing when storage is unavailable — Safari's
 * private mode and blocked-cookie settings make `localStorage` access throw —
 * so the app treats it as "signed out" instead of failing to render.
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Nothing to do: the user stays signed in for this page only.
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Already unreachable, so already cleared as far as the app can tell.
  }
}
