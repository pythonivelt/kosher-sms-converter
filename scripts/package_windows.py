"""Build a portable Windows app from the pinned, checksum-verified Electron runtime.

Python 3.9+. No npm install or third-party Python packages required for packaging.
Uses Electron's documented resources/app layout; never includes backup fixtures.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP_FILES = [
    'index.html', 'viewer.js', 'viewer.css', 'xml-attachments.js',
    'workspace.js', 'workspace.css', 'desktop/main.cjs', 'desktop/policy.cjs',
    'assets/chart.svg', 'vendor/zip.js/zip.min.js', 'vendor/zip.js/LICENSE',
    'vendor/zip.js/README.md',
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def build(output_dir):
    runtime = json.loads((ROOT / 'desktop/runtime.json').read_text(encoding='utf-8'))
    package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
    if package['devDependencies']['electron'] != runtime['version']:
        raise ValueError('Electron dependency and runtime lock must use the same version')
    filename = f"electron-v{runtime['version']}-{runtime['platform']}-{runtime['arch']}.zip"
    cache = ROOT / 'dist' / 'runtime-cache'
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / filename
    if not archive.exists() or sha256(archive) != runtime['sha256']:
        print('Downloading official Electron runtime...', flush=True)
        request = urllib.request.Request(f"https://github.com/electron/electron/releases/download/v{runtime['version']}/{filename}", headers={'User-Agent': 'Kosher-SMS-packager'})
        partial = archive.with_suffix('.download')
        with urllib.request.urlopen(request, timeout=60) as source, partial.open('wb') as destination:
            shutil.copyfileobj(source, destination, 1024 * 1024)
        if sha256(partial) != runtime['sha256']:
            raise ValueError('Electron runtime checksum mismatch; refusing to package')
        partial.replace(archive)
    print('Electron runtime checksum verified.', flush=True)
    staging = (ROOT / 'dist' / ('portable-' + uuid.uuid4().hex[:12])).resolve()
    staging.mkdir()
    app_dir = staging / 'Kosher SMS'
    app_dir.mkdir()
    with zipfile.ZipFile(archive) as source:
        for item in source.infolist():
            target = (app_dir / item.filename).resolve()
            if not target.is_relative_to(app_dir):
                raise ValueError('Unsafe runtime archive path')
            source.extract(item, app_dir)
    app_root = app_dir / 'resources' / 'app'
    app_root.mkdir()
    for name in APP_FILES:
        target = app_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    manifest = {k: package[k] for k in ['name', 'productName', 'version', 'description', 'private', 'main']}
    (app_root / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (app_dir / 'electron.exe').rename(app_dir / 'Kosher SMS.exe')
    (app_dir / 'resources' / 'default_app.asar').unlink(missing_ok=True)
    (app_dir / 'START HERE.txt').write_text(
        'Kosher SMS - Windows x64\n\n'
        '1. Extract the entire ZIP to a folder.\n'
        '2. Double-click Kosher SMS.exe inside that folder.\n'
        '3. Use Messages to view backups and contacts; use Converter to convert.\n\n'
        'Keep all files in this folder together. No installation or internet is needed.\n'
        'Your original backup files are not modified. Backups are not uploaded.\n'
        'This initial build is not code-signed.\n', encoding='utf-8')
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / f"Kosher-SMS-{package['version']}-Windows-x64.zip"
    print('Creating portable ZIP...', flush=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as destination:
        for file in sorted(app_dir.rglob('*')):
            if file.is_file():
                destination.write(file, file.relative_to(staging))
    checksum = sha256(output)
    output.with_suffix('.zip.sha256').write_text(checksum + '  ' + output.name + '\n', encoding='utf-8')
    print('App folder: ' + str(app_dir), flush=True)
    print('Portable ZIP: ' + str(output), flush=True)
    return output, app_dir


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    build(parser.parse_args().output_dir.resolve())
