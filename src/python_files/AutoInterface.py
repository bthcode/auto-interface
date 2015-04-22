##################################################################################
#
# Code Generator System
#
##################################################################################

__author__="Brian Hone"

import json, string, pprint, sys, os
import shutil




T="    "

class AutoGenerator:
    """
    Holder class for data associated with auto-interface system.

    members are:
        - basetypes
        - structs

     
    """
    def __init__(self, json_basetypes, json_file):
        self.basetypes = json.load( open( json_basetypes,  'r' ) )
        self.project   = json.load( open( json_file, 'r' ) )

        # We want the structures two ways:
        #  - ordered (by occurrence in the json file )
        #  - key/value pair
        structs   = self.project['STRUCTURES']
        self.structs = {}
        self.struct_order = []
        for struct in structs:
            self.struct_order.append( struct['NAME'] )
            self.structs[ struct['NAME'] ] = struct

        if not self.project.has_key( "PROJECT" ):
            self.project['PROJECT'] = "Untitled"

        if not self.project.has_key( "NAMESPACE" ):
            self.project['NAMESPACE'] = False

        if not self.project.has_key( "VERSION" ):
            self.project['VERSION'] = '0.0.1'

        if not self.project.has_key( "DESCRIPTION" ):
            self.project['DESCRIPTION'] = ''

        self.preprocess()
    # end __init__

    def preprocess(self):

        # go through keys, send them "to upper"

        # go through keys, setting length
        for struct_name, struct_def in self.structs.items():
            # inherit the namespace
            if self.project['NAMESPACE']:
                struct_def['NAMESPACE'] = self.project['NAMESPACE']
            for idx, f in enumerate(struct_def['FIELDS']):
                # move keys to upperclass
                for key,val in f.items():
                    f[key.upper()] = val
                # SET LENGTH 
                if not f.has_key('LENGTH'):
                    f['LENGTH'] = 1
                # Determine if is struct
                if self.structs.has_key(f['TYPE']):
                    f['IS_STRUCT'] = True
                    f['IS_BASETYPE'] = False
                elif self.basetypes.has_key(f['TYPE']):
                    f['IS_STRUCT'] = False
                    f['IS_BASETYPE'] = True
                else:
                    print ("ERROR: Unknown Type: {0}".format(f['TYPE'])) 
                if not f.has_key('DESCRIPTION'):
                    f['DESCRIPTION'] = ''

                if f['IS_BASETYPE'] and f['LENGTH'] == 1:
                    if not f.has_key('DEFAULT_VALUE'):
                        f['DEFAULT_VALUE'] = self.basetypes[f['TYPE']]['DEFAULT_VALUE'] 
                struct_def[idx] = f
                # set missing types
                # handle default values
            if not struct_def.has_key('DESCRIPTION'):
                struct_def['DESCRIPTION'] = ''
            self.structs[struct_name] = struct_def
        # turn dicts into classes

        for base_name, basetype in self.basetypes.items():
            if not basetype.has_key('IS_COMPLEX'):
                basetype['IS_COMPLEX'] = False
            else:
                if basetype['IS_COMPLEX'].upper() == "TRUE":
                    basetype['IS_COMPLEX'] = True
                else:
                    basetype['IS_COMPLEX'] = False
            self.basetypes[base_name]=basetype
    # end preprocess


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser('')
    parser.add_argument( 'basetypes' )
    parser.add_argument( 'json_file' )
    args = parser.parse_args()
    A = AutoGenerator(args.basetypes, args.json_file) 
    import pprint
    print pprint.pformat(A.basetypes)
    print pprint.pformat(A.structs)
    print pprint.pformat(A.struct_order)
