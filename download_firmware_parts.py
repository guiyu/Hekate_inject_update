from session_guard import require_session_run
require_session_run()
import concurrent.futures,hashlib,json,subprocess,time
from pathlib import Path
j=json.loads(Path('downloads/firmware-23.0.1-release.json').read_text())
a=next(a for a in j['assets'] if a['name']=='Firmware.23.0.1.zip')
url=a['browser_download_url'];total=a['size'];count=32
parts=Path('downloads/firmware-23.0.1-parts');parts.mkdir(exist_ok=True)
size=(total+count-1)//count
started=time.monotonic()
def fetch(i):
 start=i*size;end=min(total,(i+1)*size)-1
 p=parts/f'{i:02d}.part'
 if p.exists() and p.stat().st_size==end-start+1:return i
 r=subprocess.run(['curl','-fsSL','--retry','2','--connect-timeout','15','--max-time','1000','--range',f'{start}-{end}',url,'-o',str(p)],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(f'Part {i}: '+r.stderr)
 assert p.stat().st_size==end-start+1,(i,p.stat().st_size,end-start+1)
 return i
with concurrent.futures.ThreadPoolExecutor(max_workers=32) as pool:
 futures=[pool.submit(fetch,i) for i in range(count)]
 for n,f in enumerate(concurrent.futures.as_completed(futures),1):
  i=f.result();print(f'PART {i:02d} verified length; {n}/{count} complete; {time.monotonic()-started:.0f}s',flush=True)
out=Path('downloads/Firmware.23.0.1.verified.zip');h=hashlib.sha256()
with out.open('wb') as w:
 for i in range(count):
  with (parts/f'{i:02d}.part').open('rb') as r:
   while block:=r.read(1024**2):w.write(block);h.update(block)
assert h.hexdigest()==a['digest'].split(':',1)[1],h.hexdigest()
assert out.stat().st_size==total
print('FIRMWARE SHA256 VERIFIED',h.hexdigest(),out,flush=True)
