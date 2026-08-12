import unittest

from app import create_app
from visualizer import run_user_code


class VisualizerEngineTests(unittest.TestCase):
    def test_generates_trace_events(self):
        result = run_user_code("x = 1\nx = x + 2\nprint(x)")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["events"])
        self.assertEqual(result["stdout"], "3\n")

    def test_blocks_disallowed_import(self):
        result = run_user_code("import os\nprint('hi')")
        self.assertEqual(result["status"], "security_error")
        self.assertIn("not allowed", result["error"])


class ApiTests(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_trace_endpoint(self):
        response = self.client.post("/api/trace", json={"code": "x=1\nprint(x)"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("events", payload)

    def test_trace_endpoint_requires_code(self):
        response = self.client.post("/api/trace", json={"code": ""})
        self.assertEqual(response.status_code, 400)

    def test_root_serves_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Python Visualizer MVP", response.data)
        response.close()

    def test_unknown_path_falls_back_to_index(self):
        response = self.client.get("/learn/python")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Python Visualizer MVP", response.data)
        response.close()


class FrontendSmokeTests(unittest.TestCase):
    def test_index_contains_required_panels(self):
        with open("static/index.html", "r", encoding="utf-8") as handle:
            html = handle.read()
        self.assertIn("id=\"codeInput\"", html)
        self.assertIn("id=\"timeline\"", html)
        self.assertIn("id=\"variablesView\"", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
