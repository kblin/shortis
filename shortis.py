#!/usr/bin/env python
#set fileencoding: utf-8
from flask import Flask, abort, redirect, render_template, request
from redis import Redis
import string
import random

class ReverseProxied(object):
    '''
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme

        server = environ.get('HTTP_X_FORWARDED_SERVER', '')
        if server:
            environ['HTTP_HOST'] = server

        return self.app(environ, start_response)

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
redis = Redis()

def get_random_string(length=8):
    allowed = string.letters + '_'
    res = ''
    i = 0
    while i < length:
        res += random.choice(allowed)
        i += 1

    return res


def get_hash(url):
    """Get hash for url"""
    keyname = "shortis:url#%s" % url
    return redis.get(keyname)


def set_hash(url):
    """Generate a new hash for a url, or reuse existing hash"""

    value = get_hash(url)
    if value is not None:
        return value

    retries = 5
    rnd = None
    while retries > 0:
        rnd = get_random_string()
        if redis.get('shortis:hash#%s' % rnd) is None:
            break
        retries -= 1

    if rnd is None:
        return None


    if not redis.setnx('shortis:url#%s' % url, rnd):
        return get_hash(url)

    if not redis.setnx('shortis:hash#%s' % rnd, url):
        return None

    return rnd


def lookup_hash(hashed):
    """Look up URL corresponding to a given hash value"""
    return redis.get('shortis:hash#%s' % hashed)


@app.route('/', methods=['GET', 'POST'])
def add():
    error = ''
    url = ''
    try:
        if request.method == 'POST':
            url = request.form.get('url', '').strip()
            if url == '':
                raise Exception('No URL specified.')
            magic = request.form.get('magiccookie', '')
            if magic != app.config['MAGICCOOKIE']:
                raise Exception('Invalid magic, check crystal ball!')
            hashed = set_hash(url)
            if hashed is None:
                raise Exception('Failed to set up hash for %r' % url)
            return render_template('redirect.html', hashed=hashed)
    except Exception as e:
        error = unicode(e)
    return render_template('index.html', error=error, url=url)


@app.route('/<urlhash>')
def get(urlhash):
    url = lookup_hash(urlhash)
    if url is None:
        abort(404)
    return redirect(url, code=301)


if __name__ == "__main__":
    app.config.from_pyfile('shortis.cfg')
    app.run()
