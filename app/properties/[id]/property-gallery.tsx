 'use client'
import { useState } from 'react'
import PropertyPhoto from '../../property-photo'
export default function PropertyGallery({ photos, title }: { photos: string[]; title: string }) {
  const [selected, setSelected] = useState(0)
  return <div className="property-gallery-column"><div className="property-photo-preview"><PropertyPhoto urls={photos.length ? [photos[selected], ...photos] : []} alt={title} eager sizes="(max-width: 760px) 100vw, 50vw" /></div>{photos.length > 1 && <div className="property-gallery-thumbnails" aria-label="Property photos">{photos.map((photo, index) => <button key={photo} type="button" aria-label={'Show property photo ' + (index + 1)} aria-pressed={selected === index} onClick={() => setSelected(index)}><PropertyPhoto urls={[photo]} alt={title + ', photo ' + (index + 1)} sizes="100px" /></button>)}</div>}</div>
}
