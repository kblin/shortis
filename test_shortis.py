import shortis
import random
try: import unittest2 as ut
except ImportError: import unittest as ut

class FakeRedis(object):
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key, None)

    def set(self, key, value):
        self.data[key] = value
        return True

    def setnx(self, key, value):
        if key in self.data:
            return False
        return self.set(key, value)

    def __repr__(self):
        return repr(self.data)

class ShortisTestCase(ut.TestCase):
    def setUp(self):
        shortis.redis = FakeRedis()
        random.seed('shortis is cool')
        shortis.app.config['MAGICCOOKIE'] = 'testing'
        self.app = shortis.app.test_client()

    def tearDown(self):
        shortis.redis = None

    def test_get_random_string(self):
        """Test get_random_string() returns a random string"""
        first = shortis.get_random_string()
        self.assertEqual(8, len(first))
        self.assertEqual('HUxnkdfT', first)
        second = shortis.get_random_string()
        self.assertNotEqual(first, second)
        third = shortis.get_random_string(length=2)
        self.assertEqual(2, len(third))

    def test_get_hash(self):
        """Test get_hash()"""
        self.assertIsNone(shortis.get_hash('http://example.org/'))
        shortis.redis.set('shortis:url#http://example.org/', 'SHORTIS')
        self.assertEqual('SHORTIS', shortis.get_hash('http://example.org/'))

    def test_set_hash(self):
        """Test set_hash() returns a hashed URL"""
        url = "http://example.org/"
        hashed = shortis.set_hash(url)
        self.assertEqual('HUxnkdfT', hashed)
        again = shortis.set_hash(url)
        self.assertEqual(hashed, again)
        other = shortis.set_hash(url + "foo")
        self.assertNotEqual(hashed, other)

    def test_lookup_hash(self):
        """Test lookup_hash()"""
        url = shortis.lookup_hash('HUxnkdfT')
        self.assertIsNone(url)
        url = 'http://example.org'
        hashed = shortis.set_hash(url)
        res = shortis.lookup_hash(hashed)
        self.assertIsNotNone(res)
        self.assertEqual(url, res)

    def test_get(self):
        """Test get()"""
        rv = self.app.get('/SHORTIS')
        self.assertEqual(404, rv.status_code)
        shortis.redis.set('shortis:url#http://example.org/', 'SHORTIS')
        shortis.redis.set('shortis:hash#SHORTIS', 'http://example.org/')
        rv = self.app.get('/SHORTIS')
        self.assertEqual(301, rv.status_code)
        self.assertIn('Location', rv.headers)
        self.assertEqual('http://example.org/', rv.headers['Location'])

    def test_add(self):
        """Test add()"""
        rv = self.app.get('/')
        self.assertRegexpMatches(rv.data, "Kai's URL shortener")
        rv = self.app.post('/', data=dict())
        self.assertRegexpMatches(rv.data, "No URL specified")
        rv = self.app.post('/', data=dict(url='http://example.org/'))
        self.assertRegexpMatches(rv.data, "Invalid magic, check crystal ball")
        rv = self.app.post('/', data=dict(url='http://example.org/',
                                          magiccookie='wrong'))
        self.assertRegexpMatches(rv.data, "Invalid magic, check crystal ball")
        rv = self.app.post('/', data=dict(url='http://example.org/',
                                          magiccookie='testing'),
                            base_url="http://s.example.org/")
        self.assertRegexpMatches(rv.data, "Short URL is")
        self.assertRegexpMatches(rv.data, "http://s.example.org/HUxnkdfT")

if __name__ == "__main__":
    ut.main()
