"""Deterministic, runtime-only two-edition package; never publish course data."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
LITE_FILES = {'index.html', 'assignments/manifest.json', *(
    'js/' + name + '.js' for name in ('assignment-loader', 'assignment-rules',
    'assignment-validator', 'drive-materials', 'game', 'rpg-renderer'))}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_tree(directory, allowed):
    if directory.is_symlink():
        raise ValueError(f'Symlink is not allowed: {directory}')
    paths = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink is not allowed: {path}')
        if path.is_file():
            paths[path.relative_to(directory).as_posix()] = path
    if set(paths) != allowed:
        raise ValueError(f'Unexpected or missing runtime files: {directory}: '
                         f'{sorted(set(paths) ^ allowed)}')
    files = {name: path.read_bytes() for name, path in paths.items()}
    if json.loads(files['assignments/manifest.json']) != {'schemaVersion': 1, 'units': []}:
        raise ValueError(f'Unified default package requires an empty manifest: {directory}')
    return files


def package(root=ROOT, destination=None):
    version = json.loads((root / 'release/version.json').read_text(encoding='utf-8'))
    if not re.fullmatch(r'(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-rc(?:0|[1-9][0-9]*))?', version['version']):
        raise ValueError('Expected a stable SemVer or explicit -rcN release version')
    if set(version['editions']) != {'lite', '3d'} or any(
            value != version['version'] for value in version['editions'].values()):
        raise ValueError('Both editions must share the unified release version')
    lite = read_tree(root / 'student', LITE_FILES)
    if f'name="application-version" content="{version["version"]}"' not in lite['index.html'].decode():
        raise ValueError('Lite application version does not match the release')
    dist = root / 'showcase3d/dist'
    info = json.loads((dist / 'build-info.json').read_text(encoding='utf-8'))
    if info['version'] != version['version']:
        raise ValueError('3D build version does not match the release')
    runtime = set(info['files'])
    if (len(runtime) != 4 or {'index.html', 'LICENSES.txt'} - runtime or
            len([p for p in runtime if re.fullmatch(r'app-[A-Z0-9]+\.js', p)]) != 1 or
            len([p for p in runtime if re.fullmatch(r'app-[A-Z0-9]+\.css', p)]) != 1):
        raise ValueError('Unexpected 3D build file list')
    three = read_tree(dist, runtime | {'build-info.json', 'assignments/manifest.json'})
    if any(digest(three[name]) != expected for name, expected in info['files'].items()):
        raise ValueError('3D runtime hash differs from its approved build')
    files = {**{'lite/' + name: data for name, data in lite.items()},
             **{'3d/' + name: data for name, data in three.items()}}
    files['README.md'] = (root / 'release/README.md').read_bytes()
    files['release-info.json'] = (json.dumps({**version, 'files': {
        name: digest(data) for name, data in sorted(files.items())}}, indent=2) + '\n').encode()
    destination = destination or root / 'test-results/unified-release' / (
        f'Engineering-Maze-Lab-{version["version"]}.zip')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(files.items()):
            entry = ZipInfo('Engineering-Maze-Lab/' + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    archive = package(destination=args.output)
    print(json.dumps({'archive': str(archive.relative_to(ROOT)) if archive.is_relative_to(ROOT)
                     else str(archive), 'sha256': digest(archive.read_bytes())}, indent=2))
