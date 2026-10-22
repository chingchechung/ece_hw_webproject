"""Make a venue-ready static ZIP; never includes the repository or private data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import json
import subprocess
import hashlib
import re

root = Path(__file__).resolve().parents[1]
version = json.loads((root/'package.json').read_text())['version']
if not re.fullmatch(r'\d+\.\d+\.\d+-rc\d+',version):
    raise RuntimeError('Expected an explicit release-candidate version')
output = root.parent / f'test-results/3d-p2.1/showcase3d-{version}-static.zip'
output.parent.mkdir(parents=True, exist_ok=True)
published = json.loads(subprocess.check_output(['node', str(root/'scripts/check-publication.mjs'), str(root/'dist/assignments')],text=True))
build_info = json.loads((root/'dist/build-info.json').read_text())
if build_info.get('version') != version:
    raise RuntimeError('Release version differs from the built runtime; rebuild first.')
runtime = build_info['files']
app_files = [name for name in runtime if re.fullmatch(r'app-[A-Z0-9]{8}\.(js|css)',name)]
if (set(runtime) != {'index.html','LICENSES.txt',*app_files} or len(app_files)!=2
        or {Path(name).suffix for name in app_files}!={'.js','.css'}):
    raise RuntimeError('Unexpected runtime file list; rebuild the static bundle.')
for name, digest in runtime.items():
    path = root/'dist'/name
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise RuntimeError(f'Runtime file differs from the reproducible build: {name}')
files = [*(root/'dist'/name for name in sorted([*runtime,'build-info.json'])),
    *(root/'dist/assignments'/name for name in published), *(root / name for name in (
    'Start-Showcase.cmd', 'launch.ps1', 'serve.py', 'README.md', 'THIRD_PARTY.md'))]
with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
    for path in files:
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f'Missing required static package file: {path}')
        archive.write(path, f'showcase3d/{path.relative_to(root)}')
print(output)
