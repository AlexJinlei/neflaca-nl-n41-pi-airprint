#!/usr/bin/env python3
"""Read ELF64 little-endian metadata without executing a Linux binary."""
import json,struct,sys
from pathlib import Path
p=Path(sys.argv[1]);b=p.read_bytes()
assert b[:6]==b'\x7fELF\x02\x01','Expected ELF64 little-endian'
e_machine=struct.unpack_from('<H',b,18)[0]
shoff=struct.unpack_from('<Q',b,40)[0];entsize,num,strings=struct.unpack_from('<HHH',b,58)
headers=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*entsize)for i in range(num)]
names=b[headers[strings][4]:headers[strings][4]+headers[strings][5]]
def z(buf,at=0):return buf[at:buf.index(0,at)].decode()
sections={z(names,h[0]):b[h[4]:h[4]+h[5]] for h in headers}
dynstr=sections['.dynstr'];dynamic=sections['.dynamic'];needed=[]
for at in range(0,len(dynamic),16):
 tag,val=struct.unpack_from('<QQ',dynamic,at)
 if tag==1:needed.append(z(dynstr,val))
versions=[];v=sections.get('.gnu.version_r',b'');pos=0
while pos<len(v):
 _,count,file,aux,next=struct.unpack_from('<HHIII',v,pos);a=pos+aux
 for _ in range(count):
  _,_,_,name,anext=struct.unpack_from('<IHHII',v,a);versions.append({'library':z(dynstr,file),'version':z(dynstr,name)})
  if not anext:break
  a+=anext
 if not next:break
 pos+=next
assert e_machine==183,'Expected AArch64 e_machine'
print(json.dumps({'file':p.name,'elf_class':64,'machine':'AArch64 (183)','interpreter':z(sections['.interp']),'needed':needed,'symbol_versions':versions},indent=2))
