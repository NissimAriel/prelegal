'use client'

import { renderStandardTerms } from '@/lib/render'
import type { Values } from '@/lib/values'
import type { DocumentDetail } from '@/lib/documents'

/**
 * The Standard Terms, rendered verbatim from the template with each marked
 * term annotated with the value behind it. See `lib/render.ts` for why the
 * prose is annotated rather than substituted.
 */
export default function StandardTerms({
  document,
  values,
}: {
  document: DocumentDetail
  values: Values
}) {
  return (
    <div className="standardTermsWrap">
      <p className="termsNote">
        These Standard Terms are reproduced without modification. Highlighted
        terms take their meaning from the cover page above — hover one to see
        the value you entered.
      </p>
      <article
        className="standardTerms"
        dangerouslySetInnerHTML={{
          __html: renderStandardTerms(
            document.standardTerms,
            document.spec,
            values,
          ),
        }}
      />
    </div>
  )
}
