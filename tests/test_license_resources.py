import tempfile
import unittest
from pathlib import Path
from apps.prepare_app_resources import verify_notices, REQUIRED_NOTICES

class LicenseResources(unittest.TestCase):
    def test_missing_runtime_notices_block_packaging(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):verify_notices(root)
            for name in REQUIRED_NOTICES:(root/name).write_text('license text',encoding='utf-8')
            verify_notices(root)
            (root/'libusb-LGPL-2.1.txt').unlink()
            with self.assertRaises(ValueError):verify_notices(root)
