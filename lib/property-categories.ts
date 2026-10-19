export const categories = [
  { slug: 'houses-for-sale', type: 'house', transaction: 'sale', label: 'Houses for sale', introduction: 'Compare houses offered for sale across Kathmandu Valley. Review the asking price, plot or floor size, and published location before contacting the advertiser.' },
  { slug: 'houses-for-rent', type: 'house', transaction: 'rent', label: 'Houses for rent', introduction: 'Explore houses available to rent across Kathmandu Valley. Check the stated rental period, space, and available property features with the advertiser.' },
  { slug: 'land-for-sale', type: 'land', transaction: 'sale', label: 'Land for sale', introduction: 'Browse land offered for sale across Kathmandu Valley. Compare plot sizes and asking-price units, and confirm road access, boundaries, and documents directly.' },
  { slug: 'land-for-rent', type: 'land', transaction: 'rent', label: 'Land for rent', introduction: 'Find land advertised for rent across Kathmandu Valley. Ask the advertiser about the lease period, permitted use, access, and exact plot boundaries.' },
  { slug: 'apartments-for-sale', type: 'apartment', transaction: 'sale', label: 'Apartments for sale', introduction: 'Compare apartments offered for sale across Kathmandu Valley. Review published sizes, prices, and features, and ask about ownership documents and building charges.' },
  { slug: 'apartments-for-rent', type: 'apartment', transaction: 'rent', label: 'Apartments for rent', introduction: 'Browse apartments and flats available to rent across Kathmandu Valley. Compare the stated rent and available room details, and confirm deposits and additional charges.' },
] as const
export type Category = typeof categories[number]
export const districts = ['Kathmandu', 'Lalitpur', 'Bhaktapur'] as const
export function categoryFor(slug: string) { return categories.find(item => item.slug === slug) }
export function categoryForProperty(property: { property_type: string; transaction_type?: string | null }) { return categories.find(item => item.type === property.property_type && item.transaction === property.transaction_type) }
export function districtFor(slug: string) { return districts.find(item => item.toLowerCase() === slug) }
export function categoryPath(category: Category, district?: string) { return '/properties/' + category.slug + (district ? '/' + district.toLowerCase() : '') }

export function pageNumber(value?: string) { const page = Number(value); return Number.isFinite(page) ? Math.min(100000, Math.max(1, Math.floor(page || 1))) : 1 }
