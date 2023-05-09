import bs4
import datetime
import json
import os
import re
import requests
import requests_cache
import urllib.parse

session = requests_cache.CachedSession(expire_after=86400*7)

BASE = 'https://www.postofficehorizoninquiry.org.uk/hearings/listing'
BASE_EVI = 'https://www.postofficehorizoninquiry.org.uk/evidence/all-evidence'

def fetch_hearings():
    url = BASE
    while True:
        r = requests.get(url)
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        for item in soup.find_all('div', class_='hearing-item-wrapper'):
            fetch_hearing_page(item)
        n = soup.find('a', rel='next')
        if not n:
            break
        url = BASE + n.get('href')

def fetch_hearing_page(item):
    link = item.h2.a['href']
    title = item.h2.text  # e.g. Phase 2 - 25 November 2022
    date = datetime.datetime.strptime(item.time.text, '%d %B %Y').date()  # e.g. 25 November 2022
    if os.path.exists(f'data/{date}-{title}.txt'):
        return
    url = urllib.parse.urljoin(BASE, link)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    txt_link = soup.find('span', class_='file--text')
    if txt_link:
        txt_href = urllib.parse.urljoin(BASE, txt_link.a['href'])
        txt_note = txt_link.a.text
        print(date, txt_href)
        with open(f'data/{date}-{title}.txt', 'wb') as fp:
            content = session.get(txt_href).content
            content = re.sub(b'\r\n', b'\n', content)
            content = re.sub(b'\n\n', b'\n', content)
            fp.write(content)

EVIDENCE = {}
def load_evidence():
    if os.path.exists('data/evidence.json'):
        evidence = json.load(open('data/evidence.json'))
        for url, href, note in evidence:
            EVIDENCE.setdefault(url, []).append((url, href, note))

def fetch_evidence():
    url = BASE_EVI
    evidence = []
    while True:
        r = requests.get(url)
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        for item in soup.find_all('div', class_='evidence-item-wrapper'):
            evidence.extend(fetch_evidence_page(item))
        n = soup.find('a', rel='next')
        if not n:
            break
        url = BASE_EVI + n.get('href')
    json.dump(evidence, open('data/evidence.json', 'w'), indent=2)

def fetch_evidence_page(item):
    link = item.h2.a['href']
    url = urllib.parse.urljoin(BASE_EVI, link)
    if url in EVIDENCE:
        return EVIDENCE[url]
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")
    data = []
    for link in soup.find_all('span', class_='file'):
        href = urllib.parse.urljoin(BASE_EVI, link.a['href'])
        note = link.a.text
        print(url, note)
        data.append((url, href, note))
    return data

fetch_hearings()
load_evidence()
fetch_evidence()
