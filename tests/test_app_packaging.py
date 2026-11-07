import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from apps.desktop import runtime_root, App
from apps.transports import DevInfo, Overlapped
from apps.prepare_app_resources import check_pe_x64

class PackagingTests(unittest.TestCase):
    def test_frozen_resources_ignore_working_directory(self):
        with patch('sys._MEIPASS','/a/bundle',create=True):
            self.assertEqual(runtime_root(),Path('/a/bundle/resources'))
    def test_public_windows_layout(self):
        self.assertEqual(ctypes.sizeof(DevInfo),2596)
        self.assertEqual(ctypes.sizeof(Overlapped),32 if ctypes.sizeof(ctypes.c_void_p)==8 else 20)
    def test_reject_non_pe_and_wrong_architecture(self):
        for data in (b'bad',b'MZ'+bytes(256)):
            with self.assertRaises(ValueError):check_pe_x64(data)
    def test_close_during_usb_operation_is_deferred(self):
        app=object.__new__(App);app.busy=True;app.close_requested=False
        app.close()
        self.assertTrue(app.close_requested)
