Auto-Interface Code Generator
=============================

Quick Start:
===========

# Generate Code
python src/python_files/Py_Generator.py src/json_files/basetypes.json src/json_files/example.json py 

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

Syntax:
======

- Format is JSON
- Each structure is defined as:
    - 'struct_name' : struct definition
- A struct definition is:
    - 'NAME' : string
    - 'TYPE' : "STRUCT"
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

Generated Code:
==============

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

BASETYPES:
=========
    - UINT_8
    - UINT_16
    - UINT_32
    - UINT_64
    - INT_8
    - INT_16
    - INT_32
    - INT_64
    - SINGLE
    - DOUBLE
    - COMPLEX_SINGLE
    - COMPLEX_DOUBLE

Serialization Format:
====================

- Data is serialized as backed binary

EXAMPLE:
=======

Given the following Sample File:

{
    "sample" :
    {
        "NAME" : "sample",
        "TYPE" : "STRUCT",
        "FIELDS" : [
            {
                "NAME" : "field_1",
                "TYPE" : "UINT_8"
            },
            {
                "NAME" : "field2",
                "TYPE" : "SINGLE",
                "LENGTH" : "VECTOR"
            } ]
    }
}

Generate python code as follows:

Py_Generator.py <basetypes.json> <sample.json> <output_directory>

For example:

python src/python_files/Py_Generator.py src/json_files/basetypes.json src/json_files/sample.json py

The following python will be generated:

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
        self.field2 = []
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
