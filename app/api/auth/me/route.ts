import { cookies } from 'next/headers'
export async function GET() {
  const session = (await cookies()).get('land_discover_session')
  if (!session) return Response.json({ user: null }, { headers: { 'Cache-Control': 'no-store' } })
  const origin = (process.env.LAND_API_URL || process.env.BACKEND_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
  const headers: Record<string,string> = { Cookie: 'land_discover_session=' + session.value }
  if (process.env.BACKEND_PROXY_SECRET) headers['X-Land-Proxy-Token'] = process.env.BACKEND_PROXY_SECRET
  try {
    const response = await fetch(origin + '/api/auth/me', { cache: 'no-store', headers, signal: AbortSignal.timeout(8000) })
    return new Response(await response.text(), { status: response.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } })
  } catch { return Response.json({ detail:'Account service is temporarily unavailable' }, { status:503,headers:{'Cache-Control':'no-store'} }) }
}
