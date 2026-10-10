#!/usr/bin/env python3
"""Simulate system tools and files; never alters CUPS/services or contacts a host."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', BASE / 'scripts/oneclick.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
URI = 'usb://NefLaca/NL-N41?serial=TEST_ONLY_0001'


class Selection(unittest.TestCase):
    def test_serial_discovery(self):
        self.assertEqual(m.choose_uri('network ipp\ndirect ' + URI), URI)
        self.assertTrue(m.is_nln41('usb://NefLaca/NL%2DN41?serial=ABC'))
        self.assertFalse(m.is_nln41('socket://192.0.2.10:9100'))

    def test_multi_and_missing(self):
        other = URI + '2'
        listing = 'direct ' + URI + '\ndirect ' + other
        with self.assertRaises(RuntimeError): m.choose_uri(listing)
        self.assertEqual(m.choose_uri(listing, existing=URI), URI)
        with self.assertRaises(RuntimeError): m.choose_uri('network ipp')
        with self.assertRaises(ValueError): m.choose_uri('', explicit='usb://Other/Printer')

    def test_queue_injection(self):
        for q in ['', '../../etc/passwd', 'NLN41;shutdown', 'a b', 'x'*65]:
            with self.assertRaises(ValueError): m.valid_queue(q)
        self.assertEqual(m.valid_queue('NLN41-ARM'), 'NLN41-ARM')

    def test_saved_queue(self):
        config = '<DefaultPrinter NLN41>\nInfo Original Label Printer\nShared No\nState Stopped\nAccepting No\nOption cm-calibration-default false\nOption copies-default 2\n</DefaultPrinter>\n'
        self.assertEqual(m.queue_options(config, 'NLN41'),
                         {'options': {'cm-calibration-default': 'false', 'copies-default': '2'},
                          'info': 'Original Label Printer',
                          'shared': False, 'enabled': False, 'accepting': False})


class Transactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.calls = []
        self.exists = False
        self.old_uri = URI
        self.fail = False
        self.pending = False
        self.layout = {k:self.root / str(v).lstrip('/') for k,v in m.FILES.items()}
        for key,path in self.layout.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('original-' + key)
        (self.root / 'etc/cups/ppd').mkdir()
        self.states = {x:{'active':'inactive', 'enabled':'disabled'} for x in m.SERVICES}
        self.states['cups.service'] = {'active':'active', 'enabled':'enabled'}
        self.patches = [patch.object(m.os, 'chown'),
                        patch.object(m, 'STATE_ROOT', self.root / 'state'),
                        patch.object(m, 'FILES', self.layout),
                        patch.object(m, 'run', self.fake),
                        patch.object(m, 'service_state', lambda n:self.states[n]),
                        patch.object(m.shutil, 'which', return_value='/usr/bin/tool'),
                        patch.object(m, 'Path', self.redirect)]
        for p in self.patches:p.start()
        m.LOG = None

    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        m.LOG = None
        self.tmp.cleanup()

    def redirect(self, p):
        if str(p).startswith(('/etc/cups/', '/usr/local/')):
            return self.root / str(p).lstrip('/')
        return Path(p)

    def fake(self, args, check=True):
        args = list(map(str,args));self.calls.append(args)
        out='';code=0
        if args[0]=='dpkg-query':out='2.4.10-3'
        elif args[:2]==['lpstat','-v']:
            if self.exists:out='device for NLN41: ' + self.old_uri
            else:code=1;out='unknown printer'
        elif args[:3]==['lpstat','-W','not-completed']:
            out='NLN41-123 test-user 1000' if self.pending else ''
        elif args[0]=='lpinfo':out='direct ' + URI
        elif args[0]=='systemctl' and args[1]=='is-active':out='inactive'
        elif 'raster-nln41' in args[0]:code=1;out='Usage: raster-nln41'
        elif args[0]=='ipptool':
            if self.fail:raise RuntimeError('simulated capability check failure')
            out='NL-N41 network raster capabilities [PASS]'
        elif args[0]=='hostname':out='192.0.2.10' if '-I' in args else 'print-server'
        return subprocess.CompletedProcess(args,code,out)

    def install(self):
        m.install(argparse.Namespace(queue='NLN41', uri=None, no_apt=True, print_test=False))

    def test_fresh_install_and_rollback(self):
        self.install()
        state=m.STATE_ROOT / 'current'
        self.assertTrue(state.is_symlink())
        create=next(a for a in self.calls if a[0]=='lpadmin' and '-E' in a)
        self.assertEqual(create[create.index('-v')+1], URI)
        self.assertEqual(create[create.index('-D')+1], 'NefLaca NL-N41 AirPrint')
        sharing = next(a for a in self.calls if a[0]=='cupsctl')
        self.assertIn('BrowseDNSSDSubTypes=_print,_universal', sharing)
        self.assertFalse(any('_cups' in arg for arg in sharing))
        self.assertIn('cm-calibration-default=true',create)
        self.assertIn('nln41-mode=DriverDefault',create)
        self.assertIn('Dither=FloydSteinberg',create)
        self.assertFalse(any(a[0]=='lp' for a in self.calls))
        m.rollback(state)
        self.assertIn(['lpadmin','-x','NLN41'],self.calls)
        for k,p in self.layout.items():self.assertEqual(p.read_text(),'original-'+k)

    def test_new_files_removed_on_rollback(self):
        self.layout['filter'].unlink();self.layout['ppd'].unlink()
        self.install()
        self.assertTrue(self.layout['filter'].exists())
        m.rollback(m.STATE_ROOT / 'current')
        self.assertFalse(self.layout['filter'].exists())
        self.assertFalse(self.layout['ppd'].exists())
        self.assertTrue(self.layout['cupsd'].exists())

    def test_upgrade_restores_prior_queue(self):
        self.exists=True
        (self.root / 'etc/cups/ppd/NLN41.ppd').write_text('saved queue ppd')
        (self.root / 'etc/cups/printers.conf').write_text('<Printer NLN41>\nInfo Previous Label Printer\nShared No\nState Stopped\nAccepting No\nOption copies-default 2\nOption Dither Threshold\nOption nln41-mode BlackWhite\n</Printer>\n')
        self.install()
        create=next(a for a in self.calls if a[0]=='lpadmin' and '-E' in a)
        self.assertIn('nln41-mode=DriverDefault',create)
        self.assertIn('Dither=FloydSteinberg',create)
        m.rollback(m.STATE_ROOT / 'current')
        restored = next(a for a in self.calls if a[0]=='lpadmin' and '-v' in a and '-E' not in a)
        self.assertEqual(restored[restored.index('-D')+1], 'Previous Label Printer')
        self.assertIn(['lpadmin','-p','NLN41','-o','copies-default=2'],self.calls)
        self.assertIn(['lpadmin','-p','NLN41','-o','Dither=Threshold'],self.calls)
        self.assertIn(['lpadmin','-p','NLN41','-o','nln41-mode=BlackWhite'],self.calls)
        self.assertIn(['lpadmin','-p','NLN41','-R','cm-calibration-default'],self.calls)
        self.assertIn(['cupsdisable','NLN41'],self.calls)
        self.assertFalse(any(a[:2]==['lpadmin','-x'] for a in self.calls))

    def test_failed_check_rolls_back(self):
        self.fail=True
        with self.assertRaises(RuntimeError):self.install()
        for k,p in self.layout.items():self.assertEqual(p.read_text(),'original-'+k)
        self.assertIn(['lpadmin','-x','NLN41'],self.calls)

    def test_different_printer_is_preserved(self):
        self.exists=True;self.old_uri='usb://Brother/Other'
        with self.assertRaises(RuntimeError):self.install()
        self.assertFalse(any(a[0]=='lpadmin' for a in self.calls))

    def test_busy_queue_is_preserved(self):
        self.exists=True;self.pending=True
        with self.assertRaises(RuntimeError):self.install()
        self.assertFalse(any(a[0]=='lpadmin' for a in self.calls))

    def test_rollback_rejects_pending_jobs(self):
        self.install();self.pending=True
        before=len(self.calls)
        with self.assertRaises(RuntimeError):m.rollback(m.STATE_ROOT / 'current')
        self.assertFalse(any(a[0]=='lpadmin' for a in self.calls[before:]))


if __name__=='__main__':unittest.main()
