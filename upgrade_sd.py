#!/usr/bin/env python3
"""One-time, backed-up SD file update. No partition or firmware operations."""
from session_guard import require_session_run
require_session_run()
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
SD = Path('/Volumes/Untitled')
BACKUP = ROOT / 'backups/ams-1.8.0-before-1.12.1-20261027'
JOURNAL = ROOT / 'logs/sd-upgrade-20261027.json'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    before = json.loads((BACKUP / 'manifest.json').read_text())
    assert SD.is_mount() and (SD / 'emuMMC/emummc.ini').is_file()
    assert not JOURNAL.exists(), 'Journal already exists; inspect before retrying'
    # Verify saved critical files still match the card before any modification.
    for rel in ['atmosphere/package3','bootloader/hekate_ipl.ini','emuMMC/emummc.ini','exosphere.ini']:
        assert digest((SD / rel).read_bytes()) == before[rel]['sha256'], rel
    protected = ['emuMMC/emummc.ini','exosphere.ini']
    for prefix in ['atmosphere/config','atmosphere/hosts']:
        protected += [str(p.relative_to(SD)) for p in (SD / prefix).rglob('*') if p.is_file()]
    protected_hashes = {rel: digest((SD / rel).read_bytes()) for rel in protected}
    expected = json.loads((ROOT / 'checksums.json').read_text())
    writes = {}
    for archive, prefix in [('downloads/atmosphere-1.12.1.zip',''),('downloads/hekate_ctcaer_6.5.4_Nyx_1.9.4.zip','bootloader/')]:
        assert digest((ROOT / archive).read_bytes()) == expected[archive]
        with zipfile.ZipFile(ROOT / archive) as z:
            assert z.testzip() is None
            for info in z.infolist():
                if info.is_dir() or (prefix and not info.filename.startswith(prefix)): continue
                rel = Path(info.filename)
                assert not rel.is_absolute() and '..' not in rel.parts
                writes[str(rel)] = z.read(info)
    hekate = (ROOT / 'payloads/hekate_ctcaer_6.5.4.bin').read_bytes()
    fusee = (ROOT / 'payloads/fusee-1.12.1.bin').read_bytes()
    assert digest(hekate) == expected['payloads/hekate_ctcaer_6.5.4.bin']
    assert digest(fusee) == expected['payloads/fusee-1.12.1.bin']
    writes['atmosphere/reboot_payload.bin'] = hekate
    writes['payload.bin'] = hekate
    writes['bootloader/payloads/Atmosphere.bin'] = fusee
    writes['bootloader/payloads/fusee.bin'] = fusee
    ini = (SD / 'bootloader/hekate_ipl.ini').read_bytes().decode('utf-8')
    ini = ini.replace('大气层v1.8.0','大气层v1.12.1')
    ini = ini.replace('kip1patch=nosigchk', '# kip1patch=nosigchk (legacy 1.8.0 patch request disabled)')
    writes['bootloader/hekate_ipl.ini'] = ini.encode('utf-8')
    flags = [str(p.relative_to(SD)) for p in (SD / 'atmosphere/contents').glob('*/flags/boot2.flag')]
    journal = {'state':'planned','sd':str(SD),'backup':str(BACKUP),'writes':[],
               'disabled_boot_flags':flags,'protected':protected_hashes}
    for rel,data in writes.items():
        target = SD / rel
        existed = target.exists()
        if existed:
            assert rel in before, f'No backup for {rel}'
            assert digest(target.read_bytes()) == before[rel]['sha256'], f'Changed since backup: {rel}'
        journal['writes'].append({'path':rel,'existed':existed,'sha256':digest(data)})
    JOURNAL.write_text(json.dumps(journal,indent=2)+'\n')
    for rel,data in writes.items():
        target = SD / rel
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary = target.with_name(target.name+'.codex-upgrade.tmp')
        assert not temporary.exists()
        with temporary.open('wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        assert digest(temporary.read_bytes()) == digest(data), rel
        temporary.replace(target)
        print('Written and verified:',rel,flush=True)
    for rel in flags:
        p = SD / rel
        disabled = p.with_name('boot2.flag.disabled-20261027')
        assert not disabled.exists()
        p.rename(disabled)
    os.sync()
    for row in journal['writes']:
        assert digest((SD / row['path']).read_bytes()) == row['sha256'],row['path']
    for rel,h in protected_hashes.items():
        assert digest((SD / rel).read_bytes()) == h, f'Protected config changed: {rel}'
    journal['state']='written-and-readback-verified-awaiting-console-boot'
    JOURNAL.write_text(json.dumps(journal,indent=2)+'\n')
    print('VERIFIED:',len(writes),'written files;',len(flags),'boot plugins reversibly disabled;',len(protected_hashes),'protected config files unchanged.')

if __name__ == '__main__':
    main()
