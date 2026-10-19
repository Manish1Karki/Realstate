'use client'

export default function SortChoice({ sort }: { sort: string }) {
  return <select className="sort-choice" name="sort" defaultValue={sort} onChange={event => event.currentTarget.form?.requestSubmit()}>
    <option value="newest">Newest first</option>
    <option value="price_asc">Price: low to high</option>
    <option value="price_desc">Price: high to low</option>
  </select>
}
