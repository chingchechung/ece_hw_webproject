"""Deployment isolation and shared validator drift checks (no browser needed)."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StudentBundleTests(unittest.TestCase):
    def test_deployed_validators_are_exact_existing_shared_validators(self):
        for name in ('assignment-rules.js', 'assignment-validator.js'):
            self.assertEqual((ROOT / 'student/js' / name).read_bytes(),
                             (ROOT / 'js' / name).read_bytes())

    def test_student_bundle_contains_only_static_runtime_and_empty_allowlist(self):
        files = {str(p.relative_to(ROOT / 'student'))
                 for p in (ROOT / 'student').rglob('*') if p.is_file()}
        self.assertEqual(files, {'index.html', 'js/game.js', 'js/drive-materials.js', 'js/assignment-loader.js',
                                'js/assignment-rules.js', 'js/assignment-validator.js', 'js/rpg-renderer.js',
                                'assignments/manifest.json'})
        self.assertEqual(json.loads((ROOT / 'student/assignments/manifest.json').read_text()),
                         {'schemaVersion': 1, 'units': []})


if __name__ == '__main__':
    unittest.main()
