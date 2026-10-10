/* Independent behavioral implementation. No vendor code or binary required. */
#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE 1
#define _DARWIN_C_SOURCE 1
#include <cups/cups.h>
#include <cups/ppd.h>
#include <cups/raster.h>
#include <errno.h>
#include <fcntl.h>
#include <locale.h>
#include <math.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <unistd.h>

#define MAX_WIDTH 864u
#define MAX_HEIGHT 2400u
#define MAX_LINE (1024u * 1024u)
#define MAX_COPIES 999
static volatile sig_atomic_t cancelled;
static char failure[1024];
static void cancel_job(int sig) { (void)sig; cancelled = 1; }
static int fail(const char *format,...) {
 if(!failure[0]) {
  va_list ap;va_start(ap,format);vsnprintf(failure,sizeof(failure),format,ap);va_end(ap);
  for(char *p=failure;*p;p++)if((unsigned char)*p<32||*p==127)*p=' ';
 }
 fprintf(stderr,"ERROR: NL-N41: %s\n",failure);return 1;
}

/* Expose exactly requested bytes without library read-ahead so a short next
 * header can be distinguished from clean EOF. stdio buffers actual fd reads. */
typedef struct { FILE *file; uint64_t bytes; } input_stream;
static ssize_t read_input(void *ctx,unsigned char *buffer,size_t length) {
 input_stream *in=ctx;
 if(cancelled)return -1;
 if(!length)return 0;
 size_t n=fread(buffer,1,1,in->file);
 in->bytes+=n;
 return n?(ssize_t)n:(ferror(in->file)?-1:0);
}

