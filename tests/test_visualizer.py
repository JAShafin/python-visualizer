import tempfile
import unittest
from pathlib import Path

from visualizer import visualize_file, visualize_source


class VisualizerTests(unittest.TestCase):
    def test_visualize_source_shows_basic_nodes(self) -> None:
        output = visualize_source("x = 1\n")
        self.assertIn("Module", output)
        self.assertIn("Assign", output)
        self.assertIn("Name", output)
        self.assertIn("Constant", output)

    def test_visualize_file_reads_python_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script = Path(temp_dir) / "sample.py"
            script.write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
            output = visualize_file(script)
        self.assertIn("FunctionDef", output)
        self.assertIn("Return", output)


if __name__ == "__main__":
    unittest.main()
