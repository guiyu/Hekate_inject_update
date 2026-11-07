"""macOS libusb and Windows libusbK 3.1 public-API transports (GPL-2.0)."""
import ctypes as C
import hashlib
import json
import platform
from pathlib import Path
from .core import VID, PID, InjectionError, TriggerOutcome

class MacUSB:
    def __init__(self, resources=None):
        import usb.core
        import usb.util
        import libusb_package
        self.usb = usb
        backend = libusb_package.get_libusb1_backend()
        if backend is None:
            raise InjectionError('无法加载内置 libusb')
        self.dev = usb.core.find(idVendor=VID, idProduct=PID, backend=backend)
        if self.dev is None:
            raise InjectionError('未检测到 APX/RCM；请检查数据线，并将 Switch 置于 RCM')
        # No device ID read here: detection must not consume the RCM handshake.
    def read(self, n): return bytes(self.dev.read(0x81, n, timeout=1500))
    def write(self, b): return self.dev.write(0x01, b, timeout=1500)
    def trigger(self, n):
        try:
            self.dev.ctrl_transfer(0x82, 0, 0, 0, n, timeout=1500)
            return TriggerOutcome('returned', '触发请求已返回；请查看 Switch 屏幕确认启动')
        except self.usb.core.USBError as exc:
            if exc.backend_error_code in (-1, -4, -7):
                return TriggerOutcome('uncertain', f'触发阶段 USB 返回 {exc.backend_error_code}；可能已断开或超时，启动结果请查看 Switch 屏幕')
            raise InjectionError(f'触发失败：{exc}') from exc
    def close(self): self.usb.util.dispose_resources(self.dev)

# Exact fixed-width public structures from libusbK 3.1.0.0 libusbk.h.
class Common(C.Structure):
    _fields_ = [('Vid', C.c_int32), ('Pid', C.c_int32), ('MI', C.c_int32), ('InstanceID', C.c_char * 256)]
class DevInfo(C.Structure):
    _fields_ = [('Common', Common), ('DriverID', C.c_int32)] + [(n, C.c_char * 256) for n in (
        'DeviceInterfaceGUID', 'DeviceID', 'ClassGUID', 'Mfg', 'DeviceDesc', 'Service', 'SymbolicLink', 'DevicePath')
    ] + [(n, C.c_int32) for n in ('LUsb0FilterIndex', 'Connected', 'SyncFlags', 'BusNumber', 'DeviceAddress')] + [('SerialNumber', C.c_char * 256)]
class Overlapped(C.Structure):
    _fields_ = [('Internal', C.c_size_t), ('InternalHigh', C.c_size_t), ('Offset', C.c_uint32),
                ('OffsetHigh', C.c_uint32), ('hEvent', C.c_void_p)]

def load_windows_library(resources):
    dll = Path(resources) / 'libusbK.dll'
    expected = json.loads((Path(resources) / 'resources.json').read_text())['libusbK.dll']
    if hashlib.sha256(dll.read_bytes()).hexdigest() != expected:
        raise InjectionError('libusbK.dll 校验失败')
    # Absolute path, restricted DLL search: never load a DLL from the working dir.
    lib = C.WinDLL(str(dll.resolve()), use_last_error=True, winmode=0x00001100)
    signatures = {
        'LstK_Init': [C.POINTER(C.c_void_p), C.c_uint32],
        'LstK_Free': [C.c_void_p],
        'LstK_FindByVidPid': [C.c_void_p, C.c_int32, C.c_int32, C.POINTER(C.POINTER(DevInfo))],
        'UsbK_Init': [C.POINTER(C.c_void_p), C.POINTER(DevInfo)],
        'UsbK_Free': [C.c_void_p],
        'UsbK_GetProperty': [C.c_void_p, C.c_int32, C.POINTER(C.c_uint32), C.c_void_p],
        'UsbK_SetPipePolicy': [C.c_void_p, C.c_ubyte, C.c_uint32, C.c_uint32, C.c_void_p],
    }
    pipe = [C.c_void_p, C.c_ubyte, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p]
    signatures['UsbK_ReadPipe'] = signatures['UsbK_WritePipe'] = pipe
    for name, args in signatures.items():
        f = getattr(lib, name); f.argtypes = args; f.restype = C.c_int32
    return lib

