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

class Section(object):
    def __init__(self, heading, level=1):
        self.heading = heading
        self.level = level

class Speech(object):
    def __init__(self, speaker, text, speaker_display=None, typ=None):
        self.speaker = speaker
        self.speaker_display = speaker_display
        self.text = [[text]]
        self.type = typ

    def add_para(self, text):
        self.text.append([text])

    def add_text(self, text):
        self.text[-1].append(text)

META = {
    'evidence': {},
    'urls': {},
    'videos': {},
}

def load_data():
    meta = json.load(open('data/metadata.json'))
    for name in sorted(glob.glob('evidence/*.rst')):
        if m := re.match('evidence/([A-Za-z]{3,4}[0-9_]+(r|R|ds)?)', name):
            key = m.group(1).upper().replace('_', '\_')
            contents = open(name).read()
            m = re.search('Evidence on official site <(.*?)>`', contents)
            url = m.group(1)
            if 'DS' in key:
                META['evidence'][key.replace('DS', 'ds')] = url
            META['evidence'][key] = url
    META['evidence']['FUJ00077884'] = 'https://www.postofficehorizoninquiry.org.uk/evidence/fuj00077884-consolidated-risk-register-may-1998-april-2000'
    META['urls'].update(meta['urls'])
    META['videos'].update(meta['videos'])

def header(date):
    videos = META['videos'].get(date, [])
    if not videos:
        return ''

    out = f'''.. raw:: html

   <details id="hearing-meta" open>
        <summary>
            <span class="open">Hide video</span>
            <span class="closed">Show video</span>
        </summary>
'''
    seen = set()
    for v in videos:
        if v['id'] in seen:
            continue
        out += f'   <lite-youtube videoid="{v["id"]}" params="rel=0"></lite-youtube>\n'
        seen.add(v['id'])
    out += '   </details>\n\n'
    return out

