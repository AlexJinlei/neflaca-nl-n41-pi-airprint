#!/usr/bin/env python3
"""Offline macOS vendor comparisons. All stdout captured; no printing/network."""
import argparse,os,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('filter');p.add_argument('ppd');p.add_argument('--output',default='vendor-observations.json');a=p.parse_args()
root=Path(__file__).resolve().parents[1];gen=root/'build/generate'
if not gen.exists():p.error('Run make build/generate first')
env=dict(os.environ,PPD=str(Path(a.ppd).resolve()));results=[]
for bits,cs,pat,opts,padding in [(1,3,'black','',0),(1,3,'white','',0),(1,3,'pattern','',0),(8,3,'pattern','',0),(1,3,'pattern','',2),(1,3,'pattern','MirrorImage=True',2),(1,3,'pattern','NegativeImage=True',2),(1,3,'pattern','Orientation=1',2),(1,3,'pattern','Orientation=2',2),(1,3,'pattern','PrintSpeed=3 PrintDarkness=10 PaperType=1 ShiftMove=2 FowardOffset=-3',2)]:
 data=subprocess.check_output([str(gen),'13','9',str(bits),str(cs),'1',pat,'0','1',str(padding)])
 r=subprocess.run(['/usr/bin/arch','-x86_64',str(Path(a.filter).resolve()),'1','test','offline','1',opts],input=data,capture_output=True,env=env)
 results.append(dict(bits=bits,space=cs,pattern=pat,options=opts,padding=padding,returncode=r.returncode,stdout_hex=r.stdout.hex(),stderr=r.stderr.decode(errors='replace')))
Path(a.output).write_text(json.dumps(results,indent=2))
print(f'Captured {len(results)} offline cases into {a.output}')
