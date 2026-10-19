import Link from 'next/link'
import { categories, categoryPath } from '@/lib/property-categories'

export default function BrowseLinks({ simpleEnglish = false }: { simpleEnglish?: boolean }) {
  return <section className="browse-category-links" aria-labelledby="browse-category-heading"><h2 id="browse-category-heading">{simpleEnglish ? 'What are you looking for?' : 'Browse by property category'}</h2><p>{simpleEnglish ? 'Choose what you want to buy or rent.' : 'Explore a category directly, or use the filters above to narrow your search.'}</p><div>{categories.map(category => <Link key={category.slug} href={categoryPath(category)}>{simpleEnglish ? `${category.transaction === 'sale' ? 'Buy' : 'Rent'} ${category.type === 'land' ? 'land' : category.type === 'house' ? 'a house' : 'a flat'}` : category.label} <span aria-hidden="true">&rarr;</span></Link>)}</div></section>
}
