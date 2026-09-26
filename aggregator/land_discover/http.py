"""Serial, persistent host throttles; robots checks on every redirect target."""
import os, time, urllib.robotparser
from urllib.parse import urlparse, urljoin
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import httpx
from .db import connect, cached, cache_set

class AccessError(RuntimeError): pass

def throttle(host, seconds):
    with connect() as con:
        con.execute('BEGIN IMMEDIATE')
        row=con.execute('SELECT next_at FROM request_clock WHERE host=?',(host,)).fetchone()
        at=max(time.time(),row[0] if row else 0)
        con.execute('INSERT OR REPLACE INTO request_clock VALUES (?,?)',(host,at+seconds))
    time.sleep(max(0,at-time.time()))

class Client:
    def __init__(self, delay=3):
        self.delay=delay
        self.agent=os.getenv('LAND_USER_AGENT','LandDiscoverResearch/0.1')
        contact=os.getenv('LAND_CONTACT','').strip()
        self.client=httpx.Client(timeout=35,follow_redirects=False,headers={'User-Agent':self.agent+(f' ({contact})' if contact else '')})
    def close(self): self.client.close()
    def request(self, method, url, delay=None, **kwargs):
        for attempt in range(3):
            throttle(urlparse(url).netloc,max(self.delay,delay or 0))
            try:
                r=self.client.request(method,url,**kwargs)
            except httpx.TransportError:
                if attempt==2: raise
                time.sleep(2**attempt); continue
            if r.status_code in (429,500,502,503,504) and attempt<2:
                retry=r.headers.get('Retry-After','')
                try: wait=float(retry)
                except ValueError:
                    try: wait=(parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds()
                    except (ValueError,TypeError): wait=2**(attempt+1)
                # Stop rather than shorten a long server-requested cooldown.
                if wait>60: raise AccessError(f'Server requests a {wait:.0f}s cooldown; retry later')
                time.sleep(max(1,wait)); continue
            return r
        raise AccessError('Request failed')
    def robots(self, url):
        parsed=urlparse(url); origin=f'{parsed.scheme}://{parsed.netloc}'
        data=cached('robots:'+origin,1)
        if data is None:
            r=self.request('GET',origin+'/robots.txt')
            # Redirects or unreadable rules are not silently treated as permission.
            if r.status_code==404: data={'text':'User-agent: *\nAllow: /'}
            elif r.status_code==200 and '<html' not in r.text.lower(): data={'text':r.text}
            else: raise AccessError(f'Robots policy unavailable for {origin}: HTTP {r.status_code}')
            cache_set('robots:'+origin,data)
        rp=urllib.robotparser.RobotFileParser(); rp.parse(data['text'].splitlines())
        if not rp.can_fetch(self.agent,url): raise AccessError(f'robots.txt disallows {url}')
        return max(self.delay,rp.crawl_delay(self.agent) or rp.crawl_delay('*') or 0)
    def page(self, url, allowed_host):
        for _ in range(5):
            if urlparse(url).scheme!='https' or urlparse(url).hostname!=allowed_host:
                raise AccessError('Cross-origin or non-HTTPS page refused')
            delay=self.robots(url)
            r=self.request('GET',url,delay=delay)
            if r.is_redirect:
                url=urljoin(url,r.headers['location']); continue
            r.raise_for_status()
            if 'html' not in r.headers.get('content-type',''): raise AccessError('Expected HTML page')
            return r.text
        raise AccessError('Too many redirects')
