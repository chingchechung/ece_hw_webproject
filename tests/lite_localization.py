"""Reverse the explicit UI edit ledger, retaining exact historical logic checks."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'tests/fixtures/lite-english-ui.json'


def historical_source(file):
    source = (ROOT / file).read_text(encoding='utf-8')
    for edit in reversed(json.loads(LEDGER.read_text(encoding='utf-8'))[file]):
        for offset in reversed(edit['offsets']):
            after = edit['after']
            if source[offset:offset + len(after)] != after:
                raise AssertionError(f'Unrecorded localization edit: {file}:{offset}')
            source = source[:offset] + edit['before'] + source[offset + len(after):]
    return source
