"""Sterowanie lektorem z gry (próba nakładki): tempo, zapis ustawień, nazwy mówców i zgłoszenia błędów.

  stretch       zmiana tempa bez zmiany wysokości głosu (WSOLA w numpy, bez nowych bibliotek paczki)
  set_setting   zapis jednej wartości w ustawienia.toml z zachowaniem komentarzy i układu pliku
  write_report  zgłoszenie z gry: zgloszenia/<data-godzina>/zgloszenie.json obok zrzutu ekranu z pluginu
"""
import json
import os
import re
import time

TEMPO_MIN, TEMPO_MAX, TEMPO_STEP = 0.8, 1.6, 0.1
VOLUME_STEP = 0.1
REPORT_WINDOW_S = 60.0          # ile sekund zdarzeń przed zgłoszeniem trafia do pliku

CATEGORIES = {                  # id z pluginu -> opis (kolejność = cyfry 1–6 w grze)
    'glos': 'zły głos',
    'wymowa': 'zła wymowa',
    'cisza': 'cisza (brak lektora)',
    'uciecie': 'ucięta kwestia',
    'mowca': 'zły mówca',
    'inne': 'inne',
}

# Skróty w grze: nazwy klawiszy Unity (KeyCode), kilka wariantów po przecinku. Plugin dostaje je w stanie.
KEYS = {
    'szybciej': 'Ctrl+Equals, Ctrl+KeypadPlus',
    'wolniej': 'Ctrl+Minus, Ctrl+KeypadMinus',
    'wycisz': 'Ctrl+M',
    'powtorz': 'Ctrl+R',
    'utnij': 'Ctrl+S',
    'zglos': 'Ctrl+B',
    'menu': 'Ctrl+L',
}


def clamp_tempo(x):
    return round(min(TEMPO_MAX, max(TEMPO_MIN, round(x / TEMPO_STEP) * TEMPO_STEP)), 2)


def stretch(y, rate, sr, frame_s=0.03, search_s=0.012):
    """Tempo × rate (1,2 = o 20% szybciej) bez zmiany wysokości: WSOLA z oknem Hanna i zakładką 50%.

    Każda kolejna ramka wejścia jest przesuwana w oknie ±search_s tak, żeby najlepiej pasowała do naturalnej
    kontynuacji poprzedniej ramki (korelacja na sygnale przerzedzonym 3×, wystarcza przy mowie)."""
    import numpy as np
    if abs(rate - 1.0) < 1e-3 or len(y) == 0:
        return y
    frame = int(frame_s * sr) & ~1
    hop = frame // 2
    tol = int(search_s * sr)
    if len(y) < 2 * frame:
        return y
    x = np.concatenate([np.zeros(tol, np.float32), y.astype(np.float32), np.zeros(frame + 2 * tol, np.float32)])
    n_out = int(len(y) / rate)
    frames = n_out // hop + 1
    win = (0.5 - 0.5 * np.cos(2 * np.pi * np.arange(frame) / frame)).astype(np.float32)   # okresowe okno Hanna
    out = np.zeros(frames * hop + frame, np.float32)
    norm = np.zeros_like(out)
    dec = 3
    prev = tol                                  # początek poprzedniej ramki w x (z przesunięciem)
    for k in range(frames):
        nominal = tol + int(k * hop * rate)
        if nominal + frame + tol >= len(x):
            break
        if k == 0:
            pos = nominal
        else:
            target = x[prev + hop:prev + hop + frame:dec]
            region = x[nominal - tol:nominal + tol + frame:dec]
            corr = np.correlate(region, target, 'valid')
            pos = nominal - tol + int(np.argmax(corr)) * dec
        o = k * hop
        out[o:o + frame] += x[pos:pos + frame] * win
        norm[o:o + frame] += win
        prev = pos
    out = out[:n_out]
    norm = norm[:n_out]
    np.divide(out, norm, out=out, where=norm > 1e-3)
    return out


# ---------- ustawienia.toml ----------

def _toml_value(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        return ('%.2f' % v).rstrip('0').rstrip('.') if v != int(v) else '%.1f' % v
    if isinstance(v, int):
        return str(v)
    return json.dumps(str(v), ensure_ascii=False)


LINE = re.compile(r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)("(?:[^"\\]|\\.)*"|[^#\s]+)(.*)$')
SECTION = re.compile(r'^\s*\[([^\]]+)\]\s*(#.*)?$')


