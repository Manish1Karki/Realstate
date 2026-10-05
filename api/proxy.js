import { Readable } from 'node:stream';
import { pipeline } from 'node:stream/promises';

export function createProxy({ fetchImpl = fetch, env = process.env } = {}) {
  return async function proxy(req, res) {
    res.setHeader('Cache-Control', 'no-store');
    function error(status, detail) { res.statusCode = status; res.setHeader('Content-Type', 'application/json'); res.end(JSON.stringify({ detail })); }
    if (!env.BACKEND_API_URL || !env.BACKEND_PROXY_SECRET) {
      error(503, 'The property and account service is not configured yet.'); return;
    }
    let upstream;
    try {
      const backend = new URL(env.BACKEND_API_URL);
      if (backend.protocol !== 'https:' || backend.username || backend.password) throw new Error('Invalid backend');
      const path = req.query?.path;
      if (typeof path !== 'string' || !path || path.includes('\\')) throw new Error('Invalid API path');
      upstream = new URL(`/api/${path}`, backend.origin);
      if (!upstream.pathname.startsWith('/api/')) throw new Error('Invalid API path');
      const incoming = new URL(req.url, 'https://prototype.invalid');
      for (const [key, value] of incoming.searchParams) if (key !== 'path') upstream.searchParams.append(key, value);
    } catch { error(400, 'Invalid service request.'); return; }

    const host = req.headers.host;
    if (!host || !/^[a-zA-Z0-9.:-]+$/.test(host)) { error(400, 'Invalid website host.'); return; }
    const origin = `${env.VERCEL ? 'https' : 'http'}://${host}`;
    const method = req.method || 'GET';
    if (!['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'].includes(method)) { error(405, 'Method not allowed.'); return; }
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && req.headers.origin && req.headers.origin !== origin) {
      error(403, 'This request came from an untrusted website.'); return;
    }
    const headers = { 'X-Land-Proxy-Token': env.BACKEND_PROXY_SECRET, 'X-Land-Frontend-Origin': origin };
    for (const name of ['accept', 'content-type', 'cookie', 'origin', 'sec-fetch-site', 'x-land-import-token']) {
      if (req.headers[name]) headers[name] = req.headers[name];
    }
    // This value is supplied by Vercel, not an arbitrary incoming forwarding header.
    if (env.VERCEL && req.headers['x-vercel-forwarded-for']) headers['X-Land-Client-IP'] = req.headers['x-vercel-forwarded-for'];
    try {
      let body;
      if (!['GET', 'HEAD'].includes(method) && req.body != null) body = typeof req.body === 'string' || Buffer.isBuffer(req.body) ? req.body : JSON.stringify(req.body);
      // Free Render instances need time to wake after idle periods.
      const response = await fetchImpl(upstream, { method, headers, body, redirect: 'manual', signal: AbortSignal.timeout(110000) });
      res.statusCode = response.status;
      const contentType = response.headers.get('content-type');
      if (contentType) res.setHeader('Content-Type', contentType);
      const disposition = response.headers.get('content-disposition');
      if (disposition) res.setHeader('Content-Disposition', disposition);
      const retry = response.headers.get('retry-after');
      if (retry) res.setHeader('Retry-After', retry);
      const cookies = response.headers.getSetCookie();
      if (cookies.length) res.setHeader('Set-Cookie', cookies);
      if (!response.body || method === 'HEAD') res.end();
      else await pipeline(Readable.fromWeb(response.body), res);
    } catch {
      if (!res.headersSent) error(502, 'Unable to reach the property and account service. Please try again.');
      else res.destroy();
    }
  };
}

export default createProxy();
