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
