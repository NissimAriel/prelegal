'use client'

import { useEffect, useRef, useState } from 'react'
import { ApiError } from '@/lib/api'
import { sendChat, type ChatMessage, type FieldValue } from '@/lib/chat'
import type { DocumentSpec } from '@/lib/documents'
import type { Values } from '@/lib/values'

/**
 * The conversation that fills in the document.
 *
 * This is the only way to enter anything: the assistant asks, the user answers,
 * and each turn returns the document it is drafting plus the values it learned.
 * Both stay in `DocumentBuilder`, so what is on screen is always what will
 * print.
 */

/**
 * Shown before the user has said anything, so the panel is never empty.
 *
 * It asks what they need rather than assuming, because the assistant chooses
 * the document from the answer — and can say so when the answer is something
 * it cannot draft.
 */
const OPENING: ChatMessage = {
  role: 'assistant',
  content:
    "Hi — I'll help you put together a legal agreement. What do you need, " +
    'and who are the two parties?',
}

export default function ChatPanel({
  spec,
  values,
  onTurn,
  initialMessages,
}: {
  /** Null until the assistant has chosen which document to draft. */
  spec: DocumentSpec | null
  values: Values
  onTurn: (
    documentType: string | null,
    patch: FieldValue[],
    messages: ChatMessage[],
  ) => Promise<void>
  /** The transcript of a reopened draft, so it carries on rather than restarts. */
  initialMessages?: ChatMessage[]
}) {
  const [messages, setMessages] = useState<ChatMessage[]>(
    initialMessages?.length ? initialMessages : [OPENING],
  )
  const [draft, setDraft] = useState('')
  const [thinking, setThinking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const threadRef = useRef<HTMLDivElement>(null)

  // Keep the newest turn in view. `messages` covers the user's own message and
  // the reply; `thinking` covers the indicator that appears between them.
  useEffect(() => {
    const thread = threadRef.current
    if (thread) thread.scrollTop = thread.scrollHeight
  }, [messages, thinking])

  const send = async (event: React.FormEvent) => {
    event.preventDefault()
    const content = draft.trim()
    if (!content || thinking) return

    const history = [...messages, { role: 'user' as const, content }]
    setMessages(history)
    setDraft('')
    setThinking(true)
    setError(null)

    try {
      const turn = await sendChat(history, spec, values)
      const transcript: ChatMessage[] = [
        ...history,
        { role: 'assistant', content: turn.reply },
      ]
      setMessages(transcript)
      // The transcript goes with the turn so the draft is saved with the
      // conversation that produced it, not one turn behind.
      await onTurn(turn.documentType, turn.values, transcript)
    } catch (cause) {
      // The user's message stays in the thread: they said it, and retyping it
      // to retry would be a punishment for someone else's outage.
      setError(
        cause instanceof ApiError && cause.status === 401
          ? 'Your session has expired. Please sign in again.'
          : 'The assistant could not be reached. Try sending that again.',
      )
    } finally {
      setThinking(false)
    }
  }

  return (
    <div className="chatPanel">
      {/* `log` with a polite live region: replies arrive on their own, and
          without it a screen reader announces the thinking indicator and then
          nothing when the actual answer replaces it. */}
      <div
        className="chatThread"
        ref={threadRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
      >
        {messages.map((message, index) => (
          <p
            // Messages are only ever appended, so the index is stable.
            key={index}
            className={`bubble ${message.role}`}
          >
            {message.content}
          </p>
        ))}

        {thinking && (
          <p className="bubble assistant thinking" role="status">
            <span aria-hidden="true">●●●</span>
            <span className="visuallyHidden">Thinking…</span>
          </p>
        )}

        {error && (
          <p className="chatError" role="alert">
            {error}
          </p>
        )}
      </div>

      <form className="chatComposer" onSubmit={send}>
        <label htmlFor="message" className="visuallyHidden">
          Your message
        </label>
        <textarea
          id="message"
          rows={2}
          placeholder="Type your answer…"
          value={draft}
          disabled={thinking}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            // Enter sends, Shift+Enter starts a new line — the convention
            // every chat interface has trained people to expect.
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault()
              void send(event)
            }
          }}
        />
        <button
          type="submit"
          className="submitButton"
          disabled={thinking || draft.trim() === ''}
        >
          Send
        </button>
      </form>
    </div>
  )
}
