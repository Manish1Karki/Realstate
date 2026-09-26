"""Explicitly synthetic dataset. Never mixed with live source records."""
from .db import connect, now, upsert
from .normalize import normalize
from .geo import distance

AREAS=[('Baneshwor','Kathmandu',27.6915,85.3420),('Budhanilkantha','Kathmandu',27.7660,85.3620),('Lazimpat','Kathmandu',27.7250,85.3220),('Kirtipur','Kathmandu',27.6790,85.2770),('Jhamsikhel','Lalitpur',27.6760,85.3070),('Imadol','Lalitpur',27.6660,85.3510),('Bhaisepati','Lalitpur',27.6490,85.3000),('Suryabinayak','Bhaktapur',27.6610,85.4220),('Thimi','Bhaktapur',27.6790,85.3860),('Sallaghari','Bhaktapur',27.6740,85.4110)]

def seed():
    count=0
    for i,(area,district,lat,lng) in enumerate(AREAS):
        for j,kind in enumerate(['land','land','house','apartment']):
            index=i*4+j
            sqft=4+j if kind=='land' else 6 if kind=='house' else 1250
            raw=dict(source='demo',source_url=f'demo://property/{index}',title=f'{kind.title()} in {area} — demo',address=f'{area}, Ward {i%8+1}, {district}',area_name=area,property_type=kind,price_raw=f'{24+i*2+j} lakh per aana' if kind=='land' else f'{180+i*13+j*10} lakh',size=f'{sqft} aana' if kind!='apartment' else '1250 sq ft',transaction_type='sale',listing_date_raw='2026-09-20',road_access_note='Synthetic example: 16 ft access road')
            item=normalize(raw); item.update(is_demo=1,lat=lat+j*.0012,lng=lng+j*.0015,geocode_status='matched',geocode_precision='synthetic area point',enrichment_status='complete',enrichment_radius_m=1500,enriched_date=now(),nearest_school='Example Community School',school_distance_km=round(.2+i*.06+j*.03,2),nearest_hospital='Example Health Clinic',hospital_distance_km=round(.3+i*.08+j*.04,2),amenity_count=4,amenity_score=round(80-i*3-j*2,1),quality_flags=['Synthetic demonstration record — not a real listing'])
            facility_points=[(lat+.001*(k+1),lng-.001*(k+1)) for k in range(4)]
            distances=[round(distance(item['lat'],item['lng'],a,b),4) for a,b in facility_points]
            item['school_distance_km']=distances[0]
            item['hospital_distance_km']=distances[1]
            item['amenity_score']=round(sum(max(0,1-d/1.5)*50 for d in distances[:2]),1)
            id=upsert(item)
            with connect() as con:
                con.execute('DELETE FROM amenities WHERE property_id=?',(id,))
                for k,(amenity,name) in enumerate([('school','Example Community School'),('hospital','Example Health Clinic'),('transport','Example Bus Stop'),('bank','Example Bank')]):
                    con.execute('INSERT INTO amenities(property_id,osm_id,name,kind,lat,lng,distance_km) VALUES(?,?,?,?,?,?,?)',(id,f'demo/{i}-{k}',name,amenity,*facility_points[k],distances[k]))
            count+=1
    return count
