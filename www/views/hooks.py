from bottle import request, redirect

from datafly.core import g

from models import Admin, data


# before_request - all pages
def before_request():    
    c = g.template_context   

    c.update(dict(      
        layout = 'public/layout.html',        
        head = 'layout_head.html',
        scripts = 'layout_scripts.html',
        data = data       
    )) 

    if '/admin' in request.path:
        init_admin()


# before_request - admin pages
def init_admin():
    c = g.template_context
    
    g.admin = c['user'] = Admin.get_current()
    # login required for all admin pages / API requests
    if not g.admin and request.path != '/admin/login':
        return redirect('/admin/login')
    g.page_id = request.path.replace('/admin', '').strip('/')

    """
        By default we use the same template for simple page and admin version
        of that page.
        We change layout (header, content wrapper, footer) using layout var
    """
    c.update(dict(
        admin = True,
        admin_title = 'Starter',
        layout = 'admin/layout.html',
        page_id = g.page_id            
    ))    