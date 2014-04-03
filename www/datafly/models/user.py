from passlib.hash import sha512_crypt
import passlib.utils

from ..core import get_cookie, set_cookie, delete_cookie
from ..models import sequence

class CookieMixin(object):

    @classmethod
    def get_current(cls):
        document_id = get_cookie(cls.__cookie__)
        if document_id:
            document = cls.get_by_id(document_id)
            if document:
                return document
            else:       
                cls.unset_current()

    def set_as_current(self, temporary=False):
        set_cookie(self.__cookie__, str(self['_id']), temporary=temporary)

    @classmethod
    def unset_current(cls):
        delete_cookie(cls.__cookie__)

"""
    Mongo DB
    type - String if not specified

    user:
        id: Integer
        email
        password
        token
"""

class UserMixin(CookieMixin):
    __private__ = ['password']

    @classmethod
    def exists(cls, email):
        return cls.find_one({'email': email})

    @classmethod
    def from_token(cls, token):
        return cls.find_one({'token': token})

    def has_permissions(self, *perms):
        return self.type in perms

    @property
    def type(self):
        return self.__class__.__name__

    def pre_insert(self):
        self['id'] = sequence.nextval(self.__collection__)
        self.generate_token()

    def generate_password(self):
        password = passlib.utils.generate_password(8)
        self.encrypt_password(password)
        return password

    def encrypt_password(self, password=None):
        password = password if password else self['password']
        self['password'] = sha512_crypt.encrypt(password)
        self.save()    

    def verify_password(self, password):
        return sha512_crypt.verify(password, self.get('password', ''))

    def generate_token(self, save=False):
        self['token'] = passlib.utils.generate_password(40)
        if save:
            self.save()