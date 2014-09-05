import os
import sys
import inspect
sys.path.append("./plugins/")
sys.path.append("./")
from .base import ChatCmd, ChatThread

def import_libs():
    
    library_list = [] 
    for sfile in os.listdir(os.path.abspath("./plugins/")):       
        module_name, ext = os.path.splitext(sfile) 
        if ext == '.py' and not module_name.startswith("_"): 
            module = __import__(module_name)
            library_list.append(module)
 
    return library_list


lib_list = import_libs()
mod_list = [] 
routines = []

for lib in lib_list:
    mod_list = dir(lib)
    for method in mod_list:
        to_import = __import__(lib.__name__, globals(), locals(), [method], -1)
        cls = getattr(to_import, method)
        if inspect.isclass(cls):
            if issubclass(cls, ChatCmd) and cls not in [ChatCmd, ChatThread]:
                print "Importing " + to_import.__name__ + "." + method
                routines.append(cls)

avail_cmds = {}
for classobj in routines:
    if issubclass(classobj, ChatThread):
        command_list = classobj(None, None).avail_cmds
    else:
        command_list = classobj(None).avail_cmds
    for command in command_list:
        avail_cmds[command] = classobj
