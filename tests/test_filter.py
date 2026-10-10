#!/usr/bin/env python3
"""Byte-level integration tests; never opens a printer or network connection."""
import os,re,struct,subprocess,tempfile,time,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILTER=os.environ.get('FILTER',str(ROOT/'build/raster-nln41'))
GEN=str(ROOT/'build/generate')
ENV=dict(os.environ,PPD=str(ROOT/'ppd/NL-N41.ppd'))
checks=0

def raster(w=13,h=9,bits=1,cs=3,pages=1,pattern='pattern',compressed=0,copies=1,padding=2):
 if cs in [1,19] and padding%3: padding=3
 return subprocess.check_output([GEN,*map(str,[w,h,bits,cs,pages,pattern,compressed,copies,padding])])
def run(data,opts='',copies=1,ok=True,env=ENV,message=None):
 global checks
 p=subprocess.run([FILTER,'1','test','test',str(copies),opts],input=data,capture_output=True,env=env)
 assert (p.returncode==0)==ok,(opts,p.returncode,p.stderr)
 if not ok:assert b'ERROR: NL-N41:' in p.stderr, p.stderr
 if message is not None:assert message.encode() in p.stderr,(message,p.stderr)
 checks+=1
 return p.stdout

def parse(data):
 pages=[];pos=0
 while pos<len(data):
  m=re.search(rb'BITMAP (\d+),(\d+),(\d+),(\d+),(\d+),',data[pos:]);assert m
  start=pos+m.end();a=list(map(int,m.groups()));n=a[2]*a[3]
  payload=data[start:start+n];assert len(payload)==n
  p=re.match(rb'\r\nPRINT 1,(\d+)\r\n',data[start+n:]);assert p
  pages.append((data[pos:pos+m.start()],a,payload,int(p[1])))
  pos=start+n+p.end()
 return pages

def expected(w,h,pattern,page=0,rotation=0,mirror=False,negative=False):
 pixels=[[pattern=='black' or (pattern=='pattern' and (x+3*y+page)%7<3) for x in range(w)] for y in range(h)]
 if negative:pixels=[[not b for b in row]for row in pixels]
 for _ in range(rotation):pixels=[list(row)for row in zip(*pixels[::-1])]
 if mirror:pixels=[row[::-1]for row in pixels]
 out=bytearray()
 for row in pixels:
  for start in range(0,len(row),8):
   v=255
   for i,b in enumerate(row[start:start+8]):
    if b:v&=~(128>>i)
   out.append(v)
 return bytes(out)

