from bottle import Bottle

from datafly.core import merge, template, init_globals, debug, log_errors

from config import Config, init_db
from views.hooks import before_request

init_db()

### Main Application

app = Bottle()

@app.error(404)
def page404(code):
    return template('404.html')


### Import & configure modules

# /<page>
merge(app, 'views.public:public')

# /blog/<page>
merge(app, 'datafly.views.blog:public',
    config = {
        'feed': {            
            'title': 'Blog',
            'desc': 'Blog about ...',
            'email': 'info@datafly.net',
            'author': 'DataFly'
        },
        # 'addthis_id': '0123456789',
        # 'fb_id': '0123456789'
})

# /product/<page>
merge(app, 'datafly.views.gallery:public')

# /admin
merge(app, 'views.admin:admin')

# /admin/login
merge(app, 'datafly.views.users:users',
    config=dict(
        home = '/admin/home'
))

# /admin/api/pages, /admin/upload
merge(app, 'datafly.views.editor:editor')

# /admin/blog
merge(app, 'datafly.views.blog:admin')

# /admin/gallery
merge(app, 'datafly.views.gallery:admin',
    config=dict(
        size = ['800', '600']
))

# /admin/api/
merge(app, 'datafly.views.api:api')


### Hooks

app.add_hook('before_request', init_globals)
app.add_hook('before_request', before_request)


### Development mode

if __name__ == "__main__":
    merge(app, 'datafly.core:assets')

    @app.error(500)
    def custom500(error):    
        return debug(error)

    app.run(host=Config.HOST, port=Config.PORT, debug=True, reloader=True)


### Production / Staging mode

if Config.__name__ != 'Development': 
    app = log_errors(app)
