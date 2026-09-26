import argparse, csv, json, sys
from pathlib import Path
from .db import init_db, upsert
from .normalize import normalize

def main():
    p=argparse.ArgumentParser(description='Land Discover data pipeline')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('init'); sub.add_parser('demo'); sub.add_parser('sources')
    scrape=sub.add_parser('scrape'); scrape.add_argument('source'); scrape.add_argument('--pages',type=int,default=2); scrape.add_argument('--limit',type=int,default=20); scrape.add_argument('--csv',default='data/listings.csv')
    export=sub.add_parser('export');export.add_argument('path');export.add_argument('--source')
    geo=sub.add_parser('enrich'); geo.add_argument('--limit',type=int,default=10); geo.add_argument('--radius',type=int,default=1500); geo.add_argument('--retry',action='store_true')
    imp=sub.add_parser('import-csv'); imp.add_argument('path'); imp.add_argument('--source',required=True)
    parse=sub.add_parser('parse-html'); parse.add_argument('path'); parse.add_argument('--source',required=True); parse.add_argument('--url',required=True)
    args=p.parse_args(); init_db()
    if args.command=='init': result={'status':'initialized'}
    elif args.command=='demo':
        from .demo import seed
        result={'demo_records':seed()}
    elif args.command=='sources':
        from .sources import SOURCES
        result=SOURCES
    elif args.command=='scrape':
        from .scraper import scrape
        from .export import export_properties
        result=scrape(args.source,args.pages,args.limit)
        if result['status']!='failed': result['csv']=export_properties(args.csv,args.source,result.get('property_ids',[]))
    elif args.command=='export':
        from .export import export_properties
        result=export_properties(args.path,args.source)
    elif args.command=='enrich':
        from .geo import enrich
        if not 1<=args.limit<=100: p.error('Use 1–100 properties per one-time batch')
        result=enrich(args.limit,args.radius,args.retry)
    elif args.command=='parse-html':
        from .scraper import parse_detail
        result=parse_detail(Path(args.path).read_text(encoding='utf-8'),args.url,args.source)
    else:
        result={'imported':0,'errors':[]}
        with open(args.path,encoding='utf-8-sig',newline='') as f:
            for i,row in enumerate(csv.DictReader(f),2):
                try:
                    row['source']=args.source
                    if not row.get('source_url','').startswith('https://'): raise ValueError('An HTTPS source_url is required')
                    upsert(normalize(row)); result['imported']+=1
                except Exception as e: result['errors'].append({'line':i,'error':str(e)})
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if result.get('status')=='failed' or result.get('errors'): return 1
    return 0

if __name__=='__main__': sys.exit(main())
