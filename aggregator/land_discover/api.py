import csv, io, json, statistics
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .db import init_db, connect, ROOT
from .sources import SOURCES

@asynccontextmanager
async def lifespan(app):
    init_db(); yield

app=FastAPI(title='Land Discover Valley Data API',version='0.1.0',lifespan=lifespan)

def filters(dataset:Literal['live','demo']='live',district:str='',area:str='',ward:str='',property_type:Literal['','land','house','apartment']='',transaction:Literal['','sale','rent','unknown']='',min_price:float|None=Query(None,ge=0),max_price:float|None=Query(None,ge=0),school_km:float|None=Query(None,ge=0,le=2),hospital_km:float|None=Query(None,ge=0,le=2),radius_m:int|None=Query(None,ge=250,le=2000)):
    if min_price is not None and max_price is not None and min_price>max_price: raise HTTPException(422,'Minimum price exceeds maximum price')
    clauses=['is_demo=?']; values=[int(dataset=='demo')]
    for column,value in [('district',district),('area_name',area),('ward',ward),('property_type',property_type),('transaction_type',transaction)]:
        if value: clauses.append(column+'=?'); values.append(value)
    for column,op,value in [('total_price_npr','>=',min_price),('total_price_npr','<=',max_price),('school_distance_km','<=',school_km),('hospital_distance_km','<=',hospital_km),('enrichment_radius_m','=',radius_m)]:
        if value is not None: clauses.append(column+op+'?'); values.append(value)
    if school_km is not None or hospital_km is not None: clauses.append("enrichment_status='complete'")
    return ' AND '.join(clauses),values

def decode(row):
    value=dict(row); value['quality_flags']=json.loads(value['quality_flags']); return value

@app.get('/api/health')
def health(): return {'status':'ok'}

@app.get('/api/options')
def options(dataset:Literal['live','demo']='live'):
    with connect() as con:
        rows=con.execute('SELECT district,area_name,ward,enrichment_radius_m FROM properties WHERE is_demo=?',(int(dataset=='demo'),)).fetchall()
    return {'districts':sorted({r['district'] for r in rows}),'areas':sorted({r['area_name'] for r in rows}),'wards':sorted({r['ward'] for r in rows if r['ward']}),'radii':sorted({r['enrichment_radius_m'] for r in rows if r['enrichment_radius_m']})}

@app.get('/api/properties')
def properties(f=Depends(filters),page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),sort:Literal['newest','price_asc','price_desc']='newest'):
    where,args=f
    order={'newest':'scraped_date DESC,id DESC','price_asc':'total_price_npr IS NULL,total_price_npr ASC,id','price_desc':'total_price_npr IS NULL,total_price_npr DESC,id'}[sort]
    with connect() as con:
        total=con.execute('SELECT COUNT(*) FROM properties WHERE '+where,args).fetchone()[0]
        rows=con.execute('SELECT * FROM properties WHERE '+where+' ORDER BY '+order+' LIMIT ? OFFSET ?',[*args,page_size,(page-1)*page_size]).fetchall()
    return {'total':total,'items':[decode(r) for r in rows],'page':page,'page_size':page_size}

@app.get('/api/properties/{property_id}')
def detail(property_id:int):
    with connect() as con:
        row=con.execute('SELECT * FROM properties WHERE id=?',(property_id,)).fetchone()
        if row is None: raise HTTPException(404,'Property not found')
        items=con.execute('SELECT * FROM amenities WHERE property_id=? ORDER BY distance_km',(property_id,)).fetchall()
    return {**decode(row),'amenities':[dict(a) for a in items]}

@app.get('/api/map')
def map_data(f=Depends(filters)):
    where,args=f
    with connect() as con:
        total=con.execute('SELECT COUNT(*) FROM properties WHERE '+where+' AND lat IS NOT NULL AND lng IS NOT NULL',args).fetchone()[0]
        rows=con.execute('SELECT id,title,area_name,district,lat,lng,total_price_npr,amenity_score,geocode_precision,enrichment_status FROM properties WHERE '+where+' AND lat IS NOT NULL AND lng IS NOT NULL ORDER BY id LIMIT 3000',args).fetchall()
        # OSM points deduplicated across overlapping search circles, not property density.
        amenities=con.execute('SELECT a.osm_id,a.kind,AVG(a.lat) lat,AVG(a.lng) lng FROM amenities a JOIN properties p ON p.id=a.property_id WHERE '+where+" AND p.enrichment_status='complete' AND a.kind!='road' GROUP BY a.osm_id,a.kind LIMIT 10000",args).fetchall()
    return {'items':[dict(r) for r in rows],'amenities':[dict(a) for a in amenities],'mapped_total':total,'truncated':total>3000,'amenity_limit':10000}

@app.get('/api/summary')
def summary(f=Depends(filters)):
    where,args=f
    with connect() as con:
        rows=con.execute('SELECT area_name,total_price_npr,property_type,transaction_type,size_sqft,lat,enrichment_status,scraped_date FROM properties WHERE '+where,args).fetchall()
    prices=[r['total_price_npr'] for r in rows if r['total_price_npr'] is not None and r['transaction_type']=='sale']
    groups={}
    for r in rows:
        # Compare land unit asking prices only, never mix houses, rents or unknown sizes.
        if r['property_type']=='land' and r['transaction_type']=='sale' and r['total_price_npr'] and r['size_sqft']:
            groups.setdefault(r['area_name'],[]).append(r['total_price_npr']/r['size_sqft']*342.25)
    return {'total':len(rows),'mapped':sum(r['lat'] is not None for r in rows),'enriched':sum(r['enrichment_status']=='complete' for r in rows),'median_asking_price':statistics.median(prices) if prices else None,'priced_count':len(prices),'last_scraped':max((r['scraped_date'] for r in rows),default=None),'price_by_area':[{'area':a,'median_per_aana':statistics.median(p),'count':len(p)} for a,p in sorted(groups.items())]}

def csv_safe(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')): return "'"+value
    return value

@app.get('/api/export.csv')
def export(f=Depends(filters)):
    where,args=f
    def generate():
        with connect() as con:
            cursor=con.execute('SELECT * FROM properties WHERE '+where+' ORDER BY id',args)
            stream=io.StringIO(); writer=csv.writer(stream)
            writer.writerow([col[0] for col in cursor.description]); yield '\ufeff'+stream.getvalue()
            for row in cursor:
                stream.seek(0); stream.truncate(0); writer.writerow([csv_safe(v) for v in row]); yield stream.getvalue()
    return StreamingResponse(generate(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="land-discover-properties.csv"'})

@app.get('/api/sources')
def sources():
    with connect() as con: runs=con.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 10').fetchall()
    return {'sources':[dict(id=k,**v) for k,v in SOURCES.items()],'runs':[dict(r) for r in runs]}

FRONTEND=ROOT/'frontend'/'dist'
if FRONTEND.exists():
    app.mount('/assets',StaticFiles(directory=FRONTEND/'assets'),name='assets')
    @app.get('/')
    def dashboard(): return FileResponse(FRONTEND/'index.html')
