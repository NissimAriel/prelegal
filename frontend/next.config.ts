import path from 'node:path'
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // The product ships as a single FastAPI process serving both the API and the
  // frontend (see backend/app/static.py), so the frontend is exported to plain
  // HTML rather than run on a Node server. Everything dynamic comes from the
  // API at /api; nothing in this app runs per request.
  output: 'export',

  // Export each route as `<route>/index.html` rather than `<route>.html`, which
  // is what StaticFiles(html=True) resolves a directory request to.
  trailingSlash: true,

  // The templates live in the repo-root `templates/` directory, one level above
  // this app, and are read with `fs` at build time rather than imported. File
  // tracing follows imports, so it cannot discover them on its own: `Root`
  // widens the trace base to include the parent directory, and `Includes` names
  // the files explicitly.
  outputFileTracingRoot: path.join(__dirname, '..'),
  outputFileTracingIncludes: {
    '/mnda': ['../templates/**'],
  },
}

export default nextConfig
