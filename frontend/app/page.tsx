import MndaBuilder from '@/components/MndaBuilder'
import { readMndaTemplates } from '@/lib/templates'

/**
 * Mutual NDA creator (PL-3).
 *
 * A Server Component so the templates are read from the repo-root `templates/`
 * directory on the server and handed to the client as props — no API route, and
 * no copy of the legal text inside this app.
 */
export default async function Page() {
  const { standardTerms, coverPageProse } = await readMndaTemplates()

  return (
    <MndaBuilder
      standardTermsTemplate={standardTerms}
      coverPageProse={coverPageProse}
    />
  )
}
