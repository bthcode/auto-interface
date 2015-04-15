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
# Utility Functions
#
##################################################################################

##################################################################################
#
# MAT STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
#
##################################################################################

def create_c_struct_header( basetypes, structs, struct_name ):
    ''' create a pure c language struct header '''
    struct_def = structs[ struct_name ]
    ret = header_template.format( struct_name )
    ### Other generated deps
    deps = get_c_dependencies_for_struct( structs, struct_name )
    for dep in deps:
        ret = ret + '#include "%s"' % dep + "\n"

    ### Class Def
    ret = ret + " typedef struct {{\n".format( struct_name )


    ### Member Data
    ret = ret + '\n\n    // Member Fields\n\n'
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            c_decl = basetypes[ f['TYPE'] ]['C_TYPE']
        elif f['TYPE'] == 'STRUCT':
            c_decl = '%s' % ( f['STRUCT_TYPE'] )
        elif f['TYPE'] == 'VECTOR':
            if f['CONTAINED_TYPE'] == 'STRUCT':
                c_decl = '{0} **'.format( f['STRUCT_TYPE'] )
            elif basetypes.has_key( f['CONTAINED_TYPE'] ):
                c_decl = '{0} *'.format( basetypes[ f['CONTAINED_TYPE'] ][ 'C_TYPE' ] )
            elif f['CONTAINED_TYPE'] == 'COMPLEX':
                c_decl = '{0} complex *'.format( basetypes[ f['COMPLEX_TYPE' ] ][ 'C_TYPE' ] )
            else:
                print 'ERROR - vector with unknown type or no CONTAINED_TYPE key'
                sys.exit(1)
        elif f['TYPE'] == 'COMPLEX':
            c_decl = '{0} complex'.format( basetypes[ f['COMPLEX_TYPE' ] ][ 'C_TYPE' ] )
        else:
            print 'ERROR - vector with no TYPE'
            sys.exit(1)
        ret = ret + T + "{0}  {1}; ///<{2}\n".format( c_decl, f['NAME'], f['DESCRIPTION'] )
        if f['TYPE'] == 'VECTOR':
            ret = ret + T + "int32_t n_elements_{0};\n".format( f['NAME'] )


    ret = ret + T + "size_t num_fields;\n"
    ret = ret + "\n}} {0} ;\n".format( struct_name )

    ret = ret + funcs_template.format(struct_name)



    ret = ret + "#endif\n"
    return ret
# end create_c_struct_header

