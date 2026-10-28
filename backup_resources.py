from session_guard import require_session_run
require_session_run()
import hashlib,json
from pathlib import Path
sd=Path('/Volumes/Untitled');dest=Path('backups/resources-before-fw23-20261027')
assert sd.is_mount()
dest.mkdir(exist_ok=True);manifest={}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as r:
  while b:=r.read(1024**2):h.update(b)
 return h.hexdigest()
for name in ['atmosphere','bootloader','switch','config','SaltySD','exosphere.ini','payload.bin','hbmenu.nro']:
 root=sd/name
 for p in sorted(q for q in root.rglob('*') if q.is_file()) if root.is_dir() else [root]:
  rel=p.relative_to(sd);out=dest/rel;out.parent.mkdir(parents=True,exist_ok=True)
  hasher=hashlib.sha256()
  with p.open('rb') as r,out.open('wb') as w:
   while b:=r.read(1024**2):w.write(b);hasher.update(b)
  h=hasher.hexdigest()
  assert sha(out)==h,str(rel)
  manifest[str(rel)]={'size':p.stat().st_size,'sha256':h}
 print('RESOURCES BACKUP VERIFIED',name,flush=True)
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('RESOURCES BACKUP COMPLETE',len(manifest),'files',flush=True)
