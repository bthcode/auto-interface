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

def create_struct_table(basetypes,structs,struct_order):
    header = "List of Structures"
    delim  = "=" * len(header)
    ret = "{1}\n{0}\n{1}\n\n".format(delim,header,delim)
    names = []
    descriptions = []
    names_header='Structure'
    descr_header='Description'
    # gather up the information
    for struct_name in struct_order:
        struct_def = structs[struct_name]
        names.append(struct_def['NAME'])
        if 'DESCRIPTION' in struct_def:
            descriptions.append(struct_def['DESCRIPTION'])
        else:
            descriptions.append('') 
    # find the longest of each column
    names_len=len(names_header)
    descr_len=len(descr_header)
    for name in names:
        names_len = max(len(name), names_len)
    for descr in descriptions:
        descr_len = max(len(descr), descr_len)
    # make table
    magic_line = "="*names_len + " " + \
                 "="*descr_len + "\n" 
    ret = ret + magic_line
    ret = ret + names_header.ljust(names_len) + " " + descr_header.ljust(descr_len) + "\n"
    ret = ret + magic_line
    for idx in range(len(names)):
        #print names[idx]
        ret = ret + "{0} {1}\n".format(names[idx].ljust(names_len),descriptions[idx].ljust(descr_len))
    ret = ret + magic_line + "\n\n"
    return ret
# end create_struct_table

def create_rst( basetypes, structs, struct_name ):
    heading = "=" * len( struct_name )
    ret = "{1}\n{0}\n{1}\n\n".format(struct_name,heading)

    struct_def = structs[struct_name]

    if 'DESCRIPTION' in struct_def:
        ret = ret + struct_def[ 'DESCRIPTION' ] + "\n\n"


    # these are required to calculate the field width 
    #   when making the table
    fields_header = 'Field Name'
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
    units_header = 'Units'
    units_length = len(units_header)

    fields = []
    types = []
    lengths = []
    bytes_ = []
    descriptions = []
    defaults = []
    units = []


    for f in struct_def['FIELDS']:
        fields.append(f['NAME'])
        fields_length = max(len(fields[-1]),fields_length)
        #print (f['NAME'])
        doc_name = f['DOC_NAME']
        types.append(doc_name)
        types_length = max(len(types[-1]),types_length)
        if f['LENGTH'] == 1:
            lengths.append('1')
            if f['IS_BASETYPE']:
                bytes_.append(str(basetypes[f['TYPE']]['LENGTH']))
            elif f['IS_STRUCT']:
                child = structs[f['TYPE']]
                if 'SIZE' in child:
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
            if 'SIZE' in child:
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
    #if struct_def.has_key("SIZE"):
    #    fields.append( "TOTAL" )
    #    types.append("")
    #    lengths.append("")
    #    bytes_.append(str(struct_def["SIZE"]))
    #    descriptions.append("")
    #    defaults.append("")
    #    fields_length=max(len(fields[-1]),fields_length)
    #    bytes_length=max(len(fields[-1]),fields_length)    
        # no units as of yet
        units.append('')
         
    '''
    magic_row = "="*fields_length + " " + \
                "="*types_length + " " + \
                "="*lengths_length + " " + \
                "="*bytes_length + " " + \
                "="*descriptions_length + " " + \
                "="*defaults_length + "\n"
    '''

    magic_row = "="*fields_length + " " + \
                "="*types_length + " " + \
                "="*units_length + " " + \
                "="*lengths_length + " " + \
                "="*descriptions_length + \
                "\n"
    #print (magic_row)
    ret = ret + magic_row
    ret = ret + fields_header.ljust(fields_length) + " " + \
                types_header.ljust(types_length) + " " + \
                units_header.ljust(units_length) + " " + \
                lengths_header.ljust(lengths_length) + " " + \
                descriptions_header.ljust(descriptions_length) + \
                "\n"
    ret = ret + magic_row

    for idx, field in enumerate(fields):
        ret = ret + fields[idx].ljust(fields_length) + " " + \
                    types[idx].ljust(types_length) + " " + \
                    units[idx].ljust(units_length) + " " + \
                    lengths[idx].ljust(lengths_length) + " " + \
                    descriptions[idx].ljust(descriptions_length) + \
                    "\n"

    ret = ret + magic_row + "\n\n"

    ret = ret + "Size = {0}\n\n".format(struct_def['SIZE'])

    #print (ret)
        
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

####################
Generated Structures 
####################

'''.format( project_name, project_version, project_description )
    # Generate a table showing all messages
    generated = generated + create_struct_table(basetypes,structs,struct_order)
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
