export const SEARCH_COOKIE = 'land_discover_search'
export function resultsPath(value: string | null | undefined): string | null {
  if (!value?.startsWith('/properties?')) return null
  const params = new URLSearchParams(value.slice('/properties?'.length))
  if (!['sale','rent'].includes(params.get('transaction') || '') || !['house','land','apartment'].includes(params.get('property_type') || '')) return null
  const safe = new URLSearchParams()
  for (const key of ['transaction','property_type','district','q','sort','page']) {
    const item = params.get(key)
    if (item) safe.set(key,item.slice(0,200))
  }
  return '/properties?' + safe.toString()
}
export function readRememberedSearch(): string | null {
  const value = document.cookie.split('; ').find(item => item.startsWith(SEARCH_COOKIE+'='))
  try { return resultsPath(value ? decodeURIComponent(value.slice(SEARCH_COOKIE.length+1)) : null) } catch { return null }
}