def set_setting(file, key, value, section=None):
    """Podmienia wartość klucza w pliku TOML (komentarz w tej linii zostaje); brakujący klucz dopisuje do sekcji."""
    with open(file, encoding='utf-8-sig') as fh:
        lines = fh.read().split('\n')
    cur, last_in_section, found = None, None, False
    for i, ln in enumerate(lines):
        m = SECTION.match(ln)
        if m:
            cur = m.group(1).strip()
            continue
        if cur != section:
            continue
        if ln.strip() and not ln.lstrip().startswith('#'):
            last_in_section = i
        m = LINE.match(ln)
        if m and m.group(2) == key:
            lines[i] = m.group(1) + key + m.group(3) + _toml_value(value) + m.group(5)
            found = True
            break
    if not found:
        new = '%s = %s' % (key, _toml_value(value))
        if section is None:
            first = next((i for i, ln in enumerate(lines) if SECTION.match(ln)), len(lines))
            while first > 0 and not lines[first - 1].strip():
                first -= 1                      # przed pustą linią, która oddziela sekcję
            lines.insert(first, new)
        elif last_in_section is not None:
            lines.insert(last_in_section + 1, new)
        else:
            lines += ['', '[%s]' % section, new]
    tmp = file + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='') as fh:
        fh.write('\n'.join(lines))
    os.replace(tmp, file)


# ---------- mówca do wyświetlenia ----------

def speaker_label(voice):
    if not voice or voice == 'narrator':
        return 'Narrator'
    if voice.startswith('nv_'):
        return 'Postać epizodyczna'
    return voice.replace('_', ' ').title()


# ---------- zgłoszenia ----------

def reports_dir(logs):
    """zgloszenia/ obok katalogu dzienników (paczka: <paczka>/zgloszenia, deweloperski: LektorPL/zgloszenia)."""
    return os.path.join(os.path.dirname(os.path.abspath(logs)), 'zgloszenia')


def item_info(lib, item):
    """Kwestia w zgłoszeniu: klucze, głos, fragmenty z plikami i tekstem (dla przeglądu poprawek)."""
    if item is None:
        return None
    u = item.u
    line = lib.lines.get(u.key) or {}
    return {
        'token': item.token, 'src': item.src, 'key': item.key, 'resolved': u.key, 'via': u.via,
        'voice': line.get('voice'), 'category': u.category, 'toggle': u.toggle, 'missing': sorted(set(u.missing)),
        'fragments': [{'id': fid, 'file': lib.files.get(fid), 'text': lib.frag_text.get(fid), 'pause': gap}
                      for fid, gap in u.pieces],
    }


def write_report(folder, ev, director, plugin_events, companion_events, now):
    """Zapisuje zgloszenie.json; zwraca ścieżkę pliku."""
    os.makedirs(folder, exist_ok=True)
    lib = director.lib
    token = ev.get('token')
    target = director.find(token) if token else (director.current or director.last_item())
    recent = lambda evs: [{'ago_s': round(now - t, 2), **e} for t, e in evs if now - t <= REPORT_WINDOW_S]
    data = {
        'czas': time.strftime('%Y-%m-%d %H:%M:%S'),
        'kategoria': ev.get('category'),
        'opis_kategorii': CATEGORIES.get(ev.get('category')),
        'z_historii': bool(token),
        'zrzut': os.path.basename(ev['shot']) if ev.get('shot') else None,
        'plugin': ev.get('plugin'),
        'model': lib.model,
        'kwestia': item_info(lib, target),
        'gra_teraz': item_info(lib, director.current),
        'kolejka': [item_info(lib, it) for it in director.queue],
        'historia': [item_info(lib, h['item']) for h in director.history],
        'ustawienia': {'tempo': director.tempo, 'wyciszony': director.muted, 'glosnosc': director.volume,
                       'toggles': dict(director.toggles)},
        'zdarzenia_pluginu': recent(plugin_events),
        'dziennik_companiona': recent(companion_events),
    }
    path = os.path.join(folder, 'zgloszenie.json')
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    return path
