"""Publish the new stable tag from its successful main CI; invoked only on GitHub."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'chingchechung/ece_hw_webproject'
TAG = 'v1.0.0'
JOBS = {
    'English Lite / approved gameplay / Python 3.12 / Tk / Chromium',
    'WebGL 2 functional checks / software Chromium',
    'Windows PowerShell 5.1 / offline launcher',
}


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def api(path):
    return json.loads(command('gh', 'api', f'repos/{REPOSITORY}/{path}'))


def list_releases():
    pages = json.loads(command('gh', 'api', '--paginate', '--slurp',
        f'repos/{REPOSITORY}/releases?per_page=100'))
    return [release for page in pages for release in page]


def verified_run(runs, sha):
    for run in runs:
        if (run['head_sha'] == sha and run['head_branch'] == 'main'
                and run['event'] == 'push' and run['status'] == 'completed'
                and run['conclusion'] == 'success'):
            return run
    raise RuntimeError('No completed successful unified main push run at the exact tag SHA')


def verify_jobs(jobs):
    if ({job['name'] for job in jobs} != JOBS or len(jobs) != 3
            or any(job['status'] != 'completed' or job['conclusion'] != 'success'
                   for job in jobs)):
        raise RuntimeError('All three complete unified verification jobs must succeed')
    for job in jobs:
        if any(step.get('conclusion') in ('failure', 'cancelled') for step in job['steps']):
            raise RuntimeError('A verification step failed')


def verify_assets(assets, expected):
    if len(assets) != len(expected) or {a['name'] for a in assets} != set(expected):
        raise RuntimeError('Uploaded release inventory does not match the two distribution ZIPs')
    for asset in assets:
        size, digest = expected[asset['name']]
        if (asset['state'] != 'uploaded' or asset['size'] != size
                or asset.get('digest') != 'sha256:' + digest):
            raise RuntimeError(f'Uploaded release asset size/checksum differs: {asset["name"]}')


def publish():
    if command('git', 'cat-file', '-t', TAG) != 'tag':
        raise RuntimeError('The stable release requires an annotated tag')
    sha = command('git', 'rev-parse', f'{TAG}^{{commit}}')
    if command('git', 'rev-parse', 'HEAD') != sha:
        raise RuntimeError('Checkout is not the exact tagged source')
    main = api('git/ref/heads/main')['object']['sha']
    if main != sha:
        raise RuntimeError('Remote main changed; do not release another source')
    # v1.0.0 is a new release only. Never edit or replace an existing release.
    if any(release['tag_name'] == TAG for release in list_releases()):
        raise RuntimeError('v1.0.0 release already exists; stop without changing it')
    runs = api(f'actions/workflows/showcase3d.yml/runs?branch=main&event=push&head_sha={sha}&per_page=100')
    run = verified_run(runs['workflow_runs'], sha)
    verify_jobs(api(f'actions/runs/{run["id"]}/jobs?per_page=100')['jobs'])
    version = json.loads((ROOT / 'release/version.json').read_text())
    if version != {'version': '1.0.0', 'editions': {'lite': '1.0.0', '3d': '1.0.0'}}:
        raise RuntimeError('Both editions must be the approved stable version')
    # Build/publish strictly runtime-only default packages, with empty manifests.
    for directory in ('student', 'showcase3d/dist'):
        if json.loads((ROOT / directory / 'assignments/manifest.json').read_text()) != {
                'schemaVersion': 1, 'units': []}:
            raise RuntimeError('Default release manifests must be empty')
    command('python', 'release/package.py')
    command('python', 'showcase3d/scripts/package.py')
    paths = [ROOT / 'test-results/unified-release/Engineering-Maze-Lab-1.0.0.zip',
             ROOT / 'test-results/3d-p2.1/showcase3d-1.0.0-static.zip']
    expected = {p.name: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths}
    notes = f'''Engineering Maze Lab v1.0.0 contains two independently deployable static editions:

- **Lite Edition:** lightweight English 2D/2.5D educational maze.
- **3D Edition:** Three.js / WebGL 2 educational maze and separate synthetic demo.
- Both accept the same S01–S12 assignment JSON: v1/v2, four/five questions, one selected answer and any teacher-accepted label passes.
- Deploy `lite/` and `3d/` independently on Apache under nested paths. No backend, login, database, tracking or automatic deployment.
- The standalone 3D ZIP includes the Windows PowerShell 5.1 offline launcher; no Node/Python installation is needed. Keep its launcher files beside `dist/`.
- Use a current graphics-accelerated Chrome/Edge browser for 3D (WebGL 2 required). Ubuntu software Chromium verifies behavior, not GPU performance or Safari compatibility. Instructor acceptance includes university Apache and actual Windows hardware; no numerical Intel FPS claim.
- Both manifests are empty. **Published assignments must be supplied separately by the instructor.** Private drafts, unreleased answers, student information and credentials are excluded. Public static JSON exposes its answers; Google Forms and YouTube need Internet. Instructor GUI and schemas are available in the source archive.
- **Existing Apache upgrades must preserve every `assignments/` file, including manifest.json.** Back up first; upload runtime assets first and index.html last. Never replace a live manifest with the empty packaged manifest. See release/README.md and showcase3d/README.md in the source archive.

Tested main release commit: `{sha}`
Annotated tag: `{TAG}`
Successful full main CI: {run['html_url']}
All 258 automated tests, four CLI manifests and seven Windows launcher checks pass.
Historical Lite/P0/3D RC tags are preserved. No gameplay, visuals, physics, GUI or assignment rules changed during stabilization.

### SHA-256

'''
    for name, (_, digest) in expected.items():
        notes += f'`{name}`\n\n`{digest}`\n\n'
    evidence = ROOT / 'test-results/release'
    evidence.mkdir(parents=True, exist_ok=True)
    notes_file = evidence / 'release-notes.md'
    notes_file.write_text(notes, encoding='utf-8')
    # Keep the release unpublished until both asset digests have been checked.
    command('gh', 'release', 'create', TAG, *(str(p) for p in paths), '--repo', REPOSITORY,
            '--verify-tag', '--draft', '--title', 'Engineering Maze Lab v1.0.0',
            '--notes-file', str(notes_file))
    # Tag lookup returns published releases only. Resolve this new draft by ID.
    drafts = [release for release in list_releases() if release['tag_name'] == TAG]
    if len(drafts) != 1 or not drafts[0]['draft']:
        raise RuntimeError('Expected exactly one newly created draft release')
    release = api(f'releases/{drafts[0]["id"]}')
    verify_assets(release['assets'], expected)
    # Download the uploaded bytes and compare too; do not rely only on API metadata.
    downloaded = evidence / 'downloaded'
    downloaded.mkdir(exist_ok=True)
    command('gh', 'release', 'download', TAG, '--repo', REPOSITORY,
            '--dir', str(downloaded), '--pattern', '*.zip')
    for name, (size, digest) in expected.items():
        data = (downloaded / name).read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError(f'Downloaded release ZIP differs: {name}')
    # Recheck main immediately before making the stable release public.
    if api('git/ref/heads/main')['object']['sha'] != sha:
        raise RuntimeError('Main changed during packaging; leave the draft for review')
    command('gh', 'release', 'edit', TAG, '--repo', REPOSITORY,
            '--draft=false', '--prerelease=false', '--latest')
    release = api(f'releases/tags/{TAG}')
    verify_assets(release['assets'], expected)
    if release['draft'] or release['prerelease']:
        raise RuntimeError('The GitHub release is not published as stable')
    result = {'commit': sha, 'tag': TAG, 'release_url': release['html_url'],
              'main_ci': run['html_url'], 'assets': expected}
    (evidence / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    publish()
