"""Release privacy, reproducibility and exact UI-only preservation checks."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from zipfile import ZipFile

from tests.lite_localization import historical_source

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('unified_package', ROOT / 'release/package.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class UnifiedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('student', 'showcase3d/dist', 'release'):
            shutil.copytree(ROOT / folder, self.root / folder)

    def test_ui_ledger_recovers_all_historical_bytes_and_no_chinese_ui_remains(self):
        manifest = json.loads((ROOT / 'showcase3d/tests/lite-baseline.json').read_text())
        for file in json.loads((ROOT / 'tests/fixtures/lite-english-ui.json').read_text()):
            self.assertEqual(hashlib.sha256(historical_source(file).encode()).hexdigest(), manifest[file])
            self.assertIsNone(re.search(r'[\u3400-\u9fff]', (ROOT / file).read_text()))
        html = (ROOT / 'student/index.html').read_text()
        self.assertIn('<html lang="en">', html)
        self.assertNotIn('<span class="tag">', html)

    def test_repeated_package_bytes_contents_hashes_and_component_versions(self):
        first = packager.package(self.root, self.root / 'first.zip')
        # Filesystem timestamp changes must not change archive bytes.
        import os
        for p in (self.root / 'student').rglob('*'):
            os.utime(p, (1700000000, 1700000000))
        second = packager.package(self.root, self.root / 'second.zip')
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with ZipFile(first) as z:
            prefix = 'Engineering-Maze-Lab/'
            files = {n.removeprefix(prefix): z.read(n) for n in z.namelist()}
            info = json.loads(files.pop('release-info.json'))
            self.assertEqual(info['editions'], {'lite': info['version'], '3d': info['version']})
            self.assertEqual(info['files'], {n: packager.digest(b) for n, b in files.items()})
            self.assertEqual(len(files), 15)
            for edition in ('lite', '3d'):
                self.assertEqual(json.loads(files[f'{edition}/assignments/manifest.json']),
                                 {'schemaVersion': 1, 'units': []})
            self.assertEqual({i.date_time for i in z.infolist()}, {(1980, 1, 1, 0, 0, 0)})

    def test_unlisted_private_file_and_nonempty_manifests_fail_without_modifying_inputs(self):
        for folder in ('student', 'showcase3d/dist'):
            assignment = self.root / folder / 'assignments'
            private = assignment / 'S01.draft.json'
            private.write_text('{"private":"synthetic negative fixture only"}')
            with self.assertRaisesRegex(ValueError, 'Unexpected or missing'):
                packager.package(self.root)
            private.unlink()
            manifest = assignment / 'manifest.json'
            original = manifest.read_bytes()
            data = b'{"schemaVersion":1,"units":[{"unitId":"S01"}]}'
            manifest.write_bytes(data)
            with self.assertRaisesRegex(ValueError, 'empty manifest'):
                packager.package(self.root)
            self.assertEqual(manifest.read_bytes(), data)
            manifest.write_bytes(original)

    def test_symlink_and_changed_build_are_rejected(self):
        secret = self.root / 'outside.txt'
        secret.write_text('synthetic outside-runtime sentinel')
        link = self.root / 'student/js/game.js'
        original = link.read_bytes()
        link.unlink()
        link.symlink_to(secret)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            packager.package(self.root)
        link.unlink()
        link.write_bytes(original)
        (self.root / 'showcase3d/dist/index.html').write_text('synthetic modified build')
        with self.assertRaisesRegex(ValueError, 'runtime hash'):
            packager.package(self.root)

    def test_mismatched_versions_and_traversal_build_paths_are_rejected(self):
        file = self.root / 'release/version.json'
        data = json.loads(file.read_text())
        data['editions']['lite'] = '2.0.0-rc1'
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'share the unified'):
            packager.package(self.root)
        shutil.copyfile(ROOT / 'release/version.json', file)
        file = self.root / 'showcase3d/dist/build-info.json'
        data = json.loads(file.read_text())
        data['files']['../private.json'] = 'synthetic'
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'build file list'):
            packager.package(self.root)
