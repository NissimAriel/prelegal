import type { Metadata } from 'next'
import AppShell from '@/components/AppShell'
import DocumentBuilder from '@/components/DocumentBuilder'

export const metadata: Metadata = {
  title: 'Draft an agreement — Prelegal',
  description:
    'Describe the agreement you need and the assistant fills in a Common '
    + 'Paper template as you talk.',
}

/**
 * The document creator (PL-3, PL-5, PL-6), behind the sign-in screen (PL-4).
 *
 * A thin client shell: the document specs and their legal text are fetched
 * from the API, so nothing about any particular agreement is baked in here.
 */
export default function Page() {
  return (
    <AppShell subtitle="Draft an agreement">
      <DocumentBuilder />
    </AppShell>
  )
}
