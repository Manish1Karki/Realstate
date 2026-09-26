"""CSV exports for command-line collection, without starting the web server."""
import csv
from pathlib import Path
from .db import connect

def safe(value):
    if isinstance(value,str) and value.lstrip().startswith(('=','+','-','@','\t','\r')):
        return "'"+value
    return value

def export_properties(path,source=None,ids=None):
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    clauses=['is_demo=0'];args=[]
    if source:
        clauses.append('source=?');args.append(source)
    if ids is not None:
        clauses.append('id IN ('+','.join('?' for _ in ids)+')' if ids else '0=1')
        args.extend(ids)
    with connect() as con, target.open('w',encoding='utf-8-sig',newline='') as f:
        cursor=con.execute('SELECT * FROM properties WHERE '+' AND '.join(clauses)+' ORDER BY id',args)
        writer=csv.writer(f);writer.writerow([x[0] for x in cursor.description])
        count=0
        for row in cursor:
            writer.writerow([safe(value) for value in row]);count+=1
    return {'path':str(target.resolve()),'rows':count}
