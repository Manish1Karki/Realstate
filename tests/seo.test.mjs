import test from 'node:test'
import assert from 'node:assert/strict'
import ts from 'typescript'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import path from 'node:path'

const output = path.resolve('.review/seo-test-modules')
mkdirSync(output,{recursive:true})
for (const name of ['api','property-content','structured-data','property-categories','property-images']) {
  const source = readFileSync('lib/'+name+'.ts','utf8').replace(/from '(.\/[^']+)'/g, (match,target)=>"from '"+target+".mjs'")
  writeFileSync(path.join(output,name+'.mjs'),ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText)
}
const { readableTitle, propertyTitle, propertySummary, propertyDescription, jsonLdText } = await import(pathToFileURL(path.join(output,'property-content.mjs')))
const { listingSchema, websiteSchema } = await import(pathToFileURL(path.join(output,'structured-data.mjs')))
const { getProperties, getProperty, getSitemapProperties } = await import(pathToFileURL(path.join(output,'api.mjs')))
const { optimizablePhoto } = await import(pathToFileURL(path.join(output,'property-images.mjs')))
const base = { id:42,title:'HOUSE FOR SALE IN BHAKTAPUR',property_type:'house',transaction_type:'sale',district:'Bhaktapur',area_name:'Tathali',address:'Tathali, Bhaktapur',source:'fixture',source_url:'https://example.org/42',price_basis:'total',price_npr:5000000,total_price_npr:5000000 }

test('titles remove repeated district suffixes and normalize source casing',()=>{
  assert.equal(propertyTitle(base),'House For Sale In Bhaktapur')
  assert.equal(readableTitle('RESIDENTIAL HOUSE FOR SAIL'),'Residential House For Sale')
})
test('factual summaries retain monthly and per-unit price meaning',()=>{
  assert.match(propertySummary({...base,transaction_type:'rent',price_basis:'monthly',total_price_npr:null}),/\/ month/)
  assert.match(propertySummary({...base,price_basis:'per_aana',total_price_npr:null}),/per aana/)
})
test('JSON-LD cannot terminate its script and decodes to the original text',()=>{
  const malicious = { name:'</script><script>alert(1)</script>' }
  assert.ok(!jsonLdText(malicious).includes('<'))
  assert.deepEqual(JSON.parse(jsonLdText(malicious)),malicious)
})
test('property schema uses exact verified coordinates and omits invented fields',()=>{
  const lat=27.653996123456,lng=85.303110345678
  const schema=listingSchema({...base,lat,lng,geocode_precision:'source map pin',content_updated_at:null})
  assert.deepEqual(schema.mainEntity.geo,{'@type':'GeoCoordinates',latitude:lat,longitude:lng})
  assert.equal(schema.dateModified,undefined)
  assert.equal(schema.offers.availability,undefined)
  assert.equal(listingSchema({...base,lat,lng,geocode_precision:'area centroid'}).mainEntity.geo,undefined)
  assert.equal(websiteSchema()['@graph'][0].address,undefined)
})
test('optimizer only accepts reviewed HTTPS hosts',()=>{
  assert.equal(optimizablePhoto('https://nepalbhoomi.com/house.jpg'),true)
  for(const url of ['http://nepalbhoomi.com/house.jpg','https://127.0.0.1/house.jpg','https://nepalbhoomi.com.evil.test/house.jpg','https://name:password@nepalbhoomi.com/house.jpg']) assert.equal(optimizablePhoto(url),false)
})

test('server API caches only public reads and treats service outages as errors',async()=>{
  const original = globalThis.fetch
  const calls=[]
  globalThis.fetch=async(url,options)=>{calls.push({url:String(url),options});return new Response(JSON.stringify({items:[],total:0}),{status:200})}
  try {
    await getProperties(new URLSearchParams({transaction:'sale'}))
    assert.equal(calls[0].options.next.revalidate,60)
    assert.equal(calls[0].options.headers.Cookie,undefined)
    await getProperties(new URLSearchParams({q:'a private search'}))
    assert.equal(calls[1].options.cache,'no-store')
    await getSitemapProperties()
    assert.equal(calls[2].options.next.revalidate,300)
    globalThis.fetch=async()=>new Response('{}',{status:503})
    await assert.rejects(getSitemapProperties)
    await assert.rejects(()=>getProperty('42'))
    globalThis.fetch=async()=>new Response('{}',{status:404})
    assert.equal(await getProperty('42'),null)
  } finally {globalThis.fetch=original}
})

test('source navigation and repeated titles do not bury the property description',()=>{
  const title='Modern house'
  const property={...base,title,description:'Views: 10 Table of Contents Toggle Modern house Property Highlights House Layout Ground Floor First Floor Top Floor Selling Price Modern house Premium location A beautifully designed modern house with five bedrooms.'}
  assert.equal(propertyDescription(property),'A beautifully designed modern house with five bedrooms.')
})
