"""Stan kampanii z zapisu gry: ukończone i dostępne scenariusze, wydarzenia i wpisy dziennika kampanii.

Tylko odczyt. Zapis (.sav to JSON) i modele kampanii z kopii gry (d3/coreset/data, d3/narrativeevents,
d3/cityevents). Tytuły PL trafiają tylko do pliku w analysis/work/out, na konsolę idą identyfikatory.

  .venv/Scripts/python -I analysis/tools/campaign_state.py <slot albo plik .sav> [...]
"""
import glob
import json
import os
import sys

from lektor import game as G
from lektor import paths

OUT = os.path.join(paths.WORK, 'out')
MODELS = (('d3/coreset/data', 'QuestModel', '_keyName'),
          ('d3/narrativeevents', 'NarrativeEventModel', '_keyName'),
          ('d3/cityevents', 'CityEventModel', '_keyTitle'))
KIND = {'QuestModel': 'scenariusz', 'NarrativeEventModel': 'wydarzenie', 'CityEventModel': 'miasto'}


def latest_save(path):
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, '*.sav')))
        if not files:
            raise SystemExit('Brak plików .sav w %s' % path)
        return files[-1]
    return path


def models(game, terms):
    out = {}
    for bundle, cls, title_key in MODELS:
        for _, t, c in game.behaviours(bundle):
            if c != cls or not t.get('_id'):
                continue
            key = t.get(title_key)
            out[t['_id']] = {
                'id': t['_id'], 'kind': KIND[cls], 'asset': t.get('m_Name'), 'act': t.get('_act'),
                'title_key': key, 'title': (terms.get(key) or {}).get('text') or None,
                'requires_quests': [r.get('_id', r) if isinstance(r, dict) else r for r in t.get('_requiredCompletedQuests', [])],
                'scene': t.get('SceneAssetPath'), 'localization': t.get('_localizationAssetPath'),
            }
    return out


def state(save, catalog):
    d = json.loads(open(save, encoding='utf-8-sig').read())
    g = d['GameSceneData']['GameState']
    done, active = g['CompletedDestinationIds'], g['ActiveDestinationIds']
    completed = set(done) | set(g['CompletedNarrativeEventIds']) | set(g['CompletedCityEventIds'])
    log = [{'order': i + 1, 'id': e['EntryId'], 'type': ('scenariusz', 'wydarzenie', 'miasto')[e['EntryType']],
            'date': e['DateCompleted']} for i, e in enumerate(g['CampaignLogEntries'])]
    return {
        'save': save, 'version': d['Version'], 'campaign': g['CampaignId'], 'act': d['Act'],
        'hours': round(d['StorySlot']['TotalSlotTime'] / 3600, 1), 'heroes': [p['HeroId'] for p in d['AllPlayers']],
        'products': d['ProductIDs'], 'location': d['StorySlot']['LastKnownLocation'], 'quest_in_progress': g['QuestId'] or None,
        'completed': [dict(catalog.get(e['id'], {'id': e['id']}), order=e['order'], date=e['date']) for e in log],
        'completed_unlogged': sorted(completed - {e['id'] for e in log}),
        'available': [catalog.get(i, {'id': i}) for i in active],
        'not_yet': sorted(i for i, m in catalog.items() if m['act'] == d['Act'] and i not in completed and i not in active
                          and m['kind'] != 'miasto'),
    }


def markdown(s):
    row = lambda m: '| `%s` | %s | %s | %s |' % (m['id'], m.get('kind', '?'), m.get('asset') or '–', m.get('title') or '–')
    lines = ['# Stan kampanii (prywatne)', '', '- zapis: `%s`' % s['save'],
             '- wersja %s, %s, akt %s, %.1f h, bohaterowie: %s' % (s['version'], s['campaign'], s['act'], s['hours'], ', '.join(s['heroes'])),
             '- miejsce: `%s`, scenariusz w toku: %s' % (s['location'], s['quest_in_progress'] or 'brak'), '',
             '## Rozegrane (kolejność z dziennika kampanii)', '', '| id | rodzaj | zasób | tytuł PL |', '|---|---|---|---|']
    lines += [row(m) for m in s['completed']]
    lines += ['', '## Dostępne teraz', '', '| id | rodzaj | zasób | tytuł PL |', '|---|---|---|---|']
    lines += [row(m) for m in s['available']]
    return '\n'.join(lines) + '\n'


def main(argv):
    if not argv:
        raise SystemExit(__doc__)
    game = G.Game()
    catalog = models(game, game.terms())
    os.makedirs(OUT, exist_ok=True)
    states = [state(latest_save(a), catalog) for a in argv]
    best = max(states, key=lambda s: (len(s['completed']), s['hours']))
    for s in states:
        print('%s%s: %s, %.1f h, ukończone %d, dostępne %s' % ('* ' if s is best else '  ', s['save'], s['campaign'], s['hours'],
              len(s['completed']), ' '.join(m['id'] for m in s['available'])))
    with open(os.path.join(OUT, 'campaign_state.json'), 'w', encoding='utf-8') as fh:
        json.dump({'best': best, 'catalog': catalog, 'states': states}, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'campaign_state.md'), 'w', encoding='utf-8') as fh:
        fh.write(markdown(best))
    print('Rozegrane:', ' '.join(m['id'] for m in best['completed']))
    print('Szczegóły z tytułami: analysis/work/out/campaign_state.md')


if __name__ == '__main__':
    main(sys.argv[1:])
