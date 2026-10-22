"""Make a venue-ready static ZIP; never includes the repository or private data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
output = root.parent / 'test-results/3d-p1.1/showcase3d-p1.1-static.zip'
output.parent.mkdir(parents=True, exist_ok=True)
files = [*sorted((root / 'dist').glob('*')), *(root / name for name in (
    'Start-Showcase.cmd', 'launch.ps1', 'serve.py', 'README.md', 'THIRD_PARTY.md'))]
with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
    for path in files:
        if not path.is_file():
            raise RuntimeError(f'Missing required static package file: {path}')
        archive.write(path, f'showcase3d/{path.relative_to(root)}')
print(output)
