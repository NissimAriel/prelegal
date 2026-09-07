/**
 * The agreements this user has saved.
 *
 * Distinct from `lib/documents.ts`, which is the catalogue of templates the app
 * can draft: those are the same for everyone, these belong to one person. The
 * server scopes every read and write to the session, so nothing here has to
 * pass a user around.
 */

import { request } from './api'
import type { ChatMessage, FieldValue } from './chat'
import type { Values } from './values'

/** One row in the list of saved drafts. */
export interface DraftSummary {
  id: number
  documentType: string
  /** Derived from the parties by the server, so every draft is named alike. */
  title: string
  updatedAt: string
}

/** A saved draft, with everything needed to carry on where it left off. */
export interface DraftDetail extends DraftSummary {
  values: FieldValue[]
  messages: ChatMessage[]
}

interface DraftBody {
  documentType: string
  values: FieldValue[]
  messages: ChatMessage[]
}

const asBody = (
  documentType: string,
  values: Values,
  messages: ChatMessage[],
): DraftBody => ({
  documentType,
  values: Object.entries(values).map(([id, value]) => ({ id, value })),
  messages,
})

export const listDrafts = (): Promise<DraftSummary[]> => request('/drafts')

export const fetchDraft = (id: number): Promise<DraftDetail> =>
  request(`/drafts/${id}`)

export const createDraft = (
  documentType: string,
  values: Values,
  messages: ChatMessage[],
): Promise<DraftSummary> =>
  request('/drafts', {
    method: 'POST',
    body: JSON.stringify(asBody(documentType, values, messages)),
  })

export const saveDraft = (
  id: number,
  documentType: string,
  values: Values,
  messages: ChatMessage[],
): Promise<DraftSummary> =>
  request(`/drafts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(asBody(documentType, values, messages)),
  })

export const deleteDraft = (id: number): Promise<void> =>
  request(`/drafts/${id}`, { method: 'DELETE' })

/** Values as stored, back into the flat record the builder works with. */
export const toValues = (stored: FieldValue[]): Values =>
  Object.fromEntries(stored.map(({ id, value }) => [id, value]))