for w in [1,7,8,13,17,812,864]:
 for cs,bits in [(3,1),(0,1),(18,1),(3,8),(0,8),(18,8),(1,8),(19,8)]:
  for compressed in [0,1]:
   for pattern in ['black','white','pattern']:
    pp=parse(run(raster(w,9,bits,cs,2,pattern,compressed)))
    assert len(pp)==2
    for page,p in enumerate(pp):
     assert p[1]==[0,0,(w+7)//8,9,0]
     assert p[2]==expected(w,9,pattern,page),(w,cs,bits,pattern)
# Actual Apple URF and PWG streams, through the same decoder and TSPL encoder.
for encoding in [3,4]:
 for cs,bits in [(18,8),(19,8)]:
  for w in [13,812]:
   p=parse(run(raster(w=w,h=9,bits=bits,cs=cs,pages=2,compressed=encoding,padding=0)))
   assert len(p)==2
   for n,page in enumerate(p):assert page[2]==expected(w,9,'pattern',n)
for rot in range(4):
 for mirror in [False,True]:
  for neg in [False,True]:
   opts=f'Orientation={rot} MirrorImage={mirror} NegativeImage={neg}'
   p=parse(run(raster(),opts))[0]
   assert p[2]==expected(13,9,'pattern',rotation=rot,mirror=mirror,negative=neg)
for header,argv,wanted in [(1,3,3),(4,1,4),(4,3,4),(0,2,2)]:
 assert parse(run(raster(copies=header),copies=argv))[0][3]==wanted
p=parse(run(raster(), 'PrintDarkness=10 PrintSpeed=3 PaperType=2 GapLength=3 ShiftMove=2 FowardOffset=-3'))[0]
for cmd in [b'DENSITY 10\r\n',b'SPEED 3\r\n',b'BLINE 3.000 mm,0 mm\r\n',b'SHIFT 16\r\n',b'OFFSET -3.000 mm\r\n']:assert cmd in p[0]
assert b'GAP 0 mm,0 mm' in parse(run(raster(),'PaperType=3'))[0][0]
assert b'GAP' not in parse(run(raster(),'PaperType=None'))[0][0]
for bad in ['PrintDarkness=16','PrintSpeed=99','GapLength=nan','GapLength=2x','Orientation=-1','MirrorImage=oops','ShiftMove=100','Threshold=0','Dither=unknown','Collate=True']:
 run(raster(),bad,copies=2,ok=False)
run(raster(),copies=0,ok=False)
run(raster(w=865),ok=False)
run(raster(w=812,h=1218),'Orientation=1',ok=False)
for bad in [b'',b'not a raster',raster()[:80],raster()[:-1],raster(compressed=1)[:-2]]:
 out=run(bad,ok=False);assert b'PRINT' not in out
# Corrupt fixed-offset CUPS v2 header values, using host byte order of write stream.
raw=raster();assert raw[:4] in [b'2SaR',b'RaS2',b'3SaR',b'RaS3']
endian='<'if raw[:4] in [b'2SaR',b'3SaR']else '>'
for offset,val in [(276,300),(280,300),(392,1),(400,2),(372,0),(384,16)]:
 bad=bytearray(raw);struct.pack_into(endian+'I',bad,4+offset,val);run(bytes(bad),ok=False)
# A broken subsequent header must be reported, even though earlier pages were emitted.
run(raster()+b'garbage',ok=False)
# PPD defaults and stdin-less input handling.
run(raster(),env=dict(os.environ,PPD='/does/not/exist'),ok=False)
full=parse(run(raster(812,1218,padding=0)))[0]
assert b'SIZE 101.600 mm,152.400 mm' in full[0]
assert len(full[2])==102*1218
# Verify real grayscale thresholding, not only already binary samples.
for cs in [0,3,18,1,19]:
 for threshold in [64,128,192]:
  p=parse(run(raster(w=17,h=9,bits=8,cs=cs,pattern='gradient'),f'Dither=Threshold Threshold={threshold}'))[0]
  row=bytearray([255]*3)
  for x in range(17):
   if x*255//16<threshold:row[x//8]&=~(128>>(x%8))
  assert p[2]==bytes(row)*9
# Halftone quality: tonal coverage and identical interpretation across color spaces.
# These assert observable density, not a second copy of the diffusion algorithm.
for mode in ['Ordered','FloydSteinberg']:
 ratios=[]
 for gray in [0,16,32,64,96,128,160,192,224,240,255]:
  data=raster(w=128,h=96,bits=8,cs=18,pages=2,pattern=f'gray{gray}',padding=0)
  pp=parse(run(data,f'Dither={mode}'))
  assert pp[0][2]==pp[1][2], 'Error state must reset between pages'
  black=sum(8-bin(b).count('1') for b in pp[0][2])
  coverage=black/(128*96);ratios.append(coverage)
  assert abs(coverage-(255-gray)/255)<.015,(mode,gray,coverage)
 assert ratios==sorted(ratios,reverse=True)
 reference=None
 for cs in [0,3,18,1,19]:
  p=parse(run(raster(w=65,h=37,bits=8,cs=cs,pattern='gradient'),f'Dither={mode}'))[0]
  if reference is None:reference=p[2]
  assert p[2]==reference, (mode,cs)
 for width in [1,7,13,812]:
  p=parse(run(raster(w=width,h=17,bits=8,cs=18,pattern='gradient'),f'Dither={mode}'))[0]
  pad=(8-width%8)%8
  if pad:
   assert all(p[2][y*((width+7)//8)+(width+7)//8-1]&((1<<pad)-1)==(1<<pad)-1 for y in range(17))
 # Black/white source pixels must stay exact, for 1- and 8-bit input alike.
 for bits in [1,8]:
  p=parse(run(raster(bits=bits),f'Dither={mode}'))[0]
  assert p[2]==expected(13,9,'pattern')
 # Rotation, mirror and negative are applied after halftoning. Padding stays white.
 base=parse(run(raster(w=13,h=9,bits=8,cs=18,pattern='gradient'),f'Dither={mode}'))[0][2]
 source=[[not(base[y*2+x//8]&(128>>(x%8))) for x in range(13)] for y in range(9)]
 for rot in range(4):
  for mirror in [False,True]:
   for neg in [False,True]:
    pixels=[row[:] for row in source]
    for _ in range(rot):pixels=[list(row) for row in zip(*pixels[::-1])]
    if mirror:pixels=[row[::-1] for row in pixels]
    if neg:pixels=[[not b for b in row] for row in pixels]
    want=bytearray()
    for row in pixels:
     for start in range(0,len(row),8):
      v=255
      for i,b in enumerate(row[start:start+8]):
       if b:v&=~(128>>i)
      want.append(v)
    opts=f'Dither={mode} Orientation={rot} MirrorImage={mirror} NegativeImage={neg}'
    assert parse(run(raster(w=13,h=9,bits=8,cs=18,pattern='gradient'),opts))[0][2]==bytes(want)
 for encoding in [3,4]:
  p=parse(run(raster(w=65,h=37,bits=8,cs=18,pattern='gradient',compressed=encoding,padding=0),f'Dither={mode}'))[0]
  assert p[2]==reference
 assert b'PRINT' not in run(raster(bits=8,pattern='gradient')[:-1],f'Dither={mode}',ok=False)
# The desktop mode is transmitted per job and overrides the queue Dither default.
mode_data=raster(w=65,h=37,bits=8,cs=18,pattern='gradient')
threshold=run(mode_data,'Dither=Threshold')
floyd=run(mode_data,'Dither=FloydSteinberg')
ordered=run(mode_data,'Dither=Ordered')
# Fresh queues and clients without a custom mode must retain grayscale.
no_ppd=dict(os.environ)
no_ppd.pop('PPD',None)
for env in [ENV,no_ppd]:
 for opts in ['', 'nln41-mode=DriverDefault']:
  assert run(mode_data,opts,env=env)==floyd
# Black & White forces threshold conversion even for substantial grayscale.
assert run(mode_data,'nln41-mode=BlackWhite Dither=FloydSteinberg')==threshold
dark=raster(w=65,h=37,bits=8,cs=18,pattern='gray10')
assert run(dark,'nln41-mode=BlackWhite Dither=FloydSteinberg')==run(dark,'Dither=Threshold')
assert run(mode_data,'nln41-mode=Gray Dither=Threshold')==floyd
assert run(mode_data,'nln41-mode=DriverDefault Dither=Ordered')==ordered
run(mode_data,'nln41-mode=invalid',ok=False)
# Actual threshold pixels across formats: input gray/RGB never causes a
# mode-mismatch failure, and the selected mode overrides advanced dithering.
for cs in [0,3,18,1,19]:
 # Apple URF uses sGray/sRGB; a K/W/RGB header cannot represent that format.
 for encoding in [0,1,3]+([4] if cs in [18,19] else []):
  raw=raster(w=65,h=37,bits=8,cs=cs,pattern='gradient',compressed=encoding,padding=0)
  p=parse(run(raw,'nln41-mode=BlackWhite Dither=FloydSteinberg'))[0]
  want=bytearray([255]*9)
  for x in range(65):
   if x*255//64<128:want[x//8]&=~(128>>(x%8))
  assert p[2]==bytes(want)*37,(cs,encoding)
  run(raw,'nln41-mode=Gray')
for bits in [1,8]:
 for pattern in ['black','white','pattern']:
  run(raster(w=65,h=37,bits=bits,pattern=pattern),'nln41-mode=BlackWhite')
run(raster(w=65,h=37,bits=8,cs=18,pattern='antialiased-bars'),'nln41-mode=BlackWhite')
run(raster(w=65,h=37,bits=8,cs=18,pattern='gray252'),'nln41-mode=BlackWhite')
raw=raster(w=65,h=37,bits=8,cs=18,pages=2,pattern='gray-after-binary')
pp=parse(run(raw,'nln41-mode=BlackWhite'))
assert len(pp)==2, 'Gray pages following binary pages must also print'
assert all(p[2]==b'\xff'*(9*37) for p in pp), 'Gray 128 maps to white at threshold 128'
for gray in [0,16,64,127,128,192,239,255]:
 p=parse(run(raster(w=65,h=37,bits=8,cs=18,pattern=f'gray{gray}'),'nln41-mode=BlackWhite'))[0]
 want=(b'\x00'*8+b'\x7f') if gray<128 else b'\xff'*9
 assert p[2]==want*37, gray
run(raster(w=812,h=1218),'Orientation=1',ok=False,message='Select 4x6 portrait')
run(raster(),'PrintDarkness=99',ok=False,message='Choose a value from 0 to 15')
# True white stays white. Near-white data must retain its nonzero density.
for cs in [0,3,18,1,19]:
 p=parse(run(raster(w=128,h=96,bits=8,cs=cs,pattern='white-border'),'nln41-mode=Gray'))[0]
 for y in range(96):
  for x in range(128//3,128):
   assert p[2][y*16+x//8]&(128>>(x%8)),(cs,x,y)
 p=parse(run(raster(w=128,h=96,bits=8,cs=cs,pattern='near-white-border'),'nln41-mode=Gray'))[0]
 assert any(not(p[2][y*16+x//8]&(128>>(x%8))) for y in range(96) for x in range(128//3,128)),cs
for gray in [0,1,2,3,4,5,250,251,252,253,254,255]:
 p=parse(run(raster(w=812,h=256,bits=8,cs=18,pattern=f'gray{gray}'),'nln41-mode=Gray'))[0]
 black=sum(8-bin(b).count('1') for b in p[2])
 assert abs(black/(812*256)-(255-gray)/255)<.0015,(gray,black)
 if 0<gray<255:assert 0<black<812*256,(gray,black)
# PPD must request grayscale from the RIP, not lose it to upstream 1-bit conversion.
ppd=(ROOT/'ppd/NL-N41.ppd').read_text()
assert '/cupsBitsPerColor 8/cupsColorSpace 18/' in ppd
assert '*DefaultDither: FloydSteinberg' in ppd
assert '*Defaultnln41-mode: Gray' in (ROOT/'ppd/NL-N41-Network.ppd').read_text()
for mode in ['Threshold','Ordered','FloydSteinberg']:assert f'*Dither {mode}/' in ppd
# argv[6] file path, PPD default values, and a downstream broken pipe.
with tempfile.NamedTemporaryFile() as f:
 f.write(raster());f.flush()
 p=subprocess.run([FILTER,'1','test','test','1','',f.name],capture_output=True,env=ENV)
 assert p.returncode==0;checks+=1
 p=subprocess.run([FILTER,'1','test','test','1','',f.name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV)
 assert p.returncode==0
readfd,writefd=os.pipe();os.close(readfd)
try:
 p=subprocess.run([FILTER,'1','test','test','1',''],input=raster(),stdout=writefd,stderr=subprocess.PIPE,env=ENV)
 assert p.returncode!=0 and b'Cannot write TSPL' in p.stderr;checks+=1
finally:os.close(writefd)
p=subprocess.Popen([FILTER,'1','test','test','1',''],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=ENV)
time.sleep(.05);p.send_signal(signal.SIGTERM)
_,err=p.communicate(timeout=5);assert p.returncode!=0;checks+=1
if Path('/dev/full').exists():
 with open('/dev/full','wb') as sink:
  p=subprocess.run([FILTER,'1','test','test','1',''],input=raster(),stdout=sink,stderr=subprocess.PIPE,env=ENV)
  assert p.returncode!=0;checks+=1
print(f'PASS: {checks} filter invocations; bitmap polarity, padding, multi-page, formats, transforms, copies, options and failures')
