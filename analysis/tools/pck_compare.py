"""Porównuje paczki językowe Wwise (AKPK): Polish.pck vs English/German (z bundli audio/windows/*). Tylko odczyt."""
import json, os, struct, sys, hashlib, UnityPy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'bundles')

def parse_pck(data):
    assert data[:4] == b'AKPK', data[:4]
    hdr_size, ver, lang_sz, bnk_sz, stm_sz = struct.unpack_from('<5I', data, 4)
    ext_sz = struct.unpack_from('<I', data, 24)[0]
    off = 28
    off += lang_sz
    def lut(off, size, idsize):
        n = struct.unpack_from('<I', data, off)[0]
        ent = 4 * 4 + idsize
        if n and (size - 4) // n != ent:  # dopasuj szerokość id
            idsize = 8 if idsize == 4 else 4; ent = 16 + idsize
        res = {}
        for i in range(n):
            p = off + 4 + i * ent
            fid = struct.unpack_from('<Q' if idsize == 8 else '<I', data, p)[0]
            blk, fsz, start, lang = struct.unpack_from('<4I', data, p + idsize)
            o = start * blk
            res[fid] = (fsz, hashlib.md5(data[o:o + fsz]).hexdigest())
        return res
    banks = lut(off, bnk_sz, 4); off += bnk_sz
    stm = lut(off, stm_sz, 4); off += stm_sz
    return banks, stm

def from_bundle(lang):
    m = json.load(open(os.path.join(B, 'manifest.dat'), encoding='utf-8'))
    fn = next(b['filename'] for b in m['bundleInfos'] if b['name'] == 'audio/windows/' + lang)
    for o in UnityPy.load(os.path.join(B, fn)).objects:
        if o.type.name == 'TextAsset':
            s = o.read().m_Script
            return s.encode('utf-8', 'surrogateescape') if isinstance(s, str) else bytes(s)

pl_file = open(os.path.join(ROOT, 'work', 'game', 'Legends of the Dark_Data', 'StreamingAssets', 'Audio', 'GeneratedSoundBanks', 'Windows', 'Polish.pck'), 'rb').read()
pl_bundle = from_bundle('polish')
print('Polish.pck == bundle Polish.bytes:', hashlib.md5(pl_file).hexdigest() == hashlib.md5(pl_bundle).hexdigest(), len(pl_file), len(pl_bundle))
P = parse_pck(pl_bundle)
for lang in ('english', 'german', 'hungarian'):
    X = parse_pck(from_bundle(lang))
    for name, a, b in (('banks', P[0], X[0]), ('streamed', P[1], X[1])):
        common = set(a) & set(b)
        same = sum(1 for k in common if a[k][1] == b[k][1])
        print(lang, name, 'PL', len(a), lang[:2], len(b), 'wspólne id', len(common), 'identyczne', same)

def bank_media(data, banks_lut_raw):
    """Zwraca {media_id: md5} z sekcji DIDX/DATA wszystkich banków w paczce."""
    out = {}
    for fid, (fsz, _h, o) in banks_lut_raw.items():
        b = data[o:o + fsz]; p = 0; didx = []; dpos = None
        while p + 8 <= len(b):
            tag, size = b[p:p + 4], struct.unpack_from('<I', b, p + 4)[0]
            if tag == b'DIDX':
                didx = [struct.unpack_from('<3I', b, p + 8 + i * 12) for i in range(size // 12)]
            elif tag == b'DATA':
                dpos = p + 8
            p += 8 + size
        for mid, mo, ms in didx:
            out[mid] = hashlib.md5(b[dpos + mo:dpos + mo + ms]).hexdigest()
    return out

def banks_raw(data):
    hdr_size, ver, lang_sz, bnk_sz, stm_sz = struct.unpack_from('<5I', data, 4)
    off = 28 + lang_sz
    n = struct.unpack_from('<I', data, off)[0]; res = {}
    for i in range(n):
        fid, blk, fsz, start, lang = struct.unpack_from('<5I', data, off + 4 + i * 20)
        res[fid] = (fsz, None, start * blk)
    return res

PM = bank_media(pl_bundle, banks_raw(pl_bundle))
for lang in ('english', 'german', 'hungarian', 'french'):
    d = from_bundle(lang); XM = bank_media(d, banks_raw(d))
    common = set(PM) & set(XM)
    print('media', lang, 'PL', len(PM), lang[:2], len(XM), 'wspólne', len(common), 'identyczne z PL', sum(PM[k] == XM[k] for k in common))

print('--- porównanie po zawartości (md5), niezależnie od id')
pset = set(PM.values())
for lang in ('english', 'hungarian', 'korean', 'german', 'french', 'spanish'):
    d = from_bundle(lang); XM = bank_media(d, banks_raw(d)); xs = set(XM.values())
    print(lang, 'plików', len(xs), 'identycznych z PL', len(pset & xs))
d = from_bundle('english'); EM = set(bank_media(d, banks_raw(d)).values())
d = from_bundle('hungarian'); HM = set(bank_media(d, banks_raw(d)).values())
print('EN vs HU identycznych', len(EM & HM), 'z', len(EM))
