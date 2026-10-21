"""Run all required suites, preserving failure logs and continuing after failures.

Run under a desktop display or xvfb-run. Only synthetic tests generate artifacts;
this runner never reads private teacher_data/ or export/ directories.
"""
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "test-results/ci"
SUITES = [
    ("python", ["-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("gui", ["tests/gui_smoke.py"]),
    ("browser-baseline", ["tests/browser_baseline.py"]),
    ("browser-validation", ["tests/browser_validation.py"]),
    ("browser-student", ["tests/browser_student.py"]),
    ("browser-gameplay", ["tests/browser_gameplay.py"]),
    ("browser-visuals", ["tests/browser_visuals.py"]),
    ("browser-refinement", ["tests/browser_refinement.py"]),
    ("browser-atmosphere", ["tests/browser_atmosphere.py"]),
    ("browser-slash", ["tests/browser_slash.py"]),
    ("assignment-cli", ["tools/validate_assignments.py", "tests/fixtures/manifest.json",
                        "tests/fixtures/v2/manifest.json", "assignments/manifest.json",
                        "student/assignments/manifest.json"]),
]


def preflight():
    for module in ("jsonschema", "playwright.sync_api", "tkinter", "PIL.ImageGrab"):
        importlib.import_module(module)
    if not shutil.which("node"):
        raise RuntimeError("Node is required for Python/JavaScript parity tests")
    import tkinter
    root = tkinter.Tk()
    root.withdraw()
    root.destroy()


def run_suite(name, arguments):
    command = [sys.executable, *arguments]
    started = time.monotonic()
    output = []
    print(f"\nRunning {name}", flush=True)
    with (RESULTS / f"{name}.log").open("w", encoding="utf-8") as log:
        try:
            with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                  env={**os.environ, "PYTHONUNBUFFERED": "1"}) as process:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    log.write(line)
                    output.append(line)
                exit_code = process.wait()
        except OSError as error:
            log.write(str(error))
            exit_code = 1
    combined = "".join(output)
    counts = re.findall(r"Ran (\d+) tests? in", combined)
    skipped = bool(re.search(r"\bskipped=[1-9]\d*", combined))
    return {"suite": name, "command": command, "exit_code": exit_code,
            "passed": exit_code == 0 and not skipped, "skipped": skipped,
            "tests_run": int(counts[-1]) if counts else None,
            "seconds": round(time.monotonic() - started, 2)}


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    summary = {"python": sys.version.split()[0],
               "browser": os.environ.get("EMI_BROWSER", "chromium"), "suites": []}
    try:
        preflight()
    except Exception as error:
        summary["preflight_error"] = str(error)
        print(f"Required test dependency/display missing: {error}", file=sys.stderr)
    # Keep running independent suites so failures retain as much evidence as possible.
    try:
        for name, arguments in SUITES:
            summary["suites"].append(run_suite(name, arguments))
    finally:
        summary["passed"] = (len(summary["suites"]) == len(SUITES)
                             and not summary.get("preflight_error")) and all(
            item["passed"] for item in summary["suites"])
        summary["tests_run"] = sum(item["tests_run"] or 0 for item in summary["suites"])
        (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nTotal tests: {summary['tests_run']}; passed: {summary['passed']}", flush=True)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
