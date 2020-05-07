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

Generate C::

    python src/python_files/C_Generator.py \
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
- A Project is a set of key value pairs
    - 'PROJECT' : optional string 
    - 'VERSION' : optional string
    - 'NAMESPACE' : optional string
    - 'STRUCTURES' : required, array of structure defs
- Each structure is defined as:
    - 'NAME' : required struct name (no spaces)
    - 'DESCRIPTION' : optional string
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
- C
    - read_binary
    - write_binary
    - set_defaults
    - write_props

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
        "PROJECT" : "SampleProject",
        "VERSION" : "1.0.0",
        "NAMESPACE" : "SP",
        "DESCRIPTION" : "This is a project description",
        "STRUCTURES" : [
        {
            "NAME" : "sample",
            "DESCRIPTION" : "Sample Struct",
            "FIELDS" : [
                {
                    "NAME" : "field_1",
                    "TYPE" : "UINT_8"
                },
                {
                    "NAME" : "field2",
                    "TYPE" : "SINGLE",
                    "LENGTH" : "VECTOR",
                    "DEFAULT_VALUE" : [ 1,2,3,4,5 ]

                } ]
        }

        ]
    }

Generate python code as follows::

    Py_Generator.py <basetypes.json> <sample.json> <output_directory>

For example::

    python src/python_files/Py_Generator.py \
           src/json_files/basetypes.json \ 
           src/json_files/sample.json \
           py

The following python will be generated::


   
    class sAmple(object):
        """
        Auto Generated Class sAmple
        Methods:
          __init__ : Sets defaults
          read_binary( file_handle )
          write_binary( file_handle )
        """
        __slots__ = [
            "fiEld_1",
            "Field2",
        ]


        def __repr__(self):
            ret = ''
            for field in self.__slots__:
                val = getattr(self, field)
                #for key, val in sorted(vars(self).items()):
                ret = ret + "{0}: {1}\n".format( field, val )
            return ret
         # end __repr__

        def set_defaults(self):
            """
            Initializes and sets defaults
            """
            self.fiEld_1 = 0;
            self.Field2 = [ 1,2,3,4,5 ]
        # end set_defaults


        def from_dict( self, d ):
            """
        .. function:: from_dict( dict )

           Read this class from a dict object - useful for JSON

           :param dict       :rtype None

            """
            if "fiEld_1" in d:
                self.fiEld_1 = d["fiEld_1"]
            if "Field2" in d:
                self.Field2 = []
                self.Field2 = d["Field2"]
        # end from_dict

        def to_dict( self ):
            """
        .. function:: to_dict()

           Write this class to a dict - useful for JSON

           :rtype dict

            """
            d = {}
            d["fiEld_1"] = self.fiEld_1
            d["Field2"] = []
            d["Field2"] = self.Field2
            return d
        # end to_dict

        def to_json( self ):
            """
        .. function:: to_json()

           JSONify this object

           :param None       :rtype string

            """
            d = self.to_dict()
            return json.dumps(d)
        # end to_json

        def from_json( self, r_stream ):
            """
        .. function:: from_json()

           read JSON into this object

           :param file handle       :rtype None

            """
            json_obj = json.loads(r_stream.read())
            self.from_dict(json_obj)
        # end from_json

        def read_binary( self, r_stream ):
            """
        .. function:: read_binary( file_handle )

           Read this class from a packed binary message

           :param r_stream an open filehandle (opened in mode rb )
           :rtype None

            """
            self.fiEld_1 = io.read_UINT_8( r_stream )
            self.Field2 = []
            num_elems = 5
            if num_elems > 0:
                self.Field2 = io.read_SINGLE( r_stream, nElements=num_elems )
            else:
                self.Field2 = []
        # end read_binary

        def write_binary( self, r_stream, typecheck=False ):
            """
        .. function:: read_binary( file_handle )

           Write this class to a packed binary message

           :param r_stream an open filehandle (opened in mode wb )
           :typecheck if True, verify structures are correct type before including in arrays
           :rtype None

            """
            io.write_UINT_8( r_stream, self.fiEld_1 )
            num_elems = 5
            if num_elems > 0:
                io.write_SINGLE( r_stream, self.Field2, nElements=num_elems )
        # end write_binary

    # end class sAmple




