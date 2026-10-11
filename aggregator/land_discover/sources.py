"""Source inventory and reviewed public-access scope."""
SOURCES = {
 'hamrobazar': {
   'name':'Hamrobazar','host':'hamrobazaar.com',
   'start_url':'https://hamrobazaar.com/category/real-estate/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17',
   'terms_url':'https://hamrobazaar.com/terms','detail_path':'/detail/',
   'status':'public_html',
   'reason':'Public category/detail HTML checked 2026-09-26. Bounded local collection uses robots-permitted pages only; /api/ and masked information are not accessed. No commercial redistribution license is claimed.',
   'adapter':'hamrobazar',
   'auto_collect':True,
   'reviewed_on':'2026-09-26',
   'terms_sha256':'e4e769f2ab1b6e5edac7597af5d6a1bc49e9965164dc223fb4dc2adfe2a9da02',
 },
 'huku': {
   'name':'HUKU Real Estate','host':'www.hukurealestate.com',
   'start_url':'https://www.hukurealestate.com/',
   'terms_url':'https://www.hukurealestate.com/terms-and-services',
   'detail_path':'/properties/','detail_pattern':r'/properties/\d+/?',
   'status':'public_html','adapter':'huku','auto_collect':True,
   'reviewed_on':'2026-10-05',
   'terms_sha256':'adfe8573d4306295ab173fcce2cae01ad55f48261dcba163bb2724ec25eabaa1',
   'reason':'Public homepage and sale/rental/land details validated 2026-10-03; public policy clauses reviewed 2026-10-05. Collects public HTML, property photos and visible features; robots and the policy fingerprint are checked on each run. Hosting-side access may be denied by the source; collection history records failures.',
 },
 'housingnepal': {
   'name':'Housing Nepal','host':'www.housingnepal.com',
   'start_url':'https://www.housingnepal.com/search/properties',
   'terms_url':'https://www.housingnepal.com/terms_and_conditions','detail_path':None,
   'status':'permission_required',
   'reason':'Terms prohibit automated viewing and data copying without consent. No listing adapter enabled.',
   'adapter':None,
 },
 'nepalpropertybazaar': {
   'name':'Nepal Property Bazaar','host':'nepalpropertybazaar.com',
   'start_url':'https://nepalpropertybazaar.com/',
   'terms_url':'https://nepalpropertybazaar.com/terms-and-conditions/','detail_path':None,
   'status':'permission_required',
   'reason':'Terms limit reuse to personal non-commercial use; redistribution requires prior written permission. Exact intended Nepal Property source should be confirmed.',
   'adapter':None,
 },
 'gharbazar': {
   'name':'Gharbazar','host':'www.gharbazar.com',
   'start_url':'https://www.gharbazar.com/',
   'terms_url':'https://www.gharbazar.com/','detail_path':'/property/details/',
   'status':'permission_required',
   'reason':'Listing footer prohibits copying or reproducing information. Semantic adapter is offline-only until consent and live validation.',
   'adapter':'gharbazar',
 },
 'gharbeta': {
   'name':'GharBeta','host':None,'start_url':None,'terms_url':None,'detail_path':None,
   'status':'domain_unverified','reason':'No official Nepal property website could be verified for this name. No guessed domain or selectors.','adapter':None,
 }
}

# Experimental adapters never participate in the hosted/default collector.
SOURCES.update({
 'epropertynepal': {
   'name':'eProperty Nepal','host':'epropertynepal.com',
   'start_url':'https://epropertynepal.com/properties',
   'start_urls':['https://epropertynepal.com/properties','https://epropertynepal.com/properties/rents'],
   'terms_url':'https://epropertynepal.com/terms-condition',
   'detail_path':'/properties/','detail_pattern':r'/properties/\d+(?:-[^/]+)?/?',
   'status':'permission_required','adapter':'epropertynepal','auto_collect':False,
   'reviewed_on':'2026-10-08',
   'reason':'Published terms reviewed 2026-10-08: listing information is for internal use and must not be distributed, published, or used on another listing service without permission. Adapter is disabled pending written authorization.',
 },
 'nepalbhoomi': {
   'name':'Nepal Bhoomi','host':'nepalbhoomi.com',
   'start_url':'https://nepalbhoomi.com/properties/buy',
   'start_urls':['https://nepalbhoomi.com/properties/buy','https://nepalbhoomi.com/properties/rent'],
   'terms_url':None,
   'detail_path':'/properties/','detail_pattern':r'/properties/(?!buy/?$|rent/?$)[^/]+/?',
   'status':'local_trial','adapter':'nepalbhoomi','auto_collect':False,
   'reviewed_on':'2026-10-05',
   'reason':'Local trial only. Public sale/rental indexes expose detail and pagination links. Privacy policy inspected; no terms link found. Conflicting districts are rejected, unknown prices stay unknown. Publication/reuse review remains outstanding.',
 },
})

