"""Optional real-browser validation of classic scripts served over local HTTP."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.contract_cases import contract_cases
from tests.contract_cases_v2 import answer_cases
from tools.assignment_data import normalize_manifest, normalize_unit, validate_manifest, validate_unit


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserValidationTests(unittest.TestCase):
    def test_classic_browser_scripts_match_python_corpus(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=ROOT))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
                try:
                    page = browser.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    base = f"http://127.0.0.1:{server.server_port}"
                    page.goto(base + "/emi_maze_dualview_v1.2/index.html")
                    page.add_script_tag(url=base + "/js/assignment-rules.js")
                    page.add_script_tag(url=base + "/js/assignment-validator.js")
                    cases = contract_cases()
                    results = page.evaluate("""cases => cases.map(item => ({
                      errors: item.kind === 'unit'
                        ? AssignmentValidator.validateUnit(item.data, item.filename)
                        : AssignmentValidator.validateManifest(item.data),
                      normalized: item.kind === 'unit'
                        ? AssignmentValidator.normalizeUnit(item.data)
                        : AssignmentValidator.normalizeManifest(item.data)
                    }))""", cases)
                    for case, result in zip(cases, results, strict=True):
                        with self.subTest(case=case["name"]):
                            unit = case["kind"] == "unit"
                            issues = validate_unit(case["data"], case["filename"]) if unit else validate_manifest(case["data"])
                            normalized = normalize_unit(case["data"]) if unit else normalize_manifest(case["data"])
                            self.assertEqual(result, {"errors": [e.as_dict() for e in issues], "normalized": normalized})
                            self.assertEqual(not result["errors"], case["valid"])
                    answers = answer_cases()
                    actual = page.evaluate("items=>items.map(item=>AssignmentValidator.acceptsAnswer(item.question,item.selected))", answers)
                    self.assertEqual(actual, [item["expected"] for item in answers])
                    v1 = next(item["data"] for item in cases if item["kind"] == "unit" and item["valid"] and item["data"]["schemaVersion"] == 1)
                    v2 = next(item["data"] for item in cases if item["kind"] == "unit" and item["valid"] and item["data"]["schemaVersion"] == 2)
                    strict = page.evaluate("""([v1,v2]) => [
                      AssignmentValidator.validateUnitV1(v1).length === 0,
                      AssignmentValidator.validateUnitV1(v2).length > 0,
                      AssignmentValidator.validateUnitV2(v2).length === 0,
                      AssignmentValidator.validateUnitV2(v1).length > 0]""", [v1, v2])
                    self.assertEqual(strict, [True]*4)
                    self.assertEqual(errors, [])
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main(verbosity=2)
