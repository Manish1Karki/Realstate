import { propertyFacts, advertisedPrice, distance, missingFacts } from './context.mjs'

export function rentScenario(question, f) {
  const match = question.match(/monthly rent\s*(?:is|of|were|was|=|:)?\s*(?:NPR|Rs\.?)?\s*(\d[\d,]*(?:\.\d+)?)\s*(lakh|crore|k)?\b/i)
  if (!match) return null
  if (f.purpose !== 'sale' || !f.purchase_price_npr) return 'I need a total purchase price to work out rental yield. This listing does not provide one for a sale.'
  const rent = Number(match[1].replaceAll(',', '')) * ({ lakh: 100000, crore: 10000000, k: 1000 }[match[2]?.toLowerCase()] || 1)
  if (!Number.isFinite(rent) || rent <= 0 || rent > 1e9) return 'Please enter a valid positive monthly rent, for example: monthly rent is NPR 50,000.'
  const yearly = rent * 12
  return `Using your assumed monthly rent of NPR ${rent.toLocaleString('en-US')}:\n\nYearly rent: NPR ${yearly.toLocaleString('en-US')}\nAdvertised purchase price: NPR ${f.purchase_price_npr.toLocaleString('en-US')}\nGross rental yield: ${(yearly / f.purchase_price_npr * 100).toFixed(2)}% per year.\n\nThis is a scenario, not a rent estimate or promised return. It leaves out empty months, repairs, taxes, fees and other costs.`
}

