shortis
=======

A small URL shortener built on top of Flask and Redis

Installation
------------

I recommend installation in a python virtualenv.
You will also need a Redis server.

    pip install Flask redis
    git clone git://github.com/kblin/shortis.git

Setup
-----

In the shortis directory, create a shortis.cfg file. In there,
set the secret MAGICCOOKIE variable to stop spammers from using your service.

    MAGICCOOKIE="yourmagiccookiehere"

License
-------

Licensed under the GNU Affero General Public License version 3 or later.
See the LICENSE file for details
