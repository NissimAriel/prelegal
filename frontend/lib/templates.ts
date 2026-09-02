import { readFile } from 'node:fs/promises'
import path from 'node:path'

/**
 * Server-side access to the curated legal templates in the repo-root
 * `templates/` directory (see catalog.json).
 *
 * Everything the app displays is read from there, so `templates/` stays the
 * single source of truth for legal text and nothing can silently drift.
 */

/**
 * Candidate locations for the repo-root `templates/` directory, in order.
 *
 * Normally the app runs from `frontend/`, so `../templates` is correct; the
 * second entry covers being run from the repo root (`npm --prefix frontend`).
 * A module-relative anchor would be tidier, but Next compiles this into a
 * server bundle where `import.meta.dirname` is not defined.
 */
const candidateDirs = ['..', '.'].map((prefix) =>
  path.join(process.cwd(), prefix, 'templates'),
)

/** Reads one markdown template by its filename as listed in catalog.json. */
async function readTemplate(filename: string): Promise<string> {
  for (const [i, dir] of candidateDirs.entries()) {
    try {
      return await readFile(path.join(dir, filename), 'utf8')
    } catch (error) {
      const isMissing =
        (error as NodeJS.ErrnoException).code === 'ENOENT' &&
        i < candidateDirs.length - 1
      if (!isMissing) throw error
    }
  }
  // Unreachable: the final iteration either returns or rethrows.
  throw new Error(`Could not read template ${filename}`)
}

/**
 * The prose on the Cover Page, lifted verbatim from the template.
 *
 * The Cover Page is otherwise a fill-in form artifact whose structure is
 * composed in `components/CoverPage.tsx`. These two pieces are different: they
 * are substantive text whose wording is legally load-bearing — the preamble
 * incorporates the Standard Terms by reference, and the attribution is what
 * CC BY 4.0 requires — so they are taken from the template instead of being
 * copied into the component, where they could fall out of sync with it.
 */
export interface CoverPageProse {
  /** Markdown of the paragraph incorporating the Standard Terms by reference. */
  preamble: string
  /** Markdown of the closing CC BY 4.0 attribution line. */
  attribution: string
}

/**
 * Pulls the preamble and attribution out of the Cover Page template.
 *
 * Throws if either cannot be located. The page is statically prerendered, so a
 * template reshaped beyond what this understands fails the build rather than
 * quietly shipping an agreement with its preamble or licence notice missing.
 */
export function extractCoverPageProse(markdown: string): CoverPageProse {
  const lines = markdown.split('\n')

  const headingIndex = lines.findIndex((line) => /^##\s+USING THIS/i.test(line))
  if (headingIndex === -1) {
    throw new Error(
      'mutual-nda-coverpage.md: no "## USING THIS …" heading, so the preamble ' +
        'could not be located.',
    )
  }

  const preamble = lines
    .slice(headingIndex + 1)
    .find((line) => line.trim() !== '')
  if (!preamble?.startsWith('This Mutual Non-Disclosure Agreement')) {
    throw new Error(
      'mutual-nda-coverpage.md: the paragraph after the "USING THIS …" heading ' +
        'is not the expected preamble.',
    )
  }

  const attribution = lines.reduceRight<string | undefined>(
    (found, line) => found ?? (line.trim() === '' ? undefined : line),
    undefined,
  )
  if (!attribution?.startsWith('Common Paper')) {
    throw new Error(
      'mutual-nda-coverpage.md: the last line is not the expected Common Paper ' +
        'attribution, which CC BY 4.0 requires.',
    )
  }

  return { preamble, attribution }
}

/** Everything the Mutual NDA creator needs from `templates/`. */
export interface MndaTemplates {
  /** Raw markdown of the Standard Terms, rendered verbatim. */
  standardTerms: string
  /** Prose lifted from the Cover Page template. */
  coverPageProse: CoverPageProse
}

export async function readMndaTemplates(): Promise<MndaTemplates> {
  const [standardTerms, coverPage] = await Promise.all([
    readTemplate('mutual-nda.md'),
    readTemplate('mutual-nda-coverpage.md'),
  ])
  return { standardTerms, coverPageProse: extractCoverPageProse(coverPage) }
}
