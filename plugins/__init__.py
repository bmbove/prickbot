import importlib
import inspect
from base import ChatCmd

import os, sys

def import_libs():
    """ Imports the libs, returns a list of the libraries. 
    Pass in dir to scan """
    
    library_list = [] 
    for f in os.listdir(os.path.abspath("./plugins/")):       
        module_name, ext = os.path.splitext(f) 
        if ext == '.py' and not module_name.startswith("_"): 
            module = __import__(module_name)
            library_list.append(module)
 
    return library_list

def filter_builtins(module):

    # Default builtin list    
    built_in_list = [
        '__builtins__',
        '__doc__',
        '__file__',
        '__name__',
        '__package__'
    ]
    
    # get the list of methods/functions from the module
    module_methods = dir(module) 

    for b in built_in_list:
        if b in module_methods:
            module_methods.remove(b)

    return module_methods


sys.path.append("./plugins/")
lib_list = import_libs()
mod_list = [] 
routines = []

for lib in lib_list:
    mod_list = filter_builtins(lib)
    for method in mod_list:
        to_import = __import__(lib.__name__, globals(), locals(), [method], -1)
        if inspect.isclass(getattr(to_import, method)):
            if issubclass(getattr(to_import, method), ChatCmd):
                print "Importing " + to_import.__name__ + "." + method
                routines.append(getattr(to_import, method))

avail_cmds = {}
for classobj in routines:
    command_list = classobj(None).avail_cmds
    for command in command_list:
        avail_cmds[command] = classobj
