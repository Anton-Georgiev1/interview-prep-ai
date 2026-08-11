import unittest
import urllib.request
import json

class TestPythonApp(unittest.TestCase):
    def test_server_homepage(self):
        try:
            response = urllib.request.urlopen('http://localhost:3000')
            self.assertEqual(response.status, 200)
            content = response.read().decode('utf-8')
            self.assertIn('Interview Prep AI', content)
        except Exception as e:
            self.fail(f"Server home page request failed: {e}")

    def test_saved_sessions_api(self):
        try:
            response = urllib.request.urlopen('http://localhost:3000/api/saved-sessions')
            self.assertEqual(response.status, 200)
            sessions = json.loads(response.read().decode('utf-8'))
            self.IsInstance = isinstance(sessions, list)
            self.assertTrue(self.IsInstance)
        except Exception as e:
            self.fail(f"Saved sessions API request failed: {e}")

if __name__ == '__main__':
    unittest.main()
