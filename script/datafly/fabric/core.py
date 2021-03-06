import os, sys, yaml
from os import path
from time import strftime, gmtime

# fabric api - local
from fabric.api import lcd, local, get

# fabric api - server
from fabric.api import cd, run, put

# fabric api - misc
from fabric.api import env, task, hide
from fabric.colors import red
from fabric.contrib import files
from fabric.contrib.project import rsync_project


### INIT
# env.PROJECT_ROOT - set in script/fabfile.py

if hasattr(env, 'PROJECT_ROOT'):    
    # PROJECT_ROOT - /
    PROJECT_ROOT = env.PROJECT_ROOT

    # SITE_ROOT - /www
    SITE_ROOT = path.abspath(path.join(env.PROJECT_ROOT, 'www'))    
    sys.path.append(SITE_ROOT)

    # STATIC_ROOT - /www/static
    STATIC_ROOT = path.join(SITE_ROOT, 'static')    

    # import config for each env as CONFIG (dict)
    try:
        from config import config, assets
    except ImportError:
        import config
    CONFIG = {
        'default': config.Default,
        'production': getattr(config, 'Production', None),
        'staging': getattr(config, 'Staging', None)
    }

    # import devops configuration as DEVOPS (dict)
    stream = file(path.join(PROJECT_ROOT, 'script', 'devops.yaml'), 'r')
    DEVOPS = yaml.load(stream)
    env.hosts = DEVOPS['hosts']


### LOCAL

@task
def checkout(branch):    
    """ Checkout git branch and delete all *.pyc. Fab checkout:master / checkout:staging """
    local('git checkout %s' % branch)
    local("find . -name '*.pyc' -delete")

@task
def venv(debug=False):
    """ Install virtualenv or update packages from requirements.txt """
    print PROJECT_ROOT
    with lcd(PROJECT_ROOT):
        if not path.exists(path.join(PROJECT_ROOT, 'venv')):
            local('virtualenv venv')
        local('venv/bin/pip install -r server/requirements.txt')
        if debug == 'debug':       
            # Install development tools for local virtualenv
            local('venv/bin/pip install pudb bpython chromelogger')

@task
def devtools():
    """ You won't need this on server, excluded from requirements.txt """
    with lcd(PROJECT_ROOT):
        local('venv/bin/pip install pudb bpython chromelogger')

@task
def ansible(playbook): 
    """ Ansible shortcut """
    if playbook == 'accelerate':
        playbook = 'datafly/ansible/accelerate'
    local('ansible-playbook %s.yaml -i hosts' % playbook)

@task
def runserver():
    """ Run development server: install venv, import db
        and download /static/upload if needed. """
    sync = getattr(CONFIG['default'], 'SYNC', False)
    if sync:
        version = sync.lower()
        query = 'mongo %s --eval "db.stats().collections"' % CONFIG[version].DB
        collections = int(local(query, capture=True).split()[-1])
        if collections == 0:
            get_db(version)
    venv()
    with lcd(SITE_ROOT):
        local('../venv/bin/python app.py')

@task
def collect_static():
    """ Collect multiple static files (LESS, JS) into one. Compile LESS. """        
    # Needs refactoring
    # LESS
    for result in assets.CSS:
        output_css = path.join(STATIC_ROOT, 'compiled', '%s.min.css' % result)
        output_css = open(output_css, 'w')
        for file in assets.CSS[result]:
            if 'less' in file:
                file = 'static/compiled/%s.css' % path.basename(path.normpath(file))
            else:
                file = file + '.css'
            css = path.join(SITE_ROOT, file)
            file = open(css, 'r')
            output_css.write(file.read())
        output_css.close()
    # JS
    for result in assets.JS:
        output_js = path.join(STATIC_ROOT, 'compiled', '%s.min.js' % result)
        output_js = open(output_js, 'w')
        for file in assets.JS[result]:
            if 'coffee' in file:
                file = 'static/compiled/%s.js' % path.basename(path.normpath(file))
            else:
                file = file + '.js'
            js = path.join(SITE_ROOT, file)
            file = open(js, 'r')
            output_js.write(file.read())
        output_js.close()


### TRANSFER

def new_server(version):
    nginx = 'site.nginx' if version == 'production' else 'site_staging.nginx'
    if not path.exists(path.join(PROJECT_ROOT, 'server', nginx)):
        ansible('local')
    ansible('accelerate')
    ansible('server')
    remote_venv(version)
    put_db(version)

@task
def auth_keys():
    """ Upload ssh keys to new server """
    auth_keys = file(path.join(PROJECT_ROOT, 'server', 'authorized_keys'), 'r')
    run('mkdir -p /root/.ssh')
    files.append('/root/.ssh/authorized_keys', auth_keys)

