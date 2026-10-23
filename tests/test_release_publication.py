"""Offline guard regressions: no API calls, credentials or real course data."""
import importlib.util
from pathlib import Path
import unittest

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
