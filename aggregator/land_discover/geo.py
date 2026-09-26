import hashlib, json, math, os
from .db import cached, cache_set, connect, now
from .http import Client, AccessError

# Broad Valley envelope, plus administrative district verification below.
BBOX=(85.15,27.50,85.60,27.90)

def distance(lat1,lng1,lat2,lng2):
    a,b=map(math.radians,(lat1,lat2)); dlat=b-a; dlng=math.radians(lng2-lng1)
    value=math.sin(dlat/2)**2+math.cos(a)*math.cos(b)*math.sin(dlng/2)**2
    return 6371*2*math.asin(min(1,math.sqrt(value)))

def segment_distance(lat,lng,geometry):
    """Nearest point on a road polyline using local equirectangular projection."""
    if not geometry: return None
    scale=111.195; cos=math.cos(math.radians(lat))
    points=[((p['lon']-lng)*scale*cos,(p['lat']-lat)*scale,p) for p in geometry]
    best=(float('inf'),None)
    for x,y,p in points:
        if math.hypot(x,y)<best[0]: best=(math.hypot(x,y),p)
    for (x1,y1,_),(x2,y2,_) in zip(points,points[1:]):
        dx,dy=x2-x1,y2-y1; denom=dx*dx+dy*dy
        t=max(0,min(1,-(x1*dx+y1*dy)/denom)) if denom else 0
        x,y=x1+t*dx,y1+t*dy
        if math.hypot(x,y)<best[0]: best=(math.hypot(x,y),{'lat':lat+y/scale,'lon':lng+x/(scale*cos)})
    return best

def geocode(row, client):
    if row['address'].strip().lower() in ('kathmandu','lalitpur','bhaktapur'):
        return {'geocode_status':'insufficient_address','geocode_precision':'district only','geo_error':'District-only address cannot locate a property'}
    query=f"{row['address']}, Nepal"
    endpoint=os.getenv('NOMINATIM_URL','https://nominatim.openstreetmap.org').rstrip('/')
    key='geocode:'+endpoint+':'+query.lower()
    hits=cached(key,90)
    if hits is None:
        if not os.getenv('LAND_CONTACT','').strip():
            raise AccessError('Set LAND_CONTACT to your email or project URL before geocoding')
        r=client.request('GET',endpoint+'/search',delay=1.1,params={'q':query,'format':'jsonv2','countrycodes':'np','limit':5,'addressdetails':1,'viewbox':'85.15,27.90,85.60,27.50','bounded':1})
        r.raise_for_status(); hits=r.json()
        if not isinstance(hits,list): raise ValueError('Unexpected Nominatim response')
        cache_set(key,hits)
    valid=[]
    for hit in hits:
        lat,lng=float(hit['lat']),float(hit['lon']); address=hit.get('address',{})
        admin=' '.join(str(address.get(k,'')) for k in ('county','state_district','city','municipality','city_district'))
        native={'Kathmandu':'काठम','Lalitpur':'ललितपुर','Bhaktapur':'भक्तपुर'}[row['district']]
        district_matches=row['district'].lower() in admin.lower() or native in admin
        if BBOX[0]<=lng<=BBOX[2] and BBOX[1]<=lat<=BBOX[3] and district_matches: valid.append(hit)
    # Locality searches can also return a temple, bus stop or road of the same name.
    # Use a unique place feature; do not mistake a landmark for the neighbourhood.
    places=[h for h in valid if h.get('category','place')=='place']
    if places:valid=places
    if len(valid)!=1:
        return {'geocode_status':'ambiguous' if valid else 'not_found','geo_error':'Multiple matches require review' if valid else 'No unique match in expected district'}
    hit=valid[0]
    if hit.get('category')=='amenity':
        return {'geocode_status':'ambiguous','geo_error':'Only a landmark matched; property locality needs review'}
    return {'lat':float(hit['lat']),'lng':float(hit['lon']),'geocode_status':'matched','geocode_precision':'approximate '+hit.get('addresstype','location'),'geocode_label':hit.get('display_name'),'geo_error':None}

def overpass_query(lat,lng,radius):
    return f'''[out:json][timeout:25];(
      nwr(around:{radius},{lat},{lng})[amenity~"^(school|college|hospital|clinic|doctors|bank|marketplace|bus_station)$"];
      node(around:{radius},{lat},{lng})[highway=bus_stop];
      nwr(around:{radius},{lat},{lng})[public_transport=platform];
      way(around:{radius},{lat},{lng})[highway~"^(motorway|trunk|primary|secondary|tertiary)$"];
    );out center geom;'''

