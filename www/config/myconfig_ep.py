from config import Default

class Development(Default):
    BASE_URL = 'http://starter.datafly.dev'
    HOST = '127.0.0.1'
    PORT = 8092
    LIVERELOAD = True