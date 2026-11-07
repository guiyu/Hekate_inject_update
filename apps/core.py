"""Strict, platform-neutral RCM layout and transfer orchestration (GPL-2.0)."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct

VERSION = '1.0.0'
HEKATE_VERSION = '6.5.4'
VID, PID = 0x0955, 0x7321

class InjectionError(RuntimeError):
    pass

@dataclass(frozen=True)
class TriggerOutcome:
    state: str
    message: str

def build_payload(payload: bytes, relocator: bytes) -> bytes:
    # Layout follows the GPLv2 Fusée Launcher by Kate Temkin/Mikaela Szekely.
    if not payload or not relocator or len(relocator) > 0xe40:
        raise InjectionError('载荷或重定位文件大小无效')
    b = bytearray(struct.pack('<I', 0x30298) + bytes(676))
    b += relocator + bytes(0xe40 - len(relocator))
    b += payload[:0x4000]
    # Hekate is larger than this boundary; reject shorter payloads rather than
    # accidentally moving the stack spray to a different address.
    b += bytes(max(0, 0x4000 - len(payload)))
    b += struct.pack('<I', 0x40010000) * (0x21c0 // 4)
    b += payload[0x4000:]
    b += bytes(4096 - len(b) % 4096)
    if len(b) > 0x30298:
        raise InjectionError('载荷过大，拒绝发送')
    return bytes(b)

def verified_resources(root: Path):
    try:
        manifest = json.loads((root / 'resources.json').read_text(encoding='utf-8'))
        result = []
        for name in ('payload.bin', 'intermezzo.bin'):
            b = (root / name).read_bytes()
            if hashlib.sha256(b).hexdigest() != manifest[name]:
                raise InjectionError(f'文件校验失败：{name}')
            result.append(b)
        return tuple(result)
    except (OSError, KeyError, ValueError) as exc:
        raise InjectionError(f'运行资源缺失或清单无效：{exc}') from exc

def inject(backend, payload, relocator, log=print):
    """Backend is already opened. Always close it, including validation failures."""
    try:
        image = build_payload(payload, relocator)
        log('读取 RCM 握手（不记录设备标识）…')
        if len(backend.read(16)) != 16:
            raise InjectionError('RCM 握手不完整，已停止')
        log(f'发送已校验的 Hekate {HEKATE_VERSION}…')
        packets = 0
        for offset in range(0, len(image), 4096):
            chunk = image[offset:offset + 4096]
            if backend.write(chunk) != len(chunk):
                raise InjectionError('USB 写入不完整，已停止；请重新进入 RCM')
            packets += 1
        if packets % 2 == 0:
            if backend.write(bytes(4096)) != 4096:
                raise InjectionError('USB 缓冲切换不完整，已停止')
        log('载荷传输完成，提交启动触发请求…')
        return backend.trigger(0x7000)
    finally:
        backend.close()
