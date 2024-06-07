import pluggy

from . import hookspecs

# from tests.integration_tests import hookspecs as it_hookspecs

pm = pluggy.PluginManager("simple_deploy")
pm.add_hookspecs(hookspecs)
# pm.add_hookspecs(it_hookspecs)
