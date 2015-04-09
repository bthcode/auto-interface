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

def get_c_dependencies_for_struct( structs, struct_name):
    includes = {} # insert into a map to force unique -- probably a better way
    struct_def = structs[ struct_name ]
    for field in struct_def['FIELDS']:
        if field['TYPE'] == "STRUCT":
            includes[ "%s.h" % ( field['STRUCT_TYPE'] ) ] = 1
        elif  field['TYPE'] == 'VECTOR' and field['CONTAINED_TYPE'] == 'STRUCT':
            includes[ "%s.h" % ( field['STRUCT_TYPE'] ) ] = 1
    return includes.keys()
# end get_dependencies_for_struct

header_template = '''
#ifnef {0}_C_H
#define {0}_C_H

// Stock Includes
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <complex.h>
'''

funcs_template = '''
    int validate_{0}( {0} * p_{0} );
    void set_defaults_{0}( {0} * p_{0} );
    //void write_props_{0}( std::ostream& r_stream, std::string& r_prefix );
    //void read_props_{0}( std::istream& r_in_stream, std::string& r_prefix );
    //std::size_t read_props_{0}( std::map< std::string, std::string>& r_params, std::string& r_prefix );
    void write_binary_{0}( FILE * r_out_stream, {0} * p_{0} );
    void read_binary_{0}( FILE * r_in_stream, {0} * p_{0} );
    void alloc_{0}( {0} * p_{0} );
    void dealloc_{0}( {0} * p_{0} );
'''





##################################################################################
#
# C STRUCTURE DEFINITIONS AND IMPLEMENTATIONS
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
    ret = ret + "struct {0} {{\n".format( struct_name )


    ### Member Data
    ret = ret + '\n\n    // Member Fields\n\n'
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            c_decl = basetypes[ f['TYPE'] ]['C_TYPE']
        elif f['TYPE'] == 'STRUCT':
            c_decl = 'struct %s' % ( f['STRUCT_TYPE'] )
        elif f['TYPE'] == 'VECTOR':
            if f['CONTAINED_TYPE'] == 'STRUCT':
                c_decl = 'struct {0} **'.format( f['STRUCT_TYPE'] )
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
            ret = ret + T + "size_t n_elements_{0};\n".format( f['NAME'] )


    ret = ret + T + "size_t num_fields;\n"
    ret = ret + "\n};\n"

    ret = ret + funcs_template(struct_name)



    ret = ret + "#endif\n"
    return ret
# end create_c_struct_header

def create_c_struct_impl( basetypes, structs, struct_name ):
    '''Creates the Primary Structure CPP Implementation'''

    struct_def = structs[ struct_name ]

    ret = '#include "%s.h"\n\n' % ( struct_name )

    ### Allocate
    ret = ret + \
'''
void alloc_{0} ( {0} * p_{0} )
{{
    p_{0} = (p_{0} *) malloc( 1 * sizeof(p_{0}) );
}}

'''.format( struct_name )

    ### De-allocate
    ret = ret + 'void dealloc_{0}( {0} * p_{0} ){{\n'.format( struct_name )
    ret = ret + T + '// Deallocate Allocated Fields\n'
    for f in struct_def['FIELDS']:
        if f['TYPE'] == 'VECTOR':
            if f['CONTAINED_TYPE'] == 'STRUCT':
                ret = ret + \
