#!/usr/bin/env python

import struct

def read_UINT_8( fHandle, nElements=1 ):
    struct_fmt = '={0}B'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_uint_8

def read_UINT_16( fHandle, nElements=1 ):
    struct_fmt = '={0}H'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_uint_16

def read_UINT_32( fHandle, nElements=1 ):
    struct_fmt = '={0}I'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_uint32_t

def read_UINT_64( fHandle, nElements=1 ):
    struct_fmt = '={0}Q'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_uint64_t

def read_INT_8( fHandle, nElements=1 ):
    struct_fmt = '={0}b'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_int_8

def read_char( fHandle, nElements=1 ):
    struct_fmt = '={0}b'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_char


def read_INT_16( fHandle, nElements=1 ):
    struct_fmt = '={0}h'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_int_16

def read_INT_32( fHandle, nElements=1 ):
    struct_fmt = '={0}i'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_int32_t

def read_INT_64( fHandle, nElements=1 ):
    struct_fmt = '={0}q'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_int64_t

def read_DOUBLE( fHandle, nElements=1 ):
    struct_fmt = '={0}d'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_double

def read_SINGLE( fHandle, nElements=1 ):
    struct_fmt = '={0}f'.format( nElements )
    retval = read_buf(fHandle,struct_fmt,nElements)
    return retval
# end read_float

def read_COMPLEX_SINGLE( fHandle, nElements=1 ):
    fmt = '{0}f'.format(nElements*2)
    vals = read_buf(fHandle,fmt,nElements*2)
    if nElements == 1:
        retval = vals[0] + 1j*vals[1]
    else:
        retval = [ vals[i] + 1j * vals[i+1] for i in range( 0, len(vals), 2 ) ]
    return retval 
# end write_COMPLEX_SINGLE

def read_COMPLEX_DOUBLE( fHandle, nElements=1 ):
    fmt = '{0}d'.format(nElements*2)
    vals = read_buf(fHandle,fmt,nElements*2)
    if nElements == 1:
        retval = vals[0] + 1j*vals[1]
    else:
        retval = [ vals[i] + 1j * vals[i+1] for i in range( 0, len(vals), 2 ) ]
    return retval 
# end write_COMPLEX_SINGLE


def read_buf( fHandle, fmt,  nElements=1 ):
    size = struct.calcsize(fmt)
    data = fHandle.read(size)
    if len(data) != size:
        print( "Error in read_buf, asked for {0}, got {1}".format( size, len(data) ) )
        return None
    retval = struct.unpack(fmt,data)
    if nElements == 1:
        retval = retval[0]
    return retval
# end write


def write_UINT_8( fHandle, val, nElements=1 ):
    fmt = '={0}B'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_uint_8

def write_UINT_16( fHandle, val, nElements=1 ):
    fmt = '={0}H'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_uint_16

def write_UINT_32( fHandle, val, nElements=1 ):
    fmt = '={0}I'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_uint32_t

def write_UINT_64( fHandle, val, nElements=1 ):
    fmt = '={0}Q'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_uint64_t

def write_INT_8( fHandle, val, nElements=1 ):
    fmt = '={0}b'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_int_8

def write_char( fHandle, val, nElements=1 ):
    fmt = '={0}b'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_char

def write_INT_16( fHandle, val, nElements=1 ):
    fmt = '={0}h'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_int_16

def write_INT_32( fHandle, val, nElements=1 ):
    fmt = '={0}i'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_int32_t

def write_INT_64( fHandle, val, nElements=1 ):
    fmt = '={0}q'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_int64_t

def write_DOUBLE( fHandle, val, nElements=1 ):
    fmt = '={0}d'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_double

def write_SINGLE( fHandle, val, nElements=1 ):
    fmt = '={0}f'.format( nElements )
    write_buf( fHandle, val, fmt, nElements )
# end write_float

def write_COMPLEX_DOUBLE( fHandle, val, nElements=1 ):
    if nElements == 1:
        tmp = [val.real,val.imag]
    else:
        # turn complex into 2d list
        tmp = [ [x.real,x.imag] for x in val ]
        # flatten list
        tmp = [item for sublist in tmp for item in sublist]
    fmt = '={0}d'.format( len(tmp) )
    write_buf(fHandle,tmp,fmt,len(tmp))
# end write_COMPLEX_DOUBLE

def write_COMPLEX_SINGLE( fHandle, val, nElements=1 ):
    if nElements == 1:
        tmp = [val.real,val.imag]
    else:
        # turn complex into 2d list
        tmp = [ [x.real,x.imag] for x in val ]
        # flatten list
        tmp = [item for sublist in tmp for item in sublist]
    fmt = '={0}f'.format( len(tmp) )
    write_buf(fHandle,tmp,fmt,len(tmp))
# end write_COMPLEX_SINGLE

def write_buf( fHandle, val, fmt,  nElements=1 ):
    if nElements == 1:
        buf = struct.pack( fmt, val )
    else:
        buf = struct.pack( fmt, *val )
    fHandle.write( buf )
# end write

