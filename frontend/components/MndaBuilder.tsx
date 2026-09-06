'use client'

import { useState } from 'react'
import ChatPanel from './ChatPanel'
import CoverPage from './CoverPage'
import StandardTerms from './StandardTerms'
import { defaultFields, missingFields, type MndaFields } from '@/lib/fields'
import type { CoverPageProse } from '@/lib/templates'

/**
 * The Mutual NDA creator: a conversation with the assistant on the left, live
 * document preview on the right, download via the browser's print-to-PDF.
 *
 * This component owns the agreement state; the chat proposes changes to it and
 * the document is a pure view of it, so the preview always reflects exactly
 * what will print.
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

  const missing = missingFields(fields)
  const isComplete = missing.length === 0

  return (
    <div className="builder">
      <aside className="panel formPanel">
        <header className="panelHeader">
          <h2>Your assistant</h2>
          <p>Answer in your own words and the agreement fills itself in.</p>
        </header>
        <ChatPanel fields={fields} onFieldsChange={setFields} />
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