'''
    for (size_t ii=0; ii<n_elements_{0}; ii++ )
    {{
        dealloc_{1}( {2}[ii] );
    }}
'''.format( f['NAME'], f['STRUCT_TYPE'], f['NAME'] )
            else:
                ret = ret + T + 'free {0};\n'.format( f['NAME'] )
                 
    ret = ret + T + '// Deallocate {0} pointer\n'.format( struct_name )
    ret = ret + T + 'free p_{0};\n'.format( struct_name );
    ret = ret + T + 'p_{0} = 0x0;\n'.format( struct_name );
    ret = ret + "}\n\n"

    ### Read Binary 
    ret = ret + "void read_binary_{0}( FILE * r_stream, {0} * p_{0} ){{\n".format( struct_name )
    for f in struct_def['FIELDS']:
        if basetypes.has_key( f['TYPE'] ):
            ctype = basetypes[f['TYPE']]['C_TYPE']
            ret = ret + T + 'fread(&(p_{0}->{1}), sizeof({2}),1,r_stream);\n'.format(struct_name, f['NAME'], ctype )
            ret = ret + "\n"
        elif f['TYPE'] == 'COMPLEX':
            ctype = "{0} complex".format(basetypes[f['COMPLEX_TYPE']]['C_TYPE'])
            ret = ret + T + 'fread(&(p_{0}->{1}), sizeof({2}),1,r_stream);\n'.format(struct_name, f['NAME'], ctype )
            ret = ret + "\n"
        elif f['TYPE'] == 'STRUCT':
            ret = ret + T + 'read_binary_{0}(r_stream, &(p_{1}->{2}));\n'.format( f['STRUCT_TYPE'], struct_name, f['NAME'] )
            ret = ret + "\n"
        elif f['TYPE'] == 'VECTOR':
            ret = ret + T + 'uint32_t tmp_%s_size;\n' % ( f['NAME'] )
            ret = ret + T + 'fread(&(tmp_%s_size), sizeof(tmp_%s_size),1,r_stream);\n' % ( f['NAME'], f['NAME'] )
            if basetypes.has_key( f['CONTAINED_TYPE'] ):
                ctype = basetypes[ f['CONTAINED_TYPE'] ]['C_TYPE']
                # ALLOC SPACE
                ret = ret + T + 'p_{0}->{1} = ({2}*) malloc( tmp_{1}_size * sizeof({2}) );\n'.format( struct_name, f['NAME'], ctype );
                ret = ret + T + 'fread(p_{0}->{1}, sizeof({2}), tmp_{1}_size, r_stream);\n'.format( struct_name, f['NAME'], ctype ) 
                ret = ret + "\n"
            elif f['CONTAINED_TYPE'] == 'STRUCT':
                ctype = f['STRUCT_TYPE']
                # Allocate space for pointers
                ret = ret + T + 'p_{0}->{1} = ({2}**) malloc( tmp_{1}_size * sizeof({2} *) );\n'.format( struct_name, f['NAME'], ctype );
                ret = ret + T + 'for ( uint32_t ii=0; ii < tmp_{0}_size; ii++ ) {{\n'.format( f['NAME'] )
                ret = ret + "\n"
                # For each pointer, call read binary
                ret = ret + T + T + 'read_binary_{0}( r_stream, p_{1}->{2}[ii]);\n'.format( f['STRUCT_TYPE'], struct_name, f['NAME'] )
                ret = ret + T + '}\n\n'
            elif f['CONTAINED_TYPE'] == 'COMPLEX':
                ctype = '{0} complex'.format(basetypes[f['COMPLEX_TYPE']]['C_TYPE']);
                print f['NAME'], ctype
                allocator = T + 'p_{0}->{1} = ({2}*) malloc( tmp_{1}_size * sizeof({2}) );\n'.format( struct_name, f['NAME'], ctype );
                reader = T + 'fread(p_{0}->{1}, sizeof({2}), tmp_{1}_size, r_stream);\n'.format( struct_name, f['NAME'], ctype ) 
                ret = ret + "\n"
                ret = ret + allocator
                ret = ret + reader
    ret = ret + "}\n\n"

    """


        ### Write Binary
        ret = ret + "void %s::write_binary( std::ofstream& r_stream ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ) or f['TYPE'] == 'COMPLEX':
                ret = ret + T + 'r_stream.write( (char*)&(%s), sizeof(%s) );\n' %( f['NAME'], f['NAME'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + '%s.write_binary( r_stream );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                ret = ret + T + 'uint32_t tmp_%s_size = %s.size();\n' % ( f['NAME'], f['NAME'] )
                ret = ret + T + 'r_stream.write( (char*)&(tmp_%s_size), sizeof( tmp_%s_size ) );\n' % ( f['NAME'], f['NAME'] )
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ) or f['CONTAINED_TYPE'] == 'COMPLEX':
                    ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + 'r_stream.write( (char*)&(%s[ii]), sizeof(%s[ii]));\n' % ( f['NAME'], f['NAME'] )
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + 'for ( uint32_t ii=0; ii < %s.size(); ii++ ) {\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s[ii].write_binary( r_stream );\n' % ( f['NAME'] )
                    ret = ret + T + '}\n'
        ret = ret + "}\n\n"



        ### Write Props
        ret = ret + "void %s::write_props( std::ostream& r_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + "std::string tmp;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if b.has_key('STREAM_CAST'):
                    c_print = T + 'r_stream << r_prefix << "%s = " << (%s)(%s) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'], f['NAME'] )
                else:
                    c_print = T + 'r_stream << r_prefix << "%s = " << %s << "\\n";\n' % ( f['NAME'], f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'tmp = r_prefix + "%s.";\n' % ( f['NAME'] )
                c_print = T + '%s.write_props( r_stream, tmp );\n' % ( f['NAME'] )
                ret = ret + c_print
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    iter_decl  = T + T + 'std::vector< %s >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    iter_decl  = T + T + 'std::vector< std::complex< %s > >::iterator ii;\n' % ( b['C_TYPE'] )
                    if b.has_key( 'STREAM_CAST' ):
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << %s((*ii)) << "\\n";\n' % ( f['NAME'], b['STREAM_CAST'] )
                    else:
                        print_decl = T + T + T + 'r_stream << r_prefix << "%s[ " << count << " ] = "  << (*ii) << "\\n";\n' % ( f['NAME'] )
                
                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    iter_decl = T + T + 'std::vector< %s >::iterator ii;\n' % ( f['STRUCT_TYPE'] )
                    print_decl = T + T + T + 'std::stringstream ss;\n'
                    print_decl = print_decl + T + T + T + 'ss << r_prefix << "%s[ " << count << " ].";\n' % ( f['NAME'] )
                    print_decl = print_decl + T + T + T + 'std::string tmp( ss.str() );\n'
                    print_decl = print_decl + T + T + T + 'ii->write_props( r_stream, tmp );\n'
                
                ret = ret + T + '{\n'
                ret = ret + iter_decl
                ret = ret + T + T +  'std::size_t count = 0;\n'
                ret = ret + T + T +  'for ( ii = %s.begin(); ii != %s.end(); ii++ )\n' %( f['NAME'], f['NAME'] )
                ret = ret + T + T +  '{\n'
                ret = ret + print_decl
                ret = ret + T + T +T +   'count++;\n'
                ret = ret + T + T +  '}\n'
                ret = ret + T + '}\n'
        ret = ret + "}\n\n"

        ### Read Props From Params
        ret = ret + "std::size_t %s::read_props( std::map< std::string, std::string>& r_params, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + 'std::string key;\n'
        ret = ret + T + 'std::map< std::string, std::string >::iterator param_iter;\n'
        ret = ret + T + 'std::size_t fields_found=0;\n'

        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                ret = ret + T + 'key = r_prefix + "%s";\n\n' % ( f['NAME'] )
                ret = ret + T + 'param_iter = r_params.find( key );\n'
                ret = ret + T + 'if ( param_iter != r_params.end() )\n'
                ret = ret + T + '{\n'
                ret = ret + T +T +  'std::stringstream ss( param_iter->second );\n'
                if b.has_key('STREAM_CAST'):
                    ret = ret + T +T +  '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                    ret = ret + T +T +  'ss >> u;\n'
                    ret = ret + T +T +  '%s = (%s)( u );\n' % ( f['NAME'], b['STREAM_CAST' ] )
                else:
                    ret = ret + T +T +  'ss >> %s;\n' % ( f['NAME'] )
                ret = ret + T +T +  'fields_found++;\n'
                ret = ret + T + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'key = r_prefix + "%s.";\n' % ( f['NAME'] )
                ret = ret + T + 'fields_found += %s.read_props( r_params, key );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                if self.basetypes.has_key( f['CONTAINED_TYPE'] ):
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['CONTAINED_TYPE'] ]
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T +T + 'std::stringstream ss;\n'
                    ret = ret + T +T + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + T +T + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + T +T + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + T +T + T + 'break;\n'
                    ret = ret + T +T + 'else {\n'
                    ret = ret + T +T + T + 'std::stringstream ss2( param_iter->second );\n'
                    if b.has_key( 'STREAM_CAST' ):
                        ret = ret + T +T +T + '%s u;\n' % ( b[ 'STREAM_CAST' ] )
                        ret = ret + T +T +T + 'ss2 >> u;\n'
                        ret = ret + T +T +T + '%s.push_back(%s( u ));\n' % ( f['NAME'], b['STREAM_CAST' ] )
                    else:
                        ret = ret + T +T +T + '%s u;\n' % ( b[ 'C_TYPE' ] )
                        ret = ret + T +T +T + 'ss2 >> u;\n'
                        ret = ret + T +T +T + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + T +T +T + 'count++;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T +T + 'fields_found += count;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T + '}\n'
                elif f['CONTAINED_TYPE'] == 'COMPLEX':
                    # 1. Get the prefix
                    # 2. Go into a while loop incrementing count until no more keys 
                    #       are found
                    b = self.basetypes[ f['COMPLEX_TYPE'] ]
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T +T + 'std::stringstream ss;\n'
                    ret = ret + T +T + 'ss << r_prefix << "%s" << "[ " << count << " ]";\n' % ( f['NAME'] )
                    ret = ret + T +T + 'param_iter = r_params.find( ss.str() );\n' 
                    ret = ret + T +T + 'if ( param_iter == r_params.end() )\n'
                    ret = ret + T +T + T + 'break;\n'
                    ret = ret + T +T + 'else {\n'
                    ret = ret + T +T + T + 'std::stringstream ss2( param_iter->second );\n'
                    ret = ret + T +T +T + 'std::complex< %s > u;\n' % ( b[ 'C_TYPE' ] )
                    ret = ret + T +T +T + 'ss2 >> u;\n'
                    ret = ret + T +T +T + '%s.push_back(u);\n' % ( f['NAME'] ) 
                    ret = ret + T +T +T + 'count++;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T +T + 'fields_found += count;\n'
                    ret = ret + T +T + '}\n'
                    ret = ret + T + '}\n'

                elif f['CONTAINED_TYPE'] == 'STRUCT':
                    ret = ret + T + '{\n'
                    ret = ret + T + 'std::size_t count=0;\n'
                    ret = ret + T + 'while( 1 )\n'
                    ret = ret + T + '{\n'
                    ret = ret + T + T + 'std::stringstream ss;\n'
                    ret = ret + T + T + 'ss << r_prefix << "%s" << "[ " << count << " ].";\n' % ( f['NAME'] )
                    ret = ret + T + T + '%s tmp_%s;\n' % ( f[ 'STRUCT_TYPE' ], f['STRUCT_TYPE' ] )
                    ret = ret + T + T + 'tmp_%s.set_defaults();\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + T + T + 'std::string s ( ss.str() );\n'
                    ret = ret + T + T + 'if ( tmp_%s.read_props( r_params, s )) {\n' % ( f['STRUCT_TYPE'] )
                    ret = ret + T + T + T + '%s.push_back( tmp_%s );\n' % ( f['NAME'], f['STRUCT_TYPE' ] )
                    ret = ret + T + T + '}\n'
                    ret = ret + T + T +  'else { break; }\n'
                    ret = ret + T + T + T + 'count++;\n'
                    ret = ret + T + T + '}\n'
                    ret = ret + T + 'fields_found += count;\n'
                    ret = ret + T + '}\n'
                
        ret = ret + T + 'return fields_found;\n'
        ret = ret + "}\n\n"


        ### Read Props From Stream
        ret = ret + "void %s::read_props( std::istream& r_in_stream, std::string& r_prefix ){\n\n" % ( struct_name )
        ret = ret + T + 'std::map< std::string, std::string > params;\n\n'
        ret = ret + T + 'parse_param_stream( r_in_stream, params );\n\n' 
        ret = ret + T + 'std::string key;\n'
        ret = ret + T + 'read_props( params, r_prefix );\n' 
        ret = ret + "}\n\n"

        ### Defaults
        ret = ret + "void %s::set_defaults( ){\n\n" % ( struct_name )
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('DEFAULT_VALUE'):
                    ret = ret + T + "%s = %s;\n" % ( f['NAME'], f['DEFAULT_VALUE'] )
                else:
                    ret = ret + T + "%s = %s;\n" % ( f['NAME'], b['DEFAULT_VALUE'] )
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + '%s.set_defaults( );\n' % ( f['NAME'] )
            elif f['TYPE'] == 'VECTOR':
                if f.has_key( 'DEFAULT_VALUE' ):
                    arr = f['DEFAULT_VALUE'].split()
                    ret = ret + T + "{0}.resize( {1} );\n".format( f['NAME'], len(arr) )
                    for i, val in enumerate(arr):
                        ret = ret + T + "{0}[{1}] = {2};\n".format( f['NAME'], i, val )
        ret = ret + "}\n\n"

        ### Validate 
        ret = ret + "int %s::validate( std::string& err_msg ){\n\n" % ( struct_name )
        ret = ret + T + "int num_errs=0;\n"
        for f in struct_def['FIELDS']:
            if self.basetypes.has_key( f['TYPE'] ):
                b = self.basetypes[ f['TYPE'] ]
                if f.has_key('VALID_MIN'):
                    ret = ret + T + "if ( %s < %s ) {\n" % ( f['NAME'], f['VALID_MIN'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is less than %s\\n";\n' % ( f['NAME'], f['VALID_MIN'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
                if f.has_key('VALID_MAX'):
                    ret = ret + T + "if ( %s > %s ) {\n" % ( f['NAME'], f['VALID_MAX'] )
                    ret = ret + T + T + 'err_msg +=  "Failed field: %s is greater than %s\\n";\n' % ( f['NAME'], f['VALID_MAX'])
                    ret = ret + T + T + 'num_errs++;\n'
                    ret = ret + T + '}\n'
            elif f['TYPE'] == 'STRUCT':
                ret = ret + T + 'num_errs += %s.validate( err_msg );\n' % ( f['NAME'] )
        ret = ret + T + 'return num_errs;\n';
        ret = ret + "}\n\n"

        ### End Namespace
        if struct_def.has_key( 'NAMESPACE' ):
            ret = ret + '} // namepsace\n\n'
        """

    return ret
