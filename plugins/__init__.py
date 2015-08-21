#!/usr/bin/env python
import os, sys
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)


def load_plugins():
    """
    Load plugins dynamically.
    """
    imported = []
    path = os.path.dirname(os.path.abspath(__file__))
    for py in [f[:-3] for f in os.listdir(path) if f.endswith('.py') and f != '__init__.py']:
        mod = __import__('.'.join([__name__, py]), fromlist=[py])
        classes = [getattr(mod, x) for x in dir(mod) if isinstance(getattr(mod, x), type)]
        for cls in classes:
            setattr(sys.modules[__name__], cls.__name__, cls)
            globals()[cls.__name__]=cls
            imported.append(cls)
    return imported


#load_plugins()