#!/usr/bin/env python

__author__="Brian Hone"

'''
Code Generator

Generates AutoInterface documentation
'''

import json, string, pprint, sys, os
import shutil
from AutoInterface import AutoGenerator
from Templates import py_class_template
import format_utils

T="    "


def create_rst( basetypes, structs, struct_name ):
    heading = "*" * len( struct_name )
    ret = "{0}\n{1}\n{0}\n\n".format(heading,struct_name,heading)

    struct_def = structs[struct_name]

    if struct_def.has_key( 'DESCRIPTION' ):
        ret = ret + struct_def[ 'DESCRIPTION' ] + "\n\n"

    # these are required to calculate the field width 
    #   when making the table
    fields_header = 'Fields'
    fields_length = len(fields_header)
    types_header = 'Types'
    types_length = len(types_header)
    lengths_header = 'Length'
    lengths_length = len(lengths_header)
    bytes_header = 'Bytes'
    bytes_length = len(bytes_header)
    descriptions_header='Description'
    descriptions_length = len(descriptions_header)
    defaults_header='Defaults'
    defaults_length = len(defaults_header)

    fields = []
    types = []
    lengths = []
    bytes_ = []
    descriptions = []
    defaults = []
    

    for f in struct_def['FIELDS']:
        fields.append(f['NAME'])
        fields_length = max(len(fields[-1]),fields_length)
        types.append(f['TYPE'])
        types_length = max(len(types[-1]),types_length)
        if f['LENGTH'] == 1:
            lengths.append('1')
            if f['IS_BASETYPE']:
                bytes_.append(str(basetypes[f['TYPE']]['LENGTH']))
            elif f['IS_STRUCT']:
                child = structs[f['TYPE']]
                if child.has_key('SIZE'):
                    bytes_.append(str(child['SIZE']))
                else:
                    bytes_.append('STRUCTURE')
            else:
                pass
        elif f['IS_BASETYPE'] and type(f['LENGTH']) == int:
            length = f['LENGTH']
            width  = int(basetypes[f['TYPE']]['LENGTH'])
            total  = length * width
            lengths.append(str(length))
            bytes_.append('{0}/{1}'.format(width,total))
        elif f['IS_STRUCT'] and type(f['LENGTH']) == int:
            child = structs[f['TYPE']]
            length = f['LENGTH']
            lengths.append(str(length))
            if child.has_key('SIZE'):
                width  = int(child['SIZE'])
                total  = length * width
                bytes_.append('{0}/{1}'.format(width,total))
            else:
                bytes_.append('STRUCTURE')
                                                    
        else:
            lengths.append('VAR')
            bytes_.append('VAR/VAR')
        lengths_length = max(len(lengths[-1]),lengths_length)
        bytes_length = max(len(bytes_[-1]),bytes_length)
        descriptions.append(str(f['DESCRIPTION']))
        descriptions_length = max(len(descriptions[-1]),descriptions_length)
        if f['IS_BASETYPE'] and f['LENGTH']!='VECTOR':
            if f['LENGTH'] == 1:
                defaults.append(str(f['DEFAULT_VALUE']))
            else:
                defaults.append(format_utils.print_list_summary(f['DEFAULT_VALUE']))
        else:
            defaults.append('')
        defaults_length = max(len(defaults[-1]),defaults_length)
    if struct_def.has_key("SIZE"):
        fields.append( "TOTAL" )
        types.append("")
        lengths.append("")
        bytes_.append(str(struct_def["SIZE"]))
        descriptions.append("")
        defaults.append("")
        fields_length=max(len(fields[-1]),fields_length)
        bytes_length=max(len(fields[-1]),fields_length)    
         

    print fields
    print types
    print lengths
    print descriptions
    print defaults

    magic_row = "="*fields_length + " " + \
                "="*types_length + " " + \
                "="*lengths_length + " " + \
                "="*bytes_length + " " + \
                "="*descriptions_length + " " + \
                "="*defaults_length + "\n"
    print magic_row
    ret = ret + magic_row
    ret = ret + fields_header.ljust(fields_length) + " " + \
                types_header.ljust(types_length) + " " + \
                lengths_header.ljust(lengths_length) + " " + \
                bytes_header.ljust(bytes_length) + " " + \
                descriptions_header.ljust(descriptions_length) + " " + \
                defaults_header + "\n"
    ret = ret + magic_row

    for idx, field in enumerate(fields):
        ret = ret + fields[idx].ljust(fields_length) + " " + \
                    types[idx].ljust(types_length) + " " + \
                    lengths[idx].ljust(lengths_length) + " " + \
                    bytes_[idx].ljust(bytes_length) + " " + \
                    descriptions[idx].ljust(descriptions_length) + " " + \
                    defaults[idx].ljust(defaults_length) + "\n"

    ret = ret + magic_row + "\n\n"

    print ret
        
    return ret
# end generate_rst


def generate_docs( project_name, project_version, project_description, output_file, basetypes, struct_order, structs, overwrite=True ):

    fOut = open( output_file, 'w' )
    generated = '''
###########################
Project: {0}
###########################

Version: {1}
Description: {2}

====================
Generated Structures 
====================

'''.format( project_name, project_version, project_description )
    for struct_name in struct_order: 
        generated = generated + create_rst( basetypes, structs, struct_name )
    fOut.write( generated )
    fOut.close()
# end create_py_files


if __name__ == "__main__":
    import argparse 
    parser = argparse.ArgumentParser( 'AutoInterface Python Generator' )
    parser.add_argument( 'json_basetypes_file' )
    parser.add_argument( 'json_structures_file' )
    parser.add_argument( 'output_file' )
    parser.add_argument( '--pad', default=-1, type=int, help='Insert Padding For Explicit 64-Bit Word Alignment (Warning: Does Not Work With VECTOR Data Type)')
    args = parser.parse_args()

    json_basetypes = args.json_basetypes_file
    json_file = args.json_structures_file
    output_file = args.output_file 
    A = AutoGenerator( json_basetypes, json_file,pad=args.pad )
    basetypes = A.basetypes
    structs   = A.structs
    pname = A.project['PROJECT']
    pdesc = A.project['DESCRIPTION']
    pver  = A.project['VERSION']
    struct_order = A.struct_order

    generate_docs( pname, pdesc, pver, output_file, basetypes, struct_order, structs, overwrite=True )
