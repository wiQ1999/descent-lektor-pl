"""Porównanie buildu macOS (depot 1611072) z kopią Windows. Tylko odczyt; wynik bez tekstów gry.

Sprawdza:
  - backend skryptów (Data/Managed/Assembly-CSharp.dll vs GameAssembly.dylib + global-metadata.dat),
  - architekturę głównego pliku Mach-O (lief), wersję Unity z nagłówków bundli UnityFS,
  - podpis i entitlements (rcodesign print-signature-info),
  - Assembly-CSharp: hash, a po dekompilacji (ILSpy) sygnatury MessageController, StoryMessageController, MasterMessageCache,
  - manifest.dat (wersja, lista bundli), teksty loc/pl + qloc per klucz,
  - polskie audio Wwise (audio/mac/polish vs audio/windows/polish) po md5 mediów.

Wejście: work/mac_depot/ (DepotDownloader), work/game/ (kopia Windows), work/decompiled/Assembly-CSharp (Windows).
Wyjście: work/out/mac_compare.json (+ dekompilacja macOS w work/decompiled_mac/).

Uruchomienie (z katalogu głównego repozytorium):
  .venv/Scripts/python -I analysis/tools/mac_compare.py [--ilspy <ścieżka do ilspycmd.exe>]
"""
import argparse
import glob
import hashlib
import json
import os
import plistlib
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
MAC = os.path.join(ROOT, 'work', 'mac_depot')
WIN_DATA = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data')
WIN_DECOMP = os.path.join(ROOT, 'work', 'decompiled', 'Assembly-CSharp')
MAC_DECOMP = os.path.join(ROOT, 'work', 'decompiled_mac')
RCODESIGN = os.path.join(ROOT, 'work', 'bin', 'rcodesign-0.29.0', 'apple-codesign-0.29.0-x86_64-pc-windows-msvc', 'rcodesign.exe')
CLASSES = ('MessageController', 'StoryMessageController', 'MasterMessageCache')
ENTITLEMENTS = ('com.apple.security.cs.disable-library-validation', 'com.apple.security.cs.allow-dyld-environment-variables',
                'com.apple.security.cs.allow-jit', 'com.apple.security.cs.allow-unsigned-executable-memory',
                'com.apple.security.get-task-allow')


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def find_app():
    apps = glob.glob(os.path.join(MAC, '**', '*.app'), recursive=True)
    return apps[0] if apps else None


def macho_info(path):
    import lief
    fat = lief.MachO.parse(path)
    archs = []
    for b in fat:
        archs.append({'cpu': str(b.header.cpu_type).split('.')[-1], 'filetype': str(b.header.file_type).split('.')[-1],
                      'min_os': '.'.join(map(str, b.version_min.version)) if b.has_version_min else None,
                      'build_version': '.'.join(map(str, b.build_version.minos)) if b.has_build_version else None,
                      'has_code_signature': b.has_code_signature,
                      'dylibs': [l.name for l in b.libraries][:40]})
    return {'universal': len(archs) > 1, 'archs': archs}


def unity_version(data_dir):
    for p in glob.glob(os.path.join(data_dir, 'StreamingAssets', 'bundles', '*'))[:20]:
        with open(p, 'rb') as f:
            head = f.read(64)
        m = re.search(rb'\d{4}\.\d+\.\d+[abfp]\d+', head) if head.startswith(b'UnityFS') else None
        if m:
            return m.group(0).decode()
    return None


def entitlements_plist(text):
    """rcodesign wypisuje plist entitlements jako listę YAML (`- '<key>…'`) — składa ją z powrotem w XML."""
    lines, inside = [], False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith('entitlements_plist:'):
            inside, lines = True, []
            continue
        if inside:
            if not s.startswith('- '):
                break
            item = s[2:]
            if len(item) > 1 and item[0] == item[-1] == "'":
                item = item[1:-1].replace("''", "'")
            lines.append(item)
            if item.strip() == '</plist>':
                break
    return '\n'.join(lines) if lines else None


