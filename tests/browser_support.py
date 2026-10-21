"""Development-only browser selection and synthetic diagnostic artifacts."""
import json
import os
from pathlib import Path
import shutil
import sys


def launch_browser(playwright):
    """Prefer Playwright's browser; allow Cloud's system Chromium or an override."""
    name = os.environ.get("EMI_BROWSER", "chromium")
    if name not in {"chromium", "webkit"}:
        raise ValueError("EMI_BROWSER must be chromium or webkit")
    browser_type = getattr(playwright, name)
    options = {"headless": True}
    override = os.environ.get("EMI_BROWSER_EXECUTABLE")
    if override:
        if name != "chromium":
            raise ValueError("EMI_BROWSER_EXECUTABLE is supported only for Chromium")
        if not Path(override).is_file():
            raise FileNotFoundError(f"Browser executable does not exist: {override}")
        options["executable_path"] = override
    elif name == "chromium" and not Path(browser_type.executable_path).is_file():
        system_browser = shutil.which("chromium") or shutil.which("chromium-browser")
        if system_browser:
            options["executable_path"] = system_browser
    if name == "chromium" and sys.platform == "linux":
        options["args"] = ["--no-sandbox"]
    return browser_type.launch(**options)


def save_browser_artifacts(context, page, folder, name, errors):
    """Capture diagnostics before cleanup, even after an assertion/navigation fails."""
    folder.mkdir(parents=True, exist_ok=True)
    capture_errors = []
    try:
        page.screenshot(path=str(folder / f"{name}.png"))
    except Exception as error:
        capture_errors.append(f"Screenshot: {error}")
    try:
        context.tracing.stop(path=str(folder / f"{name}.trace.zip"))
    except Exception as error:
        capture_errors.append(f"Trace: {error}")
    (folder / f"{name}.errors.json").write_text(json.dumps({
        "page_errors": errors, "capture_errors": capture_errors,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
