import path from 'node:path'
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // The MNDA templates live in the repo-root `templates/` directory, one level
  // above this app, and are read with `fs` rather than imported. File tracing
  // follows imports, so it cannot discover them on its own: `Root` widens the
  // trace base to include the parent directory, and `Includes` names the files
  // explicitly. Today the page prerenders statically, so the read happens at
  // build time and these only matter if the page ever becomes dynamic — at
  // which point the read moves to request time and would otherwise ENOENT on a
  // standalone deploy.
  outputFileTracingRoot: path.join(__dirname, '..'),
  outputFileTracingIncludes: {
    '/': ['../templates/**'],
  },
}

export default nextConfig
