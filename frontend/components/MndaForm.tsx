'use client'

import { useId } from 'react'
import type { MndaFields, Party } from '@/lib/fields'

/**
 * The key-information form. Purely controlled: it owns no state, so the form
 * and the document preview can never disagree about the agreement.
 */

/** Applies a change to one top-level field of the agreement. */
export type FieldChange = <K extends keyof MndaFields>(
  key: K,
  value: MndaFields[K],
) => void

/** A single labelled input. */
function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <label className="field">
      <span className="fieldLabel">{label}</span>
      {hint ? <span className="fieldHint">{hint}</span> : null}
      {children}
    </label>
  )
}

/**
 * A choice between "N years from the effective date" and a single alternative —
 * the shape shared by the MNDA Term and the Term of Confidentiality.
 *
 * Deliberately not built on `Field`: the group holds radio inputs, and nesting
 * them inside a `<label>` would make clicking the group's caption activate the
 * first radio, silently changing a term the user had already chosen.
 */
function YearsOrAlternative({
  label,
  hint,
  name,
  isYears,
  years,
  alternativeLabel,
  onSelectYears,
  onSelectAlternative,
  onYearsChange,
}: {
  label: string
  hint: string
  name: string
  isYears: boolean
  years: number
  alternativeLabel: string
  onSelectYears: () => void
  onSelectAlternative: () => void
  onYearsChange: (years: number) => void
}) {
  const captionId = useId()

  return (
    <div className="field" role="group" aria-labelledby={captionId}>
      <span className="fieldLabel" id={captionId}>
        {label}
      </span>
      <span className="fieldHint">{hint}</span>
      <div className="choice">
        <label>
          <input
            type="radio"
            name={name}
            checked={isYears}
            onChange={onSelectYears}
          />
          <input
            type="number"
            min={1}
            max={99}
            className="yearsInput"
            aria-label={`${label} in years`}
            value={years}
            disabled={!isYears}
            onChange={(e) => onYearsChange(clampYears(e.target.value))}
          />
          year(s) from the effective date
        </label>
        <label>
          <input
            type="radio"
            name={name}
            checked={!isYears}
            onChange={onSelectAlternative}
          />
          {alternativeLabel}
        </label>
      </div>
    </div>
  )
}

/** The Name/Title/Company/Notice Address block for one signatory. */
function PartyFields({
  legend,
  party,
  onChange,
}: {
  legend: string
  party: Party
  onChange: (patch: Partial<Party>) => void
}) {
  return (
    <fieldset className="partyFields">
      <legend>{legend}</legend>
      <Field label="Print name">
        <input
          type="text"
          value={party.name}
          placeholder="Jane Doe"
          onChange={(e) => onChange({ name: e.target.value })}
        />
      </Field>
      <Field label="Title" hint="Optional">
        <input
          type="text"
          value={party.title}
          placeholder="Chief Executive Officer"
          onChange={(e) => onChange({ title: e.target.value })}
        />
      </Field>
      <Field label="Company">
        <input
          type="text"
          value={party.company}
          placeholder="Acme, Inc."
          onChange={(e) => onChange({ company: e.target.value })}
        />
      </Field>
      <Field label="Notice address" hint="Email or postal address">
        <input
          type="text"
          value={party.noticeAddress}
          placeholder="legal@acme.com"
          onChange={(e) => onChange({ noticeAddress: e.target.value })}
        />
      </Field>
    </fieldset>
  )
}

export default function MndaForm({
  fields,
  onFieldChange,
}: {
  fields: MndaFields
  onFieldChange: FieldChange
}) {
  const patchParty = (which: 'party1' | 'party2') => (patch: Partial<Party>) =>
    onFieldChange(which, { ...fields[which], ...patch })

  return (
    <form className="mndaForm" onSubmit={(e) => e.preventDefault()}>
      <fieldset>
        <legend>Agreement terms</legend>

        <Field label="Purpose" hint="How Confidential Information may be used">
          <textarea
            rows={3}
            value={fields.purpose}
            onChange={(e) => onFieldChange('purpose', e.target.value)}
          />
        </Field>

        <Field label="Effective date">
          <input
            type="date"
            value={fields.effectiveDate}
            onChange={(e) => onFieldChange('effectiveDate', e.target.value)}
          />
        </Field>

        <YearsOrAlternative
          label="MNDA term"
          hint="The length of this MNDA"
          name="termType"
          isYears={fields.termType === 'expires'}
          years={fields.termYears}
          alternativeLabel="Continues until terminated"
          onSelectYears={() => onFieldChange('termType', 'expires')}
          onSelectAlternative={() => onFieldChange('termType', 'untilTerminated')}
          onYearsChange={(y) => onFieldChange('termYears', y)}
        />

        <YearsOrAlternative
          label="Term of confidentiality"
          hint="How long Confidential Information is protected"
          name="confidentialityType"
          isYears={fields.confidentialityType === 'years'}
          years={fields.confidentialityYears}
          alternativeLabel="In perpetuity"
          onSelectYears={() => onFieldChange('confidentialityType', 'years')}
          onSelectAlternative={() =>
            onFieldChange('confidentialityType', 'perpetuity')
          }
          onYearsChange={(y) => onFieldChange('confidentialityYears', y)}
        />

        <Field label="Governing law" hint="US state">
          <input
            type="text"
            value={fields.governingLaw}
            placeholder="Delaware"
            onChange={(e) => onFieldChange('governingLaw', e.target.value)}
          />
        </Field>

        <Field
          label="Jurisdiction"
          hint='City or county and state only — "courts located in" is added for you'
        >
          <input
            type="text"
            value={fields.jurisdiction}
            placeholder="New Castle, DE"
            onChange={(e) => onFieldChange('jurisdiction', e.target.value)}
          />
        </Field>

        <Field
          label="Modifications"
          hint="Optional — any changes to the standard MNDA"
        >
          <textarea
            rows={2}
            value={fields.modifications}
            onChange={(e) => onFieldChange('modifications', e.target.value)}
          />
        </Field>
      </fieldset>

      <PartyFields
        legend="Party 1"
        party={fields.party1}
        onChange={patchParty('party1')}
      />
      <PartyFields
        legend="Party 2"
        party={fields.party2}
        onChange={patchParty('party2')}
      />
    </form>
  )
}

/**
 * Keeps the year inputs within 1–99. A cleared number input reports an empty
 * string, which would otherwise render as "NaN year(s)" in the agreement.
 */
function clampYears(raw: string): number {
  const parsed = Number.parseInt(raw, 10)
  if (Number.isNaN(parsed)) return 1
  return Math.min(99, Math.max(1, parsed))
}