def signature(path):
    if not os.path.exists(RCODESIGN):
        return {'error': 'brak rcodesign'}
    out = subprocess.run([RCODESIGN, 'print-signature-info', path], capture_output=True, text=True, encoding='utf-8', errors='replace')
    text = out.stdout + out.stderr
    res = {'raw_excerpt': text[:6000], 'returncode': out.returncode}
    res['hardened_runtime'] = 'CodeSignatureFlags(RUNTIME' in text
    res['flags'] = sorted(set(re.findall(r'flags:\s*(CodeSignatureFlags\(.*?\))', text)))
    res['runtime_version'] = sorted(set(re.findall(r'runtime_version:\s*(\S+)', text)))
    ents = {}
    plist = entitlements_plist(text)
    if plist:
        try:
            ents = plistlib.loads(plist.encode())
        except Exception as e:
            res['entitlements_error'] = str(e)
    res['entitlements'] = {k: ents.get(k) for k in ENTITLEMENTS}
    res['entitlements_all'] = sorted(ents)
    res['team_id'] = sorted(set(re.findall(r'team_name:\s*(\S+)', text)))
    return res


def decompile(ilspy, dll, out_dir):
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        return True
    os.makedirs(out_dir, exist_ok=True)
    r = subprocess.run([ilspy, '-p', '-o', out_dir, dll], capture_output=True, text=True)
    return r.returncode == 0


def members(cs_path):
    """Sygnatury publicznych/chronionych/prywatnych członków klasy (linie deklaracji) — do porównania."""
    if not os.path.exists(cs_path):
        return None
    sig = []
    for line in open(cs_path, encoding='utf-8', errors='replace'):
        s = line.strip()
        if re.match(r'(public|private|protected|internal)\b.*(\(|\bevent\b|=>|;|\{ get|\bdelegate\b)', s) and not s.startswith('//'):
            sig.append(re.sub(r'\s+', ' ', s))
    return sig


def find_cs(root, cls):
    hits = [p for p in glob.glob(os.path.join(root, '**', cls + '.cs'), recursive=True)]
    return hits[0] if hits else None


def compare_texts(mac_bundles):
    import extract_lines as X
    win_terms = json.load(open(os.path.join(ROOT, 'work', 'out', 'pl_terms.json'), encoding='utf-8'))
    X.BUNDLES = mac_bundles
    mac_terms = X.load_pl_terms(X.load_manifest())
    wk, mk = set(win_terms), set(mac_terms)
    changed = [k for k in wk & mk if (win_terms[k]['text'] or '') != (mac_terms[k]['text'] or '')]
    return {'keys_win': len(wk), 'keys_mac': len(mk), 'only_win': sorted(wk - mk)[:50], 'only_mac': sorted(mk - wk)[:50],
            'n_only_win': len(wk - mk), 'n_only_mac': len(mk - wk), 'n_text_diff': len(changed), 'text_diff_keys': sorted(changed)[:50]}


def polish_media(bundles_dir, name):
    """Media polskiego pakietu Wwise (TextAsset w bundlu audio/<platforma>/polish) → {id: md5}."""
    import UnityPy
    import extract_voices as EV
    m = json.load(open(os.path.join(bundles_dir, 'manifest.dat'), encoding='utf-8'))
    fn = next((b['filename'] for b in m['bundleInfos'] if b['name'] == name), None)
    if not fn:
        return None, None
    for o in UnityPy.load(os.path.join(bundles_dir, fn)).objects:
        if o.type.name == 'TextAsset':
            s = o.read().m_Script
            d = s.encode('utf-8', 'surrogateescape') if isinstance(s, str) else bytes(s)
            media = {}
            for bnk in EV.pck_banks(d):
                media.update(EV.bank_media(bnk))
            return d, {k: hashlib.md5(v).hexdigest() for k, v in media.items()}
    return None, None


