import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import prepare_runtime
import inject

class RuntimePreparation(unittest.TestCase):
    def test_download_is_verified_before_replacing_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'payload.bin'
            target.write_bytes(b'previous')
            with patch('urllib.request.urlopen', return_value=io.BytesIO(b'corrupt')):
                with self.assertRaises(ValueError):
                    prepare_runtime.download_file('https://example.invalid/payload', target, hashlib.sha256(b'correct').hexdigest())
            self.assertEqual(target.read_bytes(), b'previous')
            self.assertEqual(sorted(p.name for p in target.parent.iterdir()), ['payload.bin'])

    def test_valid_download_is_written(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'payload.bin'
            with patch('urllib.request.urlopen', return_value=io.BytesIO(b'correct')):
                prepare_runtime.download_file('https://example.invalid/payload', target, hashlib.sha256(b'correct').hexdigest())
            self.assertEqual(target.read_bytes(), b'correct')

    def test_injection_needs_only_selected_runtime_not_sd_archives(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            checks = {'downloads/sd.zip': '0' * 64, 'payloads/fusee-1.12.1.bin': '0' * 64}
            for rel in ['vendor/fusee_launcher.py', 'vendor/intermezzo.bin', 'payloads/hekate_ctcaer_6.5.4.bin']:
                p = root / rel
                p.parent.mkdir(exist_ok=True)
                p.write_bytes(b'verified')
                checks[rel] = hashlib.sha256(b'verified').hexdigest()
            (root / 'checksums.json').write_text(json.dumps(checks))
            inject.validate_runtime(root, 'hekate')

    def test_runtime_check_rejects_tampered_vendor_code(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'vendor/fusee_launcher.py'
            p.parent.mkdir()
            p.write_bytes(b'tampered')
            (root / 'checksums.json').write_text(json.dumps({'vendor/fusee_launcher.py': '0' * 64}))
            with self.assertRaises(ValueError):
                inject.validate_runtime(root, 'hekate')

if __name__ == '__main__':
    unittest.main()
