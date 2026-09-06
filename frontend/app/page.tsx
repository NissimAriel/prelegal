import type { Metadata } from 'next'
import LoginScreen from '@/components/LoginScreen'

export const metadata: Metadata = {
  title: 'Sign in — Prelegal',
}

/** The way into the platform (PL-4). */
export default function Page() {
  return <LoginScreen />
}
