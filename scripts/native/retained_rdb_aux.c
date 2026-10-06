#include <stdio.h>
#include "librdb-api.h"
#include "librdb-ext-api.h"
static size_t count=0,total=0;
static void quiet(RdbLogLevel level,const char *message) {(void)level;(void)message;}
static void hex(RdbParser *p,RdbBulk b) {
 const unsigned char *s=(const unsigned char*)b;
 for(size_t i=0;i<RDB_bulkLen(p,b);i++) printf("%02x",s[i]);
}
static RdbRes aux(RdbParser *p,void *u,RdbBulk key,RdbBulk value) {
 (void)u;
 size_t k=RDB_bulkLen(p,key),v=RDB_bulkLen(p,value);
 if(count>=64 || k>4096 || v>262144 || total+k+v>1048576) return (RdbRes)10000;
 if(count++) putchar(',');
 total+=k+v;
 printf("{\"field_hex\":\"");hex(p,key);printf("\",\"value_hex\":\"");hex(p,value);printf("\"}");
 return ferror(stdout)?(RdbRes)10000:RDB_OK;
}
int main(int argc,char **argv) {
 if(argc!=2) return 2;
 RdbParser *p=RDB_createParserRdb(NULL);
 if(!p) return 3;
 RDB_setLogger(p,quiet);
 RdbHandlersDataCallbacks cb={0};cb.handleAuxField=aux;
 if(!RDBX_createReaderFile(p,argv[1]) || !RDB_createHandlersData(p,&cb,NULL,NULL)) {RDB_deleteParser(p);return 3;}
 putchar('[');
 RdbStatus status=RDB_parse(p);
 printf("]\n");
 RDB_deleteParser(p);
 return status==RDB_STATUS_OK && !ferror(stdout)?0:4;
}
