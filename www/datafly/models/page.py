from datetime import datetime
from bottle import cached_property

from datafly.odm import Document
from datafly.utils.editor import slugify

from config import db

class Page(Document):
    __collection__ = 'pages'

    @staticmethod
    def get_latest(id):
        return Page.find_one({
            'id': id,
            'current': True
        })

    @cached_property
    def versions(self):        
        return db.pages.find(
            { 'id': self['id'] },
            { 'published': 1 }
        ).sort('_id', -1)

    def pre_save(self):        
        self['published'] = datetime.utcnow()                
        self.set_as_current()
        if self.is_new():
            self.set_title()
        self.set_created()

    def is_new(self):
        return ('created' not in self['meta'])

    def set_created(self):
        created = self['meta'].get('created', None)                
        if isinstance(created, datetime): return
        if created:                            
            self['meta']['created'] = \
                datetime.strptime(self['meta']['created'], '%Y-%m-%d %H:%M:%S')
        else:
            self['meta']['created'] = datetime.utcnow()

    def set_title(self):
        """ Create id from Meta Title if `new` is found in current
            URL, 'admin/blog/new' for example.
        """
        path = self['id'].split('/')
        for key, s in enumerate(path):
            if s == 'new':
                path[key] = s.replace('new', slugify(self['meta']['title']))        
        self['id'] = '/'.join(path)

    def set_as_current(self):
        # first, we must unset current from all previous versions
        db.pages.update({ 'id': self['id'] },
                    { '$unset': { 'current': True } },
                    multi=True)
        self['current'] = True