=============================
Auto-Interface Code Generator
=============================

***********
Quick Start
***********

Generate python bindings::

    # Generate Code
    python src/python_files/Py_Generator.py \
           src/json_files/basetypes.json \
           src/json_files/example.json py 

Use the generated python to serialize and de-serialize objects::

    # Use the interface
    import interface as ii

    # Stand up an object and set defaults
    a = ii.all_types()

    # Serialize
    fout=open('a.bin','wb')
    a.write_binary(fout)
    fclose(fout)

    # Deserialize
    fin = open('a.bin','rb')
    b = ii.all_types()
    b.read_binary(fin)
    fclose(fin)

***************
Sample Commands
***************

Generate CPP::

    python src/python_files/CPP_Generator.py \
           src/json_files/basetypes.json \
           src/json_files/example.json cpp cpp

Generate Python::

    python src/python_files/Py_Generator.py \
           src/json_files/basetypes.json \
           src/json_files/example.json py 

Generate Matlab::

    python src/python_files/MAT_Generator.py \
           src/json_files/basetypes.json \
           src/json_files/example.json mat

Generate Sphinx Docs::

    python src/python_files/Doc_Generator.py \
           src/json_files/basetypes.json \
           src/json_files/example.json doc

Test AutoInterface Class::

    python src/python_files/AutoInterface.py \
           src/json_files/basetypes.json \
           src/json_files/example.json

******
Syntax
******

- Format is JSON
- Each structure is defined as:
    - 'struct_name' : struct definition
- A struct definition is:
    - 'DESCRIPTION' : optional string
    - 'NAMESPACE' : optional string - used as a c++ namespace
    - 'FIELDS' : [ array of fields ]

- A field is:
     - 'NAME' : string
     - 'TYPE' : basetype or struct name, see list of basetypes
     - 'DESCRIPTION' : optional description (used for doxygen output)
     - 'DEFAULT_VALUE' : optional default value, if not specified, basetype's default value will be used
     - 'LENGTH' : 1,N,VECTOR - if not specified, will be set to 1
     - 'VALID_MIN' : optional 
     - 'VALID_MAX' : optional

**************
Generated Code
**************

Code can be generated for CPP, Matlab or Python.  The following functions are currently supported:

- CPP
    - set_defaults
    - write_binary
    - read_binary
    - read_props
    - write_props
    - validate
- Matlab
    - set_defaults_STRUCT_NAME()
    - read_binary_STRUCT_NAME()
    - write_binary_STRUCT_NAME()
- Python
    - read_binary
    - write_binary
    - set_defaults

*********
BASETYPES
*********

==============  ===================== =======  ====== ============
TYPE            C++                   MATLAB   Python Binary
==============  ===================== =======  ====== ============
UINT_8          uint8_t               uint8    int    Byte
UINT_16         uint16_t              uint16   int    (2)Byte
UINT_32         uint32_t              uint32   int    (4)Byte
UINT_64         uint64_t              uint64   int    (8)Byte
INT_8           int8_t                int8     int    Byte
INT_16          int16_t               int16    int    (2)Byte
INT_32          int32_t               int32    int    (4)Byte
INT_64          int64_t               int64    int    (8)Byte
SINGLE          float                 single   float  (4)Byte
DOUBLE          double                double   float  (8)Byte
COMPLEX_SINGLE  std::complex<float>   single   float  (8)Byte r,i
COMPLEX_DOUBLE  std::complex<double>  double   float  (16)Byte r,i
==============  ===================== =======  ====== ============

********************
Serialization Format
********************

- Data is serialized as packed binary in native endian order

*******
Example
*******

Given the following Sample File::

    {
        "sample" :
        {
            "DESCRIPTION" : "Sample Struct"
            "FIELDS" : [
                {
                    "NAME" : "field_1",
                    "TYPE" : "UINT_8"
                },
                {
                    "NAME" : "field2",
                    "TYPE" : "SINGLE",
                    "LENGTH" : "VECTOR",
                    "DEFAULT_VALUE" : [1,2,3,4,5]
                } ]
        }
    }

Generate python code as follows::

    Py_Generator.py <basetypes.json> <sample.json> <output_directory>

For example::

    python src/python_files/Py_Generator.py \
           src/json_files/basetypes.json \ 
           src/json_files/sample.json \
           py

The following python will be generated::

    class sample:
        def __init__(self):
            self.set_defaults() 
        # end __init__

        def __repr__(self):
            ret = ''
            for key, val in sorted(vars(self).items()):
                ret = ret + "{0}: {1}\n".format( key, val )
            return ret
        # end __repr__

        def set_defaults(self):
            self.field_1 = 0;
            self.field2 = [ 1,2,3,4,5 ]
        # end set_defaults

        def read_binary( self, r_stream ):
            self.field_1 = io.read_UINT_8( r_stream )
            self.field2 = []
            num_elems = io.read_INT_32( r_stream )
            self.field2 = io.read_SINGLE( r_stream, nElements=num_elems )
        # end read_binary

        def write_binary( self, r_stream, typecheck=False ):
            io.write_UINT_8( r_stream, self.field_1 )
            num_elems = len( self.field2 )
            io.write_INT_32( r_stream, num_elems )
            io.write_SINGLE( r_stream, self.field2, nElements=num_elems )
        # end write_binary

    # end class sample

