import io
import unittest
from unittest.mock import patch
from apps.build_support import configure_console

class ConsoleEncoding(unittest.TestCase):
    def test_redirected_legacy_windows_console_accepts_chinese(self):
        buffer=io.BytesIO();stream=io.TextIOWrapper(buffer,encoding='cp1252')
        with patch('sys.stdout',stream),patch('sys.stderr',None):
            configure_console();print('运行文件已校验');stream.flush()
        self.assertIn('运行文件已校验'.encode('utf-8'),buffer.getvalue())
