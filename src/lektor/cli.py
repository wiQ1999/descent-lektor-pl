"""python -I -m lektor build | refs | report | generate | eleven | evaluate | select | finalize | audio-report | progress |
companion | bundle"""
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
    g.add_argument('--acts', type=int, nargs='*', help='tylko części gry: 1 akt 1, 2 akt 2, 3 wspólne (m3, D96)')
    e = sub.add_parser('eleven', parents=[rel], help='podejścia głosów ElevenLabs (D80, .venv, płatne; wznawialne)')
    e.add_argument('--limit', type=int)
    e.add_argument('--voices', nargs='*')
    e.add_argument('--retake', action='store_true', help='ponowne podejścia z retake.json (po select)')
    e.add_argument('--dry-run', action='store_true', help='tylko liczba podejść, znaków i szacunek kredytów')
    e.add_argument('--max-credits', type=int, help='zatrzymaj wsad przed przekroczeniem tylu kredytów')
    v = sub.add_parser('evaluate', parents=[rel], help='ocena podejść: ASR, barwa, tempo (.venv, GPU; wznawialne)')
    v.add_argument('--acts', type=int, nargs='*', help='tylko części gry: 1 akt 1, 2 akt 2, 3 wspólne (m3, D96)')
    v.add_argument('--fp32', action='store_true', help='Whisper w fp32 (szybciej na GTX 1650 Ti, więcej VRAM)')
    v.add_argument('--no-asr', action='store_true', help='szybka ocena bez Whispera (CPU) do evals_quick.jsonl (D96)')
    v.add_argument('--until', help='godzina HH:MM, po której ocena się kończy (wznowienie tą samą komendą)')
    v.add_argument('--later', nargs='*', default=(), help='grupy na koniec kolejki (np. misje rozegrane w zapisie gry)')
    sub.add_parser('select', parents=[rel], help='wybór podejść i lista ponownych (choice.json, retake.json)')
    f = sub.add_parser('finalize', parents=[rel], help='pliki końcowe, manifest i strona odsłuchu (.venv)')
    f.add_argument('--listen-engine', choices=('omnivoice', 'elevenlabs'), help='odsłuch tylko głosów tego silnika')
    q = sub.add_parser('audio-report', parents=[rel], help='raport audio (analysis/E3_AUDIO.md, M2: E7_AUDIO.md)')
    q.add_argument('--db')
    s = sub.add_parser('progress', parents=[rel], help='postęp generowania według paczek i aktów (E14; bez GPU i sieci)')
    s.add_argument('--all', action='store_true', help='wszystkie paczki, nie tylko bieżące')
    s.add_argument('--mark', help='zapisz krok skryptu generowania (run_state.json) i zakończ')
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
        synth.generate(a.limit, a.voices, os.path.join(paths.AUDIO, 'retake.json') if a.retake else None, a.acts)
    elif a.cmd == 'eleven':
        import os
        from . import eleven
        eleven.generate(a.limit, a.voices, os.path.join(paths.AUDIO, 'retake.json') if a.retake else None, a.dry_run,
                        a.max_credits)
    elif a.cmd == 'evaluate':
        from . import evaluate
        until = None
        if a.until:
            import datetime
            h, m = map(int, a.until.split(':'))
            until = datetime.datetime.now().replace(hour=h, minute=m, second=0).timestamp()
        evaluate.evaluate(a.acts, a.fp32, not a.no_asr, until, set(a.later))
    elif a.cmd == 'select':
        from . import evaluate
        evaluate.select()
    elif a.cmd == 'finalize':
        from . import finalize
        m = finalize.finalize()
        page, sample = finalize.listen(a.listen_engine)
        print('%d fragmentów; odsłuch: %d: %s' % (len(m['fragments']), sample, page))
    elif a.cmd == 'audio-report':
        from .report import audio_report
        print(paths.rel(audio_report(a.db)))
    elif a.cmd == 'progress':
        from . import progress
        if a.mark:
            progress.mark(a.mark)
        else:
            print(progress.report(a.all))
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
