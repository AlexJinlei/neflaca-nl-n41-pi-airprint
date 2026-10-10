#!/usr/bin/env python3
"""NL-N41 installer. Uses system CUPS tools, not vendor code or remote scripts."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

BASE = Path(__file__).resolve().parents[1]
STATE_ROOT = Path('/var/lib/nln41-arm64-driver/oneclick')
ENV = {'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8',
       'LC_ALL': 'C.UTF-8', 'DEBIAN_FRONTEND': 'noninteractive'}
LOG = None
FILES = {'filter': Path('/usr/lib/cups/filter/raster-nln41'),
         'ppd': Path('/usr/share/ppd/nln41/NL-N41.ppd'),
         'cupsd': Path('/etc/cups/cupsd.conf')}
SERVICES = ['cups.service', 'cups.socket', 'avahi-daemon.service', 'p910nd.service']


def run(args, check=True):
    p = subprocess.run([str(a) for a in args], env=ENV, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if LOG:
        with LOG.open('a') as f:
            f.write('$ ' + ' '.join(map(str, args)) + '\n' + p.stdout + '\n')
    if check and p.returncode:
        raise RuntimeError(f'{args[0]} failed:\n{p.stdout.strip()}')
    return p


def valid_queue(name):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name):
        raise ValueError('Queue names must contain only letters, digits, underscores or hyphens (up to 64 characters).')
    return name


def is_nln41(uri):
    u = unquote(uri)
    return u.lower().startswith('usb://') and bool(re.search(r'/NL[-_]N41(?:\?|$)', u, re.I))


def choose_uri(listing, explicit=None, existing=None):
    if explicit:
        if not is_nln41(explicit):
            raise ValueError('--uri must be the complete usb:// URI for an NL-N41.')
        return explicit
    found = sorted(set(line.split()[1] for line in listing.splitlines()
                       if len(line.split()) >= 2 and is_nln41(line.split()[1])))
    if existing in found:
        return existing
    if len(found) == 1:
        return found[0]
    if not found:
        raise RuntimeError('No NL-N41 found. Turn on the printer, connect USB, then run the installer again.')
    raise RuntimeError('Multiple NL-N41 printers found. Select one using --uri:\n' + '\n'.join(found))


def service_state(name):
    return {'active': run(['systemctl', 'is-active', name], False).stdout.strip(),
            'enabled': run(['systemctl', 'is-enabled', name], False).stdout.strip()}


def queue_options(config, queue):
    # Read CUPS' saved options only; all writes go through lpadmin.
    match = re.search(r'<(?:Default)?Printer\s+' + re.escape(queue) +
                      r'>\n(.*?)</(?:Default)?Printer>', config, re.S | re.I)
    if not match:
        return {'options': {}, 'info': queue, 'shared': True, 'enabled': True, 'accepting': True}
    lines = match[1].splitlines()
    opts = {}
    fields = {}
    for line in lines:
        bits = line.split(None, 2)
        if bits and bits[0] == 'Option' and len(bits) == 3:
            opts[bits[1]] = bits[2]
        elif len(bits) >= 2:
            fields[bits[0]] = ' '.join(bits[1:])
    return {'options': opts, 'info': fields.get('Info', queue),
            'shared': fields.get('Shared', 'Yes') == 'Yes',
            'enabled': fields.get('State', 'Idle') != 'Stopped',
            'accepting': fields.get('Accepting', 'Yes') == 'Yes'}


def save(state, folder):
    temp = folder / 'state.new'
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    temp.replace(folder / 'state.json')


def backup_file(target, dest):
    if target.is_symlink():
        raise RuntimeError(f'Installation target is a symbolic link. Check it before continuing:{target}')
    if target.exists():
        shutil.copy2(target, dest)
        return True
    return False


def restore_file(target, source, existed):
    if existed:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    else:
        target.unlink(missing_ok=True)


def restore_services(services):
    # Restore only units this installer operates; package installation is retained.
    for name in ['p910nd.service', 'avahi-daemon.service', 'cups.socket', 'cups.service']:
        old = services[name]
        if old['enabled'] == 'enabled':
            run(['systemctl', 'enable', name])
        elif old['enabled'] in ['disabled', 'not-found', '']:
            run(['systemctl', 'disable', name], False)
        if old['active'] == 'active':
            run(['systemctl', 'start', name])
        else:
            run(['systemctl', 'stop', name], False)


def rollback(folder):
    state = json.loads((folder / 'state.json').read_text())
    if state['status'] == 'rolled-back':
        print('This installation has already been rolled back.')
        return
    q = valid_queue(state['queue'])
    run(['systemctl', 'start', 'cups.service'])
    pending = run(['lpstat', '-W', 'not-completed', '-o', q], False)
    if pending.returncode == 0 and pending.stdout.strip():
        raise RuntimeError('The queue has pending jobs. Complete or cancel them before rolling back.')
    # Restore queue through CUPS APIs; do not overwrite other printers' records.
    if state['queue_existed']:
        args = ['lpadmin', '-p', q, '-v', state['old_uri']]
        if state['queue_ppd']:
            args += ['-P', folder / 'queue.ppd']
        else:
            args += ['-m', 'raw']
        old = state['queue_state']
        if 'info' in old:
            args += ['-D', old['info']]
        run(args)
        for option in ['cm-calibration-default', 'copies-default']:
            if option not in old['options']:
                run(['lpadmin', '-p', q, '-R', option])
        for key, value in old['options'].items():
            run(['lpadmin', '-p', q, '-o', key + '=' + value])
        run(['lpadmin', '-p', q, '-o', 'printer-is-shared=' + str(old['shared']).lower()])
        run(['cupsenable' if old['enabled'] else 'cupsdisable', q])
        run(['cupsaccept' if old['accepting'] else 'cupsreject', q])
    else:
        # lpadmin -x also deletes its queued jobs, so check above first.
        run(['lpadmin', '-x', q], False)
    for key, target in FILES.items():
        restore_file(target, folder / key, state['files'][key])
    run(['cupsd', '-t'])
    run(['systemctl', 'restart', 'cups.service'])
    restore_services(state['services'])
    state['status'] = 'rolled-back'
    save(state, folder)
    print('Restored the previous driver, queue and sharing configuration. Dependency packages were retained.')


def print_summary(q, folder):
    hostname = run(['hostname'], False).stdout.strip() or 'raspberrypi'
    ips = run(['hostname', '-I'], False).stdout.split()
    addresses = [i for i in ips if ':' not in i and not i.startswith('127.')]
    host = addresses[0] if addresses else hostname + '.local'
    print('\nInstallation complete. Capability check: PASS. No test label will be printed automatically.')
    print('On a Mac: System Settings > Printers & Scanners > Add Printer.')
    print('Select NefLaca NL-N41 AirPrint @ your Pi from the default list.')
    print('Keep the automatically selected Use setting and click Add. No Mac script is required.')
    print('Use may show AirPrint or the Pi model name; the client uses built-in AirPrint support.')
    print('If the printer is not discovered, use the globe icon as a fallback:')
    print(f'  Address: {host}:631\n  Protocol: AirPrint\n  Queue: printers/{q}\n  Use: Select AirPrint')
    print('Name: NefLaca NL-N41 AirPrint')
    print('Paper: 4x6 inches. Orientation: Portrait. Start with one copy.')
    print('Default rendering: Gray (Floyd-Steinberg), also suitable for pure black/white labels.')
    print('No custom Gray / Black & White menu is required for normal AirPrint printing.')
    print(f'Full URI: ipp://{host}:631/printers/{q}')
    if len(addresses) > 1:
        print('The Pi has multiple addresses. Use the address on the same LAN as your client: ' + ', '.join(addresses))
    print('Installation record: ' + str(folder))
    print('Rollback: sudo /usr/local/sbin/nln41-rollback')


def install(opts):
    global LOG
    services = {n: service_state(n) for n in SERVICES}
    if not opts.no_apt:
        print('[1/5] Installing system dependencies...', flush=True)
        # Keep progress visible; do not upgrade the OS or download executable scripts.
        for args in [['apt-get', 'update'], ['apt-get', 'install', '-y', 'cups', 'cups-client',
                     'cups-filters', 'ghostscript', 'avahi-daemon', 'cups-ipp-utils', 'python3']]:
            subprocess.run(args, env=ENV, check=True)
    for tool in ['lpinfo', 'lpadmin', 'lpstat', 'cupsctl', 'cupsd', 'ipptool']:
        if not shutil.which(tool, path=ENV['PATH']):
            raise RuntimeError('Missing system tool: ' + tool)
    version = run(['dpkg-query', '-W', '-f=${Version}', 'cups-daemon']).stdout.strip()
    if not re.match(r'^(?:\d+:)?2\.', version):
        raise RuntimeError('This installer requires CUPS 2.x. Detected: ' + version)
    run(['systemctl', 'start', 'cups.service'])
    run(['lpstat', '-r'])
    q = valid_queue(opts.queue)
    classes = run(['lpstat', '-c'], False).stdout
    if re.search(r'^members of class ' + re.escape(q) + r':', classes, re.M | re.I):
        raise RuntimeError('A printer class with this name already exists. Choose another name using --queue.')
    old = run(['lpstat', '-v', q], False)
    exists = old.returncode == 0
    old_uri = old.stdout.strip().split(': ', 1)[1] if exists and ': ' in old.stdout else None
    if exists and not is_nln41(old_uri or ''):
        raise RuntimeError(f'{q} points to another device and was left unchanged. Use --queue NLN41_ARM to create a separate queue.')
    if exists and run(['lpstat', '-W', 'not-completed', '-o', q]).stdout.strip():
        raise RuntimeError('The queue has pending jobs. Complete or cancel them before running the installer.')
    # Verify payload can load before changing printer files.
    binary = BASE / 'bin/linux-aarch64/raster-nln41'
    binary.chmod(0o755)
    check = run([binary], False)
    if check.returncode != 1 or 'Usage: raster-nln41' not in check.stdout:
        raise RuntimeError('The ARM64 filter could not run:\n' + check.stdout)
    print('[2/5] Backing up the existing configuration...', flush=True)
    STATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    folder = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=STATE_ROOT))
    LOG = folder / 'install.log'
    state = {'queue': q, 'queue_existed': exists, 'old_uri': old_uri,
             'services': services, 'files': {}, 'queue_ppd': False,
             'status': 'preparing', 'version': '0.6.2'}
    for key, target in FILES.items():
        state['files'][key] = backup_file(target, folder / key)
    if exists:
        state['queue_ppd'] = backup_file(Path('/etc/cups/ppd') / (q + '.ppd'), folder / 'queue.ppd')
    config = Path('/etc/cups/printers.conf')
    state['queue_state'] = queue_options(config.read_text() if config.exists() else '', q)
    helper = Path('/usr/local/sbin/nln41-rollback')
    if helper.is_symlink():
        raise RuntimeError('The rollback script path is a symbolic link: ' + str(helper))
    if helper.exists() and 'nln41-arm64-driver/oneclick' not in helper.read_text():
        raise RuntimeError('The rollback script path is occupied by another file: ' + str(helper))
    save(state, folder)
    # Persistent helper survives removal of the downloaded installation file.
    shutil.copy2(Path(__file__), folder / 'oneclick.py')
    current = STATE_ROOT / 'current'
    link = STATE_ROOT / 'current.new'
    link.unlink(missing_ok=True)
    link.symlink_to(folder.name)
    link.replace(current)
    helper = Path('/usr/local/sbin/nln41-rollback')
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text('#!/bin/sh\nexec /usr/bin/python3 /var/lib/nln41-arm64-driver/oneclick/current/oneclick.py --rollback "$@"\n')
    helper.chmod(0o755)
    os.chown(helper, 0, 0)
    try:
        print('[3/5] Detecting the USB printer and installing the driver...', flush=True)
        if services['p910nd.service']['enabled'] != 'not-found':
            run(['systemctl', 'disable', '--now', 'p910nd.service'], False)
            if run(['systemctl', 'is-active', 'p910nd.service'], False).stdout.strip() == 'active':
                raise RuntimeError('Could not stop p910nd. Check its service status.')
        uri = choose_uri(run(['lpinfo', '-v']).stdout, opts.uri, old_uri)
        for key, source, mode in [('filter', binary, 0o755), ('ppd', BASE / 'ppd/NL-N41.ppd', 0o644)]:
            FILES[key].parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, FILES[key])
            FILES[key].chmod(mode)
            os.chown(FILES[key], 0, 0)
        run(['lpadmin', '-p', q, '-E', '-v', uri, '-P', FILES['ppd'],
             '-D', 'NefLaca NL-N41 AirPrint',
             '-o', 'PageSize=4x6', '-o', 'PaperType=1', '-o', 'GapLength=2',
             '-o', 'Orientation=0', '-o', 'MirrorImage=False', '-o', 'NegativeImage=False',
             '-o', 'nln41-mode=DriverDefault', '-o', 'Dither=FloydSteinberg',
             '-o', 'copies-default=1', '-o', 'cm-calibration-default=true',
             '-o', 'printer-is-shared=true'])
        print('[4/5] Enabling LAN printing...', flush=True)
        run(['systemctl', 'enable', '--now', 'cups.service', 'avahi-daemon.service'])
        run(['cupsctl', '--share-printers', 'BrowseLocalProtocols=dnssd',
             'BrowseDNSSDSubTypes=_print,_universal'])
        run(['cupsd', '-t'])
        run(['systemctl', 'restart', 'cups.service'])
        print('[5/5] Checking PDF / URF / PWG and 203 dpi support...', flush=True)
        response = run(['ipptool', '-T', '15', '-tv', f'ipp://localhost:631/printers/{q}',
                        BASE / 'tests/network-attributes.test'])
        if '[PASS]' not in response.stdout:
            raise RuntimeError('The capability check did not return PASS:\n' + response.stdout)
        state['status'] = 'installed'
        state['device_uri'] = uri
        save(state, folder)
    except BaseException:
        print('\nInstallation did not complete. Restoring the previous configuration...', file=sys.stderr)
        try:
            rollback(folder)
        except Exception as error:
            print('Automatic recovery did not complete: ' + str(error), file=sys.stderr)
            print('Recovery command: sudo /usr/local/sbin/nln41-rollback', file=sys.stderr)
        raise
    print_summary(q, folder)
    if opts.print_test:
        print(run(['lp', '-d', q, '-n', '1', '-o', 'PageSize=4x6', BASE / 'tests/test-label.ps']).stdout)


def main():
    parser = argparse.ArgumentParser(description='NL-N41 one-click install / upgrade (Debian ARM64, CUPS 2.x)')
    parser.add_argument('--queue', default='NLN41', help='default: NLN41')
    parser.add_argument('--uri', help='select a printer by its complete USB URI')
    parser.add_argument('--no-apt', action='store_true', help='skip apt when all dependencies are already installed')
    parser.add_argument('--print-test', action='store_true', help='print one test label after installation succeeds')
    parser.add_argument('--rollback', action='store_true', help='roll back the latest one-click installation')
    opts = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Run this installer with sudo.')
    if platform.system() != 'Linux' or platform.machine() != 'aarch64' or not Path('/etc/debian_version').exists():
        parser.error('Raspberry Pi OS 64-bit / Debian ARM64 is required.')
    STATE_ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (STATE_ROOT / 'lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error('Another installation or rollback is running. Wait for it to finish.')
    try:
        if opts.rollback:
            rollback(STATE_ROOT / 'current')
        else:
            install(opts)
    except (Exception, KeyboardInterrupt) as error:
        print('\nFailed: ' + str(error), file=sys.stderr)
        if LOG:
            print('Log: ' + str(LOG), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
