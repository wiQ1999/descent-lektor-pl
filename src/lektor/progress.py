"""Paczki generowania (E14, D83) i postęp: python -I -m lektor progress --release m3 [--all] [--credits]

Paczka to grupa kwestii (misja, wydarzenie, podróże, miasto, system). Fragment należy do pierwszej paczki w kolejności
gry, w której występuje: akt 1, akt 2, potem części wspólne (D95). Postęp liczy podejścia z takes.jsonl, przejęte
z poprzedniego wydania jako gotowe, godziny GPU i kredyty z tych podejść oraz czas do końca z tempa tego wydania.
"""
import json
import os
import time

from . import db, paths, scope
from . import direction as D

ACT2 = ('a2_', 'city_act2', 'travel_act2', 'town_act2')
COMMON = ('events', 'gear', 'enemies', 'system')
ACT_NAMES = {1: 'akt 1', 2: 'akt 2', 3: 'wspólne'}
GPU_S_PER_CHAR = 105 * 3600 / (830e3 + 3 * 255e3)     # szacunek E14 (PLAN, D38), dopóki wydanie nie ma własnego tempa
STATE_FILE = 'run_state.json'


def act(group):
    return 2 if group.startswith(ACT2) else 3 if group.startswith(COMMON) else 1


def rank(group):
    return act(group), scope.m3_rank(group)


def packages(con):
    """{fragment: paczka}: pierwsza grupa w kolejności gry; wartości luk bez kwestii (lista łupu) idą do 'system'."""
    groups = {}
    for fid, grp in con.execute('SELECT s.fragment, l.grp FROM segments s JOIN lines l ON l.key = s.key '
                                'WHERE s.fragment IS NOT NULL UNION SELECT v.fragment, l.grp FROM slot_values v '
                                'LEFT JOIN lines l ON l.key = v.key WHERE v.fragment IS NOT NULL'):
        grp = grp or 'system'
        if fid not in groups or rank(grp) < rank(groups[fid]):
            groups[fid] = grp
    return groups


def needed(voice):
    """Numery podejść, które musi mieć fragment (OmniVoice: 1 albo 3, ElevenLabs: pierwsze od 101)."""
    from .synth import takes_for
    return [D.ELEVEN_TAKE0 + 1] if D.engine(voice) == 'elevenlabs' else list(range(1, takes_for(voice) + 1))


def collect():
    from .synth import inherited, load_state
    con = db.connect(paths.DB)
    pkg = packages(con)
    state = load_state()
    done_prev = inherited()
    rows = {}
    for r in con.execute('SELECT id, voice, text FROM fragments'):
        g = pkg.get(r['id'], 'system')
        e = D.engine(r['voice'])
        p = rows.setdefault(g, {'group': g, 'act': act(g), 'omnivoice': [0, 0, 0, 0], 'elevenlabs': [0, 0, 0, 0],
                                'gpu_s': 0.0, 'credits': 0})
        # [podejścia potrzebne, gotowe, znaki potrzebne, znaki gotowe]
        for take in needed(r['voice']):
            got = r['id'] in done_prev or (r['id'], take) in state
            p[e][0] += 1
            p[e][1] += got
            p[e][2] += len(r['text'])
            p[e][3] += len(r['text']) if got else 0
            s = state.get((r['id'], take))
            if s:
                p['gpu_s'] += s.get('gen_s') or 0 if e == 'omnivoice' else 0
                p['credits'] += s.get('credits') or 0
    return sorted(rows.values(), key=lambda p: rank(p['group'])), state


def spent_credits(state=None):
    from .synth import load_state
    state = load_state() if state is None else state
    return sum(s.get('credits') or 0 for s in state.values())


def status(p):
    need = p['omnivoice'][0] + p['elevenlabs'][0]
    got = p['omnivoice'][1] + p['elevenlabs'][1]
    return 'gotowe' if got == need else 'czeka' if got == 0 else 'w toku'


