"""python -I -m lektor build | refs | report | generate | evaluate | select | finalize | audio-report | companion | bundle"""
import argparse
import sys

from . import paths


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(prog='lektor')
    sub = ap.add_subparsers(dest='cmd', required=True)
    rel = argparse.ArgumentParser(add_help=False)
    rel.add_argument('--release', choices=paths.RELEASES, default='m1', help='wydanie: baza i katalog audio')
    b = sub.add_parser('build', parents=[rel], help='baza kwestii wydania z kopii gry (SQLite)')
    b.add_argument('--db')
    b.add_argument('--only', nargs='*', help='tylko te grupy spoza M1 (np. event_e5b map)')
    r = sub.add_parser('refs', help='referencje głosów do 10 s z transkrypcją (Whisper, GPU)')
    r.add_argument('voices', nargs='*')
    p = sub.add_parser('report', parents=[rel], help='raport liczności (analysis/E2_DATA.md, M2: E7_DATA.md)')
    p.add_argument('--db')
    g = sub.add_parser('generate', parents=[rel], help='podejścia fragmentów w OmniVoice (środowisko OmniVoice, GPU; wznawialne)')
    g.add_argument('--limit', type=int)
    g.add_argument('--voices', nargs='*')
    g.add_argument('--retake', action='store_true', help='ponowne podejścia z retake.json (po select)')
    sub.add_parser('evaluate', parents=[rel], help='ocena podejść: ASR, barwa, tempo (.venv, GPU; wznawialne)')
    sub.add_parser('select', parents=[rel], help='wybór podejść i lista ponownych (choice.json, retake.json)')
    sub.add_parser('finalize', parents=[rel], help='pliki końcowe, manifest i strona odsłuchu (.venv)')
    q = sub.add_parser('audio-report', parents=[rel], help='raport audio (analysis/E3_AUDIO.md, M2: E7_AUDIO.md)')
    q.add_argument('--db')
    c = sub.add_parser('companion', help='companion lektora (serwer TCP dla pluginu) albo replay dziennika E1')
    from .companion.app import add_args
    add_args(c)
    k = sub.add_parser('bundle', parents=[rel], help='folder paczki Descent-Lektor-PL (E6) w analysis/work/')
    k.add_argument('--platform', choices=('win', 'mac'), default='win')
    k.add_argument('--dev', action='store_true', help='analysis/work/dev-bundle z Pythonem z .venv (test W1)')
    k.add_argument('--out', help='katalog docelowy')
    a = ap.parse_args(argv)
    paths.use(getattr(a, 'release', 'm1'))
    if a.cmd == 'build':
        from .build import build
        print(paths.rel(build(a.db, a.release, a.only)))
    elif a.cmd == 'refs':
        from . import refs
        refs.build(tuple(a.voices) or refs.VOICES)
    elif a.cmd == 'generate':
        import os
        from . import synth
        synth.generate(a.limit, a.voices, os.path.join(paths.AUDIO, 'retake.json') if a.retake else None)
    elif a.cmd == 'evaluate':
        from . import evaluate
        evaluate.evaluate()
    elif a.cmd == 'select':
        from . import evaluate
        evaluate.select()
    elif a.cmd == 'finalize':
        from . import finalize
        m = finalize.finalize()
        page, bad, sample = finalize.listen()
        print('%d fragmentów; odsłuch: %d odrzuconych + %d losowych: %s' % (len(m['fragments']), bad, sample, paths.rel(page)))
    elif a.cmd == 'audio-report':
        from .report import audio_report
        print(paths.rel(audio_report(a.db)))
    elif a.cmd == 'companion':
        from .companion import app
        app.main(a)
    elif a.cmd == 'bundle':
        from .bundle import build
        print(build(a.platform, a.dev, a.out))
    else:
        from .report import report
        print(paths.rel(report(a.db)))


if __name__ == '__main__':
    main()
