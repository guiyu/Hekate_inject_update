#!/usr/bin/env python3
"""macOS Switch RCM launcher; USB submission does not prove screen boot."""
import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent

def validate_file(path, digest):
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f'SHA-256 不匹配，拒绝注入: {path}')

def validate_runtime(root, payload):
    manifest = json.loads((root / 'checksums.json').read_text())
    required = ['vendor/fusee_launcher.py', 'vendor/intermezzo.bin',
                'payloads/hekate_ctcaer_6.5.4.bin' if payload == 'hekate' else 'payloads/fusee-1.12.1.bin']
    for relative in required:
        validate_file(root / relative, manifest[relative])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='只检测 USB，不发送载荷')
    parser.add_argument('--payload', choices=['hekate', 'fusee'], default='hekate')
    parser.add_argument('--sd-atmosphere-version', help='fusee 必须与 SD 卡大气层版本匹配')
    args = parser.parse_args()
    if platform.system() != 'Darwin':
        parser.error('此入口只用于 macOS')
    if args.payload == 'fusee' and args.sd_atmosphere_version != '1.12.1':
        parser.error('请先核实 SD 卡 atmosphere 版本，再传入 --sd-atmosphere-version 1.12.1')
    validate_runtime(ROOT, args.payload)
    import usb.core
    import libusb_package
    backend = libusb_package.get_libusb1_backend()
    if backend is None:
        raise RuntimeError('无法加载 libusb，请重新安装项目依赖')
    dev = usb.core.find(idVendor=0x0955, idProduct=0x7321, backend=backend)
    if dev is None:
        print('未检测到 APX/RCM。检查数据线、RCM 状态；Codex 沙箱内需要设备访问权限。', file=sys.stderr)
        return 2
    print('已检测到 NVIDIA APX 0955:7321；文件哈希通过。', flush=True)
    if args.check:
        return 0
    sys.path.insert(0, str(ROOT / 'vendor'))
    import fusee_launcher
    # Explicit backend path avoids relying on a global Homebrew libusb install.
    def find_device(self, vid=None, pid=None):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid, backend=backend)
        return self.dev
    fusee_launcher.MacOSBackend.find_device = find_device
    payload = ROOT / 'payloads' / ('hekate_ctcaer_6.5.4.bin' if args.payload == 'hekate' else 'fusee-1.12.1.bin')
    fusee_launcher.do_hax(SimpleNamespace(payload=str(payload), relocator=str(ROOT / 'vendor/intermezzo.bin'),
        wait=False, vid=None, pid=None, platform=None, skip_checks=False, permissive_id=False))
    print('注入流程已执行。上游 Launch complete 仅表示 USB 触发阶段结束；请以 Switch 屏幕为准。')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'注入失败: {exc}', file=sys.stderr)
        sys.exit(1)
