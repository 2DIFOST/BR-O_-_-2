"""Helpers shared by the tests."""
import contextlib
import io
import os
import pathlib
import shutil
import tempfile

from depgraph.cli import main

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLES_DIR = os.path.join(PROJECT_DIR, "examples")


def file_url(path):
    """Return the file:// URL of a local path (also on Windows)."""
    return pathlib.Path(path).resolve().as_uri()


def make_temp_dir(test):
    """Create a directory that is removed when the test finishes."""
    path = tempfile.mkdtemp(prefix="depgraph-test-")
    test.addCleanup(shutil.rmtree, path, True)
    return path


def write_file(directory, name, text):
    """Write a UTF-8 file into the directory and return its path."""
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(text)
    return path


def run_cli(argv):
    """Run the tool and return (exit code, stdout text, stderr text)."""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()
