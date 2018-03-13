
#include <stdint.h>
#include <stdio.h>
#include "io_utils.h"
/* --------------------- IO SUPPORT -------------------- */
void read_UINT_8( FILE * p_in_file, int nElements, uint8_t * p_ret )
{
    fread( p_ret, sizeof(uint8_t), nElements, p_in_file );
}

void read_UINT_16( FILE * p_in_file, int nElements, uint16_t * p_ret )
{
    fread( p_ret, sizeof(uint16_t), nElements, p_in_file );
}

void read_UINT_32( FILE * p_in_file, int nElements, uint32_t * p_ret )
{
    fread( p_ret, sizeof(uint32_t), nElements, p_in_file );
}

void read_UINT_64( FILE * p_in_file, int nElements, uint64_t * p_ret )
{
    fread( p_ret, sizeof(uint64_t), nElements, p_in_file );
}

void read_char( FILE * p_in_file, int nElements, char * p_ret )
{
    fread( p_ret, sizeof(char), nElements, p_in_file );
}

void read_INT_8( FILE * p_in_file, int nElements, int8_t * p_ret )
{
    fread( p_ret, sizeof(int8_t), nElements, p_in_file );
}

void read_INT_16( FILE * p_in_file, int nElements, int16_t * p_ret )
{
    fread( p_ret, sizeof(int16_t), nElements, p_in_file );
}

void read_INT_32( FILE * p_in_file, int nElements, int32_t * p_ret )
{
    fread( p_ret, sizeof(int32_t), nElements, p_in_file );
}

void read_INT_64( FILE * p_in_file, int nElements, int64_t * p_ret )
{
    fread( p_ret, sizeof(int64_t), nElements, p_in_file );
}

void read_SINGLE( FILE * p_in_file, int nElements, float * p_ret )
{
    fread( p_ret, sizeof(float), nElements, p_in_file );
}

void read_DOUBLE( FILE * p_in_file, int nElements, double * p_ret )
{
    fread( p_ret, sizeof(double), nElements, p_in_file );
}

void write_UINT_8( FILE * p_out_file, int nElements, uint8_t * p_val )
{
    fwrite( p_val, sizeof(uint8_t), nElements, p_out_file );
}

void write_UINT_16( FILE * p_out_file, int nElements, uint16_t * p_val )
{
    fwrite( p_val, sizeof(uint16_t), nElements, p_out_file );
}

void write_UINT_32( FILE * p_out_file, int nElements, uint32_t * p_val )
{
    fwrite( p_val, sizeof(uint32_t), nElements, p_out_file );
}

void write_UINT_64( FILE * p_out_file, int nElements, uint64_t * p_val )
{
    fwrite( p_val, sizeof(uint64_t), nElements, p_out_file );
}

void write_char( FILE * p_out_file, int nElements, char * p_val )
{
    fwrite( p_val, sizeof(char), nElements, p_out_file );
}

void write_INT_8( FILE * p_out_file, int nElements, int8_t * p_val )
{
    fwrite( p_val, sizeof(int8_t), nElements, p_out_file );
}

void write_INT_16( FILE * p_out_file, int nElements, int16_t * p_val )
{
    fwrite( p_val, sizeof(int16_t), nElements, p_out_file );
}

void write_INT_32( FILE * p_out_file, int nElements, int32_t * p_val )
{
    fwrite( p_val, sizeof(int32_t), nElements, p_out_file );
}

void write_INT_64( FILE * p_out_file, int nElements, int64_t * p_val )
{
    fwrite( p_val, sizeof(int64_t), nElements, p_out_file );
}

void write_SINGLE( FILE * p_out_file, int nElements, float * p_val )
{
    fwrite( p_val, sizeof(float), nElements, p_out_file );
}

void write_DOUBLE( FILE * p_out_file, int nElements, double * p_val )
{
    fwrite( p_val, sizeof(double), nElements, p_out_file );
}

void print_UINT_8( FILE * p_out_file, int nElements, char DELIM, uint8_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_UINT_16( FILE * p_out_file, int nElements, char DELIM,uint16_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_UINT_32( FILE * p_out_file, int nElements, char DELIM,uint32_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d ", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_UINT_64( FILE * p_out_file, int nElements, char DELIM,uint64_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%llu", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%llu", p_val[nElements-1] );
}

void print_char( FILE * p_out_file, int nElements, char DELIM,char * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_INT_8( FILE * p_out_file, int nElements, char DELIM,int8_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_INT_16( FILE * p_out_file, int nElements, char DELIM,int16_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_INT_32( FILE * p_out_file, int nElements, char DELIM,int32_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%d", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%d", p_val[nElements-1] );
}

void print_INT_64( FILE * p_out_file, int nElements, char DELIM,int64_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%lld", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%lld", p_val[nElements-1] );
}

void print_SINGLE( FILE * p_out_file, int nElements, char DELIM,float * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%f", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%f", p_val[nElements-1] );
}

void print_DOUBLE( FILE * p_out_file, int nElements, char DELIM,double * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements-1; ii++ )
    {
        fprintf( p_out_file, "%f", p_val[ii] );
        fprintf( p_out_file, "%c", DELIM );
    }
    fprintf( p_out_file, "%f", p_val[nElements-1] );
}

/* --------------------- IO SUPPORT -------------------- */
