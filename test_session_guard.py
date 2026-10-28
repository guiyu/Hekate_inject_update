import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ['backup_emummc.py', 'backup_resources.py', 'download_firmware_parts.py',
           'download_plugin_assets.py', 'stage_resources.py', 'upgrade_sd.py',
           'write_resources_and_firmware.py']

class SessionGuard(unittest.TestCase):
    def test_session_scripts_do_not_execute_without_opt_in(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in SCRIPTS:
                with self.subTest(script=name):
                    result = subprocess.run([sys.executable, str(ROOT / name)], cwd=folder, capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('--run-session-script', result.stderr)
                    self.assertEqual(list(Path(folder).iterdir()), [])

    def test_optimized_python_cannot_bypass_assertion_checks(self):
        result = subprocess.run([sys.executable, '-O', str(ROOT / 'upgrade_sd.py'), '--run-session-script'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('python -O', result.stderr)

if __name__ == '__main__':
    unittest.main()