typedef struct {
 int n; cups_option_t *v; ppd_file_t *ppd;
 int speed, darkness, paper, rotation, mirror, negative, threshold, tear, dither;
 double gap, offset, shift;
 int copies;
} settings;
static const char *option(settings *s, const char *name, const char *fallback) {
 const char *v=cupsGetOption(name,s->n,s->v);
 if(v) return v;
 if(s->ppd) { ppd_choice_t *c=ppdFindMarkedChoice(s->ppd,name); if(c) return c->choice; }
 return fallback;
}
static int number(const char *v, int low, int high, int *out) {
 char *end; errno=0; long x=strtol(v,&end,10);
 if(errno||end==v||*end||x<low||x>high) return 0;
 *out=(int)x; return 1;
}
static int integer(settings *s,const char *key,const char *def,int low,int high,int *out) {
 const char *v=option(s,key,def);
 if(!number(v,low,high,out))return !fail("Invalid %s=%s. Choose a value from %d to %d.",key,v,low,high);
 return 1;
}
static int real_number(settings *s,const char *key,const char *def,double low,double high,double *out) {
 const char *v=option(s,key,def); char *end;errno=0;double x=strtod(v,&end);
 if(errno||end==v||*end||!isfinite(x)||x<low||x>high)return !fail("Invalid %s=%s. Choose a value from %.1f to %.1f.",key,v,low,high);
 *out=x;return 1;
}
static int boolean(settings *s,const char *key,const char *def,int *out) {
 const char *v=option(s,key,def);
 if(!strcasecmp(v,"true")||!strcasecmp(v,"yes")||!strcmp(v,"1")) {*out=1;return 1;}
 if(!strcasecmp(v,"false")||!strcasecmp(v,"no")||!strcmp(v,"0")) {*out=0;return 1;}
 return !fail("Invalid %s=%s. Select True or False.",key,v);
}
static int optional_integer(settings *s,const char *key,int low,int high,int *out) {
 const char *v=option(s,key,"None"); if(!strcasecmp(v,"None")){*out=-1;return 1;}
 return integer(s,key,"None",low,high,out);
}
static int read_settings(settings *s,char **argv) {
 if(!number(argv[4],1,MAX_COPIES,&s->copies)) return !fail("Copies must be 1..999");
 s->n=cupsParseOptions(argv[5],0,&s->v);
 const char *path=getenv("PPD");
 if(path&&*path) {s->ppd=ppdOpenFile(path);if(!s->ppd) return !fail("Cannot open PPD");ppdMarkDefaults(s->ppd);}
 const char *dither=option(s,"Dither","FloydSteinberg");
 if(!strcasecmp(dither,"Threshold"))s->dither=0;
 else if(!strcasecmp(dither,"Ordered"))s->dither=1;
 else if(!strcasecmp(dither,"FloydSteinberg"))s->dither=2;
 else return !fail("Dither must be Threshold, Ordered or FloydSteinberg");
 /* Per-job mode from the desktop PDF-only PPD takes precedence over the
  * queue's Dither default. DriverDefault preserves the advanced Dither option. */
 const char *mode=option(s,"nln41-mode","DriverDefault");
 if(!strcasecmp(mode,"BlackWhite"))s->dither=0;
 else if(!strcasecmp(mode,"Gray"))s->dither=2;
 else if(strcasecmp(mode,"DriverDefault"))return !fail("nln41-mode must be BlackWhite, Gray or DriverDefault");
 if(!optional_integer(s,"PrintSpeed",2,5,&s->speed)||
    !optional_integer(s,"PrintDarkness",0,15,&s->darkness)||
    !integer(s,"Orientation","0",0,3,&s->rotation)||
    !boolean(s,"MirrorImage","False",&s->mirror)||
    !boolean(s,"NegativeImage","False",&s->negative)||
    !integer(s,"Threshold","128",1,255,&s->threshold)||
    !real_number(s,"GapLength","2",0,10,&s->gap)) return 0;
 const char *paper=option(s,"PaperType","1");
 if(!strcasecmp(paper,"None"))s->paper=0;
 else if(!integer(s,"PaperType","1",1,3,&s->paper))return 0;
 const char *offset=option(s,"FowardOffset","0");
 s->offset=0; if(strcasecmp(offset,"None")&&!real_number(s,"FowardOffset","0",-30,30,&s->offset))return 0;
 const char *shift=option(s,"ShiftMove","0");
 s->shift=0;if(strcasecmp(shift,"None")&&!real_number(s,"ShiftMove","0",-12,12,&s->shift))return 0;
 const char *post=option(s,"PostAction","1");
 if(!strcmp(post,"1"))s->tear=1;
 else if(!strcasecmp(post,"None")||!strcmp(post,"0"))s->tear=0;
 else return !fail("PostAction must be None, 0 or 1");
 return 1;
}
/* Grayscale intensity: zero black, 255 white. Reject unknown spaces/layouts. */
static unsigned intensity(const cups_page_header2_t *h,const unsigned char *row,unsigned x) {
 if(h->cupsBitsPerColor==1) {
  unsigned v=(row[x/8]>>(7-x%8))&1;
  return h->cupsColorSpace==CUPS_CSPACE_K?(v?0:255):(v?255:0);
 }
 if(h->cupsBitsPerPixel==24) {
  const unsigned char *p=row+3*x;
  return (77u*p[0]+150u*p[1]+29u*p[2]+128u)>>8;
 }
 return h->cupsColorSpace==CUPS_CSPACE_K?255u-row[x]:row[x];
}
/* Bayer 8x8 ordered thresholds; endpoints remain solid black and solid white. */
static const unsigned char bayer[8][8]={
 {0,48,12,60,3,51,15,63},{32,16,44,28,35,19,47,31},
 {8,56,4,52,11,59,7,55},{40,24,36,20,43,27,39,23},
 {2,50,14,62,1,49,13,61},{34,18,46,30,33,17,45,29},
 {10,58,6,54,9,57,5,53},{42,26,38,22,41,25,37,21}
};
static int validate(const cups_page_header2_t *h) {
 if(h->HWResolution[0]!=203||h->HWResolution[1]!=203)return !fail("Resolution is %ux%u dpi. Select 203 DPI.",h->HWResolution[0],h->HWResolution[1]);
 if(!h->cupsWidth||!h->cupsHeight||h->cupsWidth>MAX_HEIGHT||h->cupsHeight>MAX_HEIGHT)
  return !fail("Invalid raster dimensions");
 if(h->cupsColorOrder!=CUPS_ORDER_CHUNKED)return !fail("Only chunked raster is supported");
 int gray=h->cupsColorSpace==CUPS_CSPACE_K||h->cupsColorSpace==CUPS_CSPACE_W||h->cupsColorSpace==CUPS_CSPACE_SW;
 int rgb=h->cupsColorSpace==CUPS_CSPACE_RGB||h->cupsColorSpace==CUPS_CSPACE_SRGB;
 if(!((gray&&(h->cupsBitsPerColor==1||h->cupsBitsPerColor==8)&&h->cupsBitsPerPixel==h->cupsBitsPerColor&&h->cupsNumColors==1)||
      (rgb&&h->cupsBitsPerColor==8&&h->cupsBitsPerPixel==24&&h->cupsNumColors==3)))
  return !fail("Unsupported color space, bit depth or channel count");
 uint64_t minimum=((uint64_t)h->cupsWidth*h->cupsBitsPerPixel+7)/8;
 if(h->cupsBytesPerLine<minimum||h->cupsBytesPerLine>MAX_LINE)return !fail("Invalid raster row stride");
 if(h->Duplex)return !fail("Duplex is unsupported. Select one-sided printing.");
 if(h->NumCopies>MAX_COPIES)return !fail("Raster copies exceed 999");
 return 1;
}
static int page(cups_raster_t *r,const cups_page_header2_t *h,settings *s,unsigned page_no) {
 if(!validate(h))return 0;
 unsigned w=h->cupsWidth,ht=h->cupsHeight;
 unsigned ow=s->rotation%2?ht:w,oh=s->rotation%2?w:ht;
 if(ow>MAX_WIDTH||oh>MAX_HEIGHT) {
  return !fail("Raster %ux%u, Orientation=%d produces %ux%u; limit is %u x %u dots. Select 4x6 portrait on the client.",w,ht,s->rotation,ow,oh,MAX_WIDTH,MAX_HEIGHT);
 }
 size_t stride=(ow+7u)/8u, bytes=stride*oh;
 unsigned char *bitmap=malloc(bytes),*row=malloc(h->cupsBytesPerLine);
 size_t error_width=w+2u;
 int diffuse=s->dither==2&&h->cupsBitsPerColor==8;
 double *errors=diffuse?calloc(2*error_width,sizeof(double)):NULL;
 if(!bitmap||!row||(diffuse&&!errors)){free(bitmap);free(row);free(errors);return !fail("Out of memory");}
 double *current=errors,*next=errors?errors+error_width:NULL;
 memset(bitmap,255,bytes);
 int mirror=s->mirror||h->MirrorPrint, negative=s->negative||h->NegativePrint;
 for(unsigned y=0;y<ht;y++) {
  if(cancelled||cupsRasterReadPixels(r,row,h->cupsBytesPerLine)!=h->cupsBytesPerLine) {
   free(bitmap);free(row);free(errors);return !fail(cancelled?"Job cancelled":"Truncated raster page. Resubmit the original PDF or image.");
  }
  /* Serpentine diffusion avoids a constant left-to-right bias. Halftone in
   * source coordinates, then apply the existing rotation/mirror/inversion. */
  int direction=diffuse&&(y&1)?-1:1;
  for(unsigned i=0;i<w;i++) {
   unsigned x=direction<0?w-1-i:i;
   unsigned gray=intensity(h,row,x);
   int black;
   if(diffuse) {
    int index=(int)x+1;
    /* Use the original intensity, including near-white highlights. */
    double value=gray+current[index];
    black=value<128.0;
    double error=value-(black?0.0:255.0);
    current[index+direction]+=error*7.0/16.0;
    next[index-direction]+=error*3.0/16.0;
    next[index]+=error*5.0/16.0;
    next[index+direction]+=error/16.0;
   } else if(s->dither==1) {
    black=gray*128u<(2u*bayer[y&7][x&7]+1u)*255u;
   } else {
    black=gray<(unsigned)(s->dither==2?128:s->threshold);
   }
   if(negative)black=!black;
   if(!black)continue;
   unsigned dx=x,dy=y;
   /* Explicit filter rotation clockwise. Raster header Orientation already handled by RIP. */
   switch(s->rotation){case 1:dx=ht-1-y;dy=x;break;case 2:dx=w-1-x;dy=ht-1-y;break;case 3:dx=y;dy=w-1-x;break;}
   if(mirror)dx=ow-1-dx;
   bitmap[(size_t)dy*stride+dx/8]&=(unsigned char)~(128u>>(dx%8));
  }
  if(diffuse){double *swap=current;current=next;next=swap;memset(next,0,error_width*sizeof(double));}
 }
 free(row);free(errors);
 /* PPD supplies a full-bleed raster. Preserve physical page dimensions when available. */
 double mmw=h->cupsPageSize[0]>0?h->cupsPageSize[0]*25.4/72.0:h->PageSize[0]*25.4/72.0;
 double mmh=h->cupsPageSize[1]>0?h->cupsPageSize[1]*25.4/72.0:h->PageSize[1]*25.4/72.0;
 if(mmw<=0)mmw=w*25.4/203.0;
 if(mmh<=0)mmh=ht*25.4/203.0;
 if(s->rotation%2){double t=mmw;mmw=mmh;mmh=t;}
 if(!isfinite(mmw)||!isfinite(mmh)||mmw>108.2||mmh>300.1||mmw<0.1||mmh<0.1) {
  free(bitmap);return !fail("Page size %.1f x %.1f mm exceeds the supported range (max 108.2 x 300.1 mm). Select 4x6 portrait.",mmw,mmh);
 }
 /* Nonzero crop origins would shift content: fail explicitly instead of silently misplacing labels. */
 if(h->Margins[0]||h->Margins[1]){free(bitmap);return !fail("Raster must have zero margins; use supplied full-bleed PPD");}
 int copies=h->NumCopies>1?(int)h->NumCopies:s->copies;
 int collate=0;
 if(!boolean(s,"Collate",h->Collate?"True":"False",&collate)){free(bitmap);return 0;}
 if(collate&&copies>1){free(bitmap);return !fail("Collated copies unsupported; use Collate=False or submit copies separately");}
 if(cancelled){free(bitmap);return !fail("Job cancelled");}
 printf("SIZE %.3f mm,%.3f mm\r\n",mmw,mmh);
 if(s->paper==1||s->paper==2)printf("%s %.3f mm,0 mm\r\n",s->paper==1?"GAP":"BLINE",s->gap);
 else if(s->paper==3)printf("GAP 0 mm,0 mm\r\n");
 printf("OFFSET %.3f mm\r\nSHIFT %d\r\n",s->offset,(int)lround(s->shift*203.0/25.4));
 if(s->speed>=0)printf("SPEED %d\r\n",s->speed);
 if(s->darkness>=0)printf("DENSITY %d\r\n",s->darkness);
 printf("SET TEAR %s\r\nSET CUTTER OFF\r\nSET PEEL OFF\r\nCLS\r\nBITMAP 0,0,%zu,%u,0,",s->tear?"ON":"OFF",stride,oh);
 int ok=fwrite(bitmap,1,bytes,stdout)==bytes;
 free(bitmap);
 if(ok)ok=printf("\r\nPRINT 1,%d\r\n",copies)>0;
 if(!ok||fflush(stdout)||ferror(stdout))return !fail("Cannot write TSPL output");
 fprintf(stderr,"PAGE: %u %d\nINFO: NL-N41 %ux%u dots, %zu bytes, %d copies\n",page_no,copies,ow,oh,bytes,copies);
 return 1;
}
int main(int argc,char **argv) {
 if(argc!=6&&argc!=7)return fail("Usage: raster-nln41 job-id user title copies options [raster-file]");
 setlocale(LC_NUMERIC,"C");signal(SIGTERM,cancel_job);signal(SIGINT,cancel_job);signal(SIGPIPE,SIG_IGN);
 settings s;memset(&s,0,sizeof(s));int result=1;cups_raster_t *r=NULL;
 input_stream in={NULL,0};
 if(!read_settings(&s,argv))goto done;
 in.file=argc==7?fopen(argv[6],"rb"):stdin;
 if(!in.file){fail("Cannot open raster input");goto done;}
 r=cupsRasterOpenIO(read_input,&in,CUPS_RASTER_READ);if(!r){fail("Cannot open CUPS raster stream");goto done;}
 unsigned count=0;cups_page_header2_t h;
 while(!cancelled) {
  uint64_t before=in.bytes;
  if(!cupsRasterReadHeader2(r,&h)) {
   if(in.bytes!=before||ferror(in.file)){fail("Truncated or invalid next raster header");goto done;}
   break;
  }
  if(!page(r,&h,&s,++count))goto done;
 }
 if(cancelled){fail("Job cancelled");goto done;}
 const char *error=cupsRasterErrorString();
 if(error&&*error){fail("Raster stream: %s",error);goto done;}
 if(!count){fail("Empty or invalid raster stream");goto done;}
 result=0;
 done:
 if(r)cupsRasterClose(r);
 if(in.file&&in.file!=stdin)fclose(in.file);
 if(s.ppd)ppdClose(s.ppd);
 cupsFreeOptions(s.n,s.v);
 /* Repeat the retained first cause after our cleanup; no generic success
  * message from this filter should replace an actionable ERROR. */
 if(result&&failure[0])fprintf(stderr,"ERROR: NL-N41: %s\n",failure);
 return result;
}
