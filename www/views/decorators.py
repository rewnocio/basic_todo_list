from functools import wraps
from bottle import redirect

from datafly.core import g

def login_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if g.user:
            return f(*args, **kwargs)
        return redirect('/admin/login')
    return decorator