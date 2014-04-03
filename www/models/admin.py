from datafly.models.user import UserMixin
from datafly.odm import Document

class Admin(UserMixin, Document):
    __collection__ = 'admins'
    __cookie__ = 'admin'
