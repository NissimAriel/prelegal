'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatPanel from './ChatPanel'
import CoverPage from './CoverPage'
import DocumentPicker from './DocumentPicker'
import StandardTerms from './StandardTerms'
import { fetchDocument, type DocumentDetail } from '@/lib/documents'
import { applyValues, type ChatMessage, type FieldValue } from '@/lib/chat'
import {
  createDraft,
  fetchDraft,
  saveDraft,
  toValues,
  type DraftDetail,
} from '@/lib/drafts'
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
 * Nothing is loaded until the assistant has chosen a document, or the user has
 * picked one. Starting on a document would be a lie about what was asked for,
 * and it anchors the assistant to that choice.
 */
export default function DocumentBuilder() {
  const draftId = useSearchParams().get('id')
  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [values, setValues] = useState<Values>({})
  const [saved, setSaved] = useState<number | null>(null)
  const [restored, setRestored] = useState<DraftDetail | null>(null)
  const [ready, setReady] = useState(!draftId)
  const [error, setError] = useState<string | null>(null)
  const [loadingTemplate, setLoadingTemplate] = useState(false)
  const [turnInFlight, setTurnInFlight] = useState(false)

  // Reopening a saved draft: its document, values and transcript all come back,
  // so the conversation continues rather than starting again.
  //
  // Moving between drafts changes only the query string, and Next keeps this
  // component mounted across that — so everything it holds has to be cleared
  // by hand. Without the reset, "start a new one" from an open draft looks
  // blank-ish but keeps that draft's id, and the first message saves over it.
  useEffect(() => {
    setDocument(null)
    setValues({})
    setRestored(null)
    setSaved(null)
    setError(null)
    setReady(!draftId)

    if (!draftId) return
    let cancelled = false
    ;(async () => {
      try {
        const draft = await fetchDraft(Number(draftId))
        const detail = await fetchDocument(draft.documentType)
        if (cancelled) return
        setDocument(detail)
        setValues({ ...defaultValues(detail.spec), ...toValues(draft.values) })
        setRestored(draft)
        setSaved(draft.id)
      } catch {
        if (!cancelled) setError('Could not open that agreement.')
      } finally {
        if (!cancelled) setReady(true)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [draftId])

  /**
   * Loads a document, carrying over the values the new one also asks for.
   *
   * Shared by the assistant and the picker: switching is the same operation
   * whoever asked for it, and the values that survive should not depend on
   * which of them did.
   */
  const switchTo = async (documentId: string, patch: FieldValue[] = []) => {
    setLoadingTemplate(true)
    try {
      const next = await fetchDocument(documentId)
      const carried = document
        ? carryOver(next.spec, values)
        : defaultValues(next.spec)
      setDocument(next)
      setValues(applyValues(next.spec, carried, patch))
      setError(null)
      return next
    } catch {
      setError('Could not load that document’s template. Please try again.')
      return null
    } finally {
      setLoadingTemplate(false)
    }
  }

  /**
   * Saves after every turn, so closing the tab loses nothing.
   *
   * A failure here is reported but not dwelt on: the work is still on screen
   * and the next turn tries again. Losing the conversation to a save error
   * would be worse than a draft that is a turn behind.
   */
  const persist = async (
    spec: string,
    nextValues: Values,
    messages: ChatMessage[],
  ) => {
    try {
      if (saved === null) {
        setSaved((await createDraft(spec, nextValues, messages)).id)
      } else {
        await saveDraft(saved, spec, nextValues, messages)
      }
    } catch {
      setError('Could not save this agreement. It is still here on screen.')
    }
  }

  /**
   * Applies one turn: the document it named, then the values it set, then saves.
   *
   * Order matters. A switch replaces the spec, and the values in the same turn
   * belong to the new document — applying them against the old spec would drop
   * every field the old one happens not to have.
   */
  const onTurn = async (
    documentType: string | null,
    patch: FieldValue[],
    messages: ChatMessage[],
  ) => {
    setError(null)

    // Still choosing, so there is no document to save the conversation against.
    if (documentType === null) return

    if (documentType !== document?.spec.id) {
      const next = await switchTo(documentType, patch)
      if (next) {
        await persist(
          next.spec.id,
          applyValues(
            next.spec,
            document ? carryOver(next.spec, values) : defaultValues(next.spec),
            patch,
          ),
          messages,
        )
      }
      return
    }

    const merged = applyValues(document.spec, values, patch)
    setValues(merged)
    await persist(document.spec.id, merged, messages)
  }

  if (!ready) {
    return (
      <p className="shellStatus" role="status">
        Opening…
      </p>
    )
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
          key={draftId ?? 'new'}
          spec={document?.spec ?? null}
          values={values}
          onTurn={onTurn}
          onThinking={setTurnInFlight}
          // Only the transcript belonging to the draft in the URL right now.
          // The `key` remounts this panel during the render that follows the
          // navigation, which is before the effect below has cleared the
          // previous draft — so passing `restored` unchecked would start the
          // new conversation with the old one's messages.
          initialMessages={
            restored && String(restored.id) === draftId
              ? restored.messages
              : undefined
          }
        />
      </aside>

      <main className="panel documentPanel">
        <header className="panelHeader documentActions">
          <div>
            <div className="documentTitle">
              <h2>{document ? document.spec.name : 'Your document'}</h2>
              <DocumentPicker
                selected={document?.spec.id ?? null}
                onSelect={(id) => void switchTo(id)}
                disabled={loadingTemplate || turnInFlight}
              />
            </div>
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
