import uuid
import json
from bson.json_util import dumps
from os import path
from PIL import ImageOps, Image
from bottle import Bottle, request

from datafly.core import FileUpload
from datafly.models.page import Page

from config import Config, SITE_ROOT

editor_app = Bottle()

@editor_app.post('/admin/upload/:filetype')
def upload(filetype):
    file = request.files.get('file')
    name, ext = path.splitext(file.filename)
    file = FileUpload(file.file, file.name, file.filename)
    # set unique name
    new_name = '%s%s%s' % (Config.IMG_PREFIX, str(uuid.uuid4())[:8], ext)
    fp = path.join(SITE_ROOT, 'static', 'upload', filetype, new_name)
    file.save(fp, overwrite=True)
    im = Image.open(fp)
    # resize if bigger than maximum size
    max_width = int(request.query.get('width', 1920))
    max_height = int(request.query.get('height', 1200))
    if request.query.get('crop') == 'yes':
        WIDTH, HEIGHT = 0, 1
        resized = ImageOps.fit(
            im,        
            (max_width, max_height),
            Image.ANTIALIAS
        )
        resized.save(fp, format='jpeg')   
    else: 
        size = max_width, max_height
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(fp, 'jpeg')
    link = '/static/upload/%s/%s' % (filetype, new_name)
    return { 'filelink': link }

@editor_app.get('/admin/api/pages/<_id>/version')
def get_page(_id):
    p = Page.get_by_id(_id)
    return json.loads(dumps(p))

@editor_app.post('/admin/api/pages/id/<page_id:path>')
def save_page(page_id):    
    page = Page(request.json['page'])
    page.save()