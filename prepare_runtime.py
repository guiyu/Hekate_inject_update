#!/usr/bin/env python3
"""Fetch pinned, hash-verified runtime assets; never communicate with a Switch."""
import argparse
import hashlib
import json
import os
import ssl
import tempfile
import urllib.request
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parent

def download_file(url, target, expected_sha256):
    """Publish a download only after its digest matches; preserve existing files on error."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.runtime-', delete=False) as stream:
            temporary = Path(stream.name)
            digest = hashlib.sha256()
            request = urllib.request.Request(url, headers={'User-Agent': 'Hekate-inject-update'})
            with urllib.request.urlopen(request, timeout=60, context=ssl.create_default_context(cafile=certifi.where())) as response:
                while chunk := response.read(1024 * 1024):
                    stream.write(chunk)
                    digest.update(chunk)
            stream.flush()
            os.fsync(stream.fileno())
        if digest.hexdigest() != expected_sha256:
            raise ValueError(f'SHA-256 不匹配，未替换文件: {target}')
        temporary.replace(target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def prepare(root=ROOT, check_only=False):
    root = Path(root)
    sources = json.loads((root / 'manifests/runtime-sources.json').read_text())
    checks = json.loads((root / 'checksums.json').read_text())
    for relative, source in sources.items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError(f'非法运行文件路径: {relative}')
        if source['sha256'] != checks[relative]:
            raise ValueError(f'两个清单的哈希不一致: {relative}')
        target = root / path
        valid = target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == source['sha256']
        if not valid:
            if check_only:
                raise ValueError(f'运行文件缺失或校验失败: {relative}；请运行 python3 prepare_runtime.py')
            download_file(source['url'], target, source['sha256'])
        print(f'运行文件已校验: {relative}')
    # The vendored Python source is tracked and must match its recorded digest too.
    source = root / 'vendor/fusee_launcher.py'
    if hashlib.sha256(source.read_bytes()).hexdigest() != checks['vendor/fusee_launcher.py']:
        raise ValueError('vendor/fusee_launcher.py 校验失败')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='只检查本机文件，不联网或访问 USB')
    args = parser.parse_args()
    try:
        prepare(check_only=args.check)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f'运行环境准备失败: {exc}\n')

if __name__ == '__main__':
    main()
