#!/usr/bin/env python3
"""Collect actual native Rodin artifacts and PO inventory after a completed run."""
from pathlib import Path
import argparse,json,csv,shutil,xml.etree.ElementTree as ET
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'DelegatedAuthorization';P='org.eventb.core.'
p=argparse.ArgumentParser();p.add_argument('--workspace-project',required=True,type=Path);p.add_argument('--native-log',required=True,type=Path);args=p.parse_args();src=args.workspace_project
log=args.native_log.read_text()
destination=BASE/'validation/rodin_native.log'
if destination.exists():destination.unlink()
shutil.copy2(args.native_log,destination)
assert 'STATIC_ERRORS 0' in log and 'NATIVE_BUILD_COMPLETE' in log
components=[];inventory=[]
for source in sorted(OUT.iterdir()):
 if source.suffix not in ('.bum','.buc'):continue
 assert source.read_bytes()==(src/source.name).read_bytes(),f'Stale native source: {source}'
 stem=source.stem;sc=src/(stem+('.bcm' if source.suffix=='.bum' else '.bcc'))
 assert ET.parse(sc).getroot().get(P+'accurate')=='true'
 statuses=ET.parse(src/(stem+'.bps')).getroot().findall(P+'psStatus');discharged=0
 for po in statuses:
  confidence=int(po.get(P+'confidence'));closed=confidence>=1000
  assert confidence in (-99,1000),f'Unexpected confidence {confidence}'
  assert po.get(P+'psManual')=='false','A proof was not saved by the native AutoProver'
  discharged+=closed
  inventory.append(dict(component=stem,po=po.get('name'),confidence=confidence,status='DISCHARGED' if closed else 'OPEN',rodin_manual_flag=po.get(P+'psManual')))
 components.append(dict(component=stem,accurate=True,total=len(statuses),discharged=discharged,open=len(statuses)-discharged))
 for suffix in ('.bcm','.bcc','.bpo','.bps','.bpr'):
  artifact=src/(stem+suffix)
  if artifact.exists():shutil.copy2(artifact,OUT/artifact.name)
if (src/'.settings').exists():shutil.copytree(src/'.settings',OUT/'.settings',dirs_exist_ok=True)
with (BASE/'validation/po_inventory.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=['component','po','confidence','status','rodin_manual_flag']);w.writeheader();w.writerows(inventory)
report=dict(rodin_version='3.8.0.202304051545-af2f57e1e',java_version='17.0.20',static_errors=0,components=components,total=sum(x['total'] for x in components),discharged=sum(x['discharged'] for x in components),open=sum(x['open'] for x in components),procedure='Native AutoProver with project profile DelegatedAuto; uniform registered tactic, core transformations, built-in PP and Atelier B Provers. No interactive proof, Review, oracle or proof import.',auto_profile='DelegatedAuto',atelier_core='1.7.1.r16756',atelier_linux='2.4.0.r16756',full_verification_complete=all(x['open']==0 for x in components))
assert report['full_verification_complete'],'Some obligations remain open'
report['automatic']=report['discharged']
report['manual']=0
report['auto_rate']=1.0
(BASE/'validation/native_summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
