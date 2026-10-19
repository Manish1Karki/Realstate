import { notFound } from 'next/navigation'
import { categoryFor, districtFor, pageNumber } from '@/lib/property-categories'
import CategoryPage, { categoryMetadata } from '../../category-page'

type Props = { params: Promise<{ id: string; district: string }>; searchParams: Promise<{ page?: string }> }
async function values({ params, searchParams }: Props) {
  const { id, district: slug } = await params
  const category = categoryFor(id), district = districtFor(slug)
  if (!category || !district) notFound()
  const search = await searchParams
  return { category, district, page: pageNumber(search.page) }
}
export async function generateMetadata(props: Props) { const { category, district, page } = await values(props); return categoryMetadata(category, district, page) }
export default async function DistrictPage(props: Props) { return <CategoryPage {...await values(props)} /> }
