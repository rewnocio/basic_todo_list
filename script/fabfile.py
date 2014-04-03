from os.path import abspath, join, dirname

from fabric.api import env

env.PROJECT_ROOT = abspath(join(dirname(__file__), '..'))

from datafly.fabric.core import *

collect_static()
