# This needs to be the first thing imported in the host program so that we can save the state of the
# import system before it gets modified.
import sys

CLEAN_SYS_MODULES = sys.modules.copy()

from .plugin import Plugin
from .abstract_plugin import AbstractPlugin
