import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // The product ships as a single FastAPI process serving both the API and the
  // frontend (see backend/app/static.py), so the frontend is exported to plain
  // HTML rather than run on a Node server. Everything dynamic — the document
  // specs and their legal text included — comes from the API at /api.
  output: 'export',

  // Export each route as `<route>/index.html` rather than `<route>.html`, which
  // is what StaticFiles(html=True) resolves a directory request to.
  trailingSlash: true,
}

export default nextConfig
