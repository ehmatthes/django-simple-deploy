import pluggy

from . import hookspecs

pm = pluggy.PluginManager("simple_deploy")
pm.add_hookspecs(hookspecs)