def report(show_all=False):
    pkgs, state = collect()
    om_chars = [sum(p['omnivoice'][i] for p in pkgs) for i in (2, 3)]
    el_chars = [sum(p['elevenlabs'][i] for p in pkgs) for i in (2, 3)]
    gpu_s = sum(p['gpu_s'] for p in pkgs)
    om_rate = [(s['gen_s'], s['chars']) for s in state.values() if s.get('gen_s') and D.take_engine(s['take']) == 'omnivoice']
    per_char = sum(a for a, _ in om_rate) / max(sum(b for _, b in om_rate), 1) if len(om_rate) >= 20 else GPU_S_PER_CHAR
    om_left_h = (om_chars[0] - om_chars[1]) * per_char / 3600
    out = []
    sp = os.path.join(paths.AUDIO, STATE_FILE)
    if os.path.exists(sp):
        st = json.load(open(sp, encoding='utf-8'))
        out.append('Krok: %s (od %s)' % (st['step'], st['since']))
    out.append('OmniVoice: %s z %s znaków podejść (%.0f%%), GPU %.1f h, zostało ok. %.1f h (%s)' % (
        fmt(om_chars[1]), fmt(om_chars[0]), 100 * om_chars[1] / max(om_chars[0], 1), gpu_s / 3600, om_left_h,
        'tempo tego wydania' if len(om_rate) >= 20 else 'szacunek E14'))
    ev = os.path.join(paths.AUDIO, 'evals.jsonl')
    if os.path.exists(ev):
        out.append('Ocena: %s z %s podejść' % (fmt(sum(1 for _ in open(ev, encoding='utf-8'))), fmt(len(state))))
    out.append('ElevenLabs: %s z %s znaków (%.0f%%), zużyte %s kr., zostało ok. %s kr.' % (
        fmt(el_chars[1]), fmt(el_chars[0]), 100 * el_chars[1] / max(el_chars[0], 1), fmt(spent_credits(state)),
        fmt(round((el_chars[0] - el_chars[1]) * 0.44))))
    out.append('')
    out.append('| Część | Paczki gotowe | w toku | czekają | Znaki OmniVoice | Znaki ElevenLabs |')
    out.append('|---|---:|---:|---:|---:|---:|')
    for a in (1, 2, 3):
        ps = [p for p in pkgs if p['act'] == a]
        st = [status(p) for p in ps]
        out.append('| %s | %d | %d | %d | %s / %s | %s / %s |' % (
            ACT_NAMES[a], st.count('gotowe'), st.count('w toku'), st.count('czeka'),
            fmt(sum(p['omnivoice'][3] for p in ps)), fmt(sum(p['omnivoice'][2] for p in ps)),
            fmt(sum(p['elevenlabs'][3] for p in ps)), fmt(sum(p['elevenlabs'][2] for p in ps))))
    shown = pkgs if show_all else [p for p in pkgs if status(p) == 'w toku'] + \
        [p for p in pkgs if status(p) == 'czeka'][:3]
    if shown:
        out.append('')
        out.append('| Paczka | Stan | Podejścia | Znaki | GPU h | Kredyty |')
        out.append('|---|---|---:|---:|---:|---:|')
        for p in shown:
            need = p['omnivoice'][0] + p['elevenlabs'][0]
            got = p['omnivoice'][1] + p['elevenlabs'][1]
            chars = (p['omnivoice'][3] + p['elevenlabs'][3], p['omnivoice'][2] + p['elevenlabs'][2])
            out.append('| %s | %s | %d / %d | %s / %s | %.1f | %s |' % (
                p['group'], status(p), got, need, fmt(chars[0]), fmt(chars[1]), p['gpu_s'] / 3600, fmt(p['credits'])))
    return '\n'.join(out)


def fmt(n):
    return '{:,}'.format(int(n)).replace(',', ' ')


def mark(step):
    """Krok skryptu generowania w run_state.json (czyta go `progress`)."""
    os.makedirs(paths.AUDIO, exist_ok=True)
    json.dump({'step': step, 'since': time.strftime('%Y-%m-%d %H:%M')},
              open(os.path.join(paths.AUDIO, STATE_FILE), 'w', encoding='utf-8'), ensure_ascii=False)
