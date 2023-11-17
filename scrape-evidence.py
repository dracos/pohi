import bs4
import requests_cache
import urllib.parse
from fns import load_data, save_data, fetch_list

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
    if url in META['evidence']:
        return META['evidence'][url]
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    for link in soup.find_all('span', class_='file'):
        #href = urllib.parse.urljoin(BASE_EVI, link.a['href'])
        note = link.a.text
        print('Noting evidence', url, note)
        META['evidence'].setdefault(url, []).append(note)

META = {
    'evidence': {},
    'videos': {},
    'urls': {},
}

load_data(META)
fetch_evidence()
save_data(META)
