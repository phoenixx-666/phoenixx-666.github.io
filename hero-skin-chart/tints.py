import base64
import csv
from datetime import datetime as dt
import itertools
import json
import lzma


DFMT = '%Y-%m-%d'
NAME = 'name'
SKINS = 'skins'
TINTS = 'tints'
DATE = 'date'
TYPE = 'type'
NSKINS = 'num_skins'
RELEASE = 'release_date'
LAST_NORMAL_SKIN = 'last_normal_skin'
LAST_SEASONAL_SKIN = 'last_seasonal_skin'
LAST_ANY_SKIN = 'last_any_skin'
LAST_NORMAL_TINT = 'last_normal_tint'
LAST_SEASONAL_TINT = 'last_seasonal_tint'
LAST_ANY_TINT = 'last_any_tint'
Q = 'q'
Q2 = 'q2'
SKIN_FIX = {
    'Cyber Ghost Kerrigan': ('Queen of Ghosts Kerrigan', 'Cyber Ghost'),
    "Cyber Oni Anub'arak": ("Cyb'arak", 'Cyber Oni'),
    'Nephalem Johanna': ('Johanna', 'Nephalem'),
    'Nephalem Kharazim': ('Kharazim', 'Nephalem'),
    'Nephalem Li-Ming': ('Archon Li-Ming', 'Nephalem'),
    'Nephalem Nazeebo': ('Grimskull Nazeebo', 'Nephalem'),
    'Nephalem Sonya': ('Sonya', 'Nephalem'),
    'Nephalem Valla': ('Ordermaster Valla', 'Nephalem'),
    'RCHS Cheerleader Kerrigan': ('Cheerleader Kerrigan', 'RCHS'),
    'RCHS Striker Li-Ming': ('Striker Li-Ming', 'RCHS'),
    }
CDPS_LIST = {
    'Ana': 'Shrike Ana',
    'Artanis': 'Daelaam Artanis',
    'Brightwing': 'Bewitching Brightwing',
    'Chen': 'Brewmaster Chen',
    "Cho'gall": "Pump'kin Cho'gall",
    'Chromie': 'Creepie Chromie',
    'Gazlowe': 'Paper Bag Gazlowe',
    'Raynor': 'Stars and Stripes Raynor',
    'Tychus': 'Power Briefs Tychus',
    'Zeratul': 'High Templar Zeratul'
    }


def last_skin_date(skins, types):
    skins = filter(lambda skin: skin[TYPE] in types, skins)
    skins = sorted(skins, key=lambda skin: dt.strptime(skin[RELEASE], DFMT))
    return skins[-1][RELEASE] if len(skins) else None


last_tint_or_none = lambda lst: lst[-1][DATE] if len(lst) else None


not_none = lambda lst: list(filter(lambda item: item is not None, lst))


with open('Tints.csv', 'r', encoding='utf-8') as csvfile:
    rows = [row for row in csv.reader(csvfile, delimiter=',', quotechar='"')]

heroes = {}
for row in rows:
    hero, skin, tint, date, type = row
    
    hero = "Cho'gall" if hero == 'Cho' else hero
    skin = skin.replace('’', "'")
    skin, tint = SKIN_FIX.get(skin, (skin, tint))
    
    herodata = heroes.setdefault(hero, {NAME: hero})
    skinlist = herodata.setdefault(SKINS, {})
    skin = skinlist.setdefault(skin, {NAME: skin, TINTS: [], RELEASE: date})
    skin[TINTS].append({NAME: tint, DATE: date, TYPE: type})
    if dt.strptime(date, DFMT) < dt.strptime(skin[RELEASE], DFMT):
        skin[RELEASE] = date

