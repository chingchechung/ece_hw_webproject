"""Offline guard regressions: no API calls, credentials or real course data."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile
import hashlib
import json
import shutil

spec = importlib.util.spec_from_file_location('release_publish',
    Path(__file__).resolve().parents[1] / 'release/publish.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class ReleasePublicationTests(unittest.TestCase):
    def test_main_ci_requires_exact_sha_push_branch_and_complete_success(self):
        valid = dict(head_sha='synthetic-sha', head_branch='main', event='push',
                     status='completed', conclusion='success')
        self.assertEqual(publisher.verified_run([valid], 'synthetic-sha'), valid)
        for field, value in [('head_sha', 'other'), ('head_branch', 'feature/3d-showcase'),
                             ('event', 'pull_request'), ('status', 'in_progress'),
                             ('conclusion', 'failure')]:
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                publisher.verified_run([{**valid, field: value}], 'synthetic-sha')

    def test_all_three_jobs_must_finish_successfully(self):
        jobs = [dict(name=name, status='completed', conclusion='success',
                     steps=[dict(conclusion='success')]) for name in publisher.JOBS]
        publisher.verify_jobs(jobs)
        with self.assertRaises(RuntimeError):
            publisher.verify_jobs(jobs[:-1])
        for replacement in [dict(status='in_progress'), dict(conclusion='failure'),
                            dict(steps=[dict(conclusion='failure')])]:
            with self.subTest(replacement=replacement), self.assertRaises(RuntimeError):
                publisher.verify_jobs([{**jobs[0], **replacement}, *jobs[1:]])

    def test_exact_uploaded_asset_inventory_size_and_sha256(self):
        expected = {'synthetic.zip': (123, 'synthetic-sha256')}
        asset = dict(name='synthetic.zip', size=123, state='uploaded',
                     digest='sha256:synthetic-sha256')
        publisher.verify_assets([asset], expected)
        for replacement in [dict(name='other.zip'), dict(size=124),
                            dict(state='new'), dict(digest='sha256:other')]:
            with self.subTest(replacement=replacement), self.assertRaises(RuntimeError):
                publisher.verify_assets([{**asset, **replacement}], expected)
        with self.assertRaises(RuntimeError):
            publisher.verify_assets([asset, asset], expected)

    def test_publication_draft_id_lookup_download_verification_and_final_stable_state(self):
        # Exercise the whole publisher offline. The mock deliberately rejects tag
        # lookup before publication, matching GitHub's published-only endpoint.
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('release', 'student/assignments', 'showcase3d/dist/assignments',
                         'test-results/unified-release', 'test-results/3d-p2.1'):
                (root / name).mkdir(parents=True)
            (root / 'release/version.json').write_text(json.dumps({'version': '1.0.0',
                'editions': {'lite': '1.0.0', '3d': '1.0.0'}}))
            for name in ('student', 'showcase3d/dist'):
                (root / name / 'assignments/manifest.json').write_text(
                    json.dumps({'schemaVersion': 1, 'units': []}))
            paths = [root / 'test-results/unified-release/Engineering-Maze-Lab-1.0.0.zip',
                     root / 'test-results/3d-p2.1/showcase3d-1.0.0-static.zip']
            for index, path in enumerate(paths):
                path.write_bytes(f'synthetic mocked packager output {index}'.encode())
            assets = [dict(name=p.name, size=p.stat().st_size, state='uploaded',
                digest='sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
            jobs = [dict(name=name, status='completed', conclusion='success', steps=[])
                    for name in publisher.JOBS]
            sha = 'synthetic-verified-sha'
            run = dict(id=42, head_sha=sha, head_branch='main', event='push',
                       status='completed', conclusion='success', html_url='https://example.invalid/ci')
            state = {'created': False, 'published': False, 'downloaded': False}

            def command(*args):
                if args == ('git', 'cat-file', '-t', 'v1.0.0'):
                    return 'tag'
                if args[:2] == ('git', 'rev-parse'):
                    return sha
                if args[:3] == ('gh', 'api', '--paginate'):
                    return json.dumps([[dict(id=123, tag_name='v1.0.0', draft=True)]]
                        if state['created'] else [[]])
                if args[:2] == ('python', 'release/package.py') or args[:2] == (
                        'python', 'showcase3d/scripts/package.py'):
                    return ''
                if args[:3] == ('gh', 'release', 'create'):
                    self.assertFalse(state['created']); self.assertIn('--draft', args)
                    self.assertIn('--verify-tag', args); state['created'] = True
                    return 'https://example.invalid/draft'
                if args[:3] == ('gh', 'release', 'download'):
                    self.assertTrue(state['created']); self.assertFalse(state['published'])
                    destination = Path(args[args.index('--dir') + 1])
                    for path in paths:
                        shutil.copyfile(path, destination / path.name)
                    state['downloaded'] = True
                    return ''
                if args[:3] == ('gh', 'release', 'edit'):
                    self.assertTrue(state['downloaded']); self.assertIn('--draft=false', args)
                    self.assertIn('--prerelease=false', args); state['published'] = True
                    return ''
                raise AssertionError(f'Unexpected command: {args}')

            def api(path):
                if path == 'git/ref/heads/main':
                    return {'object': {'sha': sha}}
                if path.startswith('actions/workflows/showcase3d.yml/runs?'):
                    return {'workflow_runs': [run]}
                if path == 'actions/runs/42/jobs?per_page=100':
                    return {'jobs': jobs}
                if path == 'releases/123':
                    self.assertTrue(state['created']); self.assertFalse(state['published'])
                    return {'assets': assets, 'draft': True}
                if path == 'releases/tags/v1.0.0':
                    self.assertTrue(state['published'], 'Tag lookup cannot fetch a draft')
                    return {'assets': assets, 'draft': False, 'prerelease': False,
                            'html_url': 'https://example.invalid/release'}
                raise AssertionError(f'Unexpected API call: {path}')

            with patch.object(publisher, 'ROOT', root), patch.object(publisher, 'command', command), \
                    patch.object(publisher, 'api', api):
                publisher.publish()
            result = json.loads((root / 'test-results/release/verification.json').read_text())
            self.assertEqual(result['commit'], sha)
            self.assertEqual(len(result['assets']), 2)
            self.assertTrue(state['published'])
