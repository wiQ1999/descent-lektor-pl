"""python -I -m lektor build | refs | report | generate | evaluate | select | finalize | audio-report | companion"""
import argparse
import sys

from . import paths


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(prog='lektor')
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build', help='baza kwestii M1 z kopii gry (SQLite)')
    b.add_argument('--db', default=paths.DB)
    r = sub.add_parser('refs', help='referencje głosów do 10 s z transkrypcją (Whisper, GPU)')
    r.add_argument('voices', nargs='*')
    p = sub.add_parser('report', help='raport liczności analysis/E2_DATA.md')
    p.add_argument('--db', default=paths.DB)
    g = sub.add_parser('generate', help='podejścia fragmentów w OmniVoice (środowisko OmniVoice, GPU; wznawialne)')
    g.add_argument('--limit', type=int)
    g.add_argument('--voices', nargs='*')
    g.add_argument('--retake', action='store_true', help='ponowne podejścia z retake.json (po select)')
    sub.add_parser('evaluate', help='ocena podejść: ASR, barwa, tempo (.venv, GPU; wznawialne)')
    sub.add_parser('select', help='wybór podejść i lista ponownych (choice.json, retake.json)')
    sub.add_parser('finalize', help='pliki końcowe, manifest i strona odsłuchu (.venv)')
    q = sub.add_parser('audio-report', help='raport analysis/E3_AUDIO.md')
    q.add_argument('--db', default=paths.DB)
    c = sub.add_parser('companion', help='companion lektora (serwer TCP dla pluginu) albo replay dziennika E1')
    from .companion.app import add_args
    add_args(c)
    a = ap.parse_args(argv)
    if a.cmd == 'build':
        from .build import build
        print(paths.rel(build(a.db)))
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
    else:
        from .report import report
        print(paths.rel(report(a.db)))


if __name__ == '__main__':
    main()
