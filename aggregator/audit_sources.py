"""Bounded source reconnaissance: robots first, then permitted homepage/terms only."""
import json, pathlib, time, urllib.request, urllib.error, urllib.robotparser
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).parent / 'data' / 'audit'
ROOT.mkdir(parents=True, exist_ok=True)
class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.links += [v for k,v in attrs if k=='href']

def fetch(url):
    time.sleep(2)
    req=urllib.request.Request(url, headers={'User-Agent':'LandDiscoverResearch/0.1'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read(2_000_000).decode('utf-8','replace')
    except urllib.error.HTTPError as e: return e.code, ''
    except Exception as e: return 0, str(e)

if __name__=='__main__':
    for name,base in [('housingnepal','https://www.housingnepal.com'),('gharbazar','https://www.gharbazar.com'),('hamrobazar','https://hamrobazaar.com'),('nepalpropertybazaar','https://nepalpropertybazaar.com')]:
        status,robots=fetch(base+'/robots.txt')
        (ROOT/(name+'-robots.txt')).write_text(robots,encoding='utf-8')
        report={'source':name,'robots_status':status,'base':base}
        rp=urllib.robotparser.RobotFileParser(); rp.parse(robots.splitlines())
        # Once restrictions are known, do not fetch listing homepages during repeat audits.
        known_restricted=name in ('housingnepal','gharbazar','nepalpropertybazaar')
        if not known_restricted and (status==404 or status==200 and '<html' not in robots.lower() and rp.can_fetch('LandDiscoverResearch',base+'/')):
            code,html=fetch(base+'/'); (ROOT/(name+'-home.html')).write_text(html,encoding='utf-8')
            p=Links(); p.feed(html)
            report.update(home_status=code,policy_links=[x for x in p.links if any(w in x.lower() for w in ['term','condition','policy'])],sample_links=p.links[:35])
        print(json.dumps(report),flush=True)
