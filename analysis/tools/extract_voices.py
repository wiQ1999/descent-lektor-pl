"""Wyciąga polskie nagrania głosowe z Polish.pck (kopia robocza) do .wem i konwertuje je do WAV.

Nazwy plików i przypisanie do banków bierze z SoundbanksInfo.xml (Media/File z Language="Polish").
Wejście:  work/game/.../GeneratedSoundBanks/Windows/{Polish.pck,SoundbanksInfo.xml}
Wyjście (nieśledzone): work/voices/wem/<grupa>/*.wem, work/voices/wav/<grupa>/*.wav, work/voices/index.json
Grupy: cutscenes (Voice_Cutscenes_*), heroes (Voice_Heroes_*), villains (Voice_Villains_*).

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/extract_voices.py
"""
import json
import os
import re
import struct
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'Audio', 'GeneratedSoundBanks', 'Windows')
OUT = os.path.join(ROOT, 'work', 'voices')
VGMSTREAM = os.path.join(ROOT, 'work', 'bin', 'vgmstream-r2168', 'vgmstream-cli.exe')
GROUPS = (('Voice_Cutscenes', 'cutscenes'), ('Voice_Heroes', 'heroes'), ('Voice_Villains', 'villains'), ('Music_Cutscenes', 'cutscenes'))


def polish_media():
    """{media_id: {'name', 'banks', 'group'}} dla plików PL z SoundbanksInfo.xml."""
    media = {}
    for sb in ET.parse(os.path.join(AUDIO, 'SoundbanksInfo.xml')).getroot().iter('SoundBank'):
        if sb.get('Language') != 'Polish':
            continue
        bank = sb.findtext('ShortName')
        group = next((g for prefix, g in GROUPS if bank.startswith(prefix)), 'other')
        for f in sb.iter('File'):
            if f.get('Language') != 'Polish':
                continue
            m = media.setdefault(int(f.get('Id')), {'name': f.findtext('ShortName'), 'banks': [], 'group': group})
            m['banks'].append(bank)
    return media


def pck_banks(data):
    """Banki z paczki AKPK: lista bajtów każdego .bnk."""
    assert data[:4] == b'AKPK', data[:4]
    _hdr, _ver, lang_sz, bnk_sz, _stm_sz = struct.unpack_from('<5I', data, 4)
    off = 28 + lang_sz
    n = struct.unpack_from('<I', data, off)[0]
    banks = []
    for i in range(n):
        _fid, blk, size, start, _lang = struct.unpack_from('<5I', data, off + 4 + i * 20)
        banks.append(data[start * blk:start * blk + size])
    return banks


def bank_media(bnk):
    """{media_id: bajty .wem} z sekcji DIDX/DATA banku."""
    p, didx, dpos = 0, [], None
    while p + 8 <= len(bnk):
        tag, size = bnk[p:p + 4], struct.unpack_from('<I', bnk, p + 4)[0]
        if tag == b'DIDX':
            didx = [struct.unpack_from('<3I', bnk, p + 8 + i * 12) for i in range(size // 12)]
        elif tag == b'DATA':
            dpos = p + 8
        p += 8 + size
    return {mid: bnk[dpos + mo:dpos + mo + ms] for mid, mo, ms in didx}


def parse_name(group, name):
    """Mówca i typ kwestii z nazwy pliku, np. 'Syrus_QuestSelect_6.wav' -> ('Syrus', 'QuestSelect')."""
    stem = os.path.splitext(name)[0]
    if group in ('heroes', 'villains'):
        m = re.match(r'([A-Za-z]+)_([A-Za-z]+)_?(\d*)', stem)
        return (m.group(1), m.group(2)) if m else (stem, '')
    return ('narrator?', stem.replace('_VoiceOver', ''))


def wav_duration(path):
    with wave.open(path, 'rb') as w:
        return w.getnframes() / w.getframerate(), w.getframerate(), w.getnchannels()


def main():
    media = polish_media()
    data = open(os.path.join(AUDIO, 'Polish.pck'), 'rb').read()
    blobs = {}
    for bnk in pck_banks(data):
        blobs.update(bank_media(bnk))
    index = []
    for mid, m in sorted(media.items(), key=lambda kv: (kv[1]['group'], kv[1]['name'])):
        if mid not in blobs:
            print('brak w Polish.pck:', mid, m['name'], file=sys.stderr)
            continue
        stem = os.path.splitext(m['name'])[0].replace(' ', '_')
        wem = os.path.join(OUT, 'wem', m['group'], stem + '.wem')
        wav = os.path.join(OUT, 'wav', m['group'], stem + '.wav')
        os.makedirs(os.path.dirname(wem), exist_ok=True)
        os.makedirs(os.path.dirname(wav), exist_ok=True)
        with open(wem, 'wb') as f:
            f.write(blobs[mid])
        if not os.path.exists(wav):
            subprocess.run([VGMSTREAM, '-o', wav, wem], check=True, stdout=subprocess.DEVNULL)
        dur, sr, ch = wav_duration(wav)
        speaker, kind = parse_name(m['group'], m['name'])
        index.append({'id': mid, 'name': m['name'], 'banks': sorted(set(m['banks'])), 'group': m['group'],
                      'speaker': speaker, 'kind': kind, 'wav': os.path.relpath(wav, ROOT).replace(os.sep, '/'),
                      'duration': round(dur, 3), 'sr': sr, 'channels': ch})
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('plików:', len(index), 'łącznie s: %.1f' % sum(i['duration'] for i in index))


if __name__ == '__main__':
    main()
