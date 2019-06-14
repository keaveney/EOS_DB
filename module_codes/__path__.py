#!/usr/bin/env python
# __path__.py

def updatePath():
    ### OLD:
    # import os, sys
    # from os.path import dirname, join, abspath
    # basedir = 'production_database_scripts'
    # subdir  = abspath(dirname(__file__))
    # parts   = subdir.split(os.sep)[1:]
    # depth   = len(parts) - (parts.index(basedir) + 1)
    # sys.path.insert(0, abspath(join(dirname(__file__), *(depth * ['..']))))
    ### NEW:
    import sys
    from os.path import dirname, join, abspath
    depth = 1
    sys.path.insert(0, abspath(join(dirname(__file__), *(depth * ['..']))))
