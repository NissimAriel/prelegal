'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { deleteDraft, listDrafts, type DraftSummary } from '@/lib/drafts'

/**
 * Everything this user has drafted, most recent first.
 *
 * A list rather than a grid of cards: these are agreements between named
 * parties, and what distinguishes one from another is who and when, which
 * reads faster in rows than in tiles.
 */
export default function DraftList() {
  const [drafts, setDrafts] = useState<DraftSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listDrafts()
      .then(setDrafts)
      .catch(() => setError('Could not load your agreements. Please reload.'))
  }, [])

  const remove = async (draft: DraftSummary) => {
    // Optimistic: the row goes now, and comes back if the server disagrees.
    // Deleting is the one action here where waiting feels broken.
    const before = drafts ?? []
    setDrafts(before.filter((other) => other.id !== draft.id))
    setError(null)
    try {
      await deleteDraft(draft.id)
    } catch {
      setDrafts(before)
      setError(`Could not delete ${draft.title}.`)
    }
  }

  // A load failure is the only one that leaves nothing to show.
  if (drafts === null) {
    return error ? (
      <p className="shellStatus" role="alert">
        {error}
      </p>
    ) : (
      <p className="shellStatus" role="status">
        Loading…
      </p>
    )
  }

  return (
    <main className="drafts">
      {/* Reported above the list rather than in place of it: a delete that
          failed says nothing about the other agreements, and replacing them
          with one line leaves no way back but a reload. */}
      {error && (
        <p className="draftsError" role="alert">
          {error}
        </p>
      )}

      <header className="draftsHeader">
        <h1>Your agreements</h1>
        <Link className="submitButton" href="/draft/">
          Start a new one
        </Link>
      </header>

      {drafts.length === 0 ? (
        <div className="draftsEmpty">
          <p>Nothing drafted yet.</p>
          <p>
            Start one and describe what you need — the assistant picks the
            template and fills it in as you talk.
          </p>
        </div>
      ) : (
        <ul className="draftRows">
          {drafts.map((draft) => (
            <li key={draft.id}>
              <Link href={`/draft/?id=${draft.id}`} className="draftRow">
                <span className="draftTitle">{draft.title}</span>
                <span className="draftMeta">
                  Last worked on <Updated at={draft.updatedAt} />
                </span>
              </Link>
              <button
                type="button"
                className="linkButton draftDelete"
                onClick={() => void remove(draft)}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

/**
 * When a draft was last touched.
 *
 * Rendered from a `<time>` so the exact moment is available on hover, while
 * the text stays the thing a person actually wants: how long ago.
 */
function Updated({ at }: { at: string }) {
  const when = new Date(at)
  if (Number.isNaN(when.getTime())) return <span>recently</span>
  return (
    <time dateTime={at} title={when.toLocaleString()}>
      {relative(when)}
    </time>
  )
}

const MINUTE = 60_000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

function relative(when: Date): string {
  const ago = Date.now() - when.getTime()
  if (ago < MINUTE) return 'just now'
  if (ago < HOUR) return `${Math.round(ago / MINUTE)} min ago`
  if (ago < DAY) return `${Math.round(ago / HOUR)} h ago`
  if (ago < 7 * DAY) return `${Math.round(ago / DAY)} days ago`
  return when.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}