@task
def deploy(version=None, delete=False):
    """ Upload changes to remote. Fab deploy:production / deploy:staging. """
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    run('mkdir -p %s/www' % REMOTE_PATH)
    delete = True if version == 'staging' or delete else False
    print(red('BEGIN RSYNC'))
    print(red('==========='))
    rsync_project(REMOTE_PATH + '/', SITE_ROOT,
                  delete=delete, exclude=["*.pyc", "upload"])    
    print(red('=========='))
    print(red('END RSYNC'))
    chmod(version)
    # if upstart script exists - restart
    if files.exists('/etc/init/uwsgi.conf'):
        run('service uwsgi restart')    
    if not files.exists(path.join(REMOTE_PATH, 'venv')):
        new_server(version)

@task
def ds():
    """ shortcut for deploy:staging """
    collect_static()
    deploy('staging')

@task
def dp():
    """ shortcut for deploy:production """
    collect_static()
    deploy('production')

def backup_db(version):
    db = CONFIG[version].DB
    run('rm -rf /tmp/%s' % db)
    run('mongodump --db %s --out /tmp' % db)
    id = db + '_' + strftime("%d%b%Y%H%M", gmtime())
    filename = '%s.tar.gz' % id
    with cd('/tmp'):
        run('tar -zcf %s %s' % (filename, db))        
    backup_dir = path.join(PROJECT_ROOT, 'backup')
    local('mkdir -p %s' % backup_dir)
    get('/tmp/%s' % filename, backup_dir)
    if os.name == 'posix':        
        with lcd(backup_dir):            
            local('rm -rf %s' % db)
            local('tar xvf %s' % filename)

def get_upload(version):
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    remote_upload = path.join(REMOTE_PATH, 'www', 'static', 'upload')
    local_upload = path.join(STATIC_ROOT)
    rsync_project(remote_upload, local_upload + '/', upload=False)

@task
def get_db(version):
    """ Import database and `static/upload` files. Fab get_db:production / get_db:staging """
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    get_upload(version)
    run('mkdir -p %s/backup' % REMOTE_PATH)
    db = CONFIG[version].DB  
    backup_db(version)
    restore_from = path.abspath(path.join(PROJECT_ROOT, 'backup', db))
    local('mongorestore --drop --db %s %s' % (db, restore_from))

def put_upload(version):
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    remote_upload = path.join(REMOTE_PATH, 'www', 'static')
    local_upload = path.join(STATIC_ROOT, 'upload')
    rsync_project(remote_upload + '/', local_upload)
    chmod(version)

@task
def put_db(version):
    """ Upload database and `static/upload` files. Fab put_db:production / put_db:staging """
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    put_upload(version)
    run('mkdir -p %s/backup' % REMOTE_PATH)
    db = CONFIG[version].DB
    local('rm -rf /tmp/%s' % db)
    local('mongodump --db %s --out /tmp' % db)
    id = db + '_' + strftime("%d%b%Y%H%M", gmtime())
    filename = '%s.tar.gz' % id
    with lcd('/tmp'):
        local('tar -zcf %s %s' % (filename, db))
    put('/tmp/%s' % filename, '/tmp/%s' % filename)
    # a copy (backup) of remote database before drop
    # if db name - 'starter', copy - 'starter_tmp'
    run('''mongo --eval "db.copyDatabase('%s','%s_tmp')"''' % (db, db))
    run('rm -rf /tmp/%s' % db)    
    with cd('/tmp'):
        run('tar -xvf %s' % filename)
        run('mongorestore --drop --db %s %s' % (db, db))


### REMOTE

def chmod(version=None):
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)    
    with hide('output','running'):
        run('chown -R www-data:www-data %s/www' % REMOTE_PATH)
        run('mkdir -p %s/www/static/upload/img' % REMOTE_PATH)    
        run('chmod -R 775 %s/www/static/upload/img' % REMOTE_PATH)
        run('mkdir -p %s/www/static/upload/file' % REMOTE_PATH)
        run('chmod -R 775 %s/www/static/upload/file' % REMOTE_PATH)

@task
def remote_venv(version):
    """ REMOTE: install virtualenv or update packages from requirements.txt """
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    # upload requirements.txt
    run('mkdir -p %s/server' % REMOTE_PATH)
    requirements = '%s/server/requirements.txt'
    put(requirements % PROJECT_ROOT, requirements % REMOTE_PATH)
    # create venv if not exists
    if not files.exists('%s/venv' % REMOTE_PATH):
        run('virtualenv %s/venv' % REMOTE_PATH)
    # install or update venv packages
    with cd(REMOTE_PATH):
        run('venv/bin/pip install -r server/requirements.txt')
        run("find . -name '*.pyc' -delete")
    # restart
    run('service uwsgi restart')

@task
def migration(version, file=None):
    """ Run database migration (from JS or Python script) """
    REMOTE_PATH = path.join(DEVOPS['remote_path'], version)
    MIGRATIONS = path.join(PROJECT_ROOT, 'script', 'migrations')
    rsync_project('%s/script/' % REMOTE_PATH, MIGRATIONS, exclude=["*.pyc"])
    if file:
        with cd(REMOTE_PATH):
            run('venv/bin/python script/migrations/%s %s' % (file, version))
