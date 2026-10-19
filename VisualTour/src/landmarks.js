export const placeColors = { school:'#7453b8', police:'#2364aa', hospital:'#bf3344', pharmacy:'#bf3344', bank:'#a76c12', atm:'#a76c12', market:'#16805e', department_store:'#16805e', transport:'#287e95', park:'#39832c', playground:'#39832c' }
export function nearbyPlaces(listing) {
 const seen = new Set()
 return (listing.amenities || []).filter(place => {
   if (place.kind === 'road' || !Number.isFinite(place.lat) || !Number.isFinite(place.lng) || !Number.isFinite(place.distance_km) || place.distance_km < 0 || place.distance_km > 2 || place.lat < 27.5 || place.lat > 27.9 || place.lng < 85.15 || place.lng > 85.6) return false
   const key = place.osm_id || String(place.id)
   if(seen.has(key)) return false
   seen.add(key); return true
 }).sort((a,b) => a.distance_km-b.distance_km)
}
export const placeType = kind => String(kind || 'place').replaceAll('_',' ')
