import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('git'),'Git required')
class WindowsCheckout(unittest.TestCase):
    def test_git_windows_checkout_preserves_pinned_vendor_bytes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'vendor').mkdir();source=(ROOT/'vendor/fusee_launcher.py').read_bytes()
            (p/'vendor/fusee_launcher.py').write_bytes(source);(p/'.gitattributes').write_bytes((ROOT/'.gitattributes').read_bytes())
            subprocess.run(['git','init','-q',t],check=True,capture_output=True)
            subprocess.run(['git','-C',t,'-c','core.autocrlf=false','add','.'],check=True,capture_output=True)
            out=p/'windows';out.mkdir()
            subprocess.run(['git','-C',t,'-c','core.autocrlf=true','checkout-index','-f','-a','--prefix='+str(out)+'/'],check=True,capture_output=True)
            self.assertEqual(hashlib.sha256((out/'vendor/fusee_launcher.py').read_bytes()).hexdigest(),hashlib.sha256(source).hexdigest())
