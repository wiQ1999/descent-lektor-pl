import json
import os

import numpy as np
import soundfile as sf

from lektor import direction as D
from lektor import finalize, paths

SR = 24000


def make_take(audio, fid):
    t = np.arange(SR) / SR
    y = (0.2 * np.sin(2 * np.pi * 150 * t) * np.sin(np.pi * t)).astype(np.float32)
    os.makedirs(audio / 'takes', exist_ok=True)
    sf.write(audio / 'takes' / ('%s_t1.wav' % fid), y, SR)


def write_choice(audio, voices):
    choice = {fid: {'take': 1, 'voice': v, 'speed': None, 'problems': []} for fid, v in voices.items()}
    (audio / 'choice.json').write_text(json.dumps(choice), encoding='utf-8')


def test_voice_effect_is_baked_and_rebuilt_when_changed(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'AUDIO', str(tmp_path))
    monkeypatch.setattr(D, 'FX', {'ghost': 'ghost_c2'})
    for fid in ('a', 'b'):
        make_take(tmp_path, fid)
    write_choice(tmp_path, {'a': 'ghost', 'b': 'plain'})
    m = finalize.finalize()['fragments']
    assert m['a']['fx'] == 'ghost_c2'
    assert 'fx' not in m['b']
    assert m['a']['seconds'] > m['b']['seconds']        # ogon i narastanie efektu
    plain_mtime = os.path.getmtime(tmp_path / 'final' / 'b.wav')

    monkeypatch.setattr(D, 'FX', {'ghost': 'ghost_b2'})
    m = finalize.finalize()['fragments']
    assert m['a']['fx'] == 'ghost_b2'
    assert os.path.getmtime(tmp_path / 'final' / 'b.wav') == plain_mtime    # głos bez efektu bez zmian

    monkeypatch.setattr(D, 'FX', {})
    m = finalize.finalize()['fragments']
    assert 'fx' not in m['a']
