/**
 * `applyPatch` is the only thing between what a model returns and what the
 * user has already told us, so these are all about what it must not destroy.
 */

import { describe, expect, it } from 'vitest'
import { applyPatch } from './chat'
import { defaultFields, type MndaFields } from './fields'

/** A part-filled agreement, as it would look several turns in. */
const captured = (): MndaFields => ({
  ...defaultFields(),
  purpose: 'Evaluating a partnership.',
  governingLaw: 'Delaware',
  party1: {
    name: 'Ada Lovelace',
    title: 'CEO',
    company: 'Acme, Inc.',
    noticeAddress: 'legal@acme.com',
  },
})

describe('applyPatch', () => {
  it('sets what the turn learned', () => {
    const result = applyPatch(captured(), { jurisdiction: 'New Castle, DE' })

    expect(result.jurisdiction).toBe('New Castle, DE')
  })

  it('leaves untouched fields alone', () => {
    const before = captured()

    const result = applyPatch(before, { jurisdiction: 'New Castle, DE' })

    expect(result.purpose).toBe(before.purpose)
    expect(result.party1).toEqual(before.party1)
  })

  it('ignores nulls rather than clearing the field', () => {
    const result = applyPatch(captured(), { purpose: null, party1: null })

    expect(result.purpose).toBe('Evaluating a partnership.')
    expect(result.party1.name).toBe('Ada Lovelace')
  })

  it('ignores empty strings, which a model sends as readily as null', () => {
    const result = applyPatch(captured(), { governingLaw: '' })

    expect(result.governingLaw).toBe('Delaware')
  })

  it('merges one party key without disturbing its siblings', () => {
    const result = applyPatch(captured(), { party1: { title: 'CTO' } })

    expect(result.party1).toEqual({
      name: 'Ada Lovelace',
      title: 'CTO',
      company: 'Acme, Inc.',
      noticeAddress: 'legal@acme.com',
    })
  })

  it('does not touch the other party', () => {
    const result = applyPatch(captured(), {
      party2: { name: 'Hank Scorpio', company: 'Globex' },
    })

    expect(result.party1.name).toBe('Ada Lovelace')
    expect(result.party2.name).toBe('Hank Scorpio')
    expect(result.party2.noticeAddress).toBe('')
  })

  it('clamps a term the document could not sensibly state', () => {
    // A strict schema does not enforce numeric bounds, so 0 can arrive.
    expect(applyPatch(captured(), { termYears: 0 }).termYears).toBe(1)
    expect(applyPatch(captured(), { termYears: 500 }).termYears).toBe(99)
    expect(applyPatch(captured(), { confidentialityYears: 3 })
      .confidentialityYears).toBe(3)
  })

  it('does not mutate the agreement it was given', () => {
    const before = captured()

    applyPatch(before, { purpose: 'Something else.', party1: { title: 'CTO' } })

    expect(before.purpose).toBe('Evaluating a partnership.')
    expect(before.party1.title).toBe('CEO')
  })
})