# Additional candidate sites are tracked here so the dashboard shows why they
# are not in collection. They remain disabled until an allowed feed or written
# reuse permission is confirmed and a source adapter is validated.
SOURCES.update({
 'nepalniwas': {
   'name':'Nepal Niwas','host':'nepalniwas.com',
   'start_url':'https://nepalniwas.com/','terms_url':'https://nepalniwas.com/terms',
   'detail_path':None,'status':'permission_required','adapter':None,
   'reason':'Published terms restrict harvesting and copying listing content without authorization. No adapter enabled.',
 },
 'mlsnepal': {
   'name':'MLS Nepal','host':'www.mlsnepal.com',
   'start_url':'https://www.mlsnepal.com/','terms_url':'https://www.mlsnepal.com/terms',
   'detail_path':None,'status':'permission_required','adapter':None,
   'reason':'Terms reviewed in source audit prohibit scraping without permission. Request a partner feed or written authorization.',
 },
 'gharjaggafinder': {
   'name':'GharJaggaFinder','host':'www.gharjaggafinder.com',
   'start_url':'https://www.gharjaggafinder.com/','terms_url':'https://www.gharjaggafinder.com/terms',
   'detail_path':None,'status':'permission_required','adapter':None,
   'reason':'Published terms prohibit copying data or reverse engineering without consent. No adapter enabled.',
 },
 'realestateinnepal': {
   'name':'Real Estate in Nepal','host':'realestateinnepal.com',
   'start_url':'https://realestateinnepal.com/','terms_url':'https://realestateinnepal.com/terms-conditions/',
   'detail_path':None,'status':'permission_required','adapter':None,
   'reason':'Published terms prohibit copying, modifying, or distributing site content without prior written consent. No adapter enabled.',
 },
 'hamrobhumi': {
   'name':'HamroBhumi','host':'www.hamrobhumi.com',
   'start_url':'https://www.hamrobhumi.com/','terms_url':'https://www.hamrobhumi.com/terms',
   'detail_path':None,'status':'permission_required','adapter':None,
   'reason':'Published terms prohibit scraping or copying the platform. Request permission or a supported listing feed.',
 },
 'merobhumi': {
   'name':'MeroBhumi','host':'www.merobhumi.com',
   'start_url':'https://www.merobhumi.com/','terms_url':None,
   'detail_path':None,'status':'review_required','adapter':None,
   'reason':'Public property pages exist, but current terms and robots rules have not been verified. No adapter or collection enabled.',
 },
})

# Public HTML and original-date markup revalidated on 10 October 2026.
SOURCES['nepalbhoomi'].update(status='reviewed_public', auto_collect=True, reviewed_on='2026-10-10',
    reason='Public buy/rent/detail pages revalidated. Published dates and useful facts required, maps optional. Privacy reviewed; no public scraping prohibition found in inspected navigation.',
    terms_url='https://nepalbhoomi.com/privacy')
SOURCES.update({
 'gharjagganepal': {'name':'Ghar Jagga Nepal','host':'gharjagganepal.com',
    'start_url':'https://gharjagganepal.com/', 'start_urls':['https://gharjagganepal.com/','https://gharjagganepal.com/properties/'],
    'terms_url':None, 'detail_path':'/properties/', 'detail_pattern':r'/properties/[^/]+/[^/]+/[^/]+/?',
    'status':'reviewed_public','adapter':'public_sources','auto_collect':True,'reviewed_on':'2026-10-10',
    'reason':'Public GeoDirectory pages verified with original datePublished, price and address. Robots allow pages; no terms link found in inspected navigation.'},
 'nepalhomesearch': {'name':'Nepal Home Search','host':'nepalhomesearch.com',
    'start_url':'https://nepalhomesearch.com/', 'start_urls':['https://nepalhomesearch.com/','https://nepalhomesearch.com/property-status/property-for-sale/','https://nepalhomesearch.com/property-status/property-for-rent/'],
    'terms_url':None,'detail_path':'/property/','detail_pattern':r'/property/[^/]+/?',
    'status':'reviewed_public','adapter':'public_sources','auto_collect':True,'reviewed_on':'2026-10-10',
    'reason':'Public schema and property-specific price units validated. Original publication metadata required; modification dates do not substitute. Robots allow property pages.'},
 'tradenepal': {'name':'Trade Nepal Real Estate','host':'realestatebrokernepal.com',
    'start_url':'https://realestatebrokernepal.com/properties', 'start_urls':['https://realestatebrokernepal.com/properties','https://realestatebrokernepal.com/'],
    'terms_url':'https://realestatebrokernepal.com/pages/terms-of-use','detail_path':'/property/','detail_pattern':r'/property/[^/]+/?',
    'status':'reviewed_public','adapter':'public_sources','auto_collect':True,'reviewed_on':'2026-10-10',
    'reason':'Public schema provides datePosted, address, currency and price. Terms reviewed and robots allow public listings. No private API collection.'},
})

