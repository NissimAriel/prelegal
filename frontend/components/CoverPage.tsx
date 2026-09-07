'use client'

import { toHtml } from '@/lib/render'
import { renderField, UNFILLED, type Values } from '@/lib/values'
import type { DocumentDetail, DocumentSpec, FieldSpec } from '@/lib/documents'

/**
 * The cover page of whichever document is being drafted.
 *
 * Unlike the Standard Terms — immutable legal prose rendered straight from a
 * template — a cover page is a fill-in artifact: the template (where there is
 * one) is a skeleton of bracketed prompts and an empty signature table. Its
 * structure is composed here from the document's spec, so each value renders as
 * a resolved statement of what the parties agreed rather than a form still
 * waiting to be filled.
 *
 * The preamble and the CC BY attribution come from the server, which lifts them
 * from the template, so no legal wording is duplicated into this component.
 */

/** A value the user supplied, or a placeholder until they do. */
function Value({ text, filled }: { text: string; filled: boolean }) {
  return <span className={filled ? 'filled' : 'unfilled'}>{text}</span>
}

/**
 * One field within a section: what identifies it, then its value.
 *
 * How a field is identified depends on the company it keeps. Alone in its
 * section the heading above already names it, and a second label would just
 * repeat it. Sharing a section it needs one of its own — otherwise a section
 * like Acceptance prints three bare values with nothing to say which is the
 * rejection period and which the resubmission period. A field carrying a
 * prefix ("Governing Law: ") is already named by that.
 */
function Field({
  spec,
  field,
  values,
  labelled,
}: {
  spec: DocumentSpec
  field: FieldSpec
  values: Values
  labelled: boolean
}) {
  const { cover, filled } = renderField(spec, field, values)
  const showLabel = labelled && !field.prefix && field.label

  return (
    <p className={field.type === 'longText' ? 'longValue' : undefined}>
      {showLabel && <span className="fieldName">{field.label}</span>}
      {field.prefix}
      <Value text={cover} filled={filled} />
    </p>
  )
}

/**
 * The signature block, in the order the templates lay it out. `Signature` and
 * `Date` are left blank for wet signing; the rest are filled from the answers.
 */
const SIGNATURE_ROWS: ReadonlyArray<{
  label: string
  hint?: string
  suffix?: string
}> = [
  { label: 'Signature' },
  { label: 'Print Name', suffix: 'Name' },
  { label: 'Title', suffix: 'Title' },
  { label: 'Company', suffix: 'Company' },
  {
    label: 'Notice Address',
    hint: 'Email or postal address',
    suffix: 'NoticeAddress',
  },
  { label: 'Date' },
]

export default function CoverPage({
  document,
  values,
}: {
  document: DocumentDetail
  values: Values
}) {
  const { spec, preamble, attribution, disclaimer } = document

  return (
    <article className="coverPage">
      {/* Above the title, and printed rather than hidden with the app chrome:
          the PDF is what leaves here and reaches a counterparty, so a warning
          that lives only on screen is absent from the artifact that travels. */}
      <p className="draftNotice">{disclaimer}</p>

      <h1>{spec.title}</h1>

      {preamble && (
        <div
          className="preamble"
          dangerouslySetInnerHTML={{ __html: toHtml(preamble) }}
        />
      )}

      {spec.sections.map((section) => (
        <section className="coverSection" key={section.title}>
          <h2>
            {section.title}
            {section.hint ? <span className="hint">{section.hint}</span> : null}
          </h2>
          {section.fieldIds.map((id) => {
            const field = spec.fields.find((f) => f.id === id)
            return field ? (
              <Field
                key={id}
                spec={spec}
                field={field}
                values={values}
                labelled={section.fieldIds.length > 1}
              />
            ) : null
          })}
        </section>
      ))}

      <p className="attest">{spec.attest}</p>

      <table className="signatures">
        <thead>
          <tr>
            <th scope="col" />
            {spec.parties.map((party) => (
              <th scope="col" key={party}>
                {party}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {SIGNATURE_ROWS.map(({ label, hint, suffix }) => (
            <tr key={label}>
              <th scope="row">
                {label}
                {hint ? <span className="hint">{hint}</span> : null}
              </th>
              {spec.parties.map((party, index) => {
                const value = suffix
                  ? values[`party${index + 1}${suffix}`]?.trim()
                  : undefined
                return (
                  <td key={party} className={suffix ? undefined : 'signatureLine'}>
                    {suffix ? (
                      <Value text={value || UNFILLED} filled={Boolean(value)} />
                    ) : null}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      <div
        className="attribution"
        dangerouslySetInnerHTML={{ __html: toHtml(attribution) }}
      />
    </article>
  )
}
