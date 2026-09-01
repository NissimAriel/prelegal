'use client'

import { useState } from 'react'
import CoverPage from './CoverPage'
import MndaForm from './MndaForm'
import StandardTerms from './StandardTerms'
import { defaultFields, missingFields, type MndaFields } from '@/lib/fields'
import type { CoverPageProse } from '@/lib/templates'

/**
 * The Mutual NDA creator: key-information form on the left, live document
 * preview on the right, download via the browser's print-to-PDF.
 *
 * This component owns the agreement state; the form and the document are both
 * pure views of it, so the preview always reflects exactly what will print.
 */
export default function MndaBuilder({
  standardTermsTemplate,
  coverPageProse,
}: {
  /** Raw markdown of templates/mutual-nda.md, read on the server. */
  standardTermsTemplate: string
  /** Prose lifted from templates/mutual-nda-coverpage.md. */
  coverPageProse: CoverPageProse
}) {
  const [fields, setFields] = useState<MndaFields>(defaultFields)

  const onFieldChange = <K extends keyof MndaFields>(
    key: K,
    value: MndaFields[K],
  ) => setFields((prev) => ({ ...prev, [key]: value }))

  const missing = missingFields(fields)
  const isComplete = missing.length === 0

  return (
    <div className="builder">
      <aside className="panel formPanel">
        <header className="panelHeader">
          <h2>Key information</h2>
          <p>
            Fill these in and the agreement to the right updates as you type.
          </p>
        </header>
        <MndaForm fields={fields} onFieldChange={onFieldChange} />
      </aside>

      <main className="panel documentPanel">
        <header className="panelHeader documentActions">
          <div>
            <h2>Your agreement</h2>
            {isComplete ? (
              <p className="ready">Ready to download.</p>
            ) : (
              <p className="incomplete">
                {missing.length} field{missing.length === 1 ? '' : 's'} still to
                fill: {missing.join(', ')}.
              </p>
            )}
          </div>
          <button
            type="button"
            className="downloadButton"
            disabled={!isComplete}
            onClick={() => window.print()}
          >
            Download as PDF
          </button>
        </header>

        <div className="document">
          <CoverPage fields={fields} prose={coverPageProse} />
          <StandardTerms template={standardTermsTemplate} fields={fields} />
        </div>
      </main>
    </div>
  )
}
