import hashlib
from bs4 import BeautifulSoup
from .normalize import clean

def hamrobazar_terms_digest(html):
    text=clean(BeautifulSoup(html,'html.parser').get_text(' ',strip=True))
    start=text.find('Updated at:')
    end=text.find("You've reached the end of the page",start)
    if start<0 or end<0: raise ValueError('Terms page structure changed; review required')
    return hashlib.sha256(text[start:end].strip().encode()).hexdigest()
