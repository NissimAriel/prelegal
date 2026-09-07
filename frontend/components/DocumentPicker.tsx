'use client'

import { useEffect, useState } from 'react'
import { fetchCatalogue, type DocumentSummary } from '@/lib/documents'

/**
 * Which document is being drafted, and a way to change it.
 *
 * The assistant chooses the document from what the user asks for, which is the
 * main way in. This exists because that left no way to see what else is
 * available, or to switch without knowing you could ask: eleven templates were
 * reachable only by guessing they existed.
 */
export default function DocumentPicker({
  selected,
  onSelect,
  disabled,
}: {
  /** The document being drafted, or null before one is chosen. */
  selected: string | null
  onSelect: (documentId: string) => void
  /** True while a turn is in flight, so a switch cannot race it. */
  disabled: boolean
}) {
  const [catalogue, setCatalogue] = useState<DocumentSummary[]>([])

  useEffect(() => {
    // A failure here costs the switcher, not the product — the assistant can
    // still choose a document — so it degrades to an empty list rather than
    // reporting an error over the conversation.
    fetchCatalogue().then(setCatalogue).catch(() => setCatalogue([]))
  }, [])

  if (catalogue.length === 0) return null

  return (
    <label className="documentPicker">
      <span className="visuallyHidden">Document type</span>
      <select
        value={selected ?? ''}
        disabled={disabled}
        onChange={(event) => onSelect(event.target.value)}
      >
        {selected === null && (
          <option value="" disabled>
            Choose a document…
          </option>
        )}
        {catalogue.map((document) => (
          <option key={document.id} value={document.id}>
            {document.name}
          </option>
        ))}
      </select>
    </label>
  )
}