class WindowsUSB:
    def __init__(self, resources):
        self.lib = load_windows_library(resources)
        self.lst = C.c_void_p(); self.handle = C.c_void_p()
        try:
            if not self.lib.LstK_Init(C.byref(self.lst), 0):
                raise InjectionError('无法列出 USB 设备；请检查 APX 的 libusbK 驱动')
            info = C.POINTER(DevInfo)()
            if not self.lib.LstK_FindByVidPid(self.lst, VID, PID, C.byref(info)):
                raise InjectionError('未检测到可用 APX；请检查 RCM、数据线和 libusbK 驱动')
            if info.contents.DriverID != 0:
                raise InjectionError('APX 驱动不是 libusbK；请按说明仅为 APX 安装 libusbK 驱动')
            if not self.lib.UsbK_Init(C.byref(self.handle), info):
                raise C.WinError(C.get_last_error())
            timeout = C.c_uint32(1500)
            for endpoint in (0x81, 0x01):
                if not self.lib.UsbK_SetPipePolicy(self.handle, endpoint, 3, 4, C.byref(timeout)):
                    raise C.WinError(C.get_last_error())
            # Keep list alive until after handle initialization and all operations.
        except Exception:
            self.close(); raise
    def _pipe(self, read, value):
        n = value if read else len(value)
        b = C.create_string_buffer(n) if read else C.create_string_buffer(value, n)
        transferred = C.c_uint32()
        f = self.lib.UsbK_ReadPipe if read else self.lib.UsbK_WritePipe
        if not f(self.handle, 0x81 if read else 0x01, b, n, C.byref(transferred), None):
            raise C.WinError(C.get_last_error())
        return b.raw[:transferred.value] if read else transferred.value
    def read(self, n): return self._pipe(True, n)
    def write(self, b): return self._pipe(False, b)
    def trigger(self, n):
        # Public KUSB_PROPERTY_DEVICE_FILE_HANDLE, no private structure offsets.
        master = C.c_void_p(); size = C.c_uint32(C.sizeof(master))
        if not self.lib.UsbK_GetProperty(self.handle, 0, C.byref(size), C.byref(master)) or not master.value:
            raise InjectionError('无法取得 libusbK 控制句柄')
        k = C.WinDLL('kernel32', use_last_error=True)
        k.CreateEventW.argtypes = [C.c_void_p,C.c_int32,C.c_int32,C.c_wchar_p]; k.CreateEventW.restype=C.c_void_p
        k.CloseHandle.argtypes=[C.c_void_p]; k.CloseHandle.restype=C.c_int32
        k.DeviceIoControl.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.POINTER(Overlapped)]; k.DeviceIoControl.restype=C.c_int32
        k.WaitForSingleObject.argtypes=[C.c_void_p,C.c_uint32]; k.WaitForSingleObject.restype=C.c_uint32
        k.GetOverlappedResult.argtypes=[C.c_void_p,C.POINTER(Overlapped),C.POINTER(C.c_uint32),C.c_int32]; k.GetOverlappedResult.restype=C.c_int32
        k.CancelIoEx.argtypes=[C.c_void_p,C.POINTER(Overlapped)]; k.CancelIoEx.restype=C.c_int32
        event=k.CreateEventW(None,1,0,None)
        if not event: raise C.WinError(C.get_last_error())
        ov=Overlapped();ov.hEvent=event
        # libusb_request: timeout + 20-byte union; status.recipient=endpoint (2).
        raw=(C.c_uint32*6)(1000,2,0,0,0,0); out=C.create_string_buffer(n); count=C.c_uint32()
        try:
            ok=k.DeviceIoControl(master,0x22201c,raw,24,out,n,C.byref(count),C.byref(ov))
            code=0 if ok else C.get_last_error()
            if not ok and code==997:  # ERROR_IO_PENDING
                wait=k.WaitForSingleObject(event,2500)
                if wait!=0:
                    k.CancelIoEx(master,C.byref(ov))
                    # Drain cancellation before Python releases overlapped/buffers.
                    k.GetOverlappedResult(master,C.byref(ov),C.byref(count),1)
                    raise InjectionError('触发等待超时并已取消；请查看屏幕，重试前重新进入 RCM')
                ok=k.GetOverlappedResult(master,C.byref(ov),C.byref(count),0)
                code=0 if ok else C.get_last_error()
            if ok:
                return TriggerOutcome('returned','触发请求已返回；请查看 Switch 屏幕确认启动')
            if code in (31,121,1167):
                return TriggerOutcome('uncertain',f'触发阶段 Windows 返回 {code}；启动结果未确认，请查看 Switch 屏幕')
            raise InjectionError(f'触发失败，Windows 错误码 {code}')
        finally:
            k.CloseHandle(event)
    def close(self):
        if self.handle.value:
            self.lib.UsbK_Free(self.handle);self.handle=C.c_void_p()
        if self.lst.value:
            self.lib.LstK_Free(self.lst);self.lst=C.c_void_p()

def open_backend(resources):
    system = platform.system()
    if system == 'Darwin': return MacUSB(resources)
    if system == 'Windows': return WindowsUSB(resources)
    raise InjectionError('桌面应用仅支持 macOS 和 Windows')
