import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    // Only the pure modules under lib/ are covered. Components would need a
    // DOM environment and a rendering library; that is worth doing, but it is
    // a larger change than this one.
    include: ['lib/**/*.test.ts'],
  },
  resolve: {
    // Mirrors the `@/*` path alias in tsconfig.json.
    alias: { '@': new URL('.', import.meta.url).pathname },
  },
})
