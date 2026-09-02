/**
 * Rendering of the Mutual NDA templates for display.
 *
 * The Standard Terms (templates/mutual-nda.md) are never modified. Common Paper
 * marks every point where they reference the Cover Page with
 * `<span class="coverpage_link">Label</span>`, and those markers keep their
 * defined-term text for two reasons:
 *
 *  1. Legal integrity. The Cover Page represents that the Standard Terms are
 *     "identical to those posted at commonpaper.com/standards/mutual-nda/1.0".
 *     Editing them would make that representation false. In a real MNDA the
 *     Standard Terms are invariant boilerplate and the Cover Page alone carries
 *     the negotiated values — which is why the Cover Page controls over any
 *     conflict with the Standard Terms.
 *  2. Grammar. The prose is written around the defined term: "commences on the
 *     Effective Date" and "provisions of such Governing Law" read correctly,
 *     whereas substituting yields "commences on the March 4, 2026" and
 *     "provisions of such Delaware".
 *
 * So each marker is annotated rather than replaced — the printed text stays the
 * defined term, and the value the user entered is surfaced on screen.
 */

import { marked } from 'marked'
import {
  formatDate,
  mndaTerm,
  termOfConfidentiality,
  UNFILLED,
  type MndaFields,
} from './fields'

/** Matches a single Cover Page reference marker in the Standard Terms. */
const COVERPAGE_LINK = /<span class="coverpage_link">([^<]+)<\/span>/g

/**
 * The Cover Page value behind each reference in the Standard Terms.
 *
 * Keys are the exact marker text Common Paper uses in templates/mutual-nda.md.
 */
function coverPageValues(fields: MndaFields): Record<string, string> {
  return {
    Purpose: fields.purpose.trim() || UNFILLED,
    'Effective Date': formatDate(fields.effectiveDate),
    'MNDA Term': mndaTerm(fields).reference,
    'Term of Confidentiality': termOfConfidentiality(fields).reference,
    'Governing Law': fields.governingLaw.trim() || UNFILLED,
    Jurisdiction: fields.jurisdiction.trim() || UNFILLED,
  }
}

/** Escapes text for interpolation into the template's HTML. */
function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/** Longest tooltip we will emit, so a long Purpose cannot dominate the screen. */
const MAX_TOOLTIP = 300

/**
 * Prepares a value for use inside a `title` attribute.
 *
 * Newlines must go: the annotated markup is fed back through the markdown
 * parser, and a value containing a blank line (Purpose is a `<textarea>`) would
 * otherwise end the enclosing list item mid-sentence, spilling the raw
 * attribute text into the agreement and leaving the `<span>` unclosed.
 */
function asAttribute(value: string): string {
  const flat = value.replace(/\s+/g, ' ').trim()
  const clipped =
    flat.length > MAX_TOOLTIP ? `${flat.slice(0, MAX_TOOLTIP - 1)}…` : flat
  return escapeHtml(clipped)
}

/**
 * Rewrites each Cover Page marker as a reference to that term, annotated with
 * the value currently entered for it.
 *
 * An unrecognized label is left untouched rather than dropped, so a reference
 * added to a future version of the Standard Terms still appears in the
 * agreement instead of vanishing from it.
 */
export function annotateStandardTerms(
  markdown: string,
  fields: MndaFields,
): string {
  const values = coverPageValues(fields)

  return markdown.replace(COVERPAGE_LINK, (original, label: string) => {
    const value = values[label]
    if (value === undefined) return original

    const isSet = value !== UNFILLED
    const tooltip = isSet
      ? `${label} on the Cover Page: ${value}`
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
  fields: MndaFields,
): string {
  return toHtml(annotateStandardTerms(markdown, fields))
}
