"""One automatic, bounded multi-source collection cycle per backend startup."""
import json
import logging
import os
import subprocess
import sys
from .db import ROOT, connect, init_db, now
from .locking import single_job
from .sources import SOURCES
from .scraper import scrape

log=logging.getLogger(__name__)

def enabled():
    return os.getenv('LAND_AUTO_SCRAPE','true').strip().lower() not in ('0','false','no','off')

def auto_sources():
    return [key for key,config in SOURCES.items() if config.get('auto_collect') and config.get('adapter')]

def limit(name,default,maximum):
    try: value=int(os.getenv(name,str(default)))
    except ValueError: value=default
    return max(1,min(value,maximum))

def collect_all():
    init_db()
    with single_job('automatic_collection'):
        with connect() as con:
            # A killed worker releases the OS lock; its unfinished records
            # must not keep appearing to run after a subsequent restart.
            con.execute("UPDATE collection_cycles SET status='interrupted',finished_at=?,current_source=NULL WHERE status='running'",(now(),))
            cycle_id=con.execute("INSERT INTO collection_cycles(started_at,status) VALUES (?,'running')",(now(),)).lastrowid
        reports=[]
        try:
            for source in auto_sources():
                with connect() as con:
                    con.execute('UPDATE collection_cycles SET current_source=? WHERE id=?',(source,cycle_id))
                log.info('Collecting %s',source)
                try: report=scrape(source,limit('LAND_AUTO_SCRAPE_PAGES',2,10),limit('LAND_AUTO_SCRAPE_LIMIT',20,100))
                except Exception as exc: report={'status':'failed','imported':0,'errors':[{'message':str(exc)}]}
                reports.append(dict(source=source,**report))
                with connect() as con:
                    con.execute('UPDATE collection_cycles SET reports=? WHERE id=?',(json.dumps(reports),cycle_id))
                log.info('%s: %s, %s imported',source,report['status'],report['imported'])
            status='complete' if reports and all(r['status']=='complete' for r in reports) else 'partial' if any(r['imported'] for r in reports) else 'failed'
        except BaseException:
            status='interrupted'
            raise
        finally:
            with connect() as con:
                con.execute('UPDATE collection_cycles SET finished_at=?,status=?,current_source=NULL,reports=? WHERE id=?',(now(),status,json.dumps(reports),cycle_id))
        return dict(id=cycle_id,status=status,reports=reports)

def start_worker():
    if not enabled(): return None
    path=ROOT/'data'/'automatic-collection.log'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as output:
        process=subprocess.Popen([sys.executable,'-m','land_discover.collector'],cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log.info('Automatic collection started (process %s)',process.pid)
    return process

def stop_worker(process):
    if process is None or process.poll() is not None: return
    process.terminate()
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)

def collection_status():
    with connect() as con:
        row=con.execute('SELECT * FROM collection_cycles ORDER BY id DESC LIMIT 1').fetchone()
    cycle=dict(row) if row else None
    if cycle: cycle['reports']=json.loads(cycle['reports'])
    return dict(enabled=enabled(),sources=auto_sources(),cycle=cycle)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    try:
        result=collect_all()
        log.info('Automatic collection finished: %s',result['status'])
    except RuntimeError as exc:
        log.warning('%s',exc)
