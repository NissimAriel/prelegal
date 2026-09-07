/**
 * Rendering of the Standard Terms for display.
 *
 * The Standard Terms are never modified. Common Paper marks every point where
 * they refer to a value the parties supply with a `<span class="..._link">`,
 * and those markers keep their defined-term text for two reasons:
 *
 *  1. Legal integrity. A cover page represents that the Standard Terms are
 *     identical to those Common Paper publishes. Editing them would make that
 *     representation false. In a real agreement the Standard Terms are
 *     invariant boilerplate and the cover page alone carries the negotiated
 *     values — which is why the cover page controls over any conflict.
 *  2. Grammar. The prose is written around the defined term: "commences on the
 *     Effective Date" and "provisions of such Governing Law" read correctly,
 *     whereas substituting yields "commences on the March 4, 2026" and
 *     "provisions of such Delaware".
 *
 * So each marker is annotated rather than replaced — the printed text stays the
 * defined term, and the value behind it is surfaced on screen.
 */

import { marked } from 'marked'
import type { DocumentSpec } from './documents'
import { renderField, UNFILLED, type Values } from './values'

/**
 * Matches one marker in the Standard Terms.
 *
 * Five classes exist — keyterms, orderform, coverpage, sow, businessterms —
 * distinguishing which artifact a value belongs on. That matters to a lawyer
 * reading the template but not here: all of them mark a value the parties
 * supply, so all of them are annotated the same way.
 */
const MARKER =
  /<span class="(?:keyterms|orderform|coverpage|sow|businessterms)_link">([^<]+)<\/span>/g

/** Escapes text for interpolation into the template's HTML. */
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** Longest tooltip we will emit, so a long value cannot dominate the screen. */
const MAX_TOOLTIP = 300

/**
 * Prepares a value for use inside a `title` attribute.
 *
 * Newlines must go: the annotated markup is fed back through the markdown
 * parser, and a value containing a blank line would otherwise end the
 * enclosing list item mid-sentence, spilling the raw attribute text into the
 * agreement and leaving the `<span>` unclosed.
 */
function asAttribute(value: string): string {
  const flat = value.replace(/\s+/g, ' ').trim()
  const clipped =
    flat.length > MAX_TOOLTIP ? `${flat.slice(0, MAX_TOOLTIP - 1)}…` : flat
  return escapeHtml(clipped)
}

/** Strips a possessive so "Customer's" resolves the same as "Customer". */
const base = (marker: string): string =>
  marker.replace(/[’']s$/, '').replace(/[’']$/, '')

/**
 * What each marked term in the Standard Terms resolves to.
 *
 * Two kinds of marker end up here. Most name a value a field supplies. The
 * rest name a party — "Customer", "Provider" — which no field supplies but the
 * signature block does, so those resolve to that signatory's company.
 */
function markerValues(spec: DocumentSpec, values: Values): Map<string, string> {
  const resolved = new Map<string, string>()

  for (const field of spec.fields) {
    if (field.markers.length === 0) continue
    const { reference, filled } = renderField(spec, field, values)
    for (const marker of field.markers) {
      resolved.set(base(marker), filled ? reference : UNFILLED)
    }
  }

  spec.parties.forEach((role, index) => {
    const company = values[`party${index + 1}Company`]?.trim()
    resolved.set(base(role), company || UNFILLED)
  })

  return resolved
}

/**
 * Rewrites each marker as a reference to that term, annotated with the value
 * currently entered for it.
 *
 * An unrecognised label is left untouched rather than dropped, so a term this
 * document has no field for still appears in the agreement instead of
 * vanishing from it.
 */
export function annotateStandardTerms(
  markdown: string,
  spec: DocumentSpec,
  values: Values,
): string {
  const resolved = markerValues(spec, values)

  return markdown.replace(MARKER, (original, label: string) => {
    const value = resolved.get(base(label))
    if (value === undefined) return original

    const isSet = value !== UNFILLED
    const tooltip = isSet
      ? `${label}: ${value}`
      : `${label} — not yet entered`

    return (
      `<span class="coverpageRef ${isSet ? 'set' : 'awaiting'}"` +
      ` title="${asAttribute(tooltip)}">${escapeHtml(label)}</span>`
    )
  })
}

/**
 * Demotes every heading one level. The templates are standalone documents
 * titled `#`, but here they sit beneath the agreement's own `<h1>`, so leaving
 * them as-is would produce competing `<h1>`s and a broken document outline.
 */
const demoteHeadings = (markdown: string): string =>
  markdown.replace(/^(#{1,5}) /gm, '$1# ')

/** Renders template markdown (with its inline HTML preserved) to HTML. */
export function toHtml(markdown: string): string {
  return marked.parse(demoteHeadings(markdown), {
    async: false,
    gfm: true,
  }) as string
}

/** Annotates the Standard Terms and renders them to HTML, ready for display. */
export function renderStandardTerms(
  markdown: string,
  spec: DocumentSpec,
  values: Values,
): string {
  return toHtml(annotateStandardTerms(markdown, spec, values))
}
