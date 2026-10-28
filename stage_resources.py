from session_guard import require_session_run
require_session_run()
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
STAGE=ROOT/'staging/resources-fw23';STAGE.mkdir(exist_ok=True)
plan=json.loads((ROOT/'downloads/plugins/download-plan.json').read_text())
outputs={};versions={}
def add(rel,data,project,tag):
 q=Path(rel)
 assert not q.is_absolute() and '..' not in q.parts
 if rel in outputs:
  assert outputs[rel]['sha256']==hashlib.sha256(data).hexdigest(),f'Conflicting package file: {rel}'
 target=STAGE/q;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 outputs[rel]={'sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'project':project,'version':tag}
raw_targets={'fpslocker':'switch/.overlays/FPSLocker.ovl','reversenx-rt':'switch/.overlays/ReverseNX-RT.ovl',
'ovl-sysmodules':'switch/.overlays/ovlSysmodules.ovl','jksv':'switch/JKSV/JKSV.nro',
'checkpoint':'switch/Checkpoint.nro','nx-shell':'switch/NX-Shell/NX-Shell.nro',
'dbi':'switch/DBI-Official-912ru/DBI.nro','hekate-toolbox':'switch/HekateToolbox.nro',
'saltynx-tool':'switch/SaltyNX-Tool/SaltyNX-Tool.nro','edizon-app':'switch/EdiZon/EdiZon.nro',
'goldleaf':'switch/Goldleaf/Goldleaf.nro'}
for a in plan:
 p=ROOT/a['dest'];assert p.exists() and p.stat().st_size==a['size'],a['project']
 data=p.read_bytes();h=hashlib.sha256(data).hexdigest()
 if a.get('digest'):assert a['digest']=='sha256:'+h,a['project']
 name=a['project'];tag=a['tag'];versions[name]={'version':tag,'source':a['source']}
 if name=='ultrahand':continue # install the verified full package below
 if p.suffix=='.zip':
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   for info in z.infolist():
    if info.is_dir():continue
    rel=info.filename
    if name=='wiliwili':
     # Wiliwili is packaged at SD-relative paths by its author.
     if rel.startswith('switch/'):pass
     elif rel.startswith('wiliwili/'):rel='switch/'+rel
     elif rel=='wiliwili.nro':rel='switch/wiliwili/wiliwili.nro'
     else:raise ValueError('Review Wiliwili package path: '+rel)
    if not rel.startswith(('atmosphere/','switch/','config/','SaltySD/')):continue
    if name=='sys-clk' and rel.endswith('/flags/boot2.flag'):continue
    add(rel,z.read(info),name,tag)
 else:add(raw_targets[name],data,name,tag)
meta=json.loads((ROOT/'downloads/plugins/ultrahand/sdout-verified.json').read_text())
p=ROOT/'downloads/plugins/ultrahand/sdout.zip';assert hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None
 for info in z.infolist():
  if not info.is_dir():add(info.filename,z.read(info),'ultrahand',meta['tag'])
# Respect the previous menu shortcut while providing official Simplified Chinese strings.
add('config/ultrahand/config.ini',b'[ultrahand]\nkey_combo=L+DDOWN\ndefault_lang=zh-cn\n','local-compatible-settings','20261027')
manifest={'versions':versions,'files':outputs,'sys_clk_enabled':False,'dbi_previous_entry_preserved':True}
(ROOT/'staging/resources-fw23-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('STAGED',len(outputs),'resource files',sum(r['size'] for r in outputs.values()),'bytes')
