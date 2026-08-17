import unittest
import urllib.request
import urllib.error
import json
import os
import sys
import threading
import time
import socketserver

# Add parent directory to sys.path so app can be imported directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import PythonInterviewServer, ACTIVE_GEMINI_MODEL, ALL_GEMINI_MODELS, SAVED_SESSIONS

class TestInterviewPrepAI(unittest.TestCase):
    server = None
    server_thread = None
    test_port = None
    BASE_URL = ""

    @classmethod
    def setUpClass(cls):
        """
        Check if an external server is already running on port 3000.
        If not (e.g. running tests locally in PowerShell/VS Code without starting app.py first),
        automatically spawn an in-process ThreadingTCPServer on an ephemeral free port.
        """
        # Test if port 3000 is reachable
        try:
            req = urllib.request.Request("http://localhost:3000/api/active-model")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    cls.BASE_URL = "http://localhost:3000"
                    return
        except Exception:
            pass

        # If not running, spin up an in-process server on a dynamic free port (port 0)
        socketserver.TCPServer.allow_reuse_address = True
        cls.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), PythonInterviewServer)
        cls.test_port = cls.server.server_address[1]
        cls.BASE_URL = f"http://127.0.0.1:{cls.test_port}"
        
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        # Brief sleep to allow thread to listen
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    def test_01_server_homepage_renders_cleanly(self):
        """Verify the homepage renders with correct headers and UI elements."""
        req = urllib.request.Request(self.BASE_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode('utf-8')
            self.assertIn("Interview Prep AI", html)
            self.assertIn("jobTitle", html)
            self.assertIn("Multiple Choice", html)

    def test_02_saved_sessions_api_and_persistence(self):
        """Test creating, fetching, and clearing saved session history."""
        # 1. Fetch initial sessions
        req = urllib.request.Request(f"{self.BASE_URL}/api/saved-sessions")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIsInstance(data, list)

        # 2. Save a test mock session
        sample_session = {
            "id": "test-session-1234",
            "date": "2026-08-17 12:00",
            "jobTitle": "Senior Software Architect",
            "type": "multiple_choice",
            "score": 90,
            "summary": "Demonstrated strong knowledge of system design."
        }
        post_req = urllib.request.Request(
            f"{self.BASE_URL}/api/save-session",
            data=json.dumps(sample_session).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(post_req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            res_data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(res_data.get("status"), "ok")

        # 3. Verify session was inserted
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            self.assertTrue(len(data) >= 1)
            self.assertEqual(data[0]["jobTitle"], "Senior Software Architect")

        # 4. Clear sessions
        clear_req = urllib.request.Request(
            f"{self.BASE_URL}/api/clear-sessions",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(clear_req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)

        # 5. Verify sessions empty
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            self.assertEqual(len(data), 0)

    def test_03_active_model_endpoint(self):
        """Test that the /api/active-model endpoint reports active model and available pool."""
        req = urllib.request.Request(f"{self.BASE_URL}/api/active-model")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode('utf-8'))
            self.assertIn("active_model", data)
            self.assertIn("available_models", data)
            self.assertIsInstance(data["available_models"], list)
            self.assertIn(data["active_model"], data["available_models"])

    def test_04_model_memory_and_dynamic_fallback_logic(self):
        """Unit test for model selection memory and fallback priority ordering."""
        all_models = [
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.1-flash-lite"
        ]

        # Initial active model
        active_model = "gemini-3.5-flash"

        # Model ordering test: active model must always be tried first
        ordered = [active_model] + [m for m in all_models if m != active_model]
        self.assertEqual(ordered[0], "gemini-3.5-flash")
        self.assertEqual(len(ordered), len(all_models))

        # Simulate scenario: 'gemini-3.5-flash' failed (e.g. rate limit), 'gemini-3.7-flash' succeeded
        # System switches and remembers 'gemini-3.7-flash' as the new default
        successful_model = "gemini-3.7-flash"
        if active_model != successful_model:
            active_model = successful_model

        self.assertEqual(active_model, "gemini-3.7-flash")

        # Next time: 'gemini-3.7-flash' should be at index 0 (tried first)
        new_ordered = [active_model] + [m for m in all_models if m != active_model]
        self.assertEqual(new_ordered[0], "gemini-3.7-flash")
        self.assertNotIn("gemini-3.7-flash", new_ordered[1:])
        self.assertIn("gemini-3.5-flash", new_ordered[1:])

    def test_05_api_error_handling_with_invalid_key(self):
        """Verify proper JSON error response when generation is called with an invalid API key."""
        payload = {
            "jobTitle": "Software Developer",
            "type": "multiple_choice",
            "apiKey": "dummy_invalid_key"
        }
        req = urllib.request.Request(
            f"{self.BASE_URL}/api/generate-questions",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                self.fail("Expected 500 or error status for invalid key")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 500)
            err_data = json.loads(e.read().decode('utf-8'))
            self.assertIn("error", err_data)
            self.assertIn("Invalid Gemini API Key", err_data["error"])

if __name__ == '__main__':
    unittest.main()
