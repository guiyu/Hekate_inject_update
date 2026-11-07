import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path
from apps.core import build_payload, inject, verified_resources, InjectionError, TriggerOutcome

class FakeUSB:
    def __init__(self, read_size=16, short=False, trigger_error=None):
        self.read_size=read_size; self.short=short; self.trigger_error=trigger_error
        self.writes=[]; self.triggered=False; self.closed=False
    def read(self,n): return b'x'*self.read_size
    def write(self,b): self.writes.append(b); return len(b)-1 if self.short else len(b)
    def trigger(self,n):
        self.triggered=True
        if self.trigger_error: raise self.trigger_error
        return TriggerOutcome('returned', '请查看 Switch 屏幕')
    def close(self): self.closed=True

class PayloadTests(unittest.TestCase):
    def test_layout_and_alignment(self):
        p=bytes(range(256))*80; r=b'RELOCATOR'
        b=build_payload(p,r)
        self.assertEqual(struct.unpack_from('<I',b)[0],0x30298)
        self.assertEqual(b[680:689],r)
        self.assertEqual(b[680+0xe40:680+0x4e40],p[:0x4000])
        self.assertEqual(b[680+0x4e40:680+0x7000],struct.pack('<I',0x40010000)*(0x21c0//4))
        self.assertEqual(b[680+0x7000:680+0x7000+len(p)-0x4000],p[0x4000:])
        self.assertEqual(len(b)%4096,0)
    def test_reject_empty_oversize_payload_and_relocator(self):
        for p,r in [(b'',b'x'),(b'x'*200000,b'x'),(b'x',b''),(b'x',b'x'*0xe41)]:
            with self.subTest(p=len(p),r=len(r)),self.assertRaises(InjectionError):build_payload(p,r)
    def test_validate_all_resources_before_usb(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'payload.bin').write_bytes(b'p'); (root/'intermezzo.bin').write_bytes(b'r')
            manifest={n:hashlib.sha256(b).hexdigest() for n,b in [('payload.bin',b'p'),('intermezzo.bin',b'r')]}
            (root/'resources.json').write_text(json.dumps(manifest))
            self.assertEqual(verified_resources(root),(b'p',b'r'))
            (root/'payload.bin').write_bytes(b'tampered')
            with self.assertRaises(InjectionError): verified_resources(root)
    def test_upload_odd_buffer_and_close(self):
        usb=FakeUSB(); outcome=inject(usb,b'x'*20000,b'r',lambda _:None)
        self.assertTrue(usb.closed);self.assertTrue(usb.triggered)
        self.assertEqual(len(usb.writes)%2,1);self.assertEqual(outcome.state,'returned')
    def test_short_read_or_write_stops_before_trigger(self):
        for usb in [FakeUSB(read_size=15),FakeUSB(short=True)]:
            with self.assertRaises(InjectionError):inject(usb,b'x'*20000,b'r',lambda _:None)
            self.assertFalse(usb.triggered);self.assertTrue(usb.closed)
    def test_permission_error_is_not_success(self):
        usb=FakeUSB(trigger_error=PermissionError('denied'))
        with self.assertRaises(PermissionError):inject(usb,b'x'*20000,b'r',lambda _:None)
        self.assertTrue(usb.closed)
    def test_invalid_payload_still_closes_backend(self):
        usb=FakeUSB()
        with self.assertRaises(InjectionError):inject(usb,b'',b'r',lambda _:None)
        self.assertEqual(usb.writes,[]);self.assertTrue(usb.closed)