def parse_speech(speech):
    text = '\n\n'.join([' '.join(s) for s in speech.text])
    text = text.strip()
    if not text:
        return ''

    # Manually fix any issues
    text = text.replace('WITN01700100. ', 'WITN01700100. [MS: The actual URN should be WITN00170100.]')

    # Link to FOI request on WDTK
    text = re.sub('(Eleanor Shaikh made a request on 10 April 2023)', r'`\1 <https://www.whatdotheyknow.com/request/post_office_investigations_compl>`_', text)
    text = re.sub('(So Andrew Wise had accessed an email in order to answer a )(Freedom of Information request)', r'\1`\2 <https://www.whatdotheyknow.com/request/post_office_investigations_compl>`_', text)

    # Link to some judgments
    text = re.sub('(Horizon Issues [Jj]udgments?)', r'`\1 <https://www.bailii.org/ew/cases/EWHC/QB/2019/3408.html>`_', text)
    text = re.sub('(Common Issues [Jj]udgments?)', r'`\1 <https://www.bailii.org/ew/cases/EWHC/QB/2019/606.html>`_', text)
    text = re.sub('(Hamilton [Jj]udgment|Hamilton (&|and) [Oo]thers)', r'`\1 <https://www.bailii.org/ew/cases/EWCA/Crim/2021/577.html>`_', text)

    # Link to final set of witness statements
    text = text.replace("Can we look at slide 2, please.  May we treat as read into the record, please, the witness statements of David Farry; Julie Kay, that's Mrs Wolstenholme; Siema Kamran; John Kenneth Macaldowie; Tracy Ann Merrit; and Robert Thompson, with those URNs.  They are essentially Human Impact statements or supplemental Human Impact statements.", "Can we look at slide 2, please.  May we treat as read into the record, please, the witness statements of `David Farry <https://www.postofficehorizoninquiry.org.uk/evidence/witn02850100-david-farry-witness-statement>`_; `Julie Kay <https://www.postofficehorizoninquiry.org.uk/evidence/witn09020200-julie-kay-nee-wolstenholme-second-witness-statement>`_, that's Mrs Wolstenholme; `Siema Kamran <https://www.postofficehorizoninquiry.org.uk/evidence/witn09060100-siema-kamran-witness-statement>`_; `John Kenneth Macaldowie <https://www.postofficehorizoninquiry.org.uk/evidence/witn06070100-john-kenneth-macaldowie-witness-statement>`_; `Tracy Ann Merrit <https://www.postofficehorizoninquiry.org.uk/evidence/witn02690100-tracy-ann-merrit-witness-statement>`_; and `Robert Thompson <https://www.postofficehorizoninquiry.org.uk/evidence/witn02220100-robert-thompson-witness-statement>`_, with those URNs.  They are essentially Human Impact statements or supplemental Human Impact statements.")
    text = text.replace("Thank you, slide 3, please.  In Phase 3 can we read into the record the statements of Alison Clark; John Courtley; Paul Gardner; Russell Hancock; Davyd Nash; Jane Smith; and Philippa Wright.", "Thank you, slide 3, please.  In Phase 3 can we read into the record the statements of `Alison Clark <https://www.postofficehorizoninquiry.org.uk/evidence/witn03660100-alison-jane-clark-witness-statement>`_; `John Courtley <https://www.postofficehorizoninquiry.org.uk/evidence/witn03530100-david-john-courtley-witness-statement>`_; `Paul Gardner <https://www.postofficehorizoninquiry.org.uk/evidence/witn09550100-paul-anthony-gardner-witness-statement>`_; `Russell Hancock <https://www.postofficehorizoninquiry.org.uk/evidence/witn03670100-russell-paul-hancock-witness-statement>`_; `Davyd Nash <https://www.postofficehorizoninquiry.org.uk/evidence/witn05850100-davyd-nash-witness-statement>`_; `Jane Smith <https://www.postofficehorizoninquiry.org.uk/evidence/witn05690100-jane-smith-witness-statement>`_; and `Philippa Wright <https://www.postofficehorizoninquiry.org.uk/evidence/witn05940100-philippa-wright-witness-statement-0>`_.")
    text = text.replace("Next slide please.  Phase 4, can we read into the record, please, Malcolm Macleod's witness statement.", "Next slide please.  Phase 4, can we read into the record, please, `Malcolm Macleod's witness statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11690100-malcolm-macdonald-macleod-witness-statement>`_.")
    text = text.replace("Phases 5 and 6, there's a lot of these: Alan Barrie; Simon Baker; Peter Batten; Sir Donald Brydon;", "Phases 5 and 6, there's a lot of these: `Alan Barrie <https://www.postofficehorizoninquiry.org.uk/evidence/witn11200100-alan-barrie-witness-statement>`_; `Simon Baker <https://www.postofficehorizoninquiry.org.uk/evidence/witn04730100-simon-baker-witness-statement-0>`_; `Peter Batten <https://www.postofficehorizoninquiry.org.uk/evidence/witn11540100-peter-batten-witness-statement>`_; `Sir Donald Brydon <https://www.postofficehorizoninquiry.org.uk/evidence/witn10320100-sir-donald-hood-brydon-witness-statement>`_;")
    text = text.replace("David Cavender KC; Catherine Churchard; Jeremy Cope; Peter Corbett; David Courtley.", "`David Cavender KC <https://www.postofficehorizoninquiry.org.uk/evidence/witn10630100-david-john-cavender-kc-witness-statement-0>`_; `Catherine Churchard <https://www.postofficehorizoninquiry.org.uk/evidence/witn11230100-catherine-churchard-witness-statement>`_; `Jeremy Cope <https://www.postofficehorizoninquiry.org.uk/evidence/witn03410100-jeremy-ewart-cope-witness-statement>`_; `Peter Corbett <https://www.postofficehorizoninquiry.org.uk/evidence/witn11160100-peter-corbett-witness-statement-0>`_; `David Courtley <https://www.postofficehorizoninquiry.org.uk/evidence/witn03530100-david-john-courtley-witness-statement>`_.")
    text = text.replace("Over the page: Gareth Davies; Dr Naranker Dulay; Douglas Evans; Richard Francis; Andy Furey; Robert Gilbert; William Hayes.", "Over the page: `Gareth Davies first statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11020100-gareth-davies-first-witness-statement>`_, `Gareth Davies second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11020200-gareth-davies-second-witness-statement>`_, `Gareth Davies third statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11020300-gareth-davies-third-witness-statement>`_; `Dr Naranker Dulay <https://www.postofficehorizoninquiry.org.uk/evidence/witn11070100-dr-naranker-dulay-witness-statement>`_; `Douglas Evans <https://www.postofficehorizoninquiry.org.uk/evidence/witn11240100-douglas-evans-witness-statement>`_; `Richard Francis <https://www.postofficehorizoninquiry.org.uk/evidence/witn11210100-richard-phillip-francis-witness-statement>`_; `Andy Furey <https://www.postofficehorizoninquiry.org.uk/evidence/witn00340100-andy-furey-witness-statement>`_; `Roger Gilbert <https://www.postofficehorizoninquiry.org.uk/evidence/witn03550100-roger-gilbert-witness-statement>`_; `William Hayes <https://www.postofficehorizoninquiry.org.uk/evidence/witn10060100-william-hayes-witness-statement>`_.")
    text = text.replace("Over the page, please: Darren Heilig; Jane Hill; Jonathan Hill; Andy Holt; Gareth James; Sir Sajid Javid; The Right Honourable Alan Johnson.", "Over the page, please: `Darren Heilig first statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11030100-darren-heilig-first-witness-statement>`_, `Darren Heilig second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11030200-darren-heilig-second-witness-statement>`_; `Jane Hill <https://www.postofficehorizoninquiry.org.uk/evidence/witn10680100-jane-hill-witness-statement>`_; `Jonathan Hill first statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11110100-jonathan-hill-first-witness-statement>`_, `Jonathan Hill second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11110200-jonathan-hill-second-witness-statement>`_; `Andy Holt <https://www.postofficehorizoninquiry.org.uk/evidence/witn11040100-andy-holt-witness-statement>`_; `Gareth James <https://www.postofficehorizoninquiry.org.uk/evidence/witn09750100-gareth-james-witness-statement>`_; `Sir Sajid Javid <https://www.postofficehorizoninquiry.org.uk/evidence/witn10880100-sir-sajid-javid-witness-statement>`_; `The Right Honourable Alan Johnson <https://www.postofficehorizoninquiry.org.uk/evidence/witn03380200-rt-hon-alan-johnson-second-witness-statement>`_.")
    text = text.replace("Over the page, please: Professor Jeffrey Kramer; Sir Norman Lamb; John Lloyd; Baroness Neville-Rolfe, her second statement; The Right Honourable Lord Peter Mandelson; Alasdair Marnoch; Tony Marsh, that's his second statement.", "Over the page, please: `Professor Jeffrey Kramer <https://www.postofficehorizoninquiry.org.uk/evidence/witn11080100-professor-jeff-kramer-first-witness-statement>`_; `Sir Norman Lamb <https://www.postofficehorizoninquiry.org.uk/evidence/witn10170100-sir-norman-lamb-witness-statement>`_; `John Lloyd <https://www.postofficehorizoninquiry.org.uk/evidence/witn03430100-john-lloyd-first-witness-statement>`_; `Baroness Neville-Rolfe, her second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn10200200-baroness-neville-rolfe-second-witness-statement>`_; `The Right Honourable Lord Peter Mandelson <https://www.postofficehorizoninquiry.org.uk/evidence/witn00600100-rt-hon-lord-peter-mandelson-first-witness-statement>`_; `Alasdair Marnoch <https://www.postofficehorizoninquiry.org.uk/evidence/witn11570100-alasdair-marnoch-first-witness-statement>`_; `Tony Marsh, that's his second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn06900200-tony-marsh-second-witness-statement>`_.")
    text = text.replace("Over the page: Tim McCormack; Arthur Owen (Les Owen); Laura Thompson; Sophie Underwood; Mark Underwood; Dave Ward; Tom Wechsler; Michael Whitehead.  In Phase 5 and 6, please.", "Over the page: `Tim McCormack <https://www.postofficehorizoninquiry.org.uk/evidence/witn11100100-timothy-james-mccormack-witness-statement>`_; `Arthur Owen (Les Owen) <https://www.postofficehorizoninquiry.org.uk/evidence/witn10340100-arthur-leslie-owen-first-witness-statement>`_; `Laura Thompson <https://www.postofficehorizoninquiry.org.uk/evidence/witn11510100-laura-thompson-witness-statement>`_; `Sophie Underwood <https://www.postofficehorizoninquiry.org.uk/evidence/witn09820100-sophie-underwood-witness-statement>`_; `Mark Underwood <https://www.postofficehorizoninquiry.org.uk/evidence/witn00990100-mark-underwood-witness-statement>`_; `Dave Ward first statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn10070100-dave-ward-first-witness-statement>`_, `Dave Ward second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn10070200-dave-ward-second-witness-statement>`_); `Tom Wechsler <https://www.postofficehorizoninquiry.org.uk/evidence/witn09790100-tom-wechsler-witness-statement>`_; `Michael Whitehead <https://www.postofficehorizoninquiry.org.uk/evidence/witn11260100-michael-john-whitehead-first-witness-statement>`_.  In Phase 5 and 6, please.")
    text = text.replace("Can we move to Phase 7, please.  May we read into the record the statements of: Sarah Bell; Thomas Cooper, that's his second statement; Sir Ross Cranston; Carl Creswell, his third statement; Andrew Darfoor; Brian Gaunt; Sarah Gray; Calum Greenhow, a second statement; Lisa Harrington; Sir Gary Hickinbottom; Professor Christopher Hodges; Simon Jeffreys.", "Can we move to Phase 7, please.  May we read into the record the statements of: `Sarah Bell <https://www.postofficehorizoninquiry.org.uk/evidence/witn11630100-sarah-bell-witness-statement>`_; `Thomas Cooper, that's his second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn00200200-thomas-cooper-second-witness-statement>`_; `Sir Ross Cranston <https://www.postofficehorizoninquiry.org.uk/evidence/witn11790100-sir-ross-frederick-cranston-witness-statement>`_; `Carl Creswell, his third statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11730300-carl-creswell-third-witness-statement>`_; `Andrew Darfoor <https://www.postofficehorizoninquiry.org.uk/evidence/witn11340100-andrew-darfoor-first-witness-statement-0>`_; `Brian Gaunt <https://www.postofficehorizoninquiry.org.uk/evidence/witn11320100-brian-gaunt-first-witness-statement>`_; `Sarah Gray <https://www.postofficehorizoninquiry.org.uk/evidence/witn11440100-sarah-isabelle-gray-witness-statement>`_; `Calum Greenhow, a second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn00370200-calum-greenhow-second-witness-statement>`_; `Lisa Harrington <https://www.postofficehorizoninquiry.org.uk/evidence/witn10780100-lisa-harrington-witness-statement>`_; `Sir Gary Hickinbottom <https://www.postofficehorizoninquiry.org.uk/evidence/witn11780100-sir-gary-robert-hickinbottom-witness-statement-0>`_; `Professor Christopher Hodges <https://www.postofficehorizoninquiry.org.uk/evidence/witn11710100-professor-christopher-hodges-first-witness-statement>`_; `Simon Jeffreys <https://www.postofficehorizoninquiry.org.uk/evidence/witn11300100-simon-jeffreys-first-witness-statement>`_.")
    text = text.replace("Over the page please: Christopher Leach; Dan O'Mahoney; Zarin Patel; Martin Roberts; Rachel Scarrabelotti, her seventh statement; Carla Stent; Richard Taylor; Rod Williams, a second statement; Owen Woodley; and Paul Wood.  As read into the record, please.", "Over the page please: `Christopher Leach <https://www.postofficehorizoninquiry.org.uk/evidence/witn09630100-christopher-leach-first-witness-statement>`_; `Dan O'Mahoney first statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11760100-dan-omahoney-first-witness-statement>`_, `Dan O'Mahoney second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11760200-dan-omahoney-second-witness-statement>`_; `Zarin Patel <https://www.postofficehorizoninquiry.org.uk/evidence/witn11430100-zarin-homi-patel-witness-statement-0>`_; `Martin Roberts <https://www.postofficehorizoninquiry.org.uk/evidence/witn11580100-martin-roberts-witness-statement-0>`_; `Rachel Scarrabelotti, her seventh statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn11120700-rachel-scarrabellotti-seventh-witness-statement>`_; `Carla Stent <https://www.postofficehorizoninquiry.org.uk/evidence/witn09930100-carla-rosaline-stent-witness-statement-0>`_; `Richard Taylor <https://www.postofficehorizoninquiry.org.uk/evidence/witn11370100-richard-taylor-first-witness-statement-0>`_; `Rod Williams, a second statement <https://www.postofficehorizoninquiry.org.uk/evidence/witn08420200-rodric-david-alun-williams-second-witness-statement>`_; `Owen Woodley <https://www.postofficehorizoninquiry.org.uk/evidence/witn11380100-owen-woodley-first-witness-statement>`_; and `Paul Wood <https://www.postofficehorizoninquiry.org.uk/evidence/witn11700100-paul-wood-witness-statement>`_.  As read into the record, please.")

    for e in META['evidence'].keys():
        text = text.replace(e, f'`{e} <{META["evidence"][e]}>`_')

    # Manually fix any issues
    text = text.replace('>`_and', '>`_ and')

    # Deal with some acronyms
    for acronym, meaning in ACRONYMS.items():
        text = re.sub(fr'\b{acronym}\b', f':abbr:`{acronym} ({meaning})`', text, count=1)

    if speech.speaker:
        out = f"**{speech.speaker}**: {text}"
    else:
        out = f"*{text}*"

    if speech.type == 'answer':
        out = re.sub('\n\n', '\n\n.. rst-class:: indented\n\n', out)
        out = f".. rst-class:: indented\n\n{out}"

    return f"{out}\n\n"

