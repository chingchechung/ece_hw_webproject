"""Read-only offline v1/v2 unit and v1 manifest validation. No uploads or writes."""
import argparse
from pathlib import Path
import sys

if __package__:
    from .assignment_data import normalize_manifest, normalize_unit, read_json, validate_manifest, validate_unit
else:
    from assignment_data import normalize_manifest, normalize_unit, read_json, validate_manifest, validate_unit


def validate_path(path):
    """Return printable errors. Manifest validation checks only explicitly listed files."""
    path = Path(path)
    try:
        data = read_json(path)
    except (OSError, ValueError) as error:
        return [f"{path}: cannot read UTF-8 JSON: {error}"]
    if path.name != "manifest.json":
        return [f"{path}: {issue.path} [{issue.code}] {issue.message}" for issue in validate_unit(data, path.name)]
    issues = validate_manifest(data)
    if issues:
        return [f"{path}: {issue.path} [{issue.code}] {issue.message}" for issue in issues]
    errors = []
    for entry in normalize_manifest(data)["units"]:
        unit_path = path.parent / entry["file"]
        # Structural validation above blocks paths/URLs before touching files.
        if unit_path.is_symlink():
            errors.append(f"{unit_path}: exported unit must be a regular local file, not a symlink")
            continue
        unit_errors = validate_path(unit_path)
        errors.extend(unit_errors)
        if not unit_errors:
            unit = normalize_unit(read_json(unit_path))
            if unit["title"] != entry["title"]:
                errors.append(f"{unit_path}: title does not match the manifest entry")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Sxx.json or manifest.json (also checks its listed files)")
    args = parser.parse_args(argv)
    failed = False
    for path in args.paths:
        errors = validate_path(path)
        if errors:
            failed = True
            for message in errors:
                print(message, file=sys.stderr)
        else:
            print(f"VALID: {path}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
