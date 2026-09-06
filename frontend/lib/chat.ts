/**
 * The chat half of the API contract, and how a model turn becomes state.
 *
 * The conversation lives here in the browser: every turn sends the whole
 * history plus everything captured so far, and the server keeps none of it
 * (see backend/app/routers/chat.py).
 */

import { request } from './api'
import {
  clampYears,
  missingFields,
  type MndaFields,
  type Party,
} from './fields'

/** One turn of the conversation, in the order it was said. */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/**
 * The fields a model turn wishes to set — every one optional.
 *
 * Mirrors `MndaFieldsPatch` in backend/app/models.py. The names must match
 * `MndaFields` exactly, because a patch is merged straight into it.
 */
type PartyPatch = Partial<Record<keyof Party, string | null>>

export type MndaFieldsPatch = {
  [K in Exclude<keyof MndaFields, 'party1' | 'party2'>]?: MndaFields[K] | null
} & {
  party1?: PartyPatch | null
  party2?: PartyPatch | null
}

interface ChatResponse {
  reply: string
  fields: MndaFieldsPatch
}

/** Asks the assistant for its next turn. */
export const sendChat = (
  messages: ChatMessage[],
  fields: MndaFields,
): Promise<ChatResponse> =>
  request('/chat', {
    method: 'POST',
    body: JSON.stringify({
      messages,
      fields,
      missing: missingFields(fields),
    }),
  })

/**
 * Whether a patch value is one the model actually set.
 *
 * An empty string counts as unset, not as an instruction to clear the field.
 * The schema asks for `null` when nothing was learned, but models reach for
 * `""` just as readily, and treating that as a value would let a later turn
 * blank out a party name given several turns ago. The cost is that the model
 * cannot clear a field it has already filled — it has to be corrected with a
 * new value instead, which for a legal document is the safer direction to
 * fail in.
 */
const isSet = (value: unknown): boolean =>
  value !== null && value !== undefined && value !== ''

/**
 * Merges the fields a turn learned into the agreement.
 *
 * Unset values are skipped rather than written, so a turn that learned only
 * the purpose cannot blank out the parties named three turns ago. Parties
 * merge key by key for the same reason: hearing a company name should not
 * erase the print name beside it.
 */
export function applyPatch(
  fields: MndaFields,
  patch: MndaFieldsPatch,
): MndaFields {
  const merged = { ...fields }

  for (const [key, value] of Object.entries(patch)) {
    if (!isSet(value)) continue

    if (key === 'party1' || key === 'party2') {
      merged[key] = mergeParty(fields[key], value as PartyPatch)
    } else if (key === 'termYears' || key === 'confidentialityYears') {
      // The schema asks for 1-99, but a strict schema does not enforce numeric
      // bounds, so the model can still return 0 — and "Expires 0 years from
      // the Effective Date" would go out in a signed agreement.
      merged[key] = clampYears(value)
    } else {
      // The backend's schema is generated from the same field names and types,
      // so a value that arrives under a known key is of that key's type.
      Object.assign(merged, { [key]: value })
    }
  }

  return merged
}

function mergeParty(party: Party, patch: PartyPatch): Party {
  const merged = { ...party }
  for (const [key, value] of Object.entries(patch)) {
    if (isSet(value)) merged[key as keyof Party] = value as string
  }
  return merged
}
