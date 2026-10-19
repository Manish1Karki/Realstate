export const optimizedImageHosts = [
  'cdn03.hamrobazaar.com', 'hamrobazaar.blr1.cdn.digitaloceanspaces.com', 'hamrobazaar.blr1.digitaloceanspaces.com',
  'gharjagganepal.com', 'www.gharjagganepal.com', 'images.hukurealestate.com', 'www.hukurealestate.com',
  'nepalbhoomi.com', 'nepalhomesearch.com', 'www.nepalhomesearch.com', 'realestatebrokernepal.com', 'images.unsplash.com'
]
export function optimizablePhoto(value: string) {
  try { const url = new URL(value); return url.protocol === 'https:' && optimizedImageHosts.includes(url.hostname) && !url.username && !url.password && (!url.port || url.port === '443') } catch { return false }
}
