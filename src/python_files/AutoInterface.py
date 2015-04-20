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
        self.structs   = json.load( open( json_file, 'r' ) )
        self.preprocess()
    # end __init__

    def preprocess(self):

        # go through keys, send them "to upper"

        # go through keys, setting length
        for struct_name, struct_def in self.structs.items():
            for idx, f in enumerate(struct_def['FIELDS']):
                # SET LENGTH 
                if not f.has_key('LENGTH'):
                    f['LENGTH'] = 1
                # DETERMINE if is basetype
                if self.basetypes.has_key(f['TYPE']):
                    f['IS_BASETYPE'] = True
                # Determine if is struct
                if self.structs.has_key(f['TYPE']):
                    f['IS_STRUCT'] = True
                    f['IS_BASETYPE'] = False
                elif self.basetypes.has_key(f['TYPE']):
                    f['IS_STRUCT'] = False
                    f['IS_BASETYPE'] = True
                else:
                    print ("ERROR: Unknown Type: {0}".format(f['TYPE'])) 
                struct_def[idx] = f
                # set missing types
                # handle default values
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
