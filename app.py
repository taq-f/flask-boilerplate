"""Flask app boilerplate"""

# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import os
import random
import string
from flask import (Flask, jsonify, make_response, render_template, request,
                   session)


def get_secret_key(app, filename='secret_key'):
    """Get, or generate if not available, secret key for cookie encryption.

    Key will be saved in a file located in the application directory.
    """
    filename = os.path.join(app.root_path, filename)
    try:
        return open(filename, 'r').read()
    except IOError:
        k = ''.join([
            random.choice(string.punctuation + string.ascii_letters +
                          string.digits) for i in range(64)
        ])
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(k)
        return k


def init_logger(app):
    """Initialize logger for application"""
    log_dir = os.path.join(app.root_path, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, True)

    formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s')

    # Access log
    access_log_file = os.path.join(app.root_path, 'logs', 'access.log')
    access_log_file_handler = RotatingFileHandler(
        access_log_file, maxBytes=10000000, backupCount=10)
    access_log_file_handler.setLevel(logging.INFO)
    access_log_file_handler.setFormatter(formatter)
    app.logger.addHandler(access_log_file_handler)

    # Error log
    error_log = os.path.join(app.root_path, 'logs', 'error.log')
    error_log_file_handler = RotatingFileHandler(
        error_log, maxBytes=10000000, backupCount=10)
    error_log_file_handler.setLevel(logging.ERROR)
    error_log_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_log_file_handler)

    app.logger.setLevel(logging.INFO)


def remote_addr():
    """Workaround for retriving client ip address when reverse proxy in the middle"""
    return request.access_route[-1]


# ******************************************************************************
# Decorator
# ******************************************************************************


def skip_session_check(func):
    """Register the given function into skip session list.

    It won't be wrapped.
    """
    if 'IGNORE_SESSION_CHECK' not in app.config:
        app.config['IGNORE_SESSION_CHECK'] = []
    app.config['IGNORE_SESSION_CHECK'].append(func.__name__)
    return func


# ******************************************************************************
# Initialize Application
# ******************************************************************************

app = Flask(__name__)
app.config['IGNORE_SESSION_CHECK'] = ['static']
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = get_secret_key(app)
init_logger(app)

# ******************************************************************************
# Web
# ******************************************************************************

# *************************************
# Before each requst
# *************************************


@app.before_request
def write_access_log():
    """Write access log"""
    app.logger.info('{ip}\t{method}\t{path}\trequest start'.format(
        ip=remote_addr(), method=request.method, path=request.path))
    return


@app.before_request
def check_session():
    """Inspect session.

    Return 401 if session has not establised yet.
    If the endpoint (function) is in skip session list, does nothing.
    """
    if request.endpoint in app.config['IGNORE_SESSION_CHECK']:
        return

    session_check_result = session.get('login_id')

    if session_check_result:
        return

    return make_response('login required', 401)


# *************************************
# After each requst
# *************************************


@app.after_request
def add_no_cache_header(res):
    """Disable caching of any content"""
    # uncomment followings to enable this feature
    # res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    # res.headers["Pragma"] = "no-cache"
    # res.headers["Expires"] = "0"
    # res.headers['Cache-Control'] = 'public, max-age=0'
    return res


@app.after_request
def static_cache(res):
    """Set response headers about caching for static resources

    A year later is set in this example as advised here:
    https://developers.google.com/speed/docs/insights/LeverageBrowserCaching

    It may be better to store the expiration date somewhere else and reuse it
    since this example calculate the date in every request.
    """
    if request.endpoint == 'static':
        expires = datetime.now() + timedelta(days=365)
        res.headers['Expires'] = expires.isoformat()
    return res


@app.after_request
def write_access_result_log(res):
    """Write access log with response status code"""
    app.logger.info(
        '{ip}\t{method}\t{path}\treqeust end\t{status_code}'.format(
            ip=remote_addr(),
            method=request.method,
            path=request.path,
            status_code=res.status_code))
    return res


# *************************************
# Routes
# *************************************


@app.route('/api/return_json_response', methods=['GET'])
def return_json_response():
    """Return json response sample"""
    return jsonify({'this is': 'sample'})


@app.route('/api/return_error_response', methods=['GET'])
def return_error_response():
    """Return error response sample"""
    return make_response(jsonify({}), 403)


@app.route('/', methods=['GET'])
@skip_session_check
def index():
    """Handler for index page"""
    session['login_id'] = 'something'
    # render_template searches templates directory by default
    return render_template('index.html', name='World')


@app.errorhandler(Exception)
def handle_error(error):
    """Error handler when a routed function raises unhandled error"""
    import traceback
    for i, line in enumerate(traceback.format_exc().split('\n')):
        app.logger.error(
            '{line_no}\t{message}'.format(line_no=i + 1, message=line))
    return 'Internal Server Error', 500


if __name__ == '__main__':
    app.run(host='localhost', port=5000)