# end create_c_struct_impl

    ###############################################################
    # END STRAIGHT C
    ###############################################################

def create_c_headers( inc_dir, basetypes, structs ):
    '''Creates all structure and matlab support headers'''
    for struct_name, struct_def in structs.items():
        fOut = open( inc_dir + os.sep + "%s.h" % (struct_name), "w" )
        fOut.write( create_c_struct_header( basetypes, structs, struct_name ) )
# end create_struct_headers

def create_c_impls( src_dir, basetypes, structs):
    '''Creates all structure and matlab support c files'''
    for struct_name, struct_def in structs.items():
        c_def = create_c_struct_impl( basetypes, structs, struct_name )
        fOut = open( src_dir + os.sep + "%s.c" % (struct_name), "w" )
        fOut.write( c_def )
# end create_struct_impl

def generate_c( src_dir, inc_dir, basetypes, structs ):
    if not os.path.exists(src_dir):
        os.mkdir(src_dir)
    if not os.path.exists(inc_dir):
        os.mkdir(inc_dir)
    create_c_headers( inc_dir, basetypes, structs )
    create_c_impls( inc_dir, basetypes, structs )

if __name__ == "__main__":
    # TODO: parse tools
    if len( sys.argv ) != 4:
        print USAGE
        sys.exit(1)
    json_basetypes = sys.argv[1]
    json_file = sys.argv[2]
    out_dir = sys.argv[3]
    A = AutoGenerator( json_basetypes, json_file, out_dir  )
    basetypes = A.basetypes
    structs   = A.structs
    generate_c( 'c', 'c', basetypes, structs )
