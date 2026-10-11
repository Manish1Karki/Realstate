import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  poweredByHeader: false,
  turbopack: { root: process.cwd() },
  async headers() {
    return [{
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
      ],
    }]
  },
  async rewrites() {
    if (process.env.NODE_ENV === 'development') return {
      beforeFiles: [
        { source: '/api/sources/:path*', destination: '/backend-only-unavailable' },
        { source: '/api/import/:path*', destination: '/backend-only-unavailable' },
      ],
      afterFiles: [{ source: '/api/:path*', destination: 'http://127.0.0.1:8000/api/:path*' }],
      fallback: [],
    }
    return []
  },
}

export default nextConfig
