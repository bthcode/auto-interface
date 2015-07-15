#include "io_support.h"

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

void read_COMPLEX_SINGLE( FILE * p_in_file, int nElements, float complex * p_ret )
{
    fread( p_ret, sizeof(float complex), nElements, p_in_file );
}

void read_COMPLEX_DOUBLE( FILE * p_in_file, int nElements, double complex * p_ret )
{
    fread( p_ret, sizeof(double complex), nElements, p_in_file );
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

void write_COMPLEX_SINGLE( FILE * p_out_file, int nElements, float complex * p_val )
{
    fwrite( p_val, sizeof(float complex), nElements, p_out_file );
}

void write_COMPLEX_DOUBLE( FILE * p_out_file, int nElements, double complex * p_val )
{
    fwrite( p_val, sizeof(double complex), nElements, p_out_file );
}

void print_UINT_8( FILE * p_out_file, int nElements, uint8_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_UINT_16( FILE * p_out_file, int nElements, uint16_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_UINT_32( FILE * p_out_file, int nElements, uint32_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_UINT_64( FILE * p_out_file, int nElements, uint64_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%llu ", p_val[ii] );
}

void print_char( FILE * p_out_file, int nElements, char * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_INT_8( FILE * p_out_file, int nElements, int8_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_INT_16( FILE * p_out_file, int nElements, int16_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_INT_32( FILE * p_out_file, int nElements, int32_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%d ", p_val[ii] );
}

void print_INT_64( FILE * p_out_file, int nElements, int64_t * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%lld ", p_val[ii] );
}

void print_SINGLE( FILE * p_out_file, int nElements, float * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%f ", p_val[ii] );
}

void print_DOUBLE( FILE * p_out_file, int nElements, double * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "%f ", p_val[ii] );
}

void print_COMPLEX_SINGLE( FILE * p_out_file, int nElements, float complex * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "(%f,%f) ", creal(p_val[ii]),cimag(p_val[ii]) );
}

void print_COMPLEX_DOUBLE( FILE * p_out_file, int nElements, double complex * p_val )
{
    int32_t ii;
    for ( ii=0; ii < nElements; ii++ )
        fprintf( p_out_file, "(%f,%f) ", creal(p_val[ii]),cimag(p_val[ii]) );
}
