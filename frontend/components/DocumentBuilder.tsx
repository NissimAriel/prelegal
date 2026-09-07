'use client'

import { useState } from 'react'
import ChatPanel from './ChatPanel'
import CoverPage from './CoverPage'
import StandardTerms from './StandardTerms'
import { fetchDocument, type DocumentDetail } from '@/lib/documents'
import { applyValues, type FieldValue } from '@/lib/chat'
import {
  carryOver,
  defaultValues,
  missingFields,
  type Values,
} from '@/lib/values'

/**
 * The document creator: a conversation with the assistant on the left, live
 * document preview on the right, download via the browser's print-to-PDF.
 *
 * This component owns which document is being drafted and the values captured
 * for it. The chat proposes changes to both and the document is a pure view of
 * them, so the preview always reflects exactly what will print.
 *
 * Nothing is loaded until the assistant has chosen a document. Starting on one
 * would be a lie about what the user asked for, and it anchors the assistant
 * to that choice — told it was already drafting an NDA, it answers a request
 * for a design partnership by writing the request into the NDA.
 */
export default function DocumentBuilder() {
  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [values, setValues] = useState<Values>({})
  const [error, setError] = useState<string | null>(null)

  /**
   * Applies one turn: the document it named, then the values it set.
   *
   * Order matters. A switch replaces the spec, and the values in the same turn
   * belong to the new document — applying them against the old spec would drop
   * every field the old one happens not to have.
   */
  const onTurn = async (documentType: string | null, patch: FieldValue[]) => {
    // Still choosing. Nothing can have been captured yet, so there is nothing
    // to apply.
    if (documentType === null) return

    if (documentType !== document?.spec.id) {
      try {
        const next = await fetchDocument(documentType)
        // Carried over from the previous document, if there was one: the
        // parties and the effective date usually survive a change of mind.
        const carried = document
          ? carryOver(next.spec, values)
          : defaultValues(next.spec)
        setDocument(next)
        setValues(applyValues(next.spec, carried, patch))
        setError(null)
      } catch {
        setError(
          'Could not load that document’s template. Please try again.',
        )
      }
      return
    }

    setValues(applyValues(document.spec, values, patch))
  }

  const missing = document ? missingFields(document.spec, values) : []
  const isComplete = Boolean(document) && missing.length === 0

  return (
    <div className="builder">
      <aside className="panel formPanel">
        <header className="panelHeader">
          <h2>Your assistant</h2>
          <p>Answer in your own words and the document fills itself in.</p>
        </header>
        <ChatPanel
          spec={document?.spec ?? null}
          values={values}
          onTurn={onTurn}
        />
      </aside>

      <main className="panel documentPanel">
        <header className="panelHeader documentActions">
          <div>
            <h2>{document ? document.spec.name : 'Your document'}</h2>
            {!document ? (
              <p>Tell the assistant what you need and it will pick a template.</p>
            ) : isComplete ? (
              <p className="ready">Ready to download.</p>
            ) : (
              <p className="incomplete">
                {missing.length} field{missing.length === 1 ? '' : 's'} still to
                fill: {missing.join(', ')}.
              </p>
            )}
            {error && (
              <p className="chatError" role="alert">
                {error}
              </p>
            )}
            {document && document.spec.uncaptured.length > 0 && (
              <p className="uncaptured">
                Not captured here: {document.spec.uncaptured.join('; ')}.
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

        {document ? (
          <div className="document">
            <CoverPage document={document} values={values} />
            <StandardTerms document={document} values={values} />
          </div>
        ) : (
          <p className="documentPlaceholder">
            Your agreement will appear here as you answer.
          </p>
        )}
      </main>
    </div>
  )
}
