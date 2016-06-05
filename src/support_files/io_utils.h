
#ifndef IO_UTILS_H
#define IO_UTILS_H

#include <stdlib.h>
#include <stdio.h>
#include <complex.h>

/* ----------------  IO SUPPORT ---------------- */
void read_UINT_8( FILE * p_in_file, int nElements, uint8_t * p_ret );
void read_UINT_16( FILE * p_in_file, int nElements, uint16_t * p_ret );
void read_UINT_32( FILE * p_in_file, int nElements, uint32_t * p_ret );
void read_UINT_64( FILE * p_in_file, int nElements, uint64_t * p_ret );
void read_char( FILE * p_in_file, int nElements, char * p_ret );
void read_INT_8( FILE * p_in_file, int nElements, int8_t * p_ret );
void read_INT_16( FILE * p_in_file, int nElements, int16_t * p_ret );
void read_INT_32( FILE * p_in_file, int nElements, int32_t * p_ret );
void read_INT_64( FILE * p_in_file, int nElements, int64_t* p_ret );
void read_SINGLE( FILE * p_in_file, int nElements, float * p_ret );
void read_DOUBLE( FILE * p_in_file, int nElements, double * p_ret );
void read_COMPLEX_SINGLE( FILE * p_in_file, int nElements, float complex * p_ret );
void read_COMPLEX_DOUBLE( FILE * p_in_file, int nElements, double complex * p_ret );

void write_UINT_8( FILE * p_out_file, int nElements, uint8_t * p_val );
void write_UINT_16( FILE * p_out_file, int nElements, uint16_t * p_val );
void write_UINT_32( FILE * p_out_file, int nElements, uint32_t * p_val );
void write_UINT_64( FILE * p_out_file, int nElements, uint64_t * p_val );
void write_char( FILE * p_out_file, int nElements, char * p_val );
void write_INT_8( FILE * p_out_file, int nElements, int8_t * p_val );
void write_INT_16( FILE * p_out_file, int nElements, int16_t * p_val );
void write_INT_32( FILE * p_out_file, int nElements, int32_t * p_val );
void write_INT_64( FILE * p_out_file, int nElements, int64_t* p_val );
void write_SINGLE( FILE * p_out_file, int nElements, float * p_val );
void write_DOUBLE( FILE * p_out_file, int nElements, double * p_val );
void write_COMPLEX_SINGLE( FILE * p_out_file, int nElements, float complex * p_val );
void write_COMPLEX_DOUBLE( FILE * p_out_file, int nElements, double complex * p_val );

void print_UINT_8( FILE * p_out_file, int nElements, char DELIM,  uint8_t * p_val );
void print_UINT_16( FILE * p_out_file, int nElements, char DELIM, uint16_t * p_val );
void print_UINT_32( FILE * p_out_file, int nElements, char DELIM, uint32_t * p_val );
void print_UINT_64( FILE * p_out_file, int nElements, char DELIM, uint64_t * p_val );
void print_char( FILE * p_out_file, int nElements, char DELIM, char * p_val );
void print_INT_8( FILE * p_out_file, int nElements, char DELIM, int8_t * p_val );
void print_INT_16( FILE * p_out_file, int nElements, char DELIM, int16_t * p_val );
void print_INT_32( FILE * p_out_file, int nElements, char DELIM, int32_t * p_val );
void print_INT_64( FILE * p_out_file, int nElements, char DELIM, int64_t* p_val );
void print_SINGLE( FILE * p_out_file, int nElements, char DELIM, float * p_val );
void print_DOUBLE( FILE * p_out_file, int nElements, char DELIM, double * p_val );
void print_COMPLEX_SINGLE( FILE * p_out_file, int nElements, char DELIM, float complex * p_val );
void print_COMPLEX_DOUBLE( FILE * p_out_file, int nElements, char DELIM, double complex * p_val );
/* --------------- END IO SUPPORT -------------- */
#endif
