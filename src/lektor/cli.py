"""python -I -m lektor build | refs | report"""
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
    a = ap.parse_args(argv)
    if a.cmd == 'build':
        from .build import build
        print(paths.rel(build(a.db)))
    elif a.cmd == 'refs':
        from . import refs
        refs.build(tuple(a.voices) or refs.VOICES)
    else:
        from .report import report
        print(paths.rel(report(a.db)))


if __name__ == '__main__':
    main()
