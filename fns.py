import bs4
import json
import os
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
}

def fetch_list(base, cls, fn):
    url = base
    n = None
    while True:
        print('Fetching', url)
        r = requests.get(url, headers=headers)
        soup = bs4.BeautifulSoup(r.content, "html.parser")
        if not n: print(soup)
        for item in soup.find_all('div', class_=cls):
            fn(item)
        n = soup.find('a', rel='next')
        if not n:
            break
        url = base + n.get('href')

def load_data(meta):
    if os.path.exists('data/metadata.json'):
        meta.update(json.load(open('data/metadata.json')))

def save_data(meta):
    json.dump(meta, open('data/metadata.json', 'w'), indent=2)
