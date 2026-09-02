'use client'

import { useMemo } from 'react'
import { renderStandardTerms } from '@/lib/render'
import type { MndaFields } from '@/lib/fields'

/**
 * The Mutual NDA Standard Terms, rendered verbatim from templates/mutual-nda.md.
 *
 * The legal text is unmodified — see `annotateStandardTerms` for why the Cover
 * Page references are annotated rather than substituted. Highlighted terms
 * point back at the Cover Page, where the user's values actually live.
 *
 * The markup is trusted: the template is local repo content, and every
 * user-supplied value is HTML-escaped before rendering.
 */
export default function StandardTerms({
  template,
  fields,
}: {
  template: string
  fields: MndaFields
}) {
  const html = useMemo(
    () => renderStandardTerms(template, fields),
    [template, fields],
  )

  return (
    <section className="standardTermsSection">
      <p className="termsNote">
        These Standard Terms are Common Paper Version 1.0, reproduced without
        modification. Highlighted terms take their meaning from the Cover Page
        above — hover one to see the value you entered.
      </p>
      <article
        className="standardTerms"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </section>
  )
}
