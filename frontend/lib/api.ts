/**
 * The browser's half of the API contract in backend/app/routers/.
 *
 * The frontend is exported statically and served by the same FastAPI process
 * that answers these calls, so requests are same-origin and relative paths are
 * all that is needed — there is no API base URL to configure.
 */

import { getToken } from './session'

/** A user, as `GET /api/auth/me` reports them. */
export interface User {
  id: number
  email: string
}

/** A failed request, carrying the status so callers can tell 401 from 500. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Pulls a human-readable message out of an error response.
 *
 * FastAPI reports its own errors as `{detail}`, where `detail` is a string for
 * a raised HTTPException and a list of problems for a validation failure.
 */
async function errorMessage(response: Response): Promise<string> {
  try {
    const { detail } = await response.json()
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  } catch {
    // A non-JSON body (a proxy error page, say) tells us nothing useful.
  }
  return `Request failed (${response.status}).`
}

/** Calls the API, attaching the session token and unwrapping errors. */
export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })

  if (!response.ok) {
    throw new ApiError(response.status, await errorMessage(response))
  }
  // 204 has no body; every other endpoint here returns JSON.
  return response.status === 204 ? (undefined as T) : await response.json()
}

/** Signs in by email alone. Any valid address is accepted — login is a stub. */
export const login = (email: string): Promise<{ token: string; user: User }> =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ email }) })

/** The signed-in user. Throws `ApiError` with status 401 if the token is stale. */
export const me = (): Promise<User> => request('/auth/me')

/** Revokes the current session server-side. */
export const logout = (): Promise<void> =>
  request('/auth/logout', { method: 'POST' })
