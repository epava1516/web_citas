/* Operator-only physical census. Never executes values or restores Redis. */
#include <stdio.h>
#include <inttypes.h>
#include "librdb-api.h"
#include "librdb-ext-api.h"

static size_t events=0,keys=0,auxes=0,auxbytes=0;
static int database=-1;
static void quiet(RdbLogLevel level,const char *message) {(void)level;(void)message;}
static int next(void) {
    if(events>=8192) return 0;
    if(events++) putchar(',');
    return !ferror(stdout);
}
static void hex(RdbParser *p,RdbBulk b) {
    const unsigned char *s=(const unsigned char*)b;
    for(size_t i=0;i<RDB_bulkLen(p,b);i++) printf("%02x",s[i]);
}
static RdbRes start(RdbParser *p,void *u,int version) {
    (void)p;(void)u;if(!next()) return (RdbRes)10000;
    printf("{\"event\":\"header\",\"version\":%d}",version);return RDB_OK;
}
static RdbRes db(RdbParser *p,void *u,int number) {
    (void)p;(void)u;if(!next()) return (RdbRes)10000;
    database=number;printf("{\"event\":\"database\",\"database\":%d}",number);return RDB_OK;
}
static RdbRes size(RdbParser *p,void *u,uint64_t count,uint64_t expires) {
    (void)p;(void)u;if(!next()) return (RdbRes)10000;
    printf("{\"event\":\"database_size\",\"database\":%d,\"keys\":%" PRIu64 ",\"expires\":%" PRIu64 "}",database,count,expires);return RDB_OK;
}
static RdbRes aux(RdbParser *p,void *u,RdbBulk field,RdbBulk value) {
    (void)u;size_t f=RDB_bulkLen(p,field),v=RDB_bulkLen(p,value);
    if(auxes>=64 || f>4096 || v>262144 || auxbytes+f+v>1048576 || !next()) return (RdbRes)10000;
    auxes++;auxbytes+=f+v;
    printf("{\"event\":\"aux\",\"field_hex\":\"");hex(p,field);
    printf("\",\"value_hex\":\"");hex(p,value);printf("\"}");return RDB_OK;
}
static RdbRes key(RdbParser *p,void *u,RdbBulk name,RdbKeyInfo *info) {
    (void)u;if(keys>=4096 || RDB_bulkLen(p,name)>4096 || !next()) return (RdbRes)10000;
    keys++;
    printf("{\"event\":\"key\",\"database\":%d,\"key_hex\":\"",database);hex(p,name);
    printf("\",\"expiry\":%lld,\"lru_idle\":%lld,\"lfu_freq\":%d,\"opcode\":%d,\"data_type\":%d,\"num_metadata\":%d}",info->expiretime,info->lruIdle,info->lfuFreq,info->opcode,info->dataType,info->numMeta);
    return RDB_OK;
}
static RdbRes special(const char *event) {
    if(!next()) return (RdbRes)10000;
    printf("{\"event\":\"%s\"}",event);return RDB_OK;
}
static RdbRes function(RdbParser *p,void *u,RdbBulk code) {(void)p;(void)u;(void)code;return special("function");}
static RdbRes module(RdbParser *p,void *u,RdbBulk name,size_t bytes) {(void)p;(void)u;(void)name;(void)bytes;return special("module");}
static RdbRes moduleaux(RdbParser *p,void *u,RdbBulk name,int version,int when,size_t bytes) {(void)p;(void)u;(void)name;(void)version;(void)when;(void)bytes;return special("module_aux");}
static RdbRes stream(RdbParser *p,void *u,RdbStreamMeta *meta) {(void)p;(void)u;(void)meta;return special("stream");}
static RdbRes array(RdbParser *p,void *u,uint64_t count,uint64_t cursor) {(void)p;(void)u;(void)count;(void)cursor;return special("array");}
static RdbRes hashfield(RdbParser *p,void *u,RdbBulk field,RdbBulk value,int64_t expires) {(void)p;(void)u;(void)field;(void)value;return expires==-1?RDB_OK:special("hash_field_expiry");}
static RdbRes slot(RdbParser *p,void *u,RdbSlotInfo *info) {(void)p;(void)u;(void)info;return special("cluster_slot");}

int main(int argc,char **argv) {
    if(argc!=2) return 2;
    RdbParser *p=RDB_createParserRdb(NULL);if(!p) return 3;
    RDB_setLogger(p,quiet);RDB_setMaxRawSize(p,8388608);
    RdbHandlersDataCallbacks data={0};
    data.handleStartRdb=start;data.handleNewDb=db;data.handleDbSize=size;
    data.handleAuxField=aux;data.handleNewKey=key;data.handleSlotInfo=slot;
    data.handleFunction=function;data.handleModule=module;
    data.handleStreamMetadata=stream;data.handleArrayMetadata=array;data.handleHashField=hashfield;
    RdbHandlersRawCallbacks raw={0};raw.handleBeginModuleAux=moduleaux;
    if(!RDBX_createReaderFile(p,argv[1]) || !RDB_createHandlersData(p,&data,NULL,NULL) || !RDB_createHandlersRaw(p,&raw,NULL,NULL)) {RDB_deleteParser(p);return 3;}
    for(int type=0;type<RDB_DATA_TYPE_MAX;type++) {
        if(RDB_handleByLevel(p,(RdbDataType)type,RDB_LEVEL_DATA)) {RDB_deleteParser(p);return 3;}
    }
    putchar('[');RdbStatus status=RDB_parse(p);
    if(status==RDB_STATUS_OK && next()) printf("{\"event\":\"complete\",\"source_bytes\":%zu}",RDB_getBytesProcessed(p));
    else status=RDB_STATUS_ERROR;
    printf("]\n");int flush=fflush(stdout);
    RDB_deleteParser(p);return status==RDB_STATUS_OK && !flush && !ferror(stdout)?0:4;
}
