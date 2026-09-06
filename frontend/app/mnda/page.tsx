import type { Metadata } from 'next'
import AppShell from '@/components/AppShell'
import MndaBuilder from '@/components/MndaBuilder'
import { readMndaTemplates } from '@/lib/templates'

export const metadata: Metadata = {
  title: 'Mutual NDA creator — Prelegal',
  description:
    'Fill in a few key details and download a completed Common Paper Mutual Non-Disclosure Agreement.',
}

/**
 * Mutual NDA creator (PL-3), behind the sign-in screen (PL-4).
 *
 * A Server Component so the templates are read from the repo-root `templates/`
 * directory and baked into the export at build time — no API route, and no copy
 * of the legal text inside this app.
 */
export default async function Page() {
  const { standardTerms, coverPageProse } = await readMndaTemplates()

  return (
    <AppShell subtitle="Mutual Non-Disclosure Agreement">
      <MndaBuilder
        standardTermsTemplate={standardTerms}
        coverPageProse={coverPageProse}
      />
    </AppShell>
  )
}
