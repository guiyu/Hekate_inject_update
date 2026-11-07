"""Prepare offline resources, pinned Windows DLL and redistribution notices."""
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import shutil
import struct
import subprocess
from prepare_runtime import prepare, download_file
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE_SHA='38605d8d5a86f408a4b7bec60f6d4a096050eee72f89a63a8d5be125252d3fe7'
DLL_SHA='0690cd87d0069edac3a867e0b51f379afa77159eda3b45cd02740fc6afb546d8'

def check_pe_x64(data):
    if len(data)<64 or data[:2]!=b'MZ':raise ValueError('Invalid PE')
    offset=struct.unpack_from('<I',data,0x3c)[0]
    if offset+6>len(data) or data[offset:offset+4]!=b'PE\0\0' or struct.unpack_from('<H',data,offset+4)[0]!=0x8664:
        raise ValueError('Expected Windows AMD64 DLL')

def make(windows=None):
    prepare(ROOT)
    dest=ROOT/'apps/resources';dest.mkdir(parents=True,exist_ok=True)
    for name,source in [('payload.bin',ROOT/'payloads/hekate_ctcaer_6.5.4.bin'),('intermezzo.bin',ROOT/'vendor/intermezzo.bin'),('icon.png',ROOT/'apps/icons/ui.png')]:
        shutil.copy2(source,dest/name)
    notices=dest/'licenses';notices.mkdir(exist_ok=True)
    shutil.copy2(ROOT/'LICENSE',notices/'PROJECT-GPL-2.0.txt')
    for f in (ROOT/'apps/licenses').iterdir():
        if f.is_file(): shutil.copy2(f,notices/f.name)
    (notices/'SOURCES.txt').write_text('Hekate 6.5.4 (GPL-2.0): https://github.com/CTCaer/hekate/tree/v6.5.4\nIntermezzo (GPL-2.0): https://github.com/nh-server/fusee-interfacee-tk/tree/fc1497e30c95db83d112899de22057590f039940\nlibusbK 3.1.0.0 (LGPL-3.0 / BSD components): https://github.com/mcuee/libusbk/releases/tag/V3.1.0.0\nCorresponding libusbK source: https://github.com/mcuee/libusbk/releases/download/V3.1.0.0/libusbK-3.1.0.0-src.7z\nProject source and build scripts: https://github.com/guiyu/Hekate_inject_update\n',encoding='utf-8')
    for name in ('pyusb','libusb-package','pyinstaller','certifi','pillow'):
        dist=importlib.metadata.distribution(name)
        for f in dist.files or []:
            if any(s in str(f).lower() for s in ('license','copying','notice')) and Path(dist.locate_file(f)).is_file():
                shutil.copyfile(dist.locate_file(f),notices/(name+'-'+Path(f).name))
    if windows if windows is not None else platform.system()=='Windows':
        archive=ROOT/'build/deps/libusbK-3.1.0.0-bin.7z';archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=ARCHIVE_SHA:
            download_file('https://github.com/mcuee/libusbk/releases/download/V3.1.0.0/libusbK-3.1.0.0-bin.7z',archive,ARCHIVE_SHA)
        unzip=shutil.which('7z') or shutil.which('7zz') or r'C:\Program Files\7-Zip\7z.exe'
        unpack=ROOT/'build/deps/libusbk'
        subprocess.run([unzip,'x','-y',f'-o{unpack}',str(archive)],check=True,stdout=subprocess.DEVNULL)
        dll=unpack/'libusbK-3.1.0.0-bin/bin/dll/amd64/libusbK.dll'
        data=dll.read_bytes();check_pe_x64(data)
        if hashlib.sha256(data).hexdigest()!=DLL_SHA:raise ValueError('libusbK SHA256 mismatch')
        shutil.copy2(dll,dest/'libusbK.dll')
    manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir() if p.is_file() and p.name!='resources.json'}
    (dest/'resources.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return dest
if __name__=='__main__':make()
