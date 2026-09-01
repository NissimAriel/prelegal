# Prelegal frontend

Next.js app for creating legal documents from the curated templates in the
repo-root [`templates/`](../templates) directory (catalogued in
[`catalog.json`](../catalog.json)).

## Mutual NDA creator (PL-3)

Enter the key information in the form and the agreement builds alongside it;
download it once every required field is filled.

- **Cover Page** — rendered from your answers.
- **Standard Terms** — Common Paper Version 1.0, reproduced verbatim from
  `templates/mutual-nda.md`.

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
```

Other scripts: `npm run build`, `npm start`, `npm run typecheck`.

There is no lint setup yet — `next lint` was removed in Next 16, so ESLint needs
configuring directly. `npm run build` type-checks as part of the build.

Templates are read from `../templates` on the server, so run this from within
the repo — the app is not standalone.

## How the document is assembled

The two halves of the MNDA are treated differently, on purpose.

**Standard Terms are never modified.** Common Paper marks each point where they
reference the Cover Page with `<span class="coverpage_link">Label</span>`. Those
markers keep their defined-term text and are only *annotated* with the value you
entered (hover to see it). Substituting values there would be wrong twice over:

1. The Cover Page represents that the Standard Terms are "identical to those
   posted at commonpaper.com/standards/mutual-nda/1.0". Editing them makes that
   representation false.
2. The prose is written around the defined term. "commences on the Effective
   Date" and "provisions of such Governing Law" read correctly; substituting
   gives "commences on the March 4, 2026" and "provisions of such Delaware".

**The Cover Page carries the values,** which is how a real MNDA works — and why
it controls over any conflict with the Standard Terms. Because it is a fill-in
form artifact (bracketed prompts, `- [x]` checkbox pairs, an empty signature
table) rather than prose, its *structure* is composed in
`components/CoverPage.tsx` from the field schema instead of being pattern-matched
out of the markdown.

Its two pieces of substantive text are **not** copied into the component:
`extractCoverPageProse` lifts the preamble (which incorporates the Standard Terms
by reference) and the CC BY 4.0 attribution out of the template at build time. If
either can no longer be located, the build fails rather than shipping an
agreement with its preamble or licence notice quietly missing.

> **Trade-off:** the Cover Page's layout therefore lives in TSX. If Common Paper
> publishes a new cover page version with different *sections*, `CoverPage.tsx`
> must be updated to match — the build guard covers the prose, not the shape.
> The Standard Terms, which hold the substantive legal text, need no such
> maintenance.

## Download

`window.print()` plus the `@media print` rules in `app/globals.css`, so the user
saves a PDF through the browser with no extra dependency. Printing hides all app
chrome and the on-screen fill highlights, sets Letter sizing, keeps clauses and
the signature block from splitting across pages, and starts the Standard Terms
on their own page.

## Layout

| Path | Role |
| --- | --- |
| `app/page.tsx` | Server Component; reads the templates |
| `app/globals.css` | screen styles and the print stylesheet |
| `components/MndaBuilder.tsx` | owns agreement state; form + preview |
| `components/MndaForm.tsx` | controlled inputs |
| `components/CoverPage.tsx` | Cover Page, composed from field values |
| `components/StandardTerms.tsx` | Standard Terms, rendered from the template |
| `lib/fields.ts` | field schema, defaults, validation, formatting |
| `lib/templates.ts` | server-side reads of `../templates`, prose extraction |
| `lib/render.ts` | Cover Page annotation, markdown → HTML |

## Known gaps

- **No tests.** Three invariants are cheap to assert and worth covering first:
  the annotated Standard Terms are byte-identical to the template once tags are
  stripped; every `coverpage_link` label has an entry in `coverPageValues`; and
  the Cover Page renders each template section. The prose-drift case is already
  guarded by `extractCoverPageProse` throwing at build time.
- **No ESLint config** (see above).
- **`process.cwd()` template lookup.** `lib/templates.ts` tries `../templates`
  then `./templates`, which covers running from `frontend/` or the repo root. A
  module-relative anchor would be tidier but `import.meta.dirname` is undefined
  in Next's compiled server bundle.

## Licensing

Generated agreements derive from Common Paper templates, free to use and modify
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See
[`templates/LICENSE.txt`](../templates/LICENSE.txt). These documents are not
legal advice — have counsel review anything you intend to rely on.
