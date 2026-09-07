import type { Metadata } from 'next'
import AppShell from '@/components/AppShell'
import DraftList from '@/components/DraftList'

export const metadata: Metadata = {
  title: 'Your agreements — Prelegal',
}

/** Everything the signed-in user has drafted (PL-7). */
export default function Page() {
  return (
    <AppShell subtitle="Your agreements">
      <DraftList />
    </AppShell>
  )
}
