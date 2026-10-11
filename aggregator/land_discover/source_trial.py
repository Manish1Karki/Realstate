"""Run all adapters against an isolated local database, without publishing."""
import argparse
import json
import os


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pages',type=int,choices=range(1,11),default=4)
    parser.add_argument('--limit',type=int,choices=range(1,101),default=18)
    parser.add_argument('--sources',nargs='+',choices=('hamrobazar','huku','nepalbhoomi'))
    parser.add_argument('--serve',action='store_true',help='Serve the isolated local API; collect automatically on startup')
    parser.add_argument('--port',type=int,default=8010,help='Local API port (default: 8010)')
    args=parser.parse_args()
    if not 1024<=args.port<=65535: parser.error('Use a local port between 1024 and 65535')
    if any(os.getenv(key) for key in ('RENDER','VERCEL','TURSO_DATABASE_URL','TURSO_AUTH_TOKEN')):
        parser.error('Run this trial on the development computer without cloud database configuration')
    # Set these before db imports load .env. The existing and cloud databases
    # are never used, even when a developer .env contains hosted settings.
    os.environ.update(LAND_DB='data/source-expansion.sqlite3',TURSO_DATABASE_URL='',TURSO_AUTH_TOKEN='',
                      LAND_DATABASE_DRIVER='sqlite',LAND_REQUIRE_PERSISTENT_DB='false',LAND_REQUIRE_PROXY='false',
                      LAND_LOCAL_SOURCE_TRIAL='true',LAND_AUTO_SCRAPE_PAGES=str(args.pages),LAND_AUTO_SCRAPE_LIMIT=str(args.limit))
    from .collector import collect_all
    from .db import ROOT, connect
    if args.serve:
        if args.sources: parser.error('--sources selects a batch; the server uses all currently enabled sources')
        os.environ['LAND_AUTO_SCRAPE']='true'
        os.environ['LAND_AUTH_SECURE_COOKIE']='false'
        os.environ['LAND_AUTH_ORIGINS']='http://127.0.0.1:5175,http://localhost:5175,http://127.0.0.1:'+str(args.port)
        os.environ['LAND_PUBLIC_URL']='http://127.0.0.1:5175'
        import uvicorn
        uvicorn.run('land_discover.api:app',host='127.0.0.1',port=args.port)
        return
    result=collect_all(args.sources)
    with connect() as con:
        result['inventory']=[dict(row) for row in con.execute('SELECT source,COUNT(*) listings,SUM(CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END) with_photos FROM properties GROUP BY source')]
    destination=ROOT/'data'/'source-expansion-report.json'
    destination.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    import logging
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    main()
