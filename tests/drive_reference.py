"""Immutable approved driving artwork, evaluated only in synthetic test responses."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DRIVE_REFERENCE=(ROOT/'tests/fixtures/visuals/phase-5a3-drive.js').read_text()
assert hashlib.sha256(DRIVE_REFERENCE.encode()).hexdigest()=='01bfa3e151cdadf1b8166c97ed2e462600fe0f5f855535fa8ff148e34b3eafc2'
DRIVE_BRIDGE='\nwindow.approvedDriveRender=(function(){\n'+DRIVE_REFERENCE+'\nreturn renderDrive;})();\n'
