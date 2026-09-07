/**
 * The document types the app can draft, as the backend describes them.
 *
 * These mirror `backend/app/documents/schema.py`. The specs live on the server
 * because the prompt, the validation and this renderer all need them and one
 * copy is enough; the client fetches them rather than restating them.
 */

import { request } from './api'

export type FieldType = 'text' | 'longText' | 'date' | 'choice' | 'years'

/** One alternative a `choice` field can take. */
export interface ChoiceOption {
  id: string
  /** Cover page voice: a complete statement of what the parties agreed. */
  cover: string
  /** Standard Terms voice: a noun phrase that slots into a sentence. */
  reference: string
}

/** One value a document needs. */
export interface FieldSpec {
  id: string
  label: string | null
  hint: string | null
  type: FieldType
  required: boolean
  default: string
  /** Literal text printed before the value, e.g. "courts located in ". */
  prefix: string | null
  /** Printed instead of the value when an optional field is left blank. */
  emptyText: string | null
  guidance: string | null
  /** Labels this field supplies in the template's prose. */
  markers: string[]
  options: ChoiceOption[]
  /** For a choice whose wording includes `{years}`, the field holding it. */
  yearsField: string | null
}

/** A titled group of fields on the cover page. */
export interface SectionSpec {
  title: string
  hint: string | null
  fieldIds: string[]
}

export interface DocumentSpec {
  id: string
  name: string
  description: string
  template: string
  coverPageTemplate: string | null
  title: string
  attest: string
  parties: [string, string]
  shortName: string
  /** Every value the document captures, the signature block's included. */
  fields: FieldSpec[]
  sections: SectionSpec[]
  /** Terms the document negotiates that this app does not capture. */
  uncaptured: string[]
}

/** One entry in the catalogue, enough to list and choose from. */
export interface DocumentSummary {
  id: string
  name: string
  description: string
}

/** A spec together with the legal text it renders. */
export interface DocumentDetail {
  spec: DocumentSpec
  standardTerms: string
  preamble: string
  attribution: string
  /** The warning that this is an unreviewed draft, worded by the server. */
  disclaimer: string
}

export const fetchCatalogue = (): Promise<DocumentSummary[]> =>
  request('/documents')

export const fetchDocument = (id: string): Promise<DocumentDetail> =>
  request(`/documents/${id}`)

/** Looks a field up by id. */
export const fieldById = (
  spec: DocumentSpec,
  id: string,
): FieldSpec | undefined => spec.fields.find((field) => field.id === id)
