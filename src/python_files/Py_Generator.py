#!/usr/bin/env python

__author__="Brian Hone"

'''
Code Generator

Generates Python Reader/Writer classes for AutoInterface formatted data

Actual reading/writing is provided via io_support.py
'''

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator
from Templates import py_class_template, py_basic_methods

T="    "



def generate_gpb_for_class(basetypes, structs, struct_name, project):
    struct_def = structs[struct_name]
    # namespace does not appear to be used in python version
    gpb_namespace = '{0}_GPB'.format(project['NAMESPACE'])
    gpb_classname = struct_def['NAME']

    #
    # get gpb parser
    #
    ret = '\n' + T + 'def read_gpb_from_buf(self, buf):\n'
    ret = ret + T + T + 'gpb_obj = gpb.{0}()\n'.format(struct_name)
    ret = ret + T + T + 'gpb_obj.ParseFromString(buf)\n'
    ret = ret + T + T + 'self.read_gpb(gpb_obj)\n'
    ret = ret + T + '# end read_gpb_from_buf\n\n'

    ret = ret + T + 'def write_gpb_to_buf(self):\n'
    ret = ret + T + T + 'gpb_obj = self.write_gpb()\n'
    ret = ret + T + T + 'return gpb_obj.SerializeToString()\n\n'
    ret = ret + T + '# end write_gpb_to_buf\n'


    #
    # read gpb
    #
    ret = ret + T + 'def read_gpb(self, gpb_obj):\n'

    for f in struct_def['FIELDS']:
        field    = f['NAME']
    
        # need max count for fixed length fields
        if type(f['LENGTH']) == int and f['LENGTH'] > 1:
            ret = ret + T + T + 'max_count = min({0}, len(gpb_obj.{1}))\n'.format(f['LENGTH'],field)
        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + T +  'max_count = len(gpb_obj.{0})\n'.format(field)

        # get type
        if f['IS_BASETYPE']:
            basetype = basetypes[f['TYPE']]
            gpb_type = basetype['GPB_TYPE']

        if f['LENGTH']==1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'self.{0} = gpb_obj.{0}\n'.format(field)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'self.{0}.read_gpb(gpb_obj.{0})\n'.format(field)

        elif f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'self.{0} = []\n'.format(field)
                ret = ret + T + T + 'for ii in range(max_count):\n'
                ret = ret + T + T + T + 'self.{0}.append( gpb_obj.{0}[ii] )\n'.format(field)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'self.{0} = []\n'.format(field)
                ret = ret + T + T + 'for ii in range(max_count):\n'
                ret = ret + T + T + T + 'tmp = {0}()\n'.format(f['TYPE'])
                ret = ret + T + T + T + 'tmp.read_gpb(gpb_obj.{0}[ii])\n'.format(field)
                ret = ret + T + T + T + 'self.{0}.append(tmp)\n'.format(field)

        elif type(f['LENGTH']) == int:
            if f['IS_BASETYPE']:
                # TODO: replace warning with set default
                ret = ret + T + T + 'if len(self.{0}) != {1}:\n'.format(field, f['LENGTH'])
                ret = ret + T + T + T + 'print( "WARNING: bad field size on {0}\\n" )\n'.format(field)
                ret = ret + T + T + 'for ii in range(max_count):\n'
                ret = ret + T + T + T + 'self.{0}[ii] = gpb_obj.{0}[ii]\n'.format(field)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'if len(self.{0}) != {1}:\n'.format(field, f['LENGTH'])
                ret = ret + T + T + T + 'print( "WARNING: bad field size on {0}\\n" )\n'.format(field)
                ret = ret + T + T + 'for ii in range(max_count):\n'
                #ret = ret + T + T + T + 'tmp = {0}()\n'.format(f['TYPE'])
                #ret = ret + T + T + T + 'tmp.read_gpb(gpb_obj.{0}[ii])\n'.format(field)
                ret = ret + T + T + T + 'self.{0}[ii].read_gpb(gpb_obj.{0}[ii])\n'.format(field)


    ret = ret + T + '# end read_gpb\n\n'

    #
    # write gpb
    #
    ret = ret + '\n\n' + T + 'def write_gpb(self,gpb_obj=None):\n'

    ret = ret + T + T + 'if gpb_obj == None:\n'
    ret = ret + T + T + T + 'gpb_obj = gpb.{0}()\n'.format(struct_name)

    for f in struct_def['FIELDS']:
        field    = f['NAME']
    
        # need max count for fixed length fields
        if type(f['LENGTH']) == int and f['LENGTH'] > 1:
            ret = ret + T + T + 'max_count = min({0}, len(self.{1}))\n'.format(f['LENGTH'],field)
        elif f['LENGTH'] == 'VECTOR':
            ret = ret + T + T +  'max_count = len(self.{0})\n'.format(field)

        # get type
        if f['IS_BASETYPE']:
            basetype = basetypes[f['TYPE']]
            gpb_type = basetype['GPB_TYPE']

        if f['LENGTH']==1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'gpb_obj.{0} = self.{0}\n'.format(field)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'tmp = gpb_obj.{0}\n'.format(field)
                ret = ret + T + T + 'self.{0}.write_gpb(tmp)\n'.format(field)

        elif type(f['LENGTH']) == int or f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'for ii in range(max_count):\n'
                ret = ret + T + T + T + 'gpb_obj.{0}.append( self.{0}[ii] )\n'.format(field)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for ii in range(max_count):\n'
                ret = ret + T + T + T + 'tmp = gpb_obj.{0}.add()\n'.format(field)
                ret = ret + T + T + T + 'self.{0}[ii].write_gpb(tmp)\n'.format(field)
    ret = ret + T + T + 'return gpb_obj\n'

    ret = ret + T + '# end write_gpb\n\n'


    return ret
