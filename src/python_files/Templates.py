#!/usr/bin/python

__author__="Brian Hone"

'''
Place to store templates for AutoInteface system
'''

py_class_template = '''
class {0}:
    """
    Auto Generated Class {0}
    Methods:
      __init__ : Sets defaults
      read_binary( file_handle )
      write_binary( file_handle )
    """
    def __init__(self):
        self.set_defaults() 
    # end __init__

    
    def read_props(self):
        pass
    # end write_props

    def validate(self):
        pass
    # end validate

    def __repr__(self):
        ret = ''
        for key, val in sorted(vars(self).items()):
            ret = ret + "{{0}}: {{1}}\\n".format( key, val )
        return ret
    # end __repr__

    def set_defaults(self):
'''