def parse_transcripts():
    for f in sorted(glob.glob('data/*.txt')):
        if 'raw.txt' in f: continue # Ignore PDF processed
        date, title = re.match('data/(\d\d\d\d-\d\d-\d\d)-(.*).txt$', f).groups()
        if 'Human Impact Focus Group' in title:
            sect = 'human-impact-focus-group'
            os.makedirs(sect, exist_ok=True)
            outfile = f'{sect}/{date}'
        elif ' - ' in title:
            sect, subsect = title.split(' - ')
            sect = sect.lower().replace(' ', '-')
            title = subsect
            os.makedirs(sect, exist_ok=True)
            outfile = f'{sect}/{date}'
        else:
            sect = ''
            outfile = f'{date}'

        with open(f, 'r', encoding='iso-8859-15') as fp:
            if os.path.exists(f'{outfile}.rst'):
                print(f"Reparsing {f}")
            else:
                print(f"\033[31mPARSING {f}\033[0m")
            with open(f'{outfile}.rst', 'w') as out:
                url = META['urls'][date]
                out.write(f'.. raw:: html\n\n   <a id="hearing-link" href="{url}">Official hearing page</a>\n\n')
                speeches = list(parse_transcript(f, fp))

                level1_heading = []
                for speech in speeches:
                    if isinstance(speech, Section) and speech.level == 1 and sect != 'human-impact-focus-group':
                        words = [s for s in speech.heading.split(' ') if s not in ('Mr', 'Mrs', 'Ms', 'Dr', 'Sir', 'Lord', 'Baroness')]
                        if (len(words) == 2 or (len(words) == 4 and words[2] == 'of')) and 'Housekeeping' not in words:
                            level1_heading.append(' '.join(words))
                if level1_heading:
                    if len(level1_heading) > 2:
                        level1_heading = ', '.join(level1_heading[:-2])  + ', ' + ' and '.join(level1_heading[-2:])
                    elif len(level1_heading) == 2:
                        level1_heading = ' and '.join(level1_heading)
                    else:
                        level1_heading = level1_heading[0]
                    title += ' – ' + level1_heading

                out.write(title + '\n' + '=' * len(title) + '\n\n')
                out.write(header(date))
                for speech in speeches:
                    if isinstance(speech, Speech):
                        out.write(parse_speech(speech))
                    elif isinstance(speech, Section):
                        if speech.level == 1:
                            out.write(speech.heading + '\n' + '-' * len(speech.heading) + '\n\n')
                        elif speech.level == 2:
                            out.write(speech.heading + '\n' + '^' * len(speech.heading) + '\n\n')

