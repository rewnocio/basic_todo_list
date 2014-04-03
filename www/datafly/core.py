# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import inspect
import functools
import json
from datetime import timedelta
from bottle import (Bottle, load, request, response, template,
                    static_file, Jinja2Template, html_escape)
import pymongo
from bson.json_util import dumps

from config import Config, assets
from datafly.utils.jinja2_ext import filters, _globals

try:
    from utils.jinja2_ext import extended_filters, extended_globals
except ImportError:
    extended_filters = extended_globals = {}

try:
    import chromelogger as console
except:
    console = False


### DEFAULT BEFORE_REQUEST

def init_globals():
    g._reset()
    g.template_context = c = dict(
        env = Config.__name__,
        config = Config,
        base_url = Config.BASE_URL,
        request_path = request.path,
        request_query_string = request.query_string              
    )
    if Config.__name__ == 'Development':
        c['assets'] = get_assets()
    sentry = request.query.get('sentry', None)
    if sentry:
        raise Exception('Testing Sentry...')


### INSTALL (MERGE) APPLICATIONS

# merging default_app and sub_app is very similiar
# to Blueprint concept in Flask

def merge(default_app, sub_app, config=None):
    sub_app = load('%s_app' % sub_app)
    if config:
        sub_app.config(config)
    if Config.__name__ == 'Production':
        sub_app.catchall = False
    else:
        sub_app.add_hook('after_request', debug)
    default_app.merge(sub_app)


### ASSETS - DEVELOPMENT MODE

def get_assets():
    """ Return a list of relative paths for LESS, JS files """    
    return dict(
        css = assets.CSS,
        js = assets.JS
    )

assets_app = Bottle()

# production & staging mode - only `/static` folder is served by Nginx
# for development mode all these files are served by Bottle webserver

@assets_app.get('/js/<filename:path>')
@assets_app.get('/css/<filename:path>')
@assets_app.get('/static/<filename:path>')
@assets_app.get('/datafly/<filename:path>')
def static(filename):
    d, filename = os.path.split(request.path)
    return static_file(filename, '.' + d + '/')


### COOKIES

def get_cookie(name):
    return request.get_cookie(name, secret=Config.SECRET)

def set_cookie(name, value, temporary=False, **options):
    if 'max_age' not in options and not temporary:
        options['max_age'] = timedelta(days=30)
    return response.set_cookie(name, value, secret=Config.SECRET, path='/', **options)

def delete_cookie(name):
    return response.delete_cookie(name, secret=Config.SECRET, path='/')


### GLOBAL VARIABLES

class _AppCtxGlobals(object):
    """ Thread-safe global variables for Bottle. Shortcut to request.g """

    def __getattr__(self, name):
        return request.g.get(name, None)

    def __setattr__(self, name, value):
        request.g[name] = value

    def _reset(self):
        request.g = {}

    def _inspect(self):
        g = request.g.copy()
        g.pop('template_context')
        return g

g = _AppCtxGlobals()


### JINJA2 CONFIGURATION

# add project specific filters to default filters
filters.update(extended_filters)
_globals.update(extended_globals)

template_settings = {
    'filters': filters,
    '_globals': _globals
}

template_lookup = [
    './templates',
    './datafly/templates',
    '.'
]

