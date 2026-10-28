import hashlib
import tempfile
import unittest
from pathlib import Path
import inject

class PayloadValidation(unittest.TestCase):
    def test_rejects_corrupted_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'bad.bin'
            p.write_bytes(b'broken')
            with self.assertRaises(ValueError):
                inject.validate_file(p, hashlib.sha256(b'original').hexdigest())

    def test_accepts_exact_download(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'ok.bin'
            p.write_bytes(b'original')
            inject.validate_file(p, hashlib.sha256(b'original').hexdigest())

    def test_missing_payload_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            inject.validate_file(Path('/nonexistent/payload.bin'), '0' * 64)
