#include <cups/raster.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc,char **argv){
 if(argc<7)return 2;
 unsigned w=atoi(argv[1]), ht=atoi(argv[2]), bits=atoi(argv[3]),cs=atoi(argv[4]),pages=atoi(argv[5]);
 const char *pat=argv[6];
 int encoding=argc>7?atoi(argv[7]):0;
 if(encoding==4&&cs!=18&&cs!=19)return 2;
 cups_mode_t mode=encoding==4?CUPS_RASTER_WRITE_APPLE:encoding==3?CUPS_RASTER_WRITE_PWG:encoding?CUPS_RASTER_WRITE_COMPRESSED:CUPS_RASTER_WRITE;
 cups_raster_t *r=cupsRasterOpen(1,mode);
 cups_page_header2_t h; memset(&h,0,sizeof(h));
 h.HWResolution[0]=h.HWResolution[1]=203;h.cupsWidth=w;h.cupsHeight=ht;
 h.cupsBitsPerColor=bits;h.cupsColorSpace=cs;h.cupsNumColors=(cs==1||cs==19)?3:1;
 h.cupsBitsPerPixel=bits*h.cupsNumColors;h.cupsBytesPerLine=(w*h.cupsBitsPerPixel+7)/8+(argc>9?atoi(argv[9]):2);
 h.cupsColorOrder=CUPS_ORDER_CHUNKED;h.NumCopies=argc>8?atoi(argv[8]):1;
 h.cupsPageSize[0]=w*72.0f/203;h.cupsPageSize[1]=ht*72.0f/203;
 h.PageSize[0]=(unsigned)(h.cupsPageSize[0]+.5);h.PageSize[1]=(unsigned)(h.cupsPageSize[1]+.5);
 unsigned char *line=calloc(1,h.cupsBytesPerLine);
 for(unsigned p=0;p<pages;p++){
 if(!cupsRasterWriteHeader2(r,&h))return 3;
 for(unsigned y=0;y<ht;y++){
 memset(line,0xa5,h.cupsBytesPerLine);
 for(unsigned x=0;x<w;x++){
 int black=!strcmp(pat,"black")||(!strcmp(pat,"pattern")&&((x+3*y+p)%7<3));
 unsigned v=cs==3?(black?255:0):(black?0:255);
 if(!strcmp(pat,"gradient")) {v=w>1?x*255/(w-1):0;if(cs==3)v=255-v;}
 if(!strcmp(pat,"white-border")) {v=x<w/3?128:255;if(cs==3)v=255-v;}
 if(!strcmp(pat,"near-white-border")) {v=x<w/3?128:250+x%6;if(cs==3)v=255-v;}
 if(!strcmp(pat,"antialiased-bars")) {unsigned xx=x%12;v=xx<4?0:xx==4||xx==11?128:255;if(cs==3)v=255-v;}
 if(!strncmp(pat,"gray",4)) {int level=atoi(pat+4);if(level<0||level>255)return 2;v=cs==3?255u-(unsigned)level:(unsigned)level;}
 if(!strcmp(pat,"gray-after-binary")) {v=p?128:255;if(cs==3)v=255-v;}
 if(bits==1){unsigned mask=128>>(x%8);if(v)line[x/8]|=mask;else line[x/8]&=~mask;}
 else for(unsigned c=0;c<h.cupsNumColors;c++)line[x*h.cupsNumColors+c]=v;
 }
 if(cupsRasterWritePixels(r,line,h.cupsBytesPerLine)!=h.cupsBytesPerLine)return 4;
 }
 }
 free(line);cupsRasterClose(r);return 0;
}
