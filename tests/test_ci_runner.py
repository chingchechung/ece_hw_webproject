"""Exercise failure logging/continuation without a display or real course data."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests import run_ci


class CiRunnerTests(unittest.TestCase):
    def test_failed_suite_keeps_log_runs_next_suite_and_fails_summary(self):
        suites = [
            ("synthetic-failure", ["-c", "print('synthetic failure detail'); raise SystemExit(7)"]),
            ("synthetic-success", ["-c", "print('synthetic next suite ran')"]),
        ]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            with patch.object(run_ci, "RESULTS", folder), patch.object(run_ci, "SUITES", suites), \
                    patch.object(run_ci, "preflight"), redirect_stdout(io.StringIO()):
                self.assertEqual(run_ci.main(), 1)
            summary = json.loads((folder / "summary.json").read_text())
            self.assertFalse(summary["passed"])
            self.assertEqual([item["exit_code"] for item in summary["suites"]], [7, 0])
            self.assertIn("synthetic failure detail", (folder / "synthetic-failure.log").read_text())
            self.assertIn("synthetic next suite ran", (folder / "synthetic-success.log").read_text())

    def test_skipping_required_checks_is_a_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(run_ci, "RESULTS", Path(directory)), redirect_stdout(io.StringIO()):
                result = run_ci.run_suite("synthetic-skip", ["-c", "print('Ran 1 test in 0.01s\\nOK (skipped=1)')"])
            self.assertEqual(result["exit_code"], 0)
            self.assertTrue(result["skipped"])
            self.assertFalse(result["passed"])
