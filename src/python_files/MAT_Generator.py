##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator

T = '    '



##################################################################################
#
# MAT STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
#
##################################################################################

def create_set_defaults(basetypes,structs,struct_name):
    ret = 'function [ out ] = set_defaults_{0}()\n'.format( struct_name )
    # set defaults
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            basetype = basetypes[f['TYPE']]
            mat_type = basetype['MAT_TYPE']
            # get default value 
            if f.has_key('DEFAULT_VALUE'):
                def_val = f['DEFAULT_VALUE']
            else:
                def_val = basetype['DEFAULT_VALUE']
            # format the default value
            if basetype.has_key( 'COMPLEX' ):
                val = '{0} + {1}i'.format(def_val[0],def_val[1])
            else:
                val = '{0}'.format(def_val)
            # set the default value
            ret = ret + T + T + "out.{0} = {1}({2});\n".format(f['NAME'],mat_type,val);
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + T + 'out.{0} = set_defaults_{1}();\n'.format(f['NAME'],f['STRUCT_TYPE'])
        elif f['TYPE'] == 'VECTOR':
            if f.has_key( 'DEFAULT_VALUE' ):
                if basetypes.has_key(f['CONTAINED_TYPE']):
                    basetype = basetypes[f['CONTAINED_TYPE']]
                    def_val = f['DEFAULT_VALUE']
                    # COMPLEX
                    if basetype.has_key('COMPLEX'):
                        def_str = ''
                        for idx in range(0,len(def_val),2):
                            def_str = def_str + '{0} + {1}i '.format(def_val[idx],def_val[idx+1])
                    # Not COMPLEX
                    else:
                        def_str = ''
                        for idx in range(len(def_val)):
                            def_str = def_str + '{0} '.format(def_val[idx])
                    # set the value
                    ret = ret + T + T + 'out.{0} = [ {1} ];\n'.format(f['NAME'],def_str)
                # No method for defaulting structs yet
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + T + 'out.{0} = [];\n'.format( f['NAME'] )
            # No default value, just set the element
            else:
                ret = ret + T + T + 'out.{0} = [];\n'.format(f['NAME'])
    ret = ret + 'end\n'

    return ret
# end create_set_defaults

def create_read_binary(basetypes,structs,struct_name):
    ret = 'function [ struct_in ] = read_binary_{0}( file_handle )\n'.format(struct_name)
    ret = ret + T + 'success = 1;\n'
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if basetypes.has_key(f['TYPE']):
            b = basetypes[f['TYPE']]
            if b.has_key('COMPLEX'):
                ret = ret + T + "tmp = fread( file_handle, 2, '{0}' );\n".format(b['MAT_TYPE'])
                ret = ret + T + "struct_in.{0} = tmp(1) + tmp(2)*i;\n".format(f['NAME'])
            else:
                ret = ret + T + "struct_in.{0} = fread( file_handle, 1, '{1}' );\n".format(f['NAME'],b['MAT_TYPE'])
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + 'struct_in.{0} = read_binary_{1}( file_handle );\n'.format(f['NAME'],f['STRUCT_TYPE']) 
        elif f['TYPE'] == 'VECTOR':
            # get number of elements
            ret = ret + T + T + "num_elems = fread(file_handle,1,'uint32');\n"
            # now read in that many types
            if basetypes.has_key(f['CONTAINED_TYPE']):
                b = basetypes[f['CONTAINED_TYPE']]
                if b.has_key('COMPLEX'):
                    ret = ret + T + "tmp = fread( file_handle, num_elems*2, '{0}' );\n".format(b['MAT_TYPE'])
                    ret = ret + T + "struct_in.{0} = complex(tmp(1:2:end-1), tmp(2:2:end));\n".format(f['NAME'])
                else:
                    ret = ret + T + "struct_in.{0} = fread( file_handle, num_elems, '{1}' );\n".format(f['NAME'],b['MAT_TYPE'])
            elif f['CONTAINED_TYPE'] == 'STRUCT':
                ret = ret + T + 'struct_in.{0} = [];\n'.format(f['NAME'])
                ret = ret + T + 'for i=1:num_elems\n'   
                ret = ret + T + T + 'struct_in.{0}(end+1)=read_binary_{1}(file_handle);\n'.format(f['NAME'],f['STRUCT_TYPE'])
                ret = ret + T + 'end\n'
    ret = ret + 'end\n'
    return ret
# end create_read_binary

def create_write_binary(basetypes,structs,struct_name):
    ret = 'function [ success ] = write_binary_{0}( file_handle )\n'.format(struct_name)
    ret = ret + T + 'success = 0;\n'
    ret = ret + 'end\n'
    return ret
# end create_write_binary

def create_set_defaults_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "set_defaults_{0}.m".format(struct_name),"w")
        fOut.write(create_set_defaults(basetypes,structs,struct_name))
# end create_set_defaults

def create_read_binary_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "read_binary_{0}.m".format(struct_name),"w")
        fOut.write(create_read_binary(basetypes,structs,struct_name))
# end create_read_binary

def create_write_binary_files(mat_dir,basetypes,structs):
    for struct_name, struct_def in structs.items():
        fOut = open(mat_dir + os.sep + "write_binary_{0}.m".format(struct_name),"w")
        fOut.write(create_write_binary(basetypes,structs,struct_name))
# end create_write_binary

def generate_mat( mat_dir, basetypes, structs ):
    if not os.path.exists(mat_dir):
        os.mkdir(mat_dir)

    create_set_defaults_files(mat_dir,basetypes,structs)
    create_read_binary_files(mat_dir,basetypes,structs)
    create_write_binary_files(mat_dir,basetypes,structs)
# end generate_mat

if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'mat_dir' )
    args = parser.parse_args()

    A = AutoGenerator( args.json_basetypes_file, args.json_structures_file, "")
    basetypes = A.basetypes
    structs   = A.structs
    generate_mat( args.mat_dir, basetypes, structs )
