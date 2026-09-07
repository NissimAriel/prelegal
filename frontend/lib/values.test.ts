/**
 * The value logic every document shares.
 *
 * `applyValues` is the only thing between what a model returns and what the
 * user has already told us, so most of these are about what it must not
 * destroy.
 */

import { describe, expect, it } from 'vitest'
import { applyValues } from './chat'
import {
  carryOver,
  clampYears,
  defaultValues,
  missingFields,
  renderField,
  UNFILLED,
} from './values'
import type { DocumentSpec, FieldSpec } from './documents'

const field = (over: Partial<FieldSpec> & { id: string }): FieldSpec => ({
  label: over.id,
  hint: null,
  type: 'text',
  required: false,
  default: '',
  prefix: null,
  emptyText: null,
  guidance: null,
  markers: [],
  options: [],
  yearsField: null,
  ...over,
})

/** A stand-in with one of each field kind that behaves differently. */
const spec = (over: Partial<DocumentSpec> = {}): DocumentSpec => ({
  id: 'test-doc',
  name: 'Test Document',
  description: '',
  template: 'test.md',
  coverPageTemplate: null,
  title: 'Test Document',
  attest: 'Signed.',
  parties: ['Party 1', 'Party 2'],
  shortName: 'Doc',
  uncaptured: [],
  sections: [],
  fields: [
    field({ id: 'purpose', type: 'longText', required: true }),
    field({ id: 'effectiveDate', type: 'date', required: true }),
    field({ id: 'governingLaw', required: true }),
    field({ id: 'modifications', type: 'longText', emptyText: 'None.' }),
    field({
      id: 'termType',
      type: 'choice',
      default: 'expires',
      yearsField: 'termYears',
      options: [
        {
          id: 'expires',
          cover: 'Expires {years} from the Effective Date.',
          reference: '{years} from the Effective Date',
        },
        { id: 'untilTerminated', cover: 'Until terminated.', reference: 'until terminated' },
      ],
    }),
    field({ id: 'termYears', type: 'years', default: '1' }),
    field({ id: 'party1Name', required: true }),
    field({ id: 'party1Company', required: true }),
  ],
  ...over,
})

const captured = () => ({
  ...defaultValues(spec()),
  purpose: 'Evaluating a partnership.',
  governingLaw: 'Delaware',
  party1Name: 'Ada Lovelace',
  party1Company: 'Acme, Inc.',
})

describe('applyValues', () => {
  it('sets what the turn learned', () => {
    const result = applyValues(spec(), captured(), [
      { id: 'effectiveDate', value: '2026-03-04' },
    ])

    expect(result.effectiveDate).toBe('2026-03-04')
  })

  it('leaves untouched values alone', () => {
    const result = applyValues(spec(), captured(), [
      { id: 'effectiveDate', value: '2026-03-04' },
    ])

    expect(result.purpose).toBe('Evaluating a partnership.')
    expect(result.party1Name).toBe('Ada Lovelace')
  })

  it('ignores empty values, which a model sends as readily as omitting them', () => {
    const result = applyValues(spec(), captured(), [
      { id: 'governingLaw', value: '' },
      { id: 'party1Name', value: '   ' },
    ])

    expect(result.governingLaw).toBe('Delaware')
    expect(result.party1Name).toBe('Ada Lovelace')
  })

  it('drops values this document has no field for', () => {
    const result = applyValues(spec(), captured(), [
      { id: 'notAFieldHere', value: 'something' },
    ])

    expect(result).not.toHaveProperty('notAFieldHere')
  })

  it('clamps a term the document could not sensibly state', () => {
    const clamp = (value: string) =>
      applyValues(spec(), captured(), [{ id: 'termYears', value }]).termYears

    expect(clamp('0')).toBe('1')
    expect(clamp('500')).toBe('99')
    expect(clamp('3')).toBe('3')
  })

  it('does not mutate the values it was given', () => {
    const before = captured()

    applyValues(spec(), before, [{ id: 'purpose', value: 'Something else.' }])

    expect(before.purpose).toBe('Evaluating a partnership.')
  })
})

describe('missingFields', () => {
  it('lists required fields that are blank, in spec order', () => {
    expect(missingFields(spec(), defaultValues(spec()))).toEqual([
      'purpose',
      'effectiveDate',
      'governingLaw',
      'party1Name',
      'party1Company',
    ])
  })

  it('ignores optional fields and ones already given', () => {
    // `captured()` fills every required field but the effective date, and
    // leaves `modifications` blank — which is optional and so not missing.
    expect(missingFields(spec(), captured())).toEqual(['effectiveDate'])
  })
})

describe('carryOver', () => {
  it('keeps values the new document also asks for', () => {
    const narrower = spec({
      fields: [field({ id: 'purpose', required: true }), field({ id: 'party1Name' })],
    })

    const carried = carryOver(narrower, captured())

    expect(carried.purpose).toBe('Evaluating a partnership.')
    expect(carried.party1Name).toBe('Ada Lovelace')
  })

  it('drops values the new document has no field for', () => {
    const narrower = spec({ fields: [field({ id: 'purpose' })] })

    expect(carryOver(narrower, captured())).not.toHaveProperty('governingLaw')
  })
})

describe('renderField', () => {
  const s = spec()
  const find = (id: string) => s.fields.find((f) => f.id === id)!

  it('resolves a choice through the option picked, in both voices', () => {
    const values = { ...captured(), termType: 'expires', termYears: '3' }

    expect(renderField(s, find('termType'), values)).toEqual({
      cover: 'Expires 3 years from the Effective Date.',
      reference: '3 years from the Effective Date',
      filled: true,
    })
  })

  it('says "1 year", not "1 years"', () => {
    const values = { ...captured(), termYears: '1' }

    expect(renderField(s, find('termType'), values).cover).toBe(
      'Expires 1 year from the Effective Date.',
    )
  })

  it('formats a date for the document, not the input', () => {
    const values = { ...captured(), effectiveDate: '2026-03-04' }

    expect(renderField(s, find('effectiveDate'), values).cover).toBe('March 4, 2026')
  })

  it('echoes an unparseable date rather than printing "Invalid Date"', () => {
    const values = { ...captured(), effectiveDate: 'next Tuesday' }

    expect(renderField(s, find('effectiveDate'), values).cover).toBe('next Tuesday')
  })

  it('reads an empty optional field as its own wording, and counts it filled', () => {
    const rendered = renderField(s, find('modifications'), captured())

    expect(rendered.cover).toBe('None.')
    expect(rendered.filled).toBe(true)
  })

  it('marks a blank required field unfilled', () => {
    const rendered = renderField(s, find('effectiveDate'), captured())

    expect(rendered.cover).toBe(UNFILLED)
    expect(rendered.filled).toBe(false)
  })
})

describe('clampYears', () => {
  it('falls back to one year for anything unusable', () => {
    expect(clampYears('')).toBe('1')
    expect(clampYears('lots')).toBe('1')
  })
})
