"""Portable browser selection and failure-evidence regression checks."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from tests.browser_support import launch_browser, save_browser_artifacts


class BrowserSupportTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch("tests.browser_support.Path.is_file", return_value=True)
    def test_default_uses_playwright_managed_browser(self, _exists):
        playwright = Mock()
        playwright.chromium.executable_path = "/managed/chromium"
        launch_browser(playwright)
        options = playwright.chromium.launch.call_args.kwargs
        self.assertNotIn("executable_path", options)
        self.assertTrue(options["headless"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("tests.browser_support.Path.is_file", return_value=False)
    @patch("tests.browser_support.shutil.which", return_value="/usr/bin/chromium")
    def test_cloud_falls_back_to_available_system_chromium(self, _which, _exists):
        playwright = Mock()
        playwright.chromium.executable_path = "/managed/chromium"
        launch_browser(playwright)
        self.assertEqual(playwright.chromium.launch.call_args.kwargs["executable_path"],
                         "/usr/bin/chromium")

    @patch.dict(os.environ, {"EMI_BROWSER_EXECUTABLE": "/custom/chromium"}, clear=True)
    @patch("tests.browser_support.Path.is_file", return_value=True)
    def test_explicit_executable_takes_priority(self, _exists):
        playwright = Mock()
        playwright.chromium.executable_path = "/managed/chromium"
        launch_browser(playwright)
        self.assertEqual(playwright.chromium.launch.call_args.kwargs["executable_path"],
                         "/custom/chromium")

    @patch.dict(os.environ, {"EMI_BROWSER_EXECUTABLE": "/missing/chromium"}, clear=True)
    @patch("tests.browser_support.Path.is_file", return_value=False)
    def test_invalid_override_fails_without_silent_fallback(self, _exists):
        with self.assertRaises(FileNotFoundError):
            launch_browser(Mock())

    @patch.dict(os.environ, {"EMI_BROWSER": "webkit"}, clear=True)
    def test_optional_webkit_has_no_chromium_specific_arguments(self):
        playwright = Mock()
        playwright.chromium.executable_path = "/managed/chromium"
        launch_browser(playwright)
        playwright.webkit.launch.assert_called_once_with(headless=True)
        playwright.chromium.launch.assert_not_called()

    @patch.dict(os.environ, {"EMI_BROWSER": "unknown"}, clear=True)
    def test_unknown_browser_is_rejected(self):
        with self.assertRaises(ValueError):
            launch_browser(Mock())

    def test_trace_and_error_log_survive_screenshot_failure(self):
        context, page = Mock(), Mock()
        page.screenshot.side_effect = RuntimeError("Synthetic closed page")
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            save_browser_artifacts(context, page, folder, "failed-test", ["Synthetic error"])
            context.tracing.stop.assert_called_once_with(path=str(folder / "failed-test.trace.zip"))
            result = json.loads((folder / "failed-test.errors.json").read_text())
            self.assertEqual(result["page_errors"], ["Synthetic error"])
            self.assertIn("Synthetic closed page", result["capture_errors"][0])
