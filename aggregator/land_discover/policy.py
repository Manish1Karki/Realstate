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
    return hashlib.sha256(clean(content.get_text(' ',strip=True)).encode()).hexdigest()
