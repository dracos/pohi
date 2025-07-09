#from datetime import datetime
import glob
import json
import os
import re
import string

ACRONYMS = {
    'POL': 'Post Office Limited',
    'BEIS': 'Department for Business, Energy and Industrial Strategy',
    'UKGI': 'UK Government Investments',
    'NFSP': 'National Federation of SubPostmasters',
    'CWU': 'Communication Workers Union',
    'ARQ': 'Audit Record Query',
}

META = {
    'evidence': {},
}

def load_data():
    meta = json.load(open('data/metadata.json'))
    for name in sorted(glob.glob('evidence/*.rst')):
        if m := re.match('evidence/([A-Za-z]{3,4}[0-9_]+(r|R|ds)?)', name):
            key = m.group(1).upper().replace('_', '\_')
            if key[0:8] == 'INQ00001': continue # Ignore transcript URNs
            contents = open(name).read()
            m = re.search('Evidence on official site <(.*?)>`', contents)
            url = m.group(1)
            if 'DS' in key:
                META['evidence'][key.replace('DS', 'ds')] = url
            META['evidence'][key] = url
    META['evidence']['FUJ00077884'] = 'https://www.postofficehorizoninquiry.org.uk/evidence/fuj00077884-consolidated-risk-register-may-1998-april-2000'

def parse_content(text):
    # Reset, to re-add
    text = re.sub('`([^`]*?) <[^>]*>`_', r'\1', text)

    # Link to some judgments
    text = re.sub('(Horizon Issues [Jj]udgments?)', r'`\1 <https://www.bailii.org/ew/cases/EWHC/QB/2019/3408.html>`_', text)
    text = re.sub('(Common Issues [Jj]udgments?)', r'`\1 <https://www.bailii.org/ew/cases/EWHC/QB/2019/606.html>`_', text)
    text = re.sub('(Hamilton [Jj]udgment|Hamilton (&|and) [Oo]thers)', r'`\1 <https://www.bailii.org/ew/cases/EWCA/Crim/2021/577.html>`_', text)

    for e in META['evidence'].keys():
        text = text.replace(e, f'`{e} <{META["evidence"][e]}>`_')

    # Deal with some acronyms
    #for acronym, meaning in ACRONYMS.items():
    #    text = re.sub(fr'\b{acronym}\b', f':abbr:`{acronym} ({meaning})`', text, count=1)

    return text

def parse_report():
    for f in sorted(glob.glob('report/volume-1/**/*.rst', recursive=True)):
        print(f)
        o = open(f)
        content = o.read()
        o.close()
        content = parse_content(content)
        o = open(f, 'w')
        o.write(content)
        o.close()

load_data()
parse_report()
