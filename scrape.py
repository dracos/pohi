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

def fetch_list(base, cls, fn):
    url = base
    while True:
        r = requests.get(url)
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        for item in soup.find_all('div', class_=cls):
            fn(item)
        n = soup.find('a', rel='next')
        if not n:
            break
        url = base + n.get('href')

def fetch_hearings():
    fetch_list(BASE, 'hearing-item-wrapper', fetch_hearing_page)

def fetch_hearing_page(item):
    link = item.h2.a['href']
    title = item.h2.text  # e.g. Phase 2 - 25 November 2022
    date = datetime.datetime.strptime(item.time.text, '%d %B %Y').date()  # e.g. 25 November 2022
    if os.path.exists(f'data/{date}-{title}.txt'):
        return
    url = urllib.parse.urljoin(BASE, link)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")

    META['urls'][str(date)] = url

    for vid in soup.find_all('iframe'):
        yt_id = re.search('(?:v%3D|youtu.be/)(.*?)(?:&|%26)', vid['src']).group(1)
        yt_title = vid['title']
        META['videos'].setdefault(str(date), []).append({'title': yt_title, 'id': yt_id})

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

META = {
    'evidence': {},
    'videos': {},
    'urls': {},
}

def load_data():
    if os.path.exists('data/metadata.json'):
        META.update(json.load(open('data/metadata.json')))

def fetch_evidence():
    fetch_list(BASE_EVI, 'evidence-item-wrapper', fetch_evidence_page)

def save_data():
    json.dump(META, open('data/metadata.json', 'w'), indent=2)

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
        print(url, note)
        META['evidence'].setdefault(url, []).append(note)

load_data()
fetch_hearings()
fetch_evidence()
save_data()
