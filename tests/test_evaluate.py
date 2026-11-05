import pytest

from lektor import evaluate as E
from lektor.synth import seed_for, takes_for


def test_words_digits_to_cardinal():
    assert E.words('Masz 3 kości, ok?') == ['masz', 'trzy', 'kości', 'ok']


def test_clean_take():
    r = E.text_checks('Rycerz otwiera ciężkie drzwi do piwnicy.', 'Rycerz otwiera ciężkie drzwi do piwnicy')
    assert r == {'cer': 0.0, 'tail_cut': False, 'missing': 0, 'lost': 0}


def test_inflection_error_is_not_lost_fragment():
    r = E.text_checks('Rycerz otwiera ciężkie drzwi do piwnicy.', 'Rycerz otwiera ciężkich drzwi do piwnicy.')
    assert r['missing'] == 0 and not r['tail_cut'] and 0 < r['cer'] < E.MAX_CER


def test_tail_cut():
    r = E.text_checks('Rycerz otwiera ciężkie drzwi do piwnicy.', 'Rycerz otwiera ciężkie drzwi')
    assert r['tail_cut'] and r['missing'] == 2 and r['lost'] >= E.MAX_LOST


def test_lost_middle_fragment():
    r = E.text_checks('Rycerz otwiera drzwi, a za nimi czeka stary mag z latarnią.', 'Rycerz otwiera drzwi z latarnią.')
    assert r['missing'] >= 4 and r['lost'] >= E.MAX_LOST and not r['tail_cut']


def test_merged_words_are_not_lost():
    r = E.text_checks('Nie wiem, co się z nim dzieje na pewno.', 'Nie wiem, co sięz nim dzieje napewno.')
    assert r['lost'] < E.MAX_LOST


def test_short_last_word_must_match():
    assert E.tail_cut(E.words('idź do niego i'), E.words('idź do niego'))  # zgubione „i” z odsłuchu E3 (D43)
    assert not E.tail_cut(E.words('idź do niego i'), E.words('idź do niego i'))


def evals(**kw):
    base = {'chars': 60, 'voice': 'narrator', 'cer': 0.0, 'tail_cut': False, 'lost': 0, 'sim': 0.8, 'cps_ratio': 1.0,
            'speech_s': 4.0}
    return {**base, **kw}


def test_problems():
    med = {'narrator': 0.8}
    assert E.problems(evals(), med) == []
    assert E.problems(evals(cer=0.12), med) == ['cer']
    assert E.problems(evals(cer=0.12, chars=12), med) == []
    assert E.problems(evals(sim=0.7), med) == ['barwa']
    assert E.problems(evals(pause=1.5), med) == ['pauza']
    assert E.problems(evals(sim=None), med) == []
    assert E.problems(evals(sim=0.7, speech_s=2.0), med) == []
    assert E.problems(evals(speech_s=0.05, cer=1.0), med) == ['cisza']
    assert E.problems(evals(cps_ratio=2.0), med) == ['tempo']


def test_takes_and_seeds():
    assert takes_for('brynn') == 3 and takes_for('narrator') == 1 and takes_for('adelynn') == 1
    assert takes_for('ronan') == 3
    assert seed_for('0d54849ee9f32833', 1) != seed_for('0d54849ee9f32833', 2)
    assert 0 <= seed_for('ffffffffffffffff', 9) < 2 ** 31


def test_speech_cut_at_file_end_is_flagged():
    import numpy as np
    sr = 16000
    t = np.arange(sr) / sr
    tone = 0.5 * np.sin(2 * np.pi * 200 * t).astype(np.float32)
    pad = np.zeros(int(0.1 * sr), np.float32)
    fade = tone * np.clip((1 - t) * 3, 0, 1) ** 3
    level, gap = E.speech_end(np.concatenate([tone, pad]), sr)
    assert level >= E.END_RMS and gap <= E.END_GAP
    level, gap = E.speech_end(np.concatenate([fade, pad, pad]), sr)
    assert level < E.END_RMS or gap > E.END_GAP


def test_longest_pause():
    import numpy as np
    tone = np.sin(np.arange(8000) / 3).astype(np.float32)
    assert E.longest_pause(np.concatenate([tone, np.zeros(24000, np.float32), tone])) == pytest.approx(1.5, abs=0.1)
    assert E.longest_pause(tone) == 0.0
