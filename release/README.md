# Engineering Maze Lab — unified release candidate

This candidate contains both educational editions under one version, 1.0.0-rc1.
The English Lite UI retains the approved 5B.1 renderer and gameplay. The approved
3D runtime retains the P2.1.1 fullscreen fix. Final main/v1.0.0 publication awaits
instructor approval. The historical 3D rc1 tag is not moved by this preparation.

## Reproduce the packages

From the source repository, with Python 3.12 and Node 24:

```sh
npm ci --prefix showcase3d
npm run build --prefix showcase3d
python release/package.py
python showcase3d/scripts/package.py
```

The unified ZIP is `test-results/unified-release/Engineering-Maze-Lab-1.0.0-rc1.zip`.
It contains `Engineering-Maze-Lab/lite/`, `Engineering-Maze-Lab/3d/`, this README,
and `release-info.json` with versions and SHA-256 hashes of all packaged runtime
files. ZIP entry order, timestamps and permissions are fixed; identical inputs
produce identical ZIP bytes. Python/zlib versions should also match for identical
compressed bytes across machines. The builder rejects symlinks, unexpected files,
nonempty manifests, changed 3D build hashes and inconsistent component versions.
It reads only the explicit runtime allowlists. It never rewrites source/live JSON.

Both default manifests are empty. No course questions, private drafts, test
fixtures, student data, credentials, teacher tools or schemas enter this ZIP.
The GitHub source checkout retains `tools/` and `schemas/` together for the
offline instructor editor. Keep its private draft and export folders outside
any web root. Publish only explicitly approved exports, manually, to each
edition's `assignments/` directory. Both editions accept the same public v1/v2
formats, four/five questions and single-choice accepted-label semantics.

The separate Windows package remains
`test-results/3d-p2.1/showcase3d-1.0.0-rc1-static.zip`. Extract it, keep `dist/`
beside `Start-Showcase.cmd`, and double-click that launcher. It uses Windows
PowerShell's local static server; Node/Python installation is unnecessary.
See its included guide for local port, shutdown and troubleshooting instructions.
The unified Apache ZIP itself has no launcher and requires HTTP(S), not file://.

## First installation on Apache

Extract outside the live web root and verify the ZIP/hash evidence. Deploy the
contents of `lite/` and `3d/` independently, for example to:

```text
https://example.edu/~teacher/Engineering-Maze-Lab/lite/
https://example.edu/~teacher/Engineering-Maze-Lab/3d/
```

Apache must serve `.js` as JavaScript, `.css` as CSS and `.json` as JSON. No
rewrite rules, backend, database, login, secrets or automatic deployment are
required. All runtime and assignment URLs are relative, so arbitrary nested
paths work. A fresh installation may copy each empty bootstrap manifest. The
Lite page starts at unit selection; the 3D page also offers its synthetic demo.
Enable Allow Play in the offline teacher editor, export approved units and their
manifest, then upload those files manually into each chosen edition. Upload
unit JSON first and the matching public manifest last. Never upload draft files.

## Upgrade an existing installation safely

1. Back up each entire live edition, including its complete `assignments/`
   directory. Stage and inspect the release outside the live web root.
2. **Leave every live `assignments/` file untouched**, including `manifest.json`,
   released `Sxx.json` files and any other existing files. Never copy the ZIP's
   empty bootstrap manifest over a live manifest. Do not use a directory mirror
   or deletion sync. Application upgrades do not publish or withdraw units.
3. For Lite, upload only the six `js/*.js` runtime files, then `index.html` last.
   The localized loader/game URLs have a new version query to avoid stale cached
   Chinese UI. Keep the directory structure and existing assignments intact.
4. For 3D, upload the new `app-*.js`, `app-*.css`, `LICENSES.txt` and
   `build-info.json`, then `index.html` last. Retain older hashed assets until
   cached pages have expired. Do not upload repository tools or tests.
5. Open each edition's actual nested URL in a fresh browser session. Check the
   existing published unit list, one previously released unit, mode switching,
   full-map countdown, 3D fullscreen entry/exit and the browser console. Verify
   live assignment hashes against the backup. A hard refresh may be needed for
   an already open page. Roll back runtime files/index from the backup if needed,
   again preserving the current assignments directory.

There is no automatic upload or deployment. This RC has automated Chromium
coverage on Ubuntu and a Windows launcher check. Software WebGL results do not
establish Intel GPU performance. The instructor's prior physical Windows/Iris Xe
review applies to the preserved 3D runtime. Optional macOS/WebKit testing is
described in the source README; Safari compatibility is not claimed.