def strip_line_numbers(text):
    page, num = 1, 1
    state = 'text'
    data = []
    for line in text:
        line = line.rstrip('\n')

        # Page break
        if '\014' in line:
            page += 1
            num = 1
            line = line.replace('\014', '')

        # Empty line
        if re.match('\s*$', line):
            continue

        # Start of index, ignore from then on
        if re.match(' *\d* +I ?N ?D ?E ?X$', line) or '...............' in line:
            state = 'index'
            continue
        if state == 'index':
            continue

        # Just after last line, there should be a page number
        if num == 26:
            m = re.match(' +(\d+)$', line)
            assert int(m.group(1)) == page
            continue

        # Let's check we haven't lost a line anywhere...
        assert re.match(' *%d( |$)' % num, line), '%s != %s' % (num, line)

        # Strip the line number
        line = re.sub('^ *%d' % num, '', line)

        # Okay, here we have a non-page number, non-index line of just text
        data.append((page, num, line))
        num += 1

    return data

def remove_left_indent(data):
    # Work out how indented everything is
    min_indent = 999
    for page, num, line in data:
        left_space = len(line) - len(line.lstrip())
        if left_space:
            min_indent = min(min_indent, left_space)

    # Strip that much from every line
    left_space = ' ' * min_indent
    data = [
        (page, num, re.sub('^' + left_space, '', line))
        for page, num, line in data
    ]
    return data

