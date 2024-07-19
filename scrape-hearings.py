import bs4
import datetime
import os
import re
import requests_cache
import subprocess
import urllib.parse
from fns import fetch_list, load_data, save_data

session = requests_cache.CachedSession(expire_after=86400*7)
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
})

BASE = 'https://www.postofficehorizoninquiry.org.uk/hearings/listing'

def fetch_hearings():
    fetch_list(BASE, 'hearing-item-wrapper', fetch_hearing_page)

def fetch_hearing_page(item):
    link = item.h2.a['href']
    title = item.h2.text  # e.g. Phase 2 - 25 November 2022
    title = title.replace('Disclosure Hearing', 'Disclosure Issues Hearing')  # Keep consistent with previous
    title = title.replace('Phase 5/6', 'Phases 5/6')  # Keep consistent with previous
    title = title.replace('/', '-') # Can't have a slash in the name
    date = datetime.datetime.strptime(item.time.text, '%d %B %Y').date()  # e.g. 25 November 2022
    filename_out = f'data/{date}-{title}.txt'

    url = urllib.parse.urljoin(BASE, link)
    META['urls'][str(date)] = url

    if os.path.exists(filename_out):
        return

    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")

    for vid in soup.find_all('iframe'):
        yt_id = re.search('(?:v%3D|youtu.be/)(.*?)(?:&|%26)', vid['src']).group(1)
        yt_title = vid['title']
        if str(date) in META['videos'] and yt_id in [ x['id'] for x in META['videos'][str(date)] ]:
            continue
        META['videos'].setdefault(str(date), []).append({'title': yt_title, 'id': yt_id})

    txt_link = soup.find('span', class_='file--text')
    if txt_link:
        txt_href = urllib.parse.urljoin(BASE, txt_link.a['href'])
        txt_note = txt_link.a.text
        print('Downloading', date, txt_href)
        with open(filename_out, 'wb') as fp:
            content = session.get(txt_href).content
            content = re.sub(b'\r\n', b'\n', content)
            content = re.sub(b'\n\n', b'\n', content)
            fp.write(content)

META = {
    'evidence': {},
    'videos': {},
    'urls': {},
}

load_data(META)
fetch_hearings()
save_data(META)
