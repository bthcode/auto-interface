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
from Templates import ctypes_class_template, ctypes_basic_methods

T="    "

def create_py_class_def( basetypes, structs, struct_name, project, gpb=False ):
    struct_def = structs[ struct_name ]
    ret = ctypes_class_template.format( struct_name )

    # set pack
    if project['PAD'] > -1:
        ret = ret + T + "_pack_ = {0}\n".format(project['PAD'])

    # ctypes defs here
    ret = ret + T + "_fields_ = [\n"
    for f in struct_def['FIELDS']:
        if f['LENGTH'] == 1:
            if f['IS_STRUCT']:
                t = f['TYPE']
            else:
                basetype = basetypes[f['TYPE']]
                t = basetype['CTYPES_TYPE']
        elif f['LENGTH'] == 'VECTOR': # LATER
            if f['IS_STRUCT']:
                t = 'ctypes.c_uint32' 
            else:
                basetype = basetypes[f['TYPE']]
                t = basetype['CTYPES_TYPE']
        elif type(f['LENGTH']) == int:
            if f['IS_STRUCT']:
                t = "{0} * {1}".format(f['TYPE'], f['LENGTH'])
            else:
                basetype = basetypes[f['TYPE']]
                t = "{0} * {1}".format(basetype['CTYPES_TYPE'], f['LENGTH'])
        ret = ret + T + T + '("{0}",{1}),\n'.format(f['NAME'],t)
    ret = ret + T + "]\n\n"
    

    # slots here
    ret = ret + T + "__slots__ = [\n"
    for f in struct_def['FIELDS']:
        ret = ret + T + T + '"{0}",\n'.format(f['NAME'])
    ret = ret + T + "]\n\n"

    ret = ret + ctypes_basic_methods

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
            
        elif f['LENGTH'] == 'VECTOR': 
            ret = ret + T + T + 'self.{0} = 0\n'.format(f['NAME'])
        elif type(f['LENGTH']) == int:
            # If a default vaulue, try to set it
            if 'DEFAULT_VALUE' in f:
                if f['IS_BASETYPE']:
                    basetype = basetypes[f['TYPE']]
                    def_val = f['DEFAULT_VALUE']
                    if len(def_val) == 1:
                        ret = ret + T + T + 'self.{0} = tuple([{1}]*{2})\n'.format(f['NAME'],def_val[0],f['LENGTH'])
                    else:
                        def_str = ''
                        for idx in range(len(def_val)):
                            def_str = def_str + '{0},'.format(def_val[idx])
                        # remove trailing whitespace and comma
                        def_str = def_str.rstrip()
                        if def_str[-1] == ',':  
                            def_str = def_str[:-1]
                        # set the value
                        ret = ret + T + T + 'self.{0} = tuple([{1}])\n'.format(f['NAME'],def_str)
            elif f['IS_STRUCT']:
                if type(f['LENGTH']) == int:
                    ret = ret + T + T + 'for ii in range({0}):\n'.format(f['LENGTH'])
                    ret = ret + T + T + T + 'self.{0}[ii] = {1}()\n'.format(f['NAME'],f['TYPE'])
            # No default value, just set the element
            else:
                pass
                # vector of struct default setting not suppported
    ret = ret + T + "# end set_defaults\n\n"

    ret = ret + "# end class {0}\n\n".format(struct_name)

    return ret
    # end create_class_def


def generate_py( py_dir, basetypes, structs, project ):
    if not os.path.exists( py_dir ):
        os.mkdir( py_dir )

    python_repo_dir = os.path.dirname(os.path.realpath(__file__))
    shutil.copy( python_repo_dir + os.sep + 'io_support.py', 
                 py_dir + os.sep + 'io_support.py' )


    fOut = open( py_dir + os.sep + "{0}_interface.py".format(project['PROJECT']), "w" )
    fOut.write( "#!/usr/bin/env python\n" )
    fOut.write( "import string\n" )
    fOut.write( "import pprint\n" )
    fOut.write( "import struct\n" )
    fOut.write( "import json\n" )
    fOut.write( "import ctypes\n" )
    fOut.write( "\n\n\n" )

    fOut.write( '''"""
.. module:: AutoInterface 
   :synopsis: Generated Code via AutoInterface System

"""

import collections                                                              
try:                                                                            
    # Python 2.7+                                                               
    basestring                                                                  
except NameError:                                                               
    # Python 3.3+                                                               
    basestring = str                                                            
                                                                                
def todict(obj):                                                                
    """                                                                         
    Recursively convert a Python object graph to sequences (lists)              
    and mappings (dicts) of primitives (bool, int, float, string, ...)          
    """                                                                         
    if isinstance(obj, basestring):                                             
        return obj                                                              
    elif isinstance(obj, dict):                                                 
        return dict((key, todict(val)) for key, val in obj.items())             
    elif isinstance(obj, collections.Iterable) or isinstance(obj, ctypes.Array):
        return [todict(val) for val in obj]                                     
    elif hasattr(obj, '__dict__'):                                              
        return todict(vars(obj))                                                
    elif hasattr(obj, '__slots__'):                                             
        return todict(dict((name, getattr(obj, name)) for name in getattr(obj, '__slots__')))
    return obj                                                                  
# end todict 

def fromdict(s,d):
    # d is either:
    #   dict
    #   list
    #   scalar
    if isinstance(s, collections.Iterable) or isinstance(s,ctypes.Array):
        for idx, d in enumerate(d):
            s[idx] = fromdict(s[idx], d) 
        return s
    elif isinstance(s, ctypes.Structure):
        for name, t in s._fields_:
            if not name in d:
                continue
            obj = getattr(s,name)
            setattr(s, name, fromdict(obj, d[name]))
        return s
    else:
        return d
            
# end fromdict

    ''')

    for struct_name, struct_def in structs.items():
        ret = create_py_class_def( basetypes, structs, struct_name, project )
        fOut.write( ret )
        fOut.write( "\n\n" )
    fOut.close()
# end create_py_files


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python CTypes Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_directory' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')

    args = parser.parse_args()

    json_basetypes = args.json_basetypes_file
    json_file = args.json_structures_file
    out_dir = args.output_directory
    A = AutoGenerator(json_basetypes,json_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project
    generate_py( out_dir, basetypes, structs, project )