for hero in heroes.values():
    hero[NSKINS] = len(hero[SKINS]) - 1
    hero[RELEASE] = hero[SKINS][hero[NAME]][RELEASE]
    for skin in hero[SKINS].values():
        if any(map(lambda tint: 'Free' in tint[TYPE], skin[TINTS])):
            skin[TYPE] = 'Base'
        elif all(map(lambda tint: 'Seasonal' in tint[TYPE], skin[TINTS])):
            skin[TYPE] = 'Seasonal'
        elif all(map(lambda tint: 'Limited' in tint[TYPE], skin[TINTS])):
            skin[TYPE] = 'Limited'
        else:
            skin[TYPE] = 'Normal'
    hero[LAST_NORMAL_SKIN] = last_skin_date(hero[SKINS].values(), ['Normal'])
    hero[LAST_SEASONAL_SKIN] = last_skin_date(hero[SKINS].values(), ['Seasonal', 'Limited'])
    tints = list(itertools.chain(*map(lambda skin: skin[TINTS], hero[SKINS].values())))
    tints = sorted(tints, key=lambda tint: dt.strptime(tint[DATE], DFMT))
    hero[LAST_NORMAL_TINT] = last_tint_or_none(list(filter(lambda tint: 'Free' in tint[TYPE] or 'Normal' in tint[TYPE], tints)))
    hero[LAST_SEASONAL_TINT] = last_tint_or_none(list(filter(lambda tint: 'Seasonal' in tint[TYPE] or 'Limited' in tint[TYPE], tints)))
    hero[LAST_ANY_SKIN] = sorted(not_none([hero[LAST_NORMAL_SKIN], hero[LAST_SEASONAL_SKIN]]), key=lambda date: dt.strptime(date, DFMT))[-1]
    hero[LAST_ANY_TINT] = sorted(not_none([hero[LAST_NORMAL_TINT], hero[LAST_SEASONAL_TINT]]), key=lambda date: dt.strptime(date, DFMT))[-1]
    hero[Q] = int((dt.now() - dt.strptime(hero[RELEASE], DFMT)).days / hero[NSKINS])
    hero[Q2] = int((dt.now() - dt.strptime(hero[RELEASE], DFMT)).days / (hero[NSKINS] - (1 if hero[NAME] in CDPS_LIST else 0)))

with open('Tints.json', 'w') as jsonfile:
    jsonfile.write(json.dumps(heroes, indent=4, sort_keys=True))

with open('Tints_processed.csv', 'w', newline='\n', encoding='utf-8') as csvfile:
    w = csv.writer(csvfile, delimiter=',', quotechar='"')
    w.writerow(['Hero', 'Hero Released', 'Skins in Total', 'Last Normal Skin', 'Last Seasonal/Limited-Time Skin', 'Last Skin Overall', 'Last Normal Tint', 'Last Seasonal/Limited-Time Tint', 'Last Tint Overall', 'DPS Quotient', 'CDPS Quotient'])
    for hero in sorted(heroes.values(), key=lambda hero: hero[NAME]):
        w.writerow([hero[NAME], hero[RELEASE], hero[NSKINS], hero[LAST_NORMAL_SKIN], hero[LAST_SEASONAL_SKIN], hero[LAST_ANY_SKIN], hero[LAST_NORMAL_TINT], hero[LAST_SEASONAL_TINT], hero[LAST_ANY_TINT], hero[Q], hero[Q2]])

html = lzma.decompress(base64.b64decode('''
    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
    w6zIJuoAAdMNjj0AACbJWo6xxGf7AgAAAAAEWVo=
    ''')).decode()
tablerow = '''        <tr data-hero="{}">
          <td align="right">{}</td>
          <td>{}</td>
          <td>{}</td>
          <td>{}</td>
          <td>{}</td>
          <td></td>
          <td>{}</td>
          <td></td>
          <td>{}</td>
          <td></td>
          <td>{}</td>
          <td></td>
          <td>{}</td>
          <td></td>
          <td>{}</td>
          <td></td>
          <td></td>
          <td data-skins-exclude="{}"></td>
        </tr>'''
html = html.replace('{}', '\n'.join([tablerow.format(*list(map(lambda x: '' if x is None else x, [hero[NAME].replace('ú', '&uacute;'), n, hero[NAME].replace('ú', '&uacute;'), hero[RELEASE], hero[NSKINS], hero[LAST_NORMAL_SKIN], hero[LAST_SEASONAL_SKIN], hero[LAST_ANY_SKIN], hero[LAST_NORMAL_TINT], hero[LAST_SEASONAL_TINT], hero[LAST_ANY_TINT], 1 if hero[NAME] in CDPS_LIST else 0]))) for n, hero in enumerate(sorted(heroes.values(), key=lambda hero: hero[NAME].replace('ú', 'u')), 1)]), 1)
html = html.replace('{}', ', '.join(CDPS_LIST[hero] for hero in sorted(CDPS_LIST)))

with open('index.html', 'w', newline='\n') as htmlfile:
    htmlfile.write(html)