def parse_transcript(url, text):
    data = strip_line_numbers(text)
    data = remove_left_indent(data)

    indent = None
    speech = None
    interviewer = None
    state = 'text'
    date = None
    for page, num, line in data:
        # Okay, here we have a non-empty, non-page number, non-index line of just text
        # print(page, num, line)

        # Empty line
        if re.match('\s*$', line):
            continue

        if page == 5 and num == 5 and line == 'MR PETERS:  Yes, in 2009.':
            line = 'A.  Yes, in 2009.'
        elif page == 58 and num == 23 and line == 'MS PRICE:  Thank you, sir.':
            line = 'MS PAGE:  Thank you, sir.'
        elif page == 56 and num == 15 and line == '        Thank you very much.':
            line = 'MR BEER:  Thank you very much.'
        elif page == 113 and num == 16 and line == 'Q.  Can I start by bringing up POL00028471, page 2, please.':
            line = 'MR STEVENS:  Can I start by bringing up POL00028471, page 2, please.'
        elif page == 81 and num == 6 and line == 'Q.  Do you work closely with him?':
            line = 'MR HENRY:  Do you work closely with him?'

        line = line.replace('MAPEC_', 'MAPEC)')
        line = line.replace('**', '\*\*')
        line = line.replace('_', '\_')

        # Date at start
        m = re.match(' *(Mon|Tues|Wednes|Thurs|Fri)day,? \d+(nd|th)? (August|September|October|November|December|January|February|March|April|May|June|July),? 20[12][1234]\.?$', line)
        if m:
            date = line.strip() # datetime.strptime(line.strip(), '%A, %d %B %Y')
            continue

        if state == 'adjournment':
            state = 'text'
            if re.match(' *(.*)\)$', line):
                speech.add_text(line.strip())
                continue

        # Time/message about lunch/adjournments
        m = re.match(' *(\(.*\))$', line)
        if m:
            spkr = None
            if speech:
                spkr = getattr(speech, 'speaker', None)
                yield speech
            #try:
                #line = m.group(1)
                #if re.match('\(1[3-9]\.', line):
                #    time_format = '(%H.%M %p)'
                #else:
                #    time_format = '(%I.%M %p)'
                #time = datetime.strptime(line, time_format).time()
                #yield Speech(speaker=None, text=line)
            #except:
            yield Speech(speaker=None, text=line)
            speech = Speech( speaker=spkr, text='' )
            continue

        # Multiline message about adjournment
        m = re.match('(?i) *\((The (hearing|Inquiry) adjourned|On behalf of)', line)
        if m:
            yield speech
            state = 'adjournment'
            speech = Speech( speaker=None, text=line.strip() )
            continue

        # Questions
        m = re.match('(?:Further question|Question|Examin)(?:s|ed) (?:from|by) (.*?)(?: \(continued\))?$', line.strip())
        ignore = ('Questions from MPs on this issue.  None of these seemed',)
        if m and line.strip() not in ignore:
            yield speech
            speech = Section( heading=fix_heading(line), level=2)
            interviewer = fix_name(m.group(1))
            continue

        # Headings
        m = re.match('Focus Group Session [34]$|Housekeeping$|([A-Z ]*)$|Announcement re |Decision$', line.strip())
        ignore = ('IDENTIFYING THE UNDERLYING ROOT CAUSE OF THE', 'ASK FOR HIS MEDIA STATEMENT WITHOUT OFFERING TO SHARE')
        if m and line.strip() not in ignore:
            yield speech
            speech = Section( heading=fix_heading(line) )
            continue

        # Headings with names in
        m = re.match('(?:(?:Opening|Closing) s|S)tatement (?:by|from) ([A-Z ]*)(?:, QC)?(?: \(continued\))?$|Announcements by ([A-Z ]*)$|(?:Further s|S)ubmissions? by ([A-Z ]*)(?:, QC)?$|Reply by ([A-Z ]*)$|Witness statement of ([A-Zc ]*) adduced$', line.strip())
        if m:
            yield speech
            name = next(filter(None, m.groups()))
            line = line.replace(name, fix_name(name)).strip()
            speech = Section( heading=line )
            continue

        # Witness arriving
        m1 = re.match(" *((?:[A-Z]|Mr)(?:[A-Z0-9' ,-]|Mc|Mr|and)+?)(,?\s*\(.*\)|, (?:sworn|affirmed|statement summarised|summary read by ([A-Z ]*)))$", line)
        m2 = re.match(" *(Mr.*)(, statement summarised)$", line)
        m3 = re.match(" *(Summary of witness statement of )([A-Zc0-9 \[\]-]*)(\s*\(read\))?$", line)
        if m1 or m2 or m3:
            m = m1 or m2 or m3
            if m3:
                heading = m.group(1) + fix_name(m.group(2).strip())
                narrative = '%s%s%s.' % (m.group(1), m.group(2), m.group(3) or '')
            else:
                heading = fix_name(m.group(1).strip())
                if 'statement' not in line:
                    Speech.witness = heading
                narrative = '%s%s.' % (m.group(1), m.group(2))
            spkr = speech.speaker
            yield speech
            yield Section( heading=heading )
            yield Speech( speaker=None, text=narrative )
            if m1 and m.group(3):
                speaker = fix_name(m.group(3))
                speech = Speech( speaker=speaker, text='')
            else:
                speech = Speech( speaker=spkr, text='' )
            continue

        # Question/answer (speaker from previous lines)
        m = re.match(' *([QA])\. (.*)', line)
        if m:
            yield speech
            if m.group(1) == 'A':
                assert Speech.witness
                speaker = Speech.witness
                typ = 'answer'
            else:
                assert interviewer
                speaker = interviewer
                typ = 'question'
            speech = Speech( speaker=speaker, text=m.group(2), typ=typ )
            continue

        # New speaker
        m = re.match(' *((?:[A-Z -]|Mc)+)(?<!PPS)(?<!IT)(?<!MW): (.*)', line)
        if m:
            yield speech
            speaker = fix_name(m.group(1))
            if speaker not in ('The Stenographer', 'The Witness'):
                interviewer = speaker
            speech = Speech( speaker=speaker, text=m.group(2) )
            continue

        # New paragraph if indent at least 8 spaces
        m = re.match('        ', line)
        if m:
            speech.add_para(line.strip())
            continue

        # If we've got this far, hopefully just a normal line of speech
        speech.add_text(line.strip())

    yield speech