def create_c_struct_impl( basetypes, structs, struct_name ):
    '''Creates the Primary Structure CPP Implementation'''

    struct_def = structs[ struct_name ]

    ret = '#include "%s.h"\n\n' % ( struct_name )
    ret = ret + '#include "io_support.h"\n'

    ### Allocate
    ret = ret + 'void alloc_{0} ( {0} * p_{0} )\n{{\n'.format(struct_name)
    ret = ret + T + 'p_{0} = ({0} *) malloc( 1 * sizeof({0}) );\n'.format(struct_name)
    ret = ret + '}\n'

    ### De-allocate
    ret = ret + 'void dealloc_{0}( {0} * p_{0} ){{\n'.format(struct_name)
    ret = ret + T + '// Deallocate Allocated Fields\n'
    for f in struct_def['FIELDS']:
        if f['TYPE'] == 'VECTOR':
            if f['CONTAINED_TYPE'] == 'STRUCT':
                ret = ret + T + 'for (size_t ii=0; ii<p_{0}->n_elements_{1}; ii++ )\n'.format(struct_name,f['NAME'])
                ret = ret + T + '{\n'
                ret = ret + T + T + 'dealloc_{0}( p_{1}->{2}[ii] );\n'.format(f['STRUCT_TYPE'],struct_name,f['NAME'])
                ret = ret + T + '}\n'
            ret = ret + T + 'if (p_{0}->n_elements_{1} > 0 ){{free( p_{0}->{1} );}}\n'.format(struct_name,f['NAME'])
            ret = ret + T + 'p_{0}->n_elements_{1} = 0;\n'.format(struct_name,f['NAME'])
            ret = ret + T + 'p_{0}->{1} = 0x0;\n'.format(struct_name,f['NAME'])
        if f['TYPE'] == 'STRUCT':
            ret = ret + T + 'dealloc_{0}( &(p_{1}->{2}) );\n'.format(f['STRUCT_TYPE'],struct_name,f['NAME'])
    ret = ret + "}\n\n"

    ### Read Binary 
    ret = ret + "void read_binary_{0}( FILE * r_stream, {0} * p_{0} ){{\n".format(struct_name)
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            ret = ret + T + 'read_{0}( r_stream, 1, &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME']);
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + 'read_binary_{0}(r_stream, &(p_{1}->{2}));\n'.format(f['STRUCT_TYPE'], struct_name, f['NAME'])
            ret = ret + "\n"
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + "int32_t n_elements_{0};\n".format(f['NAME'])
            ret = ret + T + 'read_INT_32(r_stream,1,&(n_elements_{0}));\n'.format(f['NAME'])
            ret = ret + T + 'p_{0}->n_elements_{1} = n_elements_{1};\n'.format(struct_name,f['NAME'])
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                ctype = basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                # ALLOC SPACE
                ret = ret + T + 'p_{0}->{1} = ({2}*) malloc(n_elements_{1} * sizeof({2}));\n'.format(struct_name,f['NAME'],ctype);
                ret = ret + T + 'read_{0}(r_stream, n_elements_{2}, p_{1}->{2});\n'.format(f['CONTAINED_TYPE'],struct_name,f['NAME'])
                ret = ret + "\n"
            elif f['CONTAINED_TYPE'] == 'STRUCT':
                ctype = f['STRUCT_TYPE']
                # Allocate space for pointers
                ret = ret + T + 'p_{0}->{1} = ({2}**) malloc(n_elements_{1} * sizeof({2} *));\n'.format(struct_name,f['NAME'],ctype);
                ret = ret + T + 'for (int32_t ii=0; ii < p_{0}->n_elements_{1}; ii++) {{\n'.format(struct_name,f['NAME'])
                ret = ret + "\n"
                # For each pointer, call read binary
                ret = ret + T + T + '{0} * x = ({0}*) malloc( sizeof({0}) );\n'.format(f['STRUCT_TYPE'])
                ret = ret + T + T + 'read_binary_{0}(r_stream, x );\n'.format(f['STRUCT_TYPE'])
                ret = ret + T + T + 'p_{0}->{1}[ii] = x;\n'.format(struct_name,f['NAME'])
                ret = ret + T + '}\n\n'
    ret = ret + "}\n\n"

    ### Write Binary 
    ret = ret + "void write_binary_{0}( FILE * r_stream, {0} * p_{0} ){{\n".format(struct_name)
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            ret = ret + T + 'write_{0}( r_stream, 1, &(p_{1}->{2}) );\n'.format(f['TYPE'],struct_name,f['NAME']);
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + 'write_binary_{0}(r_stream, &(p_{1}->{2}));\n'.format(f['STRUCT_TYPE'], struct_name, f['NAME'])
            ret = ret + "\n"
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + 'write_INT_32(r_stream,1,&(p_{0}->n_elements_{1}));\n'.format(struct_name,f['NAME'])
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                ret = ret + T + 'write_{0}(r_stream,p_{1}->n_elements_{2},p_{1}->{2});\n'.format(f['CONTAINED_TYPE'],struct_name,f['NAME']) 
            elif f['CONTAINED_TYPE'] == 'STRUCT':
                ret = ret + T + 'for (int ii=0; ii< p_{0}->n_elements_{1}; ++ii )\n{{\n'.format(struct_name,f['NAME'])
                ret = ret + T + T + 'write_binary_{0}(r_stream, p_{1}->{2}[ii]);\n'.format(f['STRUCT_TYPE'], struct_name, f['NAME'])
                ret = ret + T + '}\n\n'
    ret = ret + "}\n\n"


    return ret
# end create_c_struct_impl

def create_set_defaults(basetypes,structs,struct_name):
    ret = 'function [ out ] = set_defaults_{0}()\n'.format( struct_name )
    # set defaults
    struct_def = structs[struct_name]
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            if f.has_key('DEFAULT_VALUE'):
                ret = ret + T + T + "out.{0} = {1}({2});\n".format(f['NAME'], basetypes[f['TYPE']]['MAT_TYPE'], f['DEFAULT_VALUE'])
            else:
                ret = ret + T + T +  "out.{0} = {1}({2});\n".format(f['NAME'], basetypes[f['TYPE']]['MAT_TYPE'],  basetypes[f['TYPE']]['DEFAULT_VALUE'])
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + T + 'out.{0} = set_defaults_{1}();\n'.format(f['NAME'],f['STRUCT_TYPE'])
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + T + 'out.{0} = [];\n'.format(f['NAME'])

    ret = ret + 'end\n'

    return ret
# end create_set_defaults

def create_read_binary(basetypes,structs,struct_name):
    ret = 'function [ success ] = read_binary_{0}( file_handle )\n'.format(struct_name)
    ret = ret + T + 'success = 0;\n'
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