# end generate_gpb_for_class

def create_gpb_test_for_class( basetypes, structs, struct_name, project ):
    ret = ''
    ret = ret + 'import {0}_interface\n\n'.format(project['PROJECT'])
    ret = ret + 'x = {0}_interface.{1}()\n'.format(project['PROJECT'],struct_name)
    
    struct_def = structs[struct_name]
    for ii, f in enumerate(struct_def['FIELDS']):
        if f['IS_BASETYPE'] and f['LENGTH'] == 1:
            ret = ret + 'x.{0} = {1}\n'.format(f['NAME'],ii)
    ret = ret + 'fout = open("out.bin", "wb")\n'
    ret = ret + 'fout.write(x.write_gpb_to_buf())\n'
    ret = ret + 'fout.close()\n'
    ret = ret + 'fin = open("out.bin", "rb" )\n'
    ret = ret + 'buf = fin.read()\n'
    ret = ret + 'y = {0}_interface.{1}()\n'.format(project['PROJECT'],struct_name)
    ret = ret + 'y.read_gpb_from_buf(buf)\n'
    ret = ret + 'print ("ORIGNAL:")\n'
    ret = ret + 'print (x)\n'
    ret = ret + 'print ("GPB:")\n'
    ret = ret + 'print (y)\n'
    return ret
# end create_gpb_test_for_class


