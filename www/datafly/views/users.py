from bottle import Bottle, request, redirect

from datafly.core import g

# needs refactoring
from models import Admin

users_app = Bottle()

@users_app.post('/admin/login')
def login():    
    user = Admin.find_one({
        'email': request.forms.email
    })
    password = request.forms.get('password', None)
    if password is None:
        # forgot password        
        if user:
            result = { 'success': 'EmailSent' }
        else:
            result = { 'error': 'EmailError' }    
    elif user and user.verify_password(password):
        # checkbox "Remember Me"
        temporary_login = 'remember' not in request.forms
        user.set_as_current(temporary=temporary_login)
        result = {
            'error': False,
            'redirect': users_app.config['home']
        }
    else:
        result = { 'error': 'LoginError' }
    return result

@users_app.post('/admin/logout')
def logout():
    g.admin.unset_current()
    return redirect('/admin/login')
