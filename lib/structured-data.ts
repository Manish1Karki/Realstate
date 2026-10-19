import { canonicalSiteUrl, type Property } from './api'
import { propertyTitle, propertyDescription } from './property-content'

export function websiteSchema() {
  return { '@context':'https://schema.org', '@graph':[
    { '@type':'Organization', '@id':canonicalSiteUrl('/#publisher'), name:'Land Discover', url:canonicalSiteUrl('/'), logo:{'@type':'ImageObject',url:canonicalSiteUrl('/apple-icon.png'),width:180,height:180} },
    { '@type':'WebSite', '@id':canonicalSiteUrl('/#website'), name:'Land Discover', url:canonicalSiteUrl('/'), inLanguage:'en',publisher:{'@id':canonicalSiteUrl('/#publisher')} }
  ] }
}
export function listingSchema(property: Property) {
  const url = canonicalSiteUrl('/properties/' + property.id)
  const validPin = Number.isFinite(property.lat) && Number.isFinite(property.lng) && property.lat! >= 27.5 && property.lat! <= 27.9 && property.lng! >= 85.15 && property.lng! <= 85.6 && String(property.geocode_precision || '').startsWith('source map pin')
  const residence = { '@type':property.property_type === 'house' ? 'House' : property.property_type === 'apartment' ? 'Apartment' : 'Place',
    name:propertyTitle(property), address:{'@type':'PostalAddress',streetAddress:property.address,addressLocality:property.area_name,addressRegion:property.district,addressCountry:'NP'},
    ...(validPin ? {geo:{'@type':'GeoCoordinates',latitude:property.lat,longitude:property.lng}} : {}),
    ...(property.property_type !== 'land' && property.bedrooms != null ? {numberOfBedrooms:property.bedrooms} : {}),
    ...(property.property_type !== 'land' && property.bathrooms != null ? {numberOfBathroomsTotal:property.bathrooms} : {}),
    ...(property.size ? {additionalProperty:[{'@type':'PropertyValue',name:'Published size',value:property.size}]} : {}) }
  const price = property.total_price_npr ?? property.price_npr
  const unit = property.total_price_npr ? '' : property.price_basis
  return { '@context':'https://schema.org','@type':'RealEstateListing','@id':url+'#listing',url,name:propertyTitle(property),description:propertyDescription(property),
    ...(property.image_url ? {image:property.image_url} : {}),
    ...(property.listing_date ? {datePosted:property.listing_date} : {}),
    ...(property.content_updated_at ? {dateModified:property.content_updated_at} : {}),
    isPartOf:{'@id':canonicalSiteUrl('/#website')}, mainEntity:residence,
    offers:{'@type':'Offer',url,businessFunction:property.transaction_type === 'rent' ? 'http://purl.org/goodrelations/v1#LeaseOut' : 'http://purl.org/goodrelations/v1#Sell',itemOffered:residence,
      ...(price != null && (property.total_price_npr || ['total','monthly','per_aana','per_ropani','per_sqft'].includes(unit || '')) ? {priceSpecification:{'@type':unit === 'monthly' || unit?.startsWith('per_') ? 'UnitPriceSpecification' : 'PriceSpecification',price,priceCurrency:'NPR',...(unit === 'monthly' ? {unitText:'month'} : unit?.startsWith('per_') ? {unitText:unit.slice(4)} : {})}} : {})},
    breadcrumb:{'@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:canonicalSiteUrl('/')},{'@type':'ListItem',position:2,name:'Properties',item:canonicalSiteUrl('/properties')},{'@type':'ListItem',position:3,name:propertyTitle(property),item:url}]}
  }
}