export function savedAnswer(question, p) {
  const f = propertyFacts(p)
  const q = question.toLowerCase()
  const parts = []
  const scenario = rentScenario(question, f)
  if (scenario) return scenario
  if (/\b(hi|hello|hey|help)\b/.test(q) && q.split(/\s+/).length < 8) return 'I can explain this property using its saved listing and map data. Ask about the price, size, road, nearby places, missing details, or what to check before a visit.'
  if (/\b(road|pitched|blacktop|asphalt|construction|access|gravel|paved)\b/.test(q)) {
    const widths=[...new Set([f.road_width_ft,...[...(f.road_access||'').matchAll(/(\d+(?:\.\d+)?)\s*(?:ft|feet|foot)\b/gi)].map(m=>Number(m[1]))].filter(n=>n!=null))]
    parts.push([
      f.road_access ? `The listing reports road access as: ${f.road_access}.` : f.road_width_ft != null ? `The reported road width is ${f.road_width_ft} ft.` : 'Road access information is not available.',
      ...(widths.length>1 ? ['The saved source gives different road widths. Ask the advertiser to confirm the correct width.'] : []),
      f.road_surface ? `Reported road surface: ${f.road_surface}.` : 'The road surface is not provided.',
      f.road_is_pitched === true ? 'The source describes the access road as pitched.' : f.road_is_pitched === false ? 'The source describes the access road as unpitched.' : 'Whether the road is pitched is not available.',
      f.access_road_under_construction === null ? 'The access road construction status is not available. Please ask the advertiser.' : f.access_road_under_construction ? 'The source reports that the access road is under construction.' : 'The source reports that the access road is not under construction.',
    ].join('\n'))
  }
  if (/\b(nearby|near|school|hospital|shop|facilit|bank|market|department|pharmacy|atm|surround|km|radius)/.test(q)) {
    const radiusMatch = q.match(/\b(\d+(?:\.\d+)?)\s*(km|kilomet(?:er|re)s?|m(?:et(?:er|re)s?)?)\b/)
    const requestedRadius = radiusMatch ? Number(radiusMatch[1]) * (radiusMatch[2].startsWith('k') ? 1 : .001) : 2
    const radius = Math.min(2,requestedRadius)
    const requested = []
    if (/hospital|clinic/.test(q)) requested.push('hospital','clinic')
    if (/school|college/.test(q)) requested.push('school')
    if (/department/.test(q)) requested.push('department_store')
    else if (/shop|market/.test(q)) requested.push('market','department_store')
    if (/pharmacy/.test(q)) requested.push('pharmacy')
    if (/\batm\b/.test(q)) requested.push('atm')
    if (/bank/.test(q)) requested.push('bank')
    const places = f.nearby_places.filter(a => a.distance_km <= radius && (!requested.length || requested.includes(a.kind))).sort((a,b) => a.distance_km-b.distance_km)
    const prefix=requestedRadius>2?'I only have saved map data for up to 2 km, so I cannot check the full requested radius.\n\n':''
    parts.push(prefix+(places.length ? `${places.length} mapped ${requested.length ? 'matching places' : 'places'} within ${radius} km (showing up to 6):\n${places.slice(0,6).map(a => `- ${a.name} (${a.kind.replaceAll('_',' ')}): ${distance(a.distance_km)}`).join('\n')}\n\nThese are straight-line distances, not walking distances. Confirm the exact property location before relying on them. Map coverage may be incomplete.${f.facilities_radius_m < radius*1000 || f.facilities_status !== 'complete' ? ' The saved map search does not fully cover the requested area.' : ''}` : `No matching nearby places are recorded within ${radius} km. This does not mean there are none. The map data may be incomplete.`))
  }
  if (/\b(price|cost|expensive|cheap|worth|priced|value|valuation)\b|how much/.test(q)) {
    parts.push(f.advertised_price === 'Not provided' ? 'A price is not available in the saved listing. Please ask the advertiser.' : `The advertised price is ${advertisedPrice(p)}. It is an asking price, not a confirmed sale price.`)
    if (/why|expensive|cheap|worth|fair|reason|value|valuation/.test(q)) parts.push('The listing does not explain how the advertiser chose this price. Land size, location, road access and building condition can affect price, but I do not have enough comparable sale data to say whether this price is fair.')
  }
  if (/\b(invest|investment|profit|return|yield|grow|growth|appreciat|future|double)\b/.test(q)) parts.push('There is not enough data to predict future prices or profit. For rental income, we need a purchase price, expected rent and running costs. You can try a clearly labelled calculation by asking: "If monthly rent is NPR 50,000, what is the gross yield?" The rent would be your assumption, not a fact from the listing.')
  if (/missing|unknown|not available/.test(q)) parts.push(`Details not provided in this saved record:\n${missingFacts(f).map(name=>'- '+name).join('\n') || 'The main fields are present, but that does not verify them.'}`)
  if (/\b(size|area|aana|ropani|bedroom|bathroom|room)\b/.test(q) && !/nearby/.test(q)) parts.push(`Reported size: ${f.size || 'not provided'}.\n${f.bedrooms != null ? `Bedrooms: ${f.bedrooms}.` : 'Bedroom count is not provided.'}\n${f.bathrooms != null ? `Bathrooms: ${f.bathrooms}.` : 'Bathroom count is not provided.'}`)
  if (/\b(contact|phone|number|owner|advertiser|agent)\b/.test(q)) {
    const role = p.contact_role === 'owner' ? 'owner' : p.contact_role === 'agent' ? 'listing agent' : 'advertiser'
    parts.push(p.contact_phone ? `Published ${role} contact: ${p.contact_phone}.\nA published number does not verify ownership or current availability.` : 'A contact number is not available for this property yet.')
  }
  if (/\b(check|visit|buy|risk|missing|unknown|verify|verified|legal|document|safe|available|availability)\b/.test(q)) parts.push('Before you decide:\n- Confirm the asking price and whether it is still available.\n- Check the land size and boundary on site.\n- Ask about legal road access and road construction.\n- Check ownership papers with the proper office or a qualified local adviser.\n- Visit the property to check its condition.\n\nSaved listings and map pins do not prove ownership, legal status or current availability.')
  if (/\b(where|location|address|map)\b/.test(q) && !/nearby/.test(q)) parts.push(`Listed location: ${[f.area,f.district].filter(Boolean).join(', ') || 'not provided'}.\n${f.map_precision?.startsWith('source map pin') ? 'The source listing includes a map pin. The boundary and exact location still need to be checked.' : 'A source-published exact map pin is not available.'}`)
  if (/\b(summary|summarize|overview|tell me|about this)\b/.test(q) || !parts.length) {
    if (!parts.length && !/summary|summarize|overview|tell me|about this/.test(q)) return 'This saved-answer demo cannot answer that question yet. Try asking about the price, size, access road, nearby places, contact details, or what to check before a visit. NVIDIA mode will support more flexible questions once a key is connected.'
    parts.push(`${f.property_type || 'Property'} for ${f.purpose === 'rent' ? 'rent' : f.purpose === 'sale' ? 'sale' : 'an unspecified purpose'} in ${[f.area,f.district].filter(Boolean).join(', ')}.\nReported size: ${f.size || 'not provided'}.\nAdvertised price: ${f.advertised_price}.\n${f.road_access ? `Road access: ${f.road_access}.` : 'Road access is not provided.'}\n\nThese are saved listing details. Please confirm them before making a decision.`)
  }
  return parts.join('\n\n')
}