def parse_amenities(elements, lat, lng, radius):
    result=[]; seen=set()
    for obj in elements:
        tags=obj.get('tags',{}); amenity=tags.get('amenity',''); highway=tags.get('highway','')
        kind='school' if amenity in ('school','college') else 'hospital' if amenity in ('hospital','clinic','doctors') else 'transport' if amenity=='bus_station' or highway=='bus_stop' or tags.get('public_transport')=='platform' else 'bank' if amenity=='bank' else 'market' if amenity=='marketplace' else 'road' if highway in ('motorway','trunk','primary','secondary','tertiary') else None
        if not kind: continue
        point=obj if 'lat' in obj else obj.get('center',{})
        if kind=='road' and obj.get('geometry'):
            dist,point=segment_distance(lat,lng,obj['geometry'])
        elif 'lat' in point and 'lon' in point:
            dist=distance(lat,lng,point['lat'],point['lon'])
        else: continue
        if dist>radius/1000: continue
        osm_id=f"{obj['type']}/{obj['id']}"
        if (osm_id,kind) in seen: continue
        seen.add((osm_id,kind))
        result.append(dict(osm_id=osm_id,name=tags.get('name:en') or tags.get('name') or f'Unnamed {kind}',kind=kind,lat=point['lat'],lng=point['lon'],distance_km=round(dist,4)))
    return sorted(result,key=lambda x:x['distance_km'])

def amenities(lat,lng,radius,client):
    endpoint=os.getenv('OVERPASS_URL','https://overpass-api.de/api/interpreter')
    query=overpass_query(lat,lng,radius)
    key='overpass:'+hashlib.sha256((endpoint+query).encode()).hexdigest()
    payload=cached(key,30)
    if payload is None:
        r=client.request('POST',endpoint,delay=5,data={'data':query}); r.raise_for_status(); payload=r.json()
        if 'remark' in payload or not isinstance(payload.get('elements'),list): raise ValueError('Overpass returned an incomplete response')
        cache_set(key,payload)
    return parse_amenities(payload['elements'],lat,lng,radius)

def enrich(limit=10,radius=1500,retry=False):
    if not 250<=radius<=2000: raise ValueError('Radius must be between 250 and 2000 metres')
    # CLI only, one process at a time; lock held for the complete small batch.
    from .locking import single_job
    with single_job('enrichment'):
        return _enrich(limit,radius,retry)

def _enrich(limit,radius,retry):
    with connect() as con:
        skip="" if retry else " AND geocode_status NOT IN ('ambiguous','not_found','insufficient_address')"
        rows=con.execute("SELECT * FROM properties WHERE is_demo=0 AND (enrichment_status!='complete' OR enrichment_radius_m!=?)"+skip+" ORDER BY id LIMIT ?",(radius,limit)).fetchall()
    c=Client(delay=1.1); report={'matched':0,'enriched':0,'errors':[]}
    try:
        for row in rows:
            row=dict(row)
            try:
                if row['geocode_status']!='matched':
                    if row['geocode_status'] in ('ambiguous','not_found') and not retry: continue
                    updates=geocode(row,c)
                    with connect() as con:
                        con.execute('UPDATE properties SET '+','.join(k+'=?' for k in updates)+' WHERE id=?',[*updates.values(),row['id']])
                    row.update(updates)
                if row['geocode_status']!='matched': continue
                report['matched']+=1
                items=amenities(row['lat'],row['lng'],radius,c)
                nearest={kind:next((a for a in items if a['kind']==kind),None) for kind in ('school','hospital')}
                # Transparent proximity index, not an AI or investment score.
                score=round(sum(max(0,1-(nearest[k]['distance_km']/(radius/1000))) *50 if nearest[k] else 0 for k in nearest),1)
                with connect() as con:
                    con.execute('DELETE FROM amenities WHERE property_id=?',(row['id'],))
                    con.executemany('INSERT INTO amenities(property_id,osm_id,name,kind,lat,lng,distance_km) VALUES (?,?,?,?,?,?,?)',[(row['id'],a['osm_id'],a['name'],a['kind'],a['lat'],a['lng'],a['distance_km']) for a in items])
                    school,hospital=nearest['school'],nearest['hospital']
                    con.execute("UPDATE properties SET nearest_school=?,school_distance_km=?,nearest_hospital=?,hospital_distance_km=?,enrichment_status='complete',enrichment_radius_m=?,enriched_date=?,amenity_count=?,amenity_score=?,geo_error=NULL WHERE id=?",(school['name'] if school else None,school['distance_km'] if school else None,hospital['name'] if hospital else None,hospital['distance_km'] if hospital else None,radius,now(),len([a for a in items if a['kind']!='road']),score,row['id']))
                report['enriched']+=1
            except Exception as e:
                report['errors'].append({'id':row['id'],'message':str(e)})
                with connect() as con: con.execute("UPDATE properties SET enrichment_status='error',geo_error=? WHERE id=?",(str(e),row['id']))
    finally: c.close()
    return report
