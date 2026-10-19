"""Public listing contacts only; never recover masked numbers or use site-wide contacts."""
import re
from bs4 import BeautifulSoup
from .normalize import clean


def extract_contact(item, html):
    from .scraper import fields
    soup = BeautifulSoup(html, 'html.parser')
    contact_blocks = '.property-contact, .listing-contact, .owner-contact, .seller-contact, .agent-contact, .property-agent, .rh_property__agent, .rh_property_agent, .rh_property_agent__agent_info'
    for node in soup.select('script, style, header, nav, footer, [hidden], [aria-hidden="true"], [class*="related"], [class*="similar"], .office-contact, .company-contact'):
        node.decompose()
    for node in soup.select('aside'):
        if not node.select_one(contact_blocks): node.decompose()
    for node in soup.select('[style]'):
        if re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', node.get('style',''), re.I): node.decompose()
    scope = soup.find('main') or soup
    candidates = []
    labels = fields(scope)
    for label, value in labels.items():
        if re.fullmatch(r'(?:owner(?:\'s)?|seller|agent|property owner)?\s*(?:contact(?: number)?|phone(?: number)?|mobile(?: number)?)', label, re.I):
            role = 'owner' if 'owner' in label else 'agent' if 'agent' in label else 'seller' if 'seller' in label else 'unknown'
            candidates.append((value, role))
    # Explicitly labelled contacts in property prose, including adapters that redact their stored description.
    for node in scope.select('p, li, .property-description, .listing-description, .property-description-text, .accordion-body'):
        text = clean(node.get_text(' ', strip=True))
        for match in re.finditer(r'\b(owner(?:\'s)?(?: contact| phone| mobile)?|seller(?: contact| phone| mobile)?|agent(?: contact| phone| mobile)?|contact(?: owner| number)?|phone(?: number)?|mobile(?: number)?)\s*[:\-]\s*([^;|\n]{7,50})', text, re.I):
            label = match[1].lower()
            role = 'owner' if 'owner' in label else 'agent' if 'agent' in label else 'seller' if 'seller' in label else 'unknown'
            candidates.append((match[2], role))
    # Listing agent widgets can sit beside (rather than inside) <main>.
    for block in soup.select(contact_blocks):
        classes = ' '.join(block.get('class',[]))
        role = 'owner' if 'owner' in classes else 'agent' if 'agent' in classes else 'seller' if 'seller' in classes else 'unknown'
        for link in block.select('a[href^="tel:"]'):
            visible = clean(link.get_text(' ',strip=True))
            # Do not turn a masked/reveal control into a stored private number.
            if re.search(r'\d{3}', visible) and not re.search(r'[*xX•]', visible):
                candidates.append((visible, role))
    if soup.find('main'):
        for link in scope.select('a[href^="tel:"]'):
            visible = clean(link.get_text(' ',strip=True))
            if not re.search(r'\d{3}', visible) or re.search(r'[*xX•]', visible): continue
            context = ' '.join(clean(parent.get_text(' ',strip=True)) for parent in list(link.parents)[:2])
            role = 'owner' if re.search(r'\b(?:property owner|contact owner|owner contact)\b',context,re.I) else 'agent' if re.search(r'\b(?:contact agent|agent details|listed by agent)\b',context,re.I) else 'unknown'
            candidates.append((visible,role))
    item.update(contact_phone=None, contact_role=None)
    # Prefer explicitly identified listing contacts over unlabelled prose matches.
    candidates.sort(key=lambda candidate: {'owner':0,'agent':1,'seller':2,'unknown':3}[candidate[1]])
    for text, role in candidates:
        text = clean(text)
        match = re.search(r'(?<!\w)(\+?\d[\d ()-]{5,24}\d)(?!\w)', text)
        if not match: continue
        number = re.sub(r'[ ()-]', '', match[1])
        masked = re.search(r'\d[\d ()-]*[*xX•]|[*xX•][\d ()-]*\d', text)
        if 7 <= len(number.lstrip('+')) <= 15 and not masked:
            item.update(contact_phone=number, contact_role=role)
            break
    return item
