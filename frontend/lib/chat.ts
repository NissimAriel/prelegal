/**
 * The chat half of the API contract, and how a model turn becomes state.
 *
 * The conversation lives here in the browser: every turn sends the whole
 * history, which document is being drafted and everything captured so far, and
 * the server keeps none of it (see backend/app/routers/chat.py).
 */

import { request } from './api'
import type { DocumentSpec } from './documents'
import { clampYears, missingFields, type Values } from './values'

/** One turn of the conversation, in the order it was said. */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/**
 * One value the model set, addressed by field id.
 *
 * A list of pairs rather than an object with a property per field, because the
 * fields differ by document type and a Structured Output needs one fixed
 * schema for all of them.
 */
export interface FieldValue {
  id: string
  value: string
}

export interface ChatTurn {
  reply: string
  /**
   * Always stated, so the client never infers which document it is drafting.
   * Null while the assistant has still to choose one.
   */
  documentType: string | null
  values: FieldValue[]
}

/**
 * Asks the assistant for its next turn.
 *
 * A null spec is the opening state, not an error: the assistant's first job is
 * to work out which document the user needs, and until it has there are no
 * fields to send or to ask about.
 */
export const sendChat = (
  messages: ChatMessage[],
  spec: DocumentSpec | null,
  values: Values,
): Promise<ChatTurn> =>
  request('/chat', {
    method: 'POST',
    body: JSON.stringify({
      messages,
      documentType: spec?.id ?? null,
      values: spec
        ? Object.entries(values).map(([id, value]) => ({ id, value }))
        : [],
      missing: spec ? missingFields(spec, values) : [],
    }),
  })

/**
 * Merges the values a turn learned into the document.
 *
 * Empty values are skipped. The schema asks the model for a value only when it
 * learned one, but models send `""` just as readily, and treating that as a
 * value would let a later turn blank out a party name given several turns
 * earlier. The cost is that the model cannot clear a field it has filled — it
 * has to be corrected with a new value instead, which for a legal document is
 * the safer direction to fail in.
 *
 * Values for fields this document does not have are dropped: the server drops
 * them too, so one arriving here means the two disagree, and writing it would
 * put something on screen that no field explains.
 */
export function applyValues(
  spec: DocumentSpec,
  values: Values,
  patch: FieldValue[],
): Values {
  const merged = { ...values }

  for (const { id, value } of patch) {
    if (!value?.trim()) continue
    const field = spec.fields.find((f) => f.id === id)
    if (!field) continue
    // A strict schema does not enforce numeric bounds, so the model can still
    // return 0 — and "Expires 0 years from the Effective Date" would go out in
    // a signed agreement.
    merged[id] = field.type === 'years' ? clampYears(value) : value
  }

  return merged
}
