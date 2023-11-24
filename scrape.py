import bs4
import datetime
import json
import os
import re
import requests
import requests_cache
import subprocess
import urllib.parse

session = requests_cache.CachedSession(expire_after=86400*7)
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
}

BASE = 'https://www.postofficehorizoninquiry.org.uk/hearings/listing'
BASE_EVI = 'https://www.postofficehorizoninquiry.org.uk/evidence/all-evidence'

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

def fetch_hearings():
    fetch_list(BASE, 'hearing-item-wrapper', fetch_hearing_page)

def fetch_hearing_page(item):
    link = item.h2.a['href']
    title = item.h2.text  # e.g. Phase 2 - 25 November 2022
    date = datetime.datetime.strptime(item.time.text, '%d %B %Y').date()  # e.g. 25 November 2022
    filename_out = f'data/{date}-{title}.txt'
    if os.path.exists(filename_out):
        return
    url = urllib.parse.urljoin(BASE, link)
    r = session.get(url)
    soup = bs4.BeautifulSoup(r.content, "html.parser")

    META['urls'][str(date)] = url

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

    if f'{date}' == '2023-10-17': # No txt output
        filename_pdf = f'data/{date}-{title}.raw.pdf'
        filename_raw = filename_pdf.replace('.pdf', '.txt')

        pdf_link = soup.find('span', class_='file--application-pdf')
        if pdf_link:
            pdf_href = urllib.parse.urljoin(BASE, pdf_link.a['href'])
            print('Downloading', date, pdf_href)
            with open(filename_pdf, 'wb') as fp:
                content = session.get(pdf_href).content
                fp.write(content)

            subprocess.run(['pdftotext', '-layout', filename_pdf])

            with open(filename_raw, 'r') as fp:
                text = convert_four_up_pdf(fp.read())

            with open(filename_out, 'w') as fp:
                fp.write(text)

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
        print('Noting evidence', url, note)
        META['evidence'].setdefault(url, []).append(note)

def convert_four_up_pdf(text):
    # Remove header/footer from all pages
    text = re.sub('\014? *The Post Office Horizon IT Inquiry *\d+ .*? 202\d', '', text)
    text = re.sub(' *\(\d+\) Pages \d+ - \d+', '', text)
    #text = re.sub('\xef\xbf\xbd', '', text)

    # Loop through, slurping up the pages by page number
    text_l, text_r = [], []
    pages = {}
    text = re.split('\r?\n', text)
    state = 'okay'

    for line in text:
        #print('*', line)
        if re.match('\s*$', line): continue
        if re.match(r' ?1 +INDEX', line): break
        elif 'INDEX' in line: state = 'index'

        m = re.match(r' +(\d+)(?: +(\d+))? *$', line)
        if m:
            page_l = int(m.group(1))
            pages[page_l] = text_l
            if m.group(2) and len(text_r):
                page_r = int(m.group(2))
                pages[page_r] = text_r
            text_l, text_r = [], []
            if state == 'index':
                break
            continue

        # Left and right pages
        m = re.match(r' *(\d+)( .*?) + \1(  .*)?$', line)
        if m:
            line_n = int(m.group(1))
            line_l = '       %s' % m.group(2).rstrip()
            line_r = '       %s' % m.group(3) if m.group(3) else ''
            text_l.append('%2d%s' % (line_n, line_l))
            text_r.append('%2d%s' % (line_n, line_r))
            continue

        # Just left page at the end
        m = re.match(r' ?(\d+)( .*)?$', line)
        line_n = int(m.group(1))
        line_l = '       %s' % m.group(2) if m.group(2) else ''
        if state == 'index':
            line_l = re.sub('                    .*', '', line_l) # Remove RHS index
        text_l.append('%2d%s' % (line_n, line_l))

    # Reconstruct in page order for normal processing
    text = ''
    for num, page in sorted(pages.items()):
        for line in page:
            text += line + '\n'
        text += '    %d\n\014\n' % num
    return text

load_data()
fetch_hearings()
save_data()
fetch_evidence()
save_data()
