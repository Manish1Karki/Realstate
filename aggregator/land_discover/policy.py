import hashlib
from bs4 import BeautifulSoup
from .normalize import clean

def hamrobazar_terms_digest(html):
    text=clean(BeautifulSoup(html,'html.parser').get_text(' ',strip=True))
    start=text.find('Updated at:')
    end=text.find("You've reached the end of the page",start)
    if start<0 or end<0: raise ValueError('Terms page structure changed; review required')
    return hashlib.sha256(text[start:end].strip().encode()).hexdigest()

def huku_terms_digest(html):
    soup=BeautifulSoup(html,'html.parser')
    content=soup.select_one('.prose')
    if not content or 'User-Generated Content' not in content.get_text():
        raise ValueError('HUKU terms page structure changed; review required')
    # The contact section can contain a Cloudflare-obfuscated email, changing
    # between environments without a change to the actual policy clauses.
    # Exclude only that section; retain any later policy sections as well.
    for heading in list(content.find_all(['h1','h2','h3','h4','h5','h6'])):
        if clean(heading.get_text(' ',strip=True)).lower()!='contact us': continue
        level=int(heading.name[1])
        for sibling in list(heading.next_siblings):
            if getattr(sibling,'name',None) in ('h1','h2','h3','h4','h5','h6') and int(sibling.name[1])<=level: break
            sibling.extract()
        heading.extract()
    return hashlib.sha256(clean(content.get_text(' ',strip=True)).encode()).hexdigest()
