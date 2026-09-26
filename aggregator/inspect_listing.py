"""Fetch one explicitly supplied, robots-permitted public Hamrobazar page."""
import argparse,re
from pathlib import Path
from bs4 import BeautifulSoup
from land_discover.db import init_db
from land_discover.http import Client
p=argparse.ArgumentParser();p.add_argument('url');p.add_argument('--name',default='sample');args=p.parse_args()
if not re.fullmatch(r'[a-z0-9-]+',args.name): p.error('Use a simple filename')
init_db();c=Client()
try:
    html=c.page(args.url,'hamrobazaar.com')
    Path('data/audit').mkdir(parents=True,exist_ok=True)
    Path(f'data/audit/{args.name}.html').write_text(html,encoding='utf8')
    s=BeautifulSoup(html,'html.parser')
    for script in s.select('script[type="application/ld+json"]'):
        import json
        data=json.loads(script.get_text())
        if data.get('@type')=='Product':
            description=re.sub(r'\b\d{8,}\b','[contact omitted]',data.get('description',''))
            print(json.dumps({k:data.get(k) for k in ('name','category','sku')}|{'price':data.get('offers',{}).get('price'),'description':description},ensure_ascii=False),flush=True)
    for h in s.find_all(['h1','h2','h3']):
        if h.get_text(strip=True) in ('Specifications','About this listing'):
            print(str(h.parent)[:8000],flush=True)
    if args.name=='terms':
        print(s.get_text(' ',strip=True),flush=True)
finally:c.close()
