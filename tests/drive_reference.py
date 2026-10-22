"""Immutable approved driving artwork, evaluated only in synthetic test responses."""
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DRIVE_REFERENCE=(ROOT/'tests/fixtures/visuals/phase-5a3-drive.js').read_text()
assert hashlib.sha256(DRIVE_REFERENCE.encode()).hexdigest()=='01bfa3e151cdadf1b8166c97ed2e462600fe0f5f855535fa8ff148e34b3eafc2'
DRIVE_BRIDGE='\nwindow.approvedDriveRender=(function(){\n'+DRIVE_REFERENCE+'\nreturn renderDrive;})();\n'

PHASE5B_REFERENCE=(ROOT/'tests/fixtures/visuals/phase-5b-drive.js').read_text()
assert hashlib.sha256(PHASE5B_REFERENCE.encode()).hexdigest()=='30b43edfffbc7c12b4bf2044ef1689c4ddaba775a7a8aff9d2634f5a30f9186d'
PHASE5B_BRIDGE='\nwindow.phase5bRender=(function(){\n'+PHASE5B_REFERENCE+'\nreturn renderDrive;})();\n'