def compare_audio(mac_bundles, win_bundles):
    md, mm = polish_media(mac_bundles, 'audio/mac/polish')
    wd, wm = polish_media(win_bundles, 'audio/windows/polish')
    if mm is None or wm is None:
        return {'error': 'brak bundla audio/*/polish'}
    common = set(mm) & set(wm)
    return {'pck_bytes_mac': len(md), 'pck_bytes_win': len(wd), 'pck_identical': md == wd,
            'media_mac': len(mm), 'media_win': len(wm), 'media_common': len(common),
            'media_identical': sum(mm[k] == wm[k] for k in common)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ilspy', default=None)
    a = ap.parse_args()
    app = find_app()
    res = {'app': os.path.relpath(app, ROOT) if app else None}
    if not app:
        print('brak .app w', MAC)
        return
    info = plistlib.load(open(os.path.join(app, 'Contents', 'Info.plist'), 'rb'))
    res['info_plist'] = {k: info.get(k) for k in ('CFBundleExecutable', 'CFBundleIdentifier', 'CFBundleShortVersionString',
                                                  'CFBundleVersion', 'LSMinimumSystemVersion', 'LSArchitecturePriority')}
    exe = os.path.join(app, 'Contents', 'MacOS', info['CFBundleExecutable'])
    data = os.path.join(app, 'Contents', 'Resources', 'Data')
    res['backend'] = {
        'managed_assembly_csharp': os.path.exists(os.path.join(data, 'Managed', 'Assembly-CSharp.dll')),
        'game_assembly_dylib': bool(glob.glob(os.path.join(app, 'Contents', '**', 'GameAssembly.dylib'), recursive=True)),
        'global_metadata': bool(glob.glob(os.path.join(data, '**', 'global-metadata.dat'), recursive=True)),
        'mono_dylib': [os.path.relpath(p, app) for p in glob.glob(os.path.join(app, 'Contents', '**', 'libmono*.dylib'), recursive=True)],
        'frameworks': sorted(os.path.basename(p) for p in glob.glob(os.path.join(app, 'Contents', 'Frameworks', '*'))),
    }
    res['macho'] = macho_info(exe)
    res['unity_version'] = unity_version(data)
    res['unity_version_windows'] = unity_version(WIN_DATA)
    res['signature_app'] = signature(app)
    res['signature_exe'] = signature(exe)
    mac_dll = os.path.join(data, 'Managed', 'Assembly-CSharp.dll')
    win_dll = os.path.join(WIN_DATA, 'Managed', 'Assembly-CSharp.dll')
    if os.path.exists(mac_dll):
        res['assembly_md5'] = {'mac': md5(mac_dll), 'win': md5(win_dll) if os.path.exists(win_dll) else None}
        if a.ilspy and decompile(a.ilspy, mac_dll, MAC_DECOMP):
            cmp = {}
            for cls in CLASSES:
                wm, mm = members(find_cs(WIN_DECOMP, cls) or ''), members(find_cs(MAC_DECOMP, cls) or '')
                cmp[cls] = {'win_members': len(wm or []), 'mac_members': len(mm or []),
                            'only_win': sorted(set(wm or []) - set(mm or [])), 'only_mac': sorted(set(mm or []) - set(wm or [])),
                            'file_identical': (wm is not None and mm is not None and
                                               open(find_cs(WIN_DECOMP, cls), encoding='utf-8').read() == open(find_cs(MAC_DECOMP, cls), encoding='utf-8').read())}
            res['classes'] = cmp
    mb = os.path.join(data, 'StreamingAssets', 'bundles')
    mm = json.load(open(os.path.join(mb, 'manifest.dat'), encoding='utf-8'))
    wm = json.load(open(os.path.join(WIN_DATA, 'StreamingAssets', 'bundles', 'manifest.dat'), encoding='utf-8'))
    wn = {b['name']: b for b in wm['bundleInfos']}
    mn = {b['name']: b for b in mm['bundleInfos']}
    res['manifest'] = {'version_mac': mm.get('version'), 'version_win': wm.get('version'),
                       'bundles_mac': len(mn), 'bundles_win': len(wn),
                       'only_mac': sorted(set(mn) - set(wn)), 'only_win': sorted(set(wn) - set(mn)),
                       'text_bundles_same_name': sorted(n for n in mn if n.startswith(('loc/', 'qloc/', 'localization')))[:5]}
    res['texts'] = compare_texts(mb)
    res['audio_polish'] = compare_audio(mb, os.path.join(WIN_DATA, 'StreamingAssets', 'bundles'))
    json.dump(res, open(os.path.join(ROOT, 'work', 'out', 'mac_compare.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k not in ('signature_app', 'signature_exe')}, ensure_ascii=False, indent=1)[:6000])


if __name__ == '__main__':
    main()
