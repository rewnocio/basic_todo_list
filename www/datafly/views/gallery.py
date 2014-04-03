from bottle import Bottle, request

from datafly.core import template
from datafly.utils.editor import slugify

from config import db

# PUBLIC

public_app = Bottle()

@public_app.get('/gallery/<id>')
def view_gallery(id):    
    gallery = db.galleries.find_one({ 'id': id })
    return template('gallery.html', gallery=gallery)

# ADMIN

admin_app = Bottle()

@admin_app.get('/admin/gallery/<id>')
def manage_gallery(id):
    template_context = dict(
        gallery = db.galleries.find_one({ 'id': id }),
        id=id,
        size=admin_app.config['size']
    )
    return template('admin/gallery.html', **template_context)    

@admin_app.post('/admin/api/gallery')
def save_gallery():
    data = request.json['data']
    data['id'] = slugify(data['title']) if data['id'] == 'new' else data['id']
    db.galleries.update({ 'id': data['id'] }, data, upsert=True)
    return { 'id': data['id'] }   