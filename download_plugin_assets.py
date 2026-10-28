from session_guard import require_session_run
require_session_run()
import concurrent.futures,json,subprocess,hashlib,time
from pathlib import Path
plan=json.loads(Path('downloads/plugins/download-plan.json').read_text())
def fetch(a):
 p=Path(a['dest'])
 if not p.exists() or p.stat().st_size!=a['size']:
  r=subprocess.run(['curl','-fsSL','--retry','2','--connect-timeout','15','--max-time','1800',a['url'],'-o',str(p)],capture_output=True,text=True)
  if r.returncode: return {'project':a['project'],'error':r.stderr.strip()}
 if p.stat().st_size!=a['size']:return {'project':a['project'],'error':'length mismatch'}
 h=hashlib.sha256(p.read_bytes()).hexdigest()
 if a.get('digest') and a['digest']!='sha256:'+h:return {'project':a['project'],'error':'SHA256 mismatch'}
 a['sha256']=h;a['state']='downloaded-and-verified'
 return a
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 for r in pool.map(fetch,plan):
  results.append(r)
  print(r['project'],r.get('state',r.get('error')),flush=True)
  Path('downloads/plugins/download-results.json').write_text(json.dumps(results,indent=2)+'\n')
print('PLUGIN DOWNLOADS DONE',len(results),flush=True)
