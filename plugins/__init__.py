import os
import sys
import inspect
from base import ChatCmd

def import_libs():
    
    library_list = [] 
    for sfile in os.listdir(os.path.abspath("./plugins/")):       
        module_name, ext = os.path.splitext(sfile) 
        if ext == '.py' and not module_name.startswith("_"): 
            module = __import__(module_name)
            library_list.append(module)
 
    return library_list


sys.path.append("./plugins/")
lib_list = import_libs()
mod_list = [] 
routines = []

for lib in lib_list:
    mod_list = dir(lib)
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
