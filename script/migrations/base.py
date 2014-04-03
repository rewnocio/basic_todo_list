import sys
import os
from os.path import abspath, dirname, join

def app_init():
    # go up two times from /migrations, append /www
    sys.path.append(abspath(join(dirname(__file__), os.pardir, os.pardir, 'www')))

    set_config = sys.argv[1] if len(sys.argv) > 1 else None
    if set_config:
        os.environ['CONFIG'] = set_config.capitalize()