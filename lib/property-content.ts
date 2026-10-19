import { formatPrice, type Property } from './api'
export function readableTitle(value: string) {
  const original = value.replace(/\s+/g, ' ').trim()
  const title = original.replace(/\bfor sail\b/gi, 'for sale')
  return original === original.toUpperCase() ? title.toLowerCase().replace(/\b[a-z]/g, letter => letter.toUpperCase()).replace(/\bbhk\b/gi, 'BHK').replace(/\bnpr\b/gi, 'NPR') : title
}
export function propertyTitle(property: Property) {
  const title = readableTitle(property.title)
  const place = [property.area_name, property.district].filter(Boolean).join(', ')
  return title.toLowerCase().includes(property.district.toLowerCase()) ? title : title + ' in ' + place
}
export function cleanDescription(value?: string | null) {
  return (value || '').replace(/<[^>]*>/g, ' ').replace(/^Views:.*?Table of Contents Toggle\s*/i, '').split(/Owner Contact|Email:|Contact:|Phone:|Mobile:/i)[0]
    .replace(/\b[\w.+-]+@[\w.-]+\.\w+\b/g, '').replace(/\s+/g, ' ').trim()
}
export function propertySummary(property: Property) {
  const kind = property.property_type.charAt(0).toUpperCase() + property.property_type.slice(1)
  const facts = [kind + ' for ' + (property.transaction_type === 'rent' ? 'rent' : 'sale') + ' in ' + [property.area_name, property.district].filter(Boolean).join(', ') + '.',
    'Advertised price: ' + formatPrice(property) + '.', property.size ? 'Published size: ' + property.size + '.' : '',
    property.bedrooms != null ? property.bedrooms + ' bedrooms.' : '', property.bathrooms != null ? property.bathrooms + ' bathrooms.' : '',
    property.road_access_note ? 'Road access reported by the source: ' + property.road_access_note + '.' : '']
  return facts.filter(Boolean).join(' ')
}
export function propertyDescription(property: Property) {
  let text = cleanDescription(property.description)
  const navigation = /Property Highlights.*House Layout/i.test(text)
  text = text.replace(/Property Highlights\s+(?:(?:House Layout|Ground Floor|First Floor|Top Floor|Selling Price)\s*)+/gi, '')
  for (let repeat = 0; repeat < 2; repeat++) if (text.toLowerCase().startsWith(property.title.toLowerCase())) text = text.slice(property.title.length).trim()
  if (navigation) {
    const start = text.search(/\b(?:A|An|This)\s+(?:[a-z-]+\s+){0,5}(?:house|home|land|plot|apartment|property)\b/i)
    if (start > 0) text = text.slice(start)
  }
  return text.length >= 30 ? text : propertySummary(property)
}

export const sourceNames: Record<string, string> = { huku: 'HUKU Real Estate', hamrobazar: 'Hamrobazar', nepalbhoomi: 'Nepal Bhoomi', nepalhomesearch: 'Nepal Home Search', gharjagganepal: 'Ghar Jagga Nepal', tradenepal: 'Trade Nepal', community: 'Property owner' }
export function jsonLdText(value: unknown) { return JSON.stringify(value).replace(/</g, '\\u003c') }
