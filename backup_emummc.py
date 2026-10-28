from session_guard import require_session_run
require_session_run()
import hashlib,json,os,shutil,time
from pathlib import Path
sd=Path('/Volumes/Untitled');src=sd/'emuMMC/SD00/eMMC'
dest=Path('backups/emummc-19.0.0-before-23.0.1-20261027')
assert src.is_dir() and sd.is_mount()
files=sorted(p for p in src.iterdir() if p.is_file());total=sum(p.stat().st_size for p in files)
dest.mkdir(exist_ok=True)
progress=dest/'progress.json';result=json.loads(progress.read_text()) if progress.exists() else {}
def filehash(p):
 h=hashlib.sha256()
 with p.open('rb') as r:
  while b:=r.read(8*1024**2):h.update(b)
 return h.hexdigest()
for name,row in result.items():
 assert (dest/name).stat().st_size==row['size'] and filehash(dest/name)==row['sha256'],name
remaining=sum(p.stat().st_size-(dest/p.name).stat().st_size if (dest/p.name).exists() else p.stat().st_size for p in files if p.name not in result)
assert shutil.disk_usage('.').free > remaining+5*1024**3
started=time.monotonic();written=0;done=sum(row['size'] for row in result.values())
print('RESUMING; complete verified files:',list(result),flush=True)
for p in files:
 if p.name in result:continue
 st=p.stat();out=dest/p.name;offset=out.stat().st_size if out.exists() else 0
 assert offset<=st.st_size
 h=hashlib.sha256();copied=offset;next_report=offset+512*1024**2
 with p.open('rb') as r:
  if offset:
   prefix=hashlib.sha256()
   with out.open('rb') as old:
    left=offset
    while left:
     b=r.read(min(8*1024**2,left));ob=old.read(len(b))
     assert b and b==ob,f'Partial backup prefix differs: {p.name}'
     h.update(b);left-=len(b)
   print('PARTIAL PREFIX VERIFIED',p.name,offset,flush=True)
  with out.open('ab') as w:
   while b:=r.read(8*1024**2):
    w.write(b);h.update(b);copied+=len(b);written+=len(b)
    if copied>=next_report:
     print(f'COPY {(done+copied)/1024**3:.1f}/{total/1024**3:.1f} GiB, {written/max(1,time.monotonic()-started)/1024**2:.1f} MiB/s',flush=True);next_report+=512*1024**2
   w.flush();os.fsync(w.fileno())
 assert copied==st.st_size and filehash(out)==h.hexdigest(),p.name
 assert p.stat().st_size==st.st_size and p.stat().st_mtime_ns==st.st_mtime_ns,p.name
 result[p.name]={'size':copied,'sha256':h.hexdigest()};done+=copied
 progress.write_text(json.dumps(result,indent=2)+'\n');print('VERIFIED',p.name,copied,flush=True)
for name in ['emuMMC/emummc.ini','emuMMC/SD00/file_based']:
 t=dest/name;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(sd/name,t)
(dest/'manifest.json').write_text(json.dumps({'state':'complete-and-verified','bytes':total,'files':result},indent=2)+'\n')
print('FULL EMUMMC BACKUP VERIFIED',total,'bytes',flush=True)
