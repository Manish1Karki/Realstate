import { optimizedImageHosts } from './lib/property-images'
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    remotePatterns: optimizedImageHosts.map(hostname => ({ protocol: 'https' as const, hostname, port: '', pathname: '/**' })),
    formats: ['image/avif', 'image/webp'], qualities: [75], minimumCacheTTL: 86400,
    maximumRedirects: 0, dangerouslyAllowLocalIP: false, dangerouslyAllowSVG: false,
  },
  distDir: process.env.LAND_NEXT_DIST_DIR || '.next',
  poweredByHeader: false,
  turbopack: { root: process.cwd() },
  async headers() {
    return [{ source: '/visual-tour/:path*', headers: [{ key: 'X-Robots-Tag', value: 'noindex' }] },{
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
        { source: '/api/asking-range/:path*', destination: '/backend-only-unavailable' },
        { source: '/api/property-chat/:path*', destination: 'http://127.0.0.1:3100/api/:path*' },
      ],
      afterFiles: [{ source: '/api/:path*', destination: (process.env.LAND_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '') + '/api/:path*' }],
      fallback: [],
    }
    return []
  },
}

export default nextConfig