class Jinja2TemplateSafeDefaults(Jinja2Template):
    def prepare(self, filters=None, tests=None, _globals=None, **kwargs):
        """
            patch for env.globals Jinja2 issue
            https://github.com/defnull/bottle/pull/423
        """
        from jinja2 import Environment, FunctionLoader
        if 'prefix' in kwargs: # TODO: to be removed after a while
            raise RuntimeError('The keyword argument `prefix` has been removed. '
                'Use the full jinja2 environment name line_statement_prefix instead.')
        self.env = Environment(loader=FunctionLoader(self.loader), **kwargs)
        if filters: self.env.filters.update(filters)                
        if tests: self.env.tests.update(tests)
        if _globals: self.env.globals.update(_globals)
        if self.source:
            self.tpl = self.env.from_string(self.source)
        else:
            self.tpl = self.env.get_template(self.filename)

    def render(self, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        # Bottle self.defaults are not thread-safe
        # were replaced by g.template_context
        _defaults = g.template_context
        _defaults.update(kwargs)
        log('--- TEMPLATE CONTEXT ---')
        for k, v in _defaults.items():
            try:
                log('%s =' % k, v)
            except (AttributeError, TypeError):                
                if isinstance(v, pymongo.cursor.Cursor):
                    collection = [json.loads(dumps(obj)) for obj in v]
                    log('%s =' % k, { 'collection' : collection })
                    v.rewind()
                else:
                    log('%s =' % k, json.loads(dumps(v)))
        try:
            r = get_route()        
            log('--- ROUTE ---')
            log(str(r))
            log(str(inspect.getmodule(r.callback)))
        except:
            pass
        log('--- TEMPLATE ---')
        log('name =', self.tpl.name)
        return self.tpl.render(**_defaults)
    
template = functools.partial(template,
                             template_adapter=Jinja2TemplateSafeDefaults,
                             template_lookup=template_lookup,
                             template_settings=template_settings)


### DEBUG

def get_route():
    return request.environ.get('bottle.route', None)

def log(*args):    
    if Config.__name__ != 'Development':
        return
    r = get_route()
    if r and '/static' in r.rule:
        return
    # logging only on staging / development env
    if console:
        console.log(*args)

def debug(error=None):
    if hasattr(error, 'traceback'):
        msg = error.traceback
        if not msg:
            # Bottle raised exception
            msg = error.body
    else:
        msg = error
    if console:
        header = console.get_header()
        if header:
            k,v = header
            response.headers[k] = v
    if error:    
        if request.is_xhr and console:
            console.log(msg)
            return { 'error': True }
        else:
            return '<pre>%s</pre>' %  html_escape(msg)

def print_routes(app):
    """ Inspect all the routes (including mounted sub-apps)
        for the root Bottle application
    """
    def inspect_routes(app):
        for route in app.routes:
            if 'mountpoint' in route.config:
                prefix = route.config['mountpoint']['prefix']
                subapp = route.config['mountpoint']['target']

                for prefixes, route in inspect_routes(subapp):
                    yield [prefix] + prefixes, route
            else:
                yield [], route
    for prefixes, route in inspect_routes(app):
        abs_prefix = '/'.join(part for p in prefixes for part in p.split('/'))
        print abs_prefix, route.name, route.rule, route.method, route.callback


### SENTRY

def log_errors(default_app):
    from raven import Client
    from raven.middleware import Sentry
    default_app.catchall = False
    return Sentry(
        default_app,
        Client(Config.SENTRY['Python'])
    )


### FileUpload - taken from Bottle 0.12 dev

import re
from bottle import cached_property, HeaderDict, HeaderProperty

class FileUpload(object):

    def __init__(self, fileobj, name, filename, headers=None):
        ''' Wrapper for file uploads. '''
        #: Open file(-like) object (BytesIO buffer or temporary file)
        self.file = fileobj
        #: Name of the upload form field
        self.name = name
        #: Raw filename as sent by the client (may contain unsafe characters)
        self.raw_filename = filename
        #: A :class:`HeaderDict` with additional headers (e.g. content-type)
        self.headers = HeaderDict(headers) if headers else HeaderDict()

    content_type = HeaderProperty('Content-Type')
    content_length = HeaderProperty('Content-Length', reader=int, default=-1)

    @cached_property
    def filename(self):
        ''' Name of the file on the client file system, but normalized to ensure
            file system compatibility (lowercase, no whitespace, no path
            separators, no unsafe characters, ASCII only). An empty filename
            is returned as 'empty'.
        '''
        from unicodedata import normalize #TODO: Module level import?
        fname = self.raw_filename
        if isinstance(fname, unicode):
            fname = normalize('NFKD', fname).encode('ASCII', 'ignore')
        fname = fname.decode('ASCII', 'ignore')
        fname = os.path.basename(fname.replace('\\', os.path.sep))
        fname = re.sub(r'[^a-zA-Z0-9-_.\s]', '', fname).strip().lower()
        fname = re.sub(r'[-\s]+', '-', fname.strip('.').strip())
        return fname or 'empty'

    def _copy_file(self, fp, chunk_size=2**16):
        read, write, offset = self.file.read, fp.write, self.file.tell()
        while 1:
            buf = read(chunk_size)
            if not buf: break
            write(buf)
        self.file.seek(offset)

    def save(self, destination, overwrite=False, chunk_size=2**16):
        ''' Save file to disk or copy its content to an open file(-like) object.
            If *destination* is a directory, :attr:`filename` is added to the
            path. Existing files are not overwritten by default (IOError).

            :param destination: File path, directory or file(-like) object.
            :param overwrite: If True, replace existing files. (default: False)
            :param chunk_size: Bytes to read at a time. (default: 64kb)
        '''
        if isinstance(destination, basestring): # Except file-likes here
            if os.path.isdir(destination):
                destination = os.path.join(destination, self.filename)
            if not overwrite and os.path.exists(destination):
                raise IOError('File exists.')
            with open(destination, 'wb') as fp:
                self._copy_file(fp, chunk_size)
        else:
            self._copy_file(destination, chunk_size)