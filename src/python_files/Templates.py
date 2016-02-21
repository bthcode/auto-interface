#!/usr/bin/python

__author__="Brian Hone"

'''
Place to store templates for AutoInteface system
'''

py_class_template = '''
class {0}(object):
    """
    Auto Generated Class {0}
    Methods:
      __init__ : Sets defaults
      read_binary( file_handle )
      write_binary( file_handle )
    """
'''

py_basic_methods = '''
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
        for field in self.__slots__:
            val = getattr(self, field)
            #for key, val in sorted(vars(self).items()):
            ret = ret + "{0}: {1}\\n".format( field, val )
        return ret
     # end __repr__

    def set_defaults(self):
'''

