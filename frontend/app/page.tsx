import type { Metadata } from 'next'
import AuthScreen from '@/components/AuthScreen'

export const metadata: Metadata = {
  title: 'Sign in — Prelegal',
}

/** The way into the platform (PL-4, real accounts in PL-7). */
export default function Page() {
  return <AuthScreen />
}