SOURCES['nepalbhoomi']['terms_sha256']='568edfdcc796d44853d0e749d1ab9d4da1554c3939d57721f190d566d2f8f3a7'
SOURCES['tradenepal']['terms_sha256']='878d53b3d40a1a576423c9a9302973f1379f92cc667dfaae6d9c34defe3d16e3'

for key in ('gharjagganepal','nepalhomesearch'): SOURCES[key]['canonical_trailing_slash']=True

SOURCES.update({
 '99aana': {'name':'99aana','host':'99aana.com','start_url':'https://99aana.com/','terms_url':'https://99aana.com/terms-conditions/','detail_path':'/property/','status':'permission_required','adapter':None,'reason':'Terms inspected 2026-10-10 expressly prohibit automated extraction without written consent.'},
 'gharghaderi': {'name':'Gharghaderi','host':'www.gharghaderi.com','start_url':'https://www.gharghaderi.com/','terms_url':'https://www.gharghaderi.com/terms-of-use/','detail_path':None,'status':'permission_required','adapter':None,'reason':'Terms inspected 2026-10-10 prohibit automated viewing and copying without consent.'},
 'merogarh': {'name':'Mero Garh','host':'www.merogarh.com','start_url':'https://www.merogarh.com/','terms_url':'https://www.merogarh.com/terms/','detail_path':'/property/','status':'permission_required','adapter':None,'reason':'Public terms inspected 2026-10-10 explicitly say no scraping.'},
 'jaggadhani': {'name':'JaggaDhani','host':'www.jaggadhani.com','start_url':'https://www.jaggadhani.com/','terms_url':'https://www.jaggadhani.com/terms','detail_path':'/property-details/','status':'permission_required','adapter':None,'reason':'Terms inspected 2026-10-10 require prior consent to reuse platform content.'},
 'gharjaggabazar': {'name':'GharJaggaBazar','host':'gharjaggabazar.com','start_url':'https://gharjaggabazar.com/','terms_url':'https://gharjaggabazar.com/page/copy-right-policy/','detail_path':'/property/details/','status':'permission_required','adapter':None,'reason':'Published policy inspected 2026-10-10 prohibits copying text and pictures.'},
 'nepalgharjagga': {'name':'Nepal Ghar Jagga','host':'nepalgharjagga.com','start_url':'https://nepalgharjagga.com/','terms_url':None,'detail_path':'/estate/','status':'review_required','adapter':None,'reason':'Inspected detail page contains template placeholders and unrelated education reviews; no reliable original posting date.'},
 'gharjaggadealer': {'name':'Ghar Jagga Dealer','host':'www.gharjaggadealer.com','start_url':'https://www.gharjaggadealer.com/','terms_url':None,'detail_path':'/home/detail/','status':'review_required','adapter':None,'reason':'Public detail checked 2026-10-10 but original listing date unavailable, so six-month eligibility cannot be established.'},
 'neopropertynepal': {'name':'Neo Property Nepal','host':'neopropertynepal.com','start_url':'https://neopropertynepal.com/','terms_url':None,'detail_path':None,'status':'review_required','adapter':None,'reason':'Inspected category and terms links return 404.'},
 'leafpropertyhub': {'name':'Leaf Property Hub','host':'www.leafpropertyhub.com','start_url':'https://www.leafpropertyhub.com/','terms_url':'https://www.leafpropertyhub.com/terms/','detail_path':'/properties/','status':'review_required','adapter':None,'reason':'Sample listing says imported for development from another site and unverified; exclude imported development inventory.'},
})


def local_trials_enabled():
    import os
    from .db import cloud_config
    return (os.getenv('LAND_LOCAL_SOURCE_TRIAL','false').lower()=='true'
            and not cloud_config()
            and not any(os.getenv(key) for key in ('RENDER','VERCEL'))
            and os.getenv('LAND_REQUIRE_PROXY','false').lower()!='true')


def source_enabled(key):
    config=SOURCES[key]
    if config.get('status')=='local_trial': return local_trials_enabled()
    return bool(config.get('auto_collect') and config.get('adapter'))
