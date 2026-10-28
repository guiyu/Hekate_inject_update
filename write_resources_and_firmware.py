"""Apply verified SD resources; stage firmware only, never install system firmware."""
from session_guard import require_session_run
require_session_run()
import hashlib,json,os,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent;SD=Path('/Volumes/Untitled')
BACKUP=ROOT/'backups/resources-before-fw23-20261027'
JOURNAL=ROOT/'logs/resources-fw23-write.json'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as r:
  while b:=r.read(1024**2):h.update(b)
 return h.hexdigest()
def main():
 assert SD.is_mount()
 emu=json.loads((ROOT/'backups/emummc-19.0.0-before-23.0.1-20261027/manifest.json').read_text())
 assert emu['state']=='complete-and-verified' and len(emu['files'])==10
 assert sha(SD/'emuMMC/SD00/eMMC/BOOT0')==emu['files']['BOOT0']['sha256'], 'SD boot identity changed'
 before=json.loads((BACKUP/'manifest.json').read_text())
 resources=json.loads((ROOT/'staging/resources-fw23-manifest.json').read_text())
 firmware=json.loads((ROOT/'downloads/firmware-23.0.1-files.json').read_text())
 assert not JOURNAL.exists(), 'Existing journal: inspect before retry'
 protected=['emuMMC/emummc.ini','exosphere.ini','atmosphere/config/system_settings.ini']
 protected += [str(p.relative_to(SD)) for p in (SD/'atmosphere/hosts').rglob('*') if p.is_file()]
 protected_hashes={rel:sha(SD/rel) for rel in protected}
 emu_ini=(SD/'emuMMC/emummc.ini').read_text()
 assert 'enabled=1' in emu_ini and 'path=emuMMC/SD00' in emu_ini
 writes={};skipped=[]
 for rel,row in resources['files'].items():
  p=ROOT/'staging/resources-fw23'/rel;assert sha(p)==row['sha256'],rel
  target=SD/rel
  if target.exists() and ((rel.startswith('config/') and rel.endswith('.ini')) or rel=='SaltySD/exceptions.txt'):
   skipped.append(rel);continue
  writes[rel]={'source':str(p),'sha256':row['sha256'],'project':row['project']}
 # Scope all sys-patch operations to emuMMC, preserving other settings.
 config_rel='config/sys-patch/config.ini';config=(SD/config_rel).read_bytes().decode('utf-8')
 assert re.search(r'(?m)^patch_sysmmc\s*=\s*[01]',config)
 config=re.sub(r'(?m)^patch_sysmmc\s*=\s*[01]','patch_sysmmc=0',config)
 config_source=ROOT/'staging/sys-patch-emummc-only.ini';config_source.write_bytes(config.encode('utf-8'))
 writes[config_rel]={'source':str(config_source),'sha256':sha(config_source),'project':'emuMMC-only-settings'}
 for name,row in firmware['files'].items():
  source=ROOT/'staging/firmware-23.0.1'/name;assert sha(source)==row['sha256']
  writes['firmware/23.0.1/'+name]={'source':str(source),'sha256':row['sha256'],'project':'firmware-staging-only'}
 renames=[]
 for rel in ['switch/.overlays/EdiZon.ovl','switch/.overlays/StatusMonitor.ovl','switch/.overlays/sys-clk.ovl','switch/.overlays/ovl-sysmodules.ovl','switch/Goldleaf0.9.nro','switch/HekateToolbox-4.0.3.nro','switch/sys-clk/sys-clk.nro','switch/ReverseNX-Tool3.1.2.nro','switch/KosmosToolbox/KosmosToolbox.nro']:
  if (SD/rel).is_file():
   assert rel in before and sha(SD/rel)==before[rel]['sha256'],rel
   dest=rel+'.disabled-20261027';assert not (SD/dest).exists();renames.append({'from':rel,'to':dest})
 for rel,row in writes.items():
  target=SD/rel;row['existed']=target.exists()
  if target.exists():assert rel in before and sha(target)==before[rel]['sha256'],f'No current backup: {rel}'
 # Do not enable the original sys-clk build on unconfirmed firmware 23.x.
 clock_flag=SD/'atmosphere/contents/00FF0000636C6BFF/flags/boot2.flag'
 assert not clock_flag.exists()
 journal={'state':'planned','writes':writes,'renames':renames,'preserved_settings':skipped,'protected_hashes':protected_hashes,'versions':resources['versions'],'system_firmware_installed':False}
 JOURNAL.write_text(json.dumps(journal,indent=2)+'\n')
 for i,(rel,row) in enumerate(writes.items(),1):
  source=Path(row['source']);target=SD/rel;target.parent.mkdir(parents=True,exist_ok=True)
  temp=target.with_name(target.name+'.codex-upgrade.tmp');assert not temp.exists(),str(temp)
  with source.open('rb') as r,temp.open('xb') as w:
   while b:=r.read(1024**2):w.write(b)
   w.flush();os.fsync(w.fileno())
  assert sha(temp)==row['sha256'],rel;temp.replace(target)
  if i%25==0:print('SD WRITE',i,'/',len(writes),flush=True)
 for row in renames:(SD/row['from']).rename(SD/row['to'])
 os.sync()
 for rel,row in writes.items():assert sha(SD/rel)==row['sha256'],rel
 for rel,h in protected_hashes.items():assert sha(SD/rel)==h,rel
 assert not clock_flag.exists()
 assert 'patch_sysmmc=0' in (SD/config_rel).read_text()
 journal['state']='resources-written-and-readback-verified-firmware-staged-awaiting-Daybreak'
 JOURNAL.write_text(json.dumps(journal,indent=2)+'\n')
 print('SD RESOURCES VERIFIED',len(writes),'files;',len(renames),'old aliases reversibly disabled; firmware staged, NOT installed',flush=True)
if __name__=='__main__':main()