#name_fixes = { }
def fix_name(name):
    name = name.title()
    name = name.replace('Qc', 'QC').replace('Kc', 'KC')
    name = name.replace(' Of ', ' of ')
    name = name.replace('The Right Honourable ', '').replace(' Mp', '')
    # Deal with the McNames
    name = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), name)
    #s = name_fixes.get(s, s)
    # More than one name given, or Lord name that doesn't include full name
    #if ' and ' in name or (' of ' in name and ',' not in name):
    #    return name
    # Remove middle names
    name = re.sub('^(DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir) (\S+ )(?:\S+ )+?(\S+)((?: [QK]C)?| of \S+)$', r'\1 \2\3\4', name)
    name = re.sub('^(?!DAC|DS|Dr|Miss|Mrs|Mr|Ms|Baroness|Lord|Professor|Sir)(\S+) (?!Court)(?:\S+ )+?(\S+)((?: [QK]C)?)$', r'\1 \2', name)
    # Special cases
    name = name.replace('Richard Atkinson', 'Duncan Atkinson')
    name = name.replace('William Patterson', 'Paul Patterson')
    name = name.replace('Angela Bogerd', 'Angela van den Bogerd')
    name = name.replace('Sir John Cable', 'Sir Vince Cable')
    return name

def fix_heading(s):
    s = string.capwords(s.strip())
    rep = [ 'Kc', 'Uk', 'Qc' ]
    s = re.sub('|'.join(rep), lambda m: m.group(0).upper(), s)
    rep = [ 'Of', 'By', 'The', 'To', 'On', 'For', 'And', 'Re' ]
    s = re.sub('\\b' + '\\b|\\b'.join(rep) + '\\b', lambda m: m.group(0).lower(), s)
    return s

load_data()
parse_transcripts()
