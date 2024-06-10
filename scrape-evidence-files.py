import bs4
import json
import os
import requests_cache
import urllib.parse
from fns import fetch_list

session = requests_cache.CachedSession(expire_after=86400*7)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
})

BASE_EVI = 'https://www.postofficehorizoninquiry.org.uk/evidence/all-evidence'

def fetch_evidence():
    fetch_list(BASE_EVI, 'evidence-item-wrapper', fetch_evidence_page)

def fetch_evidence_page(item):
    link = item.h2.a['href']
    url = urllib.parse.urljoin(BASE_EVI, link)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    title = soup.h1.text.strip()
    for link in soup.find_all('span', class_='file'):
        href = urllib.parse.urljoin(BASE_EVI, link.a['href'])
        note = link.a.text.strip()
        typ = link.a['type']
        if 'pdf' in typ and 'pdf' not in note:
            note += '.pdf'
        if 'excel' in typ and 'xls' not in note:
            note += '.xls'
        note = note.replace("/", "_")
        filename_out = f'evidence/process/{note}'

        META[note] = [url, title]

        if os.path.exists(filename_out):
            continue

        print('Noting evidence', url, note, href, link.a['type'])
        with open(filename_out, 'wb') as fp:
            content = session.get(href).content
            fp.write(content)

META = {}
fetch_evidence()
json.dump(META, open('data/evidence-pdf-metadata.json', 'w'), indent=2)
