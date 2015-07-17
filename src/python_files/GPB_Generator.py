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

def create_proto_for_struct(basetypes,structs,struct_name):
    ret = '\n// Struct: {0}\n'.format(struct_name)
    ret = ret + 'message {0} {{\n'.format(struct_name)
    struct = structs[struct_name]
    # TODO:
    # -- add gpb field type into basetypes
    # -- handle default setting

    for idx,f in enumerate(struct['FIELDS']):
        name = f['NAME']
        field_count = idx+1
        if f['LENGTH'] == 1:
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                gpb_type = basetype['GPB_TYPE']
                default = f['DEFAULT_VALUE']
                ret = ret + T + 'optional {0} {1} = {2} [default={3}];\n'.format(gpb_type,name,field_count,default)
            elif f['IS_STRUCT']:
                gpb_type = f['TYPE']
                ret = ret + T + 'optional {0} {1} = {2};\n'.format(gpb_type,name,field_count)
        elif type( f['LENGTH'] ) == int or f['LENGTH'] == 'VECTOR':
            if f['IS_BASETYPE']:
                basetype = basetypes[f['TYPE']]
                gpb_type = basetype['GPB_TYPE']
                default = f['DEFAULT_VALUE']
                ret = ret + T + 'repeated {0} {1} = {2};\n'.format(gpb_type,name,field_count)
            elif f['IS_STRUCT']:
                gpb_type = f['TYPE']
                ret = ret + T + 'repeated {0} {1} = {2};\n'.format(gpb_type,name,field_count)

    ret = ret + '}\n\n'
    return ret
# end gen_proto_for_struct

def create_proto_file(basetypes,structs,project):
    ret = 'syntax="proto2"\n'
    ret = 'package {0}_GPB;\n'.format(project['NAMESPACE'])
    # namespace?
    # version?
    for struct_name, struct_def in structs.items():
        ret = ret + create_proto_for_struct(basetypes,structs,struct_name)
    return ret
# end create_proto_file

def generate_gpb(src_dir,inc_dir,basetypes,structs,project):
    if not os.path.exists( src_dir ):
        os.mkdir(src_dir)
    if not os.path.exists( inc_dir ):
        os.mkdir(inc_dir)

    python_repo_dir = os.path.dirname(os.path.realpath(__file__))

    proto_text = create_proto_file(basetypes,structs,project)
    proto_file = src_dir + os.sep + '{0}_structs.proto'.format(project['PROJECT'])
    fOut = open(proto_file , 'w')
    fOut.write(proto_text)
    fOut.close()
    return proto_file

# end generate_gpb



if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface GPB Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'inc_dir' )
    parser.add_argument( 'src_dir' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    A = AutoGenerator(args.json_basetypes_file, args.json_structures_file,pad=args.pad)
    basetypes = A.basetypes
    structs   = A.structs
    project   = A.project
    generate_gpb(args.src_dir,args.inc_dir,basetypes,structs,project)
