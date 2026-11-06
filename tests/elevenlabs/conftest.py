import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'analysis', 'tools', 'elevenlabs'))

import common  # noqa: E402

KEY = 'sk_test_0123456789'


@pytest.fixture
def box(tmp_path, monkeypatch):
    """Katalog zastępczy repozytorium z kluczem testowym. Żaden test nie łączy się z siecią."""
    usage = tmp_path / 'usage'
    monkeypatch.setattr(common, 'ROOT', tmp_path)
    monkeypatch.setattr(common, 'AUDIO', tmp_path / 'audio')
    monkeypatch.setattr(common, 'USAGE', usage)
    monkeypatch.setattr(common, 'LOG', usage / 'elevenlabs.jsonl')
    monkeypatch.setattr(common, 'PENDING', usage / 'pending')
    monkeypatch.setattr(common, 'ERRORS', usage / 'errors.log')
    (tmp_path / common.KEY_FILE).write_text('# komentarz\n%s=%s\n' % (common.KEY_NAME, KEY), encoding='utf-8')

    def offline(path, key):
        raise AssertionError('test bez atrapy API: ' + path)

    monkeypatch.setattr(common, 'get_json', offline)
    return tmp_path
