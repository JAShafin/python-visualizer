import unittest

from app import create_app
from visualizer import run_user_code


class VisualizerTests(unittest.TestCase):
	def test_run_user_code_mocks_input(self):
		result = run_user_code("name = input()\nprint(name.upper())", "alice\n")

		self.assertEqual(result["status"], "ok")
		self.assertEqual(result["stdout"], "ALICE\n")
		self.assertTrue(any(event["event"] == "line" for event in result["events"]))

	def test_run_user_code_returns_empty_string_for_blank_input(self):
		result = run_user_code("value = input()\nprint(value)", "")

		self.assertEqual(result["status"], "ok")
		self.assertEqual(result["stdout"], "\n")

	def test_trace_api_accepts_program_input(self):
		app = create_app()
		client = app.test_client()

		response = client.post(
			"/api/trace",
			json={"code": "print(input())", "stdin": "hello\n"},
		)

		self.assertEqual(response.status_code, 200)
		payload = response.get_json()
		self.assertEqual(payload["status"], "ok")
		self.assertEqual(payload["stdout"], "hello\n")


if __name__ == "__main__":
	unittest.main()

