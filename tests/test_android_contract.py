import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from apps.core import build_payload
ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(shutil.which('javac') and shutil.which('java'),'JDK required')
class AndroidPayloadContract(unittest.TestCase):
    def test_java_payload_matches_python_and_rejects_invalid_sizes(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            (p/'Vector.java').write_text('''import java.nio.file.*;import io.github.guiyu.hekate.PayloadBuilder;
public class Vector {public static void main(String[] a)throws Exception {
byte[] b=new byte[20480];for(int i=0;i<b.length;i++)b[i]=(byte)i;
Files.write(Paths.get(a[0]),PayloadBuilder.build(b,"RELOCATOR".getBytes("UTF-8")));
try{PayloadBuilder.build(new byte[0],new byte[1]);throw new AssertionError("empty accepted");}catch(IllegalArgumentException expected){}
try{PayloadBuilder.build(new byte[200000],new byte[1]);throw new AssertionError("oversize accepted");}catch(IllegalArgumentException expected){}
try{PayloadBuilder.build(new byte[1],new byte[0xe41]);throw new AssertionError("relocator accepted");}catch(IllegalArgumentException expected){}
}}''')
            source=ROOT/'apps/android/app/src/main/java/io/github/guiyu/hekate/PayloadBuilder.java'
            subprocess.run(['javac','-d',t,str(source),str(p/'Vector.java')],check=True,capture_output=True)
            subprocess.run(['java','-cp',t,'Vector',str(p/'payload')],check=True,capture_output=True)
            self.assertEqual((p/'payload').read_bytes(),build_payload(bytes(range(256))*80,b'RELOCATOR'))