def create_py_class_def( basetypes, structs, struct_name, project, gpb=False ):
    struct_def = structs[ struct_name ]
    ret = py_class_template.format( struct_name )

    # slots here
    ret = ret + T + "__slots__ = [\n"
    for f in struct_def['FIELDS']:
        ret = ret + T + T + '"{0}",\n'.format(f['NAME'])
    ret = ret + T + "]\n\n"

    ret = ret + py_basic_methods

    # set defaults
    ret = ret + T + T + '"""\n'
    ret = ret + T + T + 'Initializes and sets defaults\n'
    ret = ret + T + T + '"""\n'
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                def_val = f['DEFAULT_VALUE']
                ret = ret + T + T + "self.{0} = {1};\n".format(f['NAME'], def_val)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'self.{0} = {1}()\n'.format(f['NAME'], f['TYPE'])
                ret = ret + T + T + 'self.{0}.set_defaults();\n'.format(f['NAME'])
            
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            # If a default vaulue, try to set it
            if 'DEFAULT_VALUE' in f:
                if f['IS_BASETYPE']:
                    basetype = basetypes[f['TYPE']]
                    def_val = f['DEFAULT_VALUE']
                    if len(def_val) == 1:
                        ret = ret + T + T + 'self.{0} = [{1}] * {2}\n'.format(f['NAME'],def_val[0],f['LENGTH'])
                    else:
                        def_str = ''
                        for idx in range(len(def_val)):
                            def_str = def_str + '{0},'.format(def_val[idx])
                        # remove trailing whitespace and comma
                        def_str = def_str.rstrip()
                        if def_str[-1] == ',':  
                            def_str = def_str[:-1]
                        # set the value
                        ret = ret + T + T + 'self.{0} = [ {1} ]\n'.format(f['NAME'],def_str)
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'self.{0} = []\n'.format( f['NAME'] )
                if type(f['LENGTH']) == int:
                    ret = ret + T + T + 'for ii in range({0}):\n'.format(f['LENGTH'])
                    ret = ret + T + T + T + 'self.{0}.append( {1}() )\n'.format(f['NAME'],f['TYPE'])
            # No default value, just set the element
            else:
                ret = ret + T + T + 'self.{0} = []\n'.format(f['NAME'])
                # vector of struct default setting not suppported
    ret = ret + T + "# end set_defaults\n\n"


    # equals operator for testing
    ret = ret + T + "def __ne__(self, obj):\n"
    ret = ret + T + T + "retval = not(self.__eq__(obj))\n"
    ret = ret + T + T + "return retval\n\n"

    ret = ret + T + "def __eq__(self, obj):\n"
    ret = ret + T + T + "retval = True\n"
    ret = ret + T + T + "if obj.__class__ != self.__class__:\n"
    ret = ret + T + T + T + "return False\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            ret = ret + T + T + 'if not self.{0} == obj.{0}:\n'.format(f['NAME'])
            ret = ret + T + T + T + 'retval = False\n'
            #ret = ret + T + T + T + 'print("Mismatch in {0}, {{0}}:{{1}}".format(self.{0},obj.{0}))\n'.format(f['NAME'])

        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            ret = ret + T + T + 'if len(self.{0}) != len(obj.{0}):\n'.format(f['NAME'])
            #ret = ret + T + T + T + 'print("Length mismatch in {0}, {{0}}:{{1}}".format(self.{0},obj.{0}))\n'.format(f['NAME'])
            ret = ret + T + T + T + 'retval = False\n'
            ret = ret + T + T + 'else:\n'
            ret = ret + T + T + T + 'for ii in range(len(self.{0})):\n'.format(f['NAME'])
            ret = ret + T + T + T + T + 'if not self.{0} == obj.{0}:\n'.format(f['NAME'])
            ret = ret + T + T + T + T + T + 'retval = False\n'
            #ret = ret + T + T + T + T + T + 'print("Mismatch in {0} at index {{0}}, {{1}}:{{2}}".format(ii,self.{0}[ii],obj.{0}[ii]))\n'.format(f['NAME'])

    ret = ret + T + T + "return retval\n"
    ret = ret + T + "# end __eq__\n\n"
    
    # from_dict
    ret = ret + T + "def from_dict( self, d ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: from_dict( dict )\n\n'
    ret = ret + T + '   Read this class from a dict object - useful for JSON\n\n'
    ret = ret + T + '   :param dict'
    ret = ret + T + '   :rtype None\n\n'
    ret = ret + T + T + '"""\n'
    for f in struct_def['FIELDS']:
        ret = ret + T + T + 'if "{0}" in d:\n'.format(f['NAME'])
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + T + 'self.{0} = d["{0}"]\n'.format(f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + T + 'self.{0}.from_dict( d )\n'.format(f['NAME'])
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            ret = ret + T + T + T + "self.{0} = []\n".format(f['NAME'])
            if f['IS_BASETYPE']:
                ret = ret + T + T + T  + 'self.{0} = d["{0}"]\n'.format(f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + T + 'for idx in range(len(d["{0}"])):\n'.format(f['NAME'])
                ret = ret + T + T + T + T + 'tmp = {0}()\n'.format( f['TYPE'] )
                ret = ret + T + T + T + T + 'tmp.from_dict(d["{0}"][idx])\n'.format(f['NAME'])
                ret = ret + T + T + T + T + 'self.{0}.append(tmp)\n'.format(f['NAME'])
    ret = ret + T + "# end from_dict\n\n"

    # to_dict
    ret = ret + T + "def to_dict( self ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: to_dict()\n\n'
    ret = ret + T + '   Write this class to a dict - useful for JSON\n\n'
    ret = ret + T + '   :rtype dict\n\n'
    ret = ret + T + T + '"""\n'
    ret = ret + T + T + 'd = {}\n' 
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'd["{0}"] = self.{0}\n'.format(f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'd["{0}"] = self.{0}.to_dict()\n'.format(f['NAME'])
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            ret = ret + T + T + 'd["{0}"] = []\n'.format(f['NAME'])
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'd["{0}"] = self.{0}\n'.format(f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for idx in range(len(self.{0})):\n'.format(f['NAME'])
                ret = ret + T + T + T + 'd["{0}"].append(self.{0}[idx].to_dict())\n'.format(f['NAME'])
    ret = ret + T + T + 'return d\n'
    ret = ret + T + "# end to_dict\n\n"

    # read json
    ret = ret + T + "def to_json( self ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: to_json()\n\n'
    ret = ret + T + '   JSONify this object\n\n'
    ret = ret + T + '   :param None'
    ret = ret + T + '   :rtype string\n\n'
    ret = ret + T + T + '"""\n'
    ret = ret + T + T + 'd = self.to_dict()\n'
    ret = ret + T + T + 'return json.dumps(d)\n'
    ret = ret + T + "# end to_json\n\n"

    # read json
    ret = ret + T + "def from_json( self, r_stream ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: from_json()\n\n'
    ret = ret + T + '   read JSON into this object\n\n'
    ret = ret + T + '   :param file handle'
    ret = ret + T + '   :rtype None\n\n'
    ret = ret + T + T + '"""\n'
    ret = ret + T + T + 'json_obj = json.loads(r_stream.read())\n'
    ret = ret + T + T + 'self.from_dict(json_obj)\n'
    ret = ret + T + "# end from_json\n\n"



    # read binary
    ret = ret + T + "def read_binary( self, r_stream ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: read_binary( file_handle )\n\n'
    ret = ret + T + '   Read this class from a packed binary message\n\n'
    ret = ret + T + '   :param r_stream an open filehandle (opened in mode rb )\n'
    ret = ret + T + '   :rtype None\n\n'
    ret = ret + T + T + '"""\n'
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'self.{0} = io.read_{1}( r_stream )\n'.format(f['NAME'], f['TYPE'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'self.{0}.read_binary( r_stream );\n'.format(f['NAME'])
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            ret = ret + T + T + "self.{0} = []\n".format(f['NAME'])
            # TODO - this needs to be uint32_t
            if f['LENGTH'] == 'VECTOR':
                ret = ret + T + T + "num_elems = io.read_INT_32( r_stream )\n"
            else: # fixed length, no num_elems
                ret = ret + T + T + "num_elems = {0}\n".format(f['LENGTH'])
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'if num_elems > 0:\n'
                ret = ret + T + T + T + 'self.{0} = io.read_{1}( r_stream, nElements=num_elems )\n'.format(f['NAME'], f['TYPE'])
                ret = ret + T + T + 'else:\n'
                ret = ret + T + T + T + 'self.{0} = []\n'.format(f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for idx in range( num_elems ):\n'
                ret = ret + T + T + T + 'tmp = {0}()\n'.format( f['TYPE'] )
                ret = ret + T + T + T + 'tmp.read_binary(r_stream)\n'
                ret = ret + T + T + T + 'self.{0}.append( tmp )\n'.format(f['NAME'])
    ret = ret + T + "# end read_binary\n\n"


    # write binary
    ret = ret + T + "def write_binary( self, r_stream, typecheck=False ):\n"
    ret = ret + T + T + '"""\n'
    ret = ret + T + '.. function:: read_binary( file_handle )\n\n'
    ret = ret + T + '   Write this class to a packed binary message\n\n'
    ret = ret + T + '   :param r_stream an open filehandle (opened in mode wb )\n'
    ret = ret + T + '   :typecheck if True, verify structures are correct type before including in arrays\n'
    ret = ret + T + '   :rtype None\n\n'

    ret = ret + T + T + '"""\n'
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'io.write_{0}( r_stream, self.{1} )\n'.format(f['TYPE'], f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'if typecheck:\n'
                ret = ret + T + T + T + 'if self.{0}.__class__ != {1}:\n'.format(f['NAME'],f['TYPE'])
                ret = ret + T + T + T + T + 'print ("ERROR: {0} should be type {1}, but is {{0}}".format(self.{0}.__class__.__name__))\n'.format(f['NAME'],f['TYPE'])
                ret = ret + T + T + T + T + 'return\n'
                ret = ret + T + T + 'self.{0}.write_binary(r_stream);\n'.format(f['NAME'])
        elif f['LENGTH'] == 'VECTOR' or type(f['LENGTH']) == int:
            if f['LENGTH'] == 'VECTOR':
                # TODO - this needs to be uint32_t
                ret = ret + T + T + "num_elems = len( self.{0} )\n".format(f['NAME'])
                ret = ret + T + T + "io.write_INT_32( r_stream, num_elems )\n"
            else:
                ret = ret + T + T + "num_elems = {0}\n".format(f['LENGTH'])
            if f['IS_BASETYPE']:
                ret = ret + T + T + 'if num_elems > 0:\n'
                ret = ret + T + T + T + 'io.write_{0}( r_stream, self.{1}, nElements=num_elems )\n'.format(f['TYPE'],f['NAME'])
            elif f['IS_STRUCT']:
                ret = ret + T + T + 'for idx in range( num_elems ):\n'
                ret = ret + T + T + T + 'if typecheck:\n'
                ret = ret + T + T + T + T + 'if self.{0}[idx].__class__ != {1}:\n'.format(f['NAME'],f['TYPE'])
                ret = ret + T + T + T + T + T + 'print ("ERROR: {0}[{{0}}] should be type {1}, but is {{1}}".format(idx,self.{0}[idx].__class__.__name__))\n'.format(f['NAME'],f['TYPE'])
                ret = ret + T + T + T + T + T + 'return\n'
                ret = ret + T + T + T + 'self.{0}[idx].write_binary(r_stream)\n'.format(f['NAME'])

    if gpb:
        ret = ret + generate_gpb_for_class(basetypes, structs, struct_name, project)
    ret = ret + T + "# end write_binary\n\n"
    ret = ret + "# end class {0}\n\n".format(struct_name)
 

    return ret
    # end create_class_def


def generate_py( py_dir, basetypes, structs, project, gpb=False ):
    if not os.path.exists( py_dir ):
        os.mkdir( py_dir )

    python_repo_dir = os.path.dirname(os.path.realpath(__file__))
    shutil.copy( python_repo_dir + os.sep + 'io_support.py', 
                 py_dir + os.sep + 'io_support.py' )

    # proto file
    if gpb:
        print ("Creating GPB Proto File")
        import GPB_Generator as gg
        proto_file = gg.generate_gpb(py_dir,py_dir,basetypes,structs,project)
        proto_file = os.path.split(proto_file)[-1]
        # Call protoc - need to be in the directory with it
        here = os.getcwd()
        os.chdir(py_dir)
        cmd = '''protoc --python_out={0} {1}'''.format('.',proto_file)
        print ("Calling {0}".format(cmd))
        os.popen(cmd)
        os.chdir(here)

        # gpb tests
        for struct_name, struct_def in structs.items():
            ret = create_gpb_test_for_class( basetypes, structs, struct_name, project )
            print ("creating test_gpb_{0}.py".format(struct_name))
            fOut = open( '{0}/test_gpb_{1}.py'.format(py_dir,struct_name), "w")
            fOut.write(ret)
            fOut.close
        # end for each struct


    fOut = open( py_dir + os.sep + "{0}_interface.py".format(project['PROJECT']), "w" )
    fOut.write( "#!/usr/bin/env python\n" )
    fOut.write( "import string\n" )
    fOut.write( "import pprint\n" )
    fOut.write( "import struct\n" )
    fOut.write( "import json\n" )
    fOut.write( "import io_support as io\n\n\n" )

    fOut.write( '''"""
.. module:: AutoInterface 
   :synopsis: Generated Code via AutoInterface System

"""
    ''')

    if gpb:
        fOut.write( "\nimport {0}_structs_pb2 as gpb\n\n".format(project['PROJECT']))

    for struct_name, struct_def in structs.items():
        ret = create_py_class_def( basetypes, structs, struct_name, project, gpb )
        fOut.write( ret )
        fOut.write( "\n\n" )
    fOut.close()
# end create_py_files


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_directory' )
    parser.add_argument( '--gpb', action='store_true', help='If selected, generate google protocol buffers serializer')
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')

    args = parser.parse_args()

    json_basetypes = args.json_basetypes_file
    json_file = args.json_structures_file
    out_dir = args.output_directory
    A = AutoGenerator(json_basetypes,json_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project
    generate_py( out_dir, basetypes, structs, project, args.gpb )
