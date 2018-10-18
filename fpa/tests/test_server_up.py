import urllib2
from flask_testing import LiveServerTestCase

class MyTest(LiveServerTestCase):

    def create_app(self):
        from fp_web_admin import app
        app.config['TESTING'] = True

        # Set to 0 to have the OS pick the port.
        app.config['LIVESERVER_PORT'] = 0

        return app

    def setUp(self):
        pass

    def test_server_is_up_and_running(self):
        f = open('tests/data/server_root_response.html')
        expected_response = f.read()
        f.close()

        response = urllib2.urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)
        self.assertEqual(response.read(),expected_response)
