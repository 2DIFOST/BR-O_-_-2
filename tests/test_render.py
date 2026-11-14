"""Tests of the rendering of the PNG image (stage 5)."""
import os
import shutil
import unittest
from unittest import mock

from depgraph import render
from depgraph.errors import OutputError
from helpers import make_temp_dir

PNG = render.PNG_SIGNATURE + b"data"
TEXT = 'flowchart TD\n    n0["A"]\n'


class FakeAnswer:
    """The object returned by urlopen."""

    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        """Return the body of the answer."""
        return self.data


class PathTest(unittest.TestCase):
    """Names of the files."""

    def test_text_file_has_the_name_of_the_image(self):
        self.assertEqual(render.mermaid_path("a/graph.png"), "a/graph.mmd")

    def test_choose_renderer(self):
        with mock.patch("shutil.which", return_value="/bin/mmdc"):
            self.assertEqual(render.choose_renderer("auto"), "mmdc")
        with mock.patch("shutil.which", return_value=None):
            self.assertEqual(render.choose_renderer("auto"), "online")
        self.assertEqual(render.choose_renderer("online"), "online")


class OnlineTest(unittest.TestCase):
    """The mermaid.ink renderer with a fake network."""

    def test_image_and_text_are_saved(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        with mock.patch(
                "urllib.request.urlopen", return_value=FakeAnswer(PNG)) as op:
            text_path = render.draw(TEXT, image, "online")
        with open(image, "rb") as file:
            self.assertEqual(file.read(), PNG)
        with open(text_path, encoding="utf-8") as file:
            self.assertEqual(file.read(), TEXT)
        self.assertIn("https://mermaid.ink/img/", op.call_args[0][0])

    def test_not_a_png_is_an_error(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        with mock.patch(
                "urllib.request.urlopen", return_value=FakeAnswer(b"<html>")):
            with self.assertRaisesRegex(OutputError, "did not return a PNG"):
                render.draw(TEXT, image, "online")

    def test_network_failure_is_an_error(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            with self.assertRaisesRegex(OutputError, "not available"):
                render.draw(TEXT, image, "online")

    def test_text_stays_when_rendering_fails(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        with mock.patch("urllib.request.urlopen", side_effect=OSError("down")):
            with self.assertRaises(OutputError):
                render.draw(TEXT, image, "online")
        self.assertTrue(os.path.isfile(render.mermaid_path(image)))


class MmdcTest(unittest.TestCase):
    """The Mermaid CLI renderer."""

    def test_missing_program_is_an_error(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(OutputError, "not installed"):
                render.draw(TEXT, image, "mmdc")

    def test_failure_of_the_program_is_reported(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        done = mock.Mock(returncode=1, stderr="Parse error", stdout="")
        with mock.patch("shutil.which", return_value="/bin/mmdc"), \
                mock.patch("subprocess.run", return_value=done):
            with self.assertRaisesRegex(OutputError, "Parse error"):
                render.draw(TEXT, image, "mmdc")

    def test_command_line_of_the_program(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        done = mock.Mock(returncode=0, stderr="", stdout="")
        with mock.patch("shutil.which", return_value="/bin/mmdc"), \
                mock.patch("subprocess.run", return_value=done) as run:
            render.draw(TEXT, image, "mmdc")
        command = run.call_args[0][0]
        self.assertEqual(command[0], "/bin/mmdc")
        self.assertEqual(command[command.index("-i") + 1],
                         render.mermaid_path(image))
        self.assertEqual(command[command.index("-o") + 1], image)

    @unittest.skipUnless(shutil.which("mmdc"), "mmdc is not installed")
    def test_real_program_draws_a_png(self):
        image = os.path.join(make_temp_dir(self), "g.png")
        render.draw(TEXT, image, "mmdc")
        with open(image, "rb") as file:
            self.assertTrue(file.read().startswith(render.PNG_SIGNATURE))


if __name__ == "__main__":
    unittest.main()
