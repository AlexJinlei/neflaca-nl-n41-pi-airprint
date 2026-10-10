#!/usr/bin/env python3
"""Build the public Pi package from this tree; no network or installation."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parents[1]
VERSION = '0.6.2'
EXCLUDED = {'build', '__pycache__', '.git', 'packages', 'dist', 'work'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files():
    return sorted(p for p in BASE.rglob('*') if p.is_file() and not p.is_symlink()
                  and not EXCLUDED.intersection(p.relative_to(BASE).parts)
                  and p.name not in {'SHA256SUMS', '.DS_Store'}
                  and p.suffix not in {'.pyc', '.log'})


def zip_folder(folder, output):
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(folder.rglob('*')):
            if not p.is_file():
                continue
            info = zipfile.ZipInfo(folder.name + '/' + p.relative_to(folder).as_posix(),
                                   date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = p.stat().st_mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, p.read_bytes())


def main():
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else BASE / 'packages'
    output.mkdir(parents=True, exist_ok=True)
    binary = BASE / 'bin/linux-aarch64/raster-nln41'
    if not binary.is_file() or binary.read_bytes()[:4] != b'\x7fELF':
        raise SystemExit('Build the Linux ARM64 filter before packaging.')
    files = source_files()
    manifest = BASE / 'SHA256SUMS'
    manifest.write_text(''.join(digest(p) + '  ' + p.relative_to(BASE).as_posix() + '\n'
                                for p in files))
    files.append(manifest)
    run = output / ('nln41-pi-airprint-v' + VERSION + '.run')
    subprocess.run([sys.executable, str(BASE / 'scripts/build-oneclick.py'), str(run)], check=True)
    artifacts = [run]
    with tempfile.TemporaryDirectory(prefix='nln41-pi-package-') as temp:
        folder = Path(temp) / ('nln41-pi-airprint-v' + VERSION)
        folder.mkdir()
        shutil.copy2(run, folder / run.name)
        shutil.copy2(BASE / 'docs/INSTALL-PI.md', folder / 'README.md')
        # Put complete docs beside the install README for offline reading.
        for p in sorted((BASE / 'docs').iterdir()):
            if p.is_file():
                shutil.copy2(p, folder / p.name)
        shutil.copy2(BASE / 'LICENSE', folder / 'LICENSE')
        for p in files:
            target = folder / 'src' / p.relative_to(BASE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
        members = sorted(p for p in folder.rglob('*') if p.is_file())
        (folder / 'CONTENTS-SHA256SUMS').write_text(''.join(
            digest(p) + '  ' + p.relative_to(folder).as_posix() + '\n' for p in members))
        package = output / (folder.name + '.zip')
        zip_folder(folder, package)
        artifacts.append(package)
        print(package.name, package.stat().st_size, 'bytes')
    (output / 'SHA256SUMS').write_text(''.join(digest(p) + '  ' + p.name + '\n' for p in artifacts))
    print('Built the Pi package. Gray is the default; no printer was contacted.')


if __name__ == '__main__':
    main()
