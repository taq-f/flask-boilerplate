"""Start server for production purpose"""

# -*- coding: utf-8 -*-

import os
from app import app
from gevent.wsgi import WSGIServer
from gevent import monkey

if __name__ == '__main__':
    monkey.patch_all()

    HOST = os.environ.get('HOST', 'localhost')
    PORT = int(os.environ.get('PORT', 5000))
    HTTP_SERVER = WSGIServer((HOST, PORT), app)
    HTTP_SERVER.serve_forever()
