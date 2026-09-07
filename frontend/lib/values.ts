/**
 * The values a user has given, and how each one reads in the document.
 *
 * Values are a flat record keyed by field id, whatever the document: a choice
 * holds the id of the option picked, a years field the number, everything else
 * the text as typed. Keeping them flat means merging a patch is a merge rather
 * than a recursive walk, and the shape does not change from one document type
 * to the next.
 */

import type { DocumentSpec, FieldSpec } from './documents'

/** Everything captured, keyed by field id. */
export type Values = Record<string, string>

/** Placeholder shown wherever a value has not been given yet. */
export const UNFILLED = '—'

/** The starting values for a document: its fields' defaults. */
export function defaultValues(spec: DocumentSpec): Values {
  return Object.fromEntries(spec.fields.map((field) => [field.id, field.default]))
}

const isBlank = (value: string | undefined): boolean => !value?.trim()

/**
 * Labels of every required field still blank.
 *
 * These are what the assistant is told to ask for and what the user sees
 * counted down, so the order follows the spec's own field order rather than
 * anything the user has done.
 */
export function missingFields(spec: DocumentSpec, values: Values): string[] {
  return spec.fields
    .filter((field) => field.required && isBlank(values[field.id]))
    .map((field) => field.label ?? field.id)
}

/**
 * Carries values over to a different document type.
 *
 * Switching document keeps what the new one also asks for — the parties and the
 * effective date usually survive — and drops the rest. Anything the new
 * document does not have a field for would be invisible on screen and
 * unexplainable, so it does not travel.
 */
export function carryOver(spec: DocumentSpec, values: Values): Values {
  const carried = defaultValues(spec)
  for (const field of spec.fields) {
    const value = values[field.id]
    if (!isBlank(value)) carried[field.id] = value
  }
  return carried
}

/** Keeps a term length within the 1–99 years a document can sensibly state. */
export function clampYears(value: string): string {
  const parsed = Number.parseInt(value, 10)
  if (!Number.isFinite(parsed)) return '1'
  return String(Math.min(99, Math.max(1, parsed)))
}

/**
 * Formats an ISO date as e.g. "March 4, 2026".
 *
 * Anything unparseable is echoed back unchanged rather than rendering
 * "Invalid Date" into a legal document.
 */
export function formatDate(iso: string): string {
  if (!iso.trim()) return UNFILLED
  const date = new Date(`${iso}T00:00:00`)
  if (Number.isNaN(date.getTime())) return iso
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const years = (n: string): string => {
  const count = Number.parseInt(n, 10) || 1
  return `${count} ${count === 1 ? 'year' : 'years'}`
}

/** The two voices a value needs, since neither can be derived from the other. */
export interface Rendered {
  /** A complete statement, for the cover page. */
  cover: string
  /** A noun phrase, for annotating the Standard Terms. */
  reference: string
  /** Whether the user has actually supplied this. */
  filled: boolean
}

/**
 * How one field reads in the document.
 *
 * A choice resolves through the option the user picked, whose two wordings the
 * spec carries; everything else reads the same in both voices.
 */
export function renderField(
  spec: DocumentSpec,
  field: FieldSpec,
  values: Values,
): Rendered {
  const raw = values[field.id] ?? ''

  if (field.type === 'choice') {
    const option =
      field.options.find((o) => o.id === raw) ?? field.options[0]
    if (!option) return { cover: UNFILLED, reference: UNFILLED, filled: false }
    const count = years(values[field.yearsField ?? ''] ?? '1')
    return {
      cover: option.cover.replaceAll('{years}', count),
      reference: option.reference.replaceAll('{years}', count),
      filled: true,
    }
  }

  if (isBlank(raw)) {
    // An optional field with wording for the empty case reads as that wording
    // and counts as filled: "None." is the answer, not a gap.
    const text = field.emptyText ?? UNFILLED
    return { cover: text, reference: text, filled: field.emptyText !== null }
  }

  const text = field.type === 'date' ? formatDate(raw) : raw.trim()
  return { cover: text, reference: text, filled: true }
}
