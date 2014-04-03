import os
from os.path import abspath, join, dirname

CONFIG_ROOT = abspath(dirname(__file__))
# SITE ROOT - /www
SITE_ROOT = abspath(join(CONFIG_ROOT, '..'))
# one level above site
PROJECT_ROOT = abspath(join(SITE_ROOT, '..'))

class Default(object):
    """ Uncomment SYNC to download db and `static/upload` only once
        with "fab runserver" command from specified remote version """
    # SYNC = 'Staging'
    CACHE_TIMESTAMP = 'Sep14-0225' 
    WEBSITE = 'DataFly'    
    MONGO = {
        'host': 'localhost',
        'port': 27017        
    }
    ADMIN_USER = {
        'login': 'demo@datafly.net',
        'password': 'demo'
    }   
    DB = 'starter'
    IMG_PREFIX = ''
    SECRET = 'EJdDcCRXHTyW8UXcQnRhWyujGWnK7Bjf4ZD68ve9Heu9tvCwacPc9zYjwJrb'
    SENTRY = {
        'Python': 'http://5bed9d39ccc34c24999e328032e16557:d70098e241204a9591a0e1a5bab4f8a7@sentry.datafly.net/5',
        'JS': 'http://5bed9d39ccc34c24999e328032e16557@sentry.datafly.net/5'
    }  

class Production(Default):
    BASE_URL = 'http://starter.datafly.net'

class Staging(Default):
    BASE_URL = 'http://staging.starter.datafly.net'

class Development(Default):
    BASE_URL = 'http://127.0.0.1:8080'
    HOST = '127.0.0.1'
    PORT = 8080    

"""
    please, define class Development(Default) in myconfig.py
    with your local settings    

    myconfig.py file is not versioned by Git, however
    add a copy of yours as myconfig_name.py to Git
    (or better add a symlink `ln -s myconfig.py myconfig_name.py`)
"""

# environ variable is defined in uwsgi.ini uWSGI configuration file
config_name = os.environ.get('CONFIG', False)
if config_name:
    # Config = Production or Config = Staging
    Config = vars()[config_name]
else:        
    try:  
        import myconfig
        Config = myconfig.Development
    except ImportError:
        Config = Development