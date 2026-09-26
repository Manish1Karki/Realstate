from pathlib import Path
from bs4 import BeautifulSoup
from land_discover.db import init_db
from land_discover.http import Client

init_db(); c=Client()
# Bounded, user-requested live validation of public HTML. Client.page enforces
# robots and origin restrictions; this does not enable the production crawler.
base='https://hamrobazaar.com'
url=base+'/category/real-estate/06B8B8E6-4CDE-4D79-AE65-38B8BAA9FF17'
html=c.page(url,'hamrobazaar.com')
Path('data/audit/hamro-category.html').write_text(html,encoding='utf8')
s=BeautifulSoup(html,'html.parser')
links=list(dict.fromkeys(a['href'] for a in s.select('a[href]') if '/detail/' in a['href']))
print('DETAIL LINKS',links[:4],flush=True)
print('SCRIPTS',[(x.get('type'),x.get('id')) for x in s.find_all('script') if x.get('type')=='application/ld+json' or x.get('id')],flush=True)
if links:
    url=base+links[0] if links[0].startswith('/') else links[0]
    detail=c.page(url,'hamrobazaar.com')
    Path('data/audit/hamro-detail.html').write_text(detail,encoding='utf8')
    Path('data/audit/hamro-detail-url.txt').write_text(url,encoding='utf8')
    d=BeautifulSoup(detail,'html.parser')
    print(d.get_text('\n',strip=True)[:18000])
    print('LD JSON', [x.get_text()[:5000] for x in d.select('script[type="application/ld+json"]')])
c.close()
