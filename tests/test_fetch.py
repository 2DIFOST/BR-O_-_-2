"""Tests of the download of repository files (stage 2)."""
import io
import os
import unittest
import urllib.error
from unittest import mock

from depgraph.errors import PackageNotFoundError, RepositoryError
from depgraph.fetch import fetch_bytes
from helpers import file_url, make_temp_dir, write_file


class FileUrlTest(unittest.TestCase):
    """The file scheme is used for offline repositories."""

    def test_existing_file(self):
        path = write_file(make_temp_dir(self), "a.pom", "<project/>")
        self.assertEqual(fetch_bytes(file_url(path)), b"<project/>")

    def test_missing_file(self):
        path = os.path.join(make_temp_dir(self), "no.pom")
        with self.assertRaises(PackageNotFoundError):
            fetch_bytes(file_url(path))

    def test_directory_is_not_a_pom(self):
        with self.assertRaises(RepositoryError):
            fetch_bytes(file_url(make_temp_dir(self)))


class HttpTest(unittest.TestCase):
    """HTTP failures are converted to repository errors."""

    def fail_with(self, error):
        """Make urlopen raise the error and call fetch_bytes."""
        with mock.patch("urllib.request.urlopen", side_effect=error):
            return fetch_bytes("https://example.org/x.pom")

    def test_not_found(self):
        error = urllib.error.HTTPError(
            "https://example.org/x.pom", 404, "Not Found", {}, io.BytesIO())
        with self.assertRaises(PackageNotFoundError):
            self.fail_with(error)

    def test_server_error(self):
        error = urllib.error.HTTPError(
            "https://example.org/x.pom", 500, "Error", {}, io.BytesIO())
        with self.assertRaisesRegex(RepositoryError, "HTTP 500"):
            self.fail_with(error)

    def test_no_network(self):
        error = urllib.error.URLError("name resolution failed")
        with self.assertRaisesRegex(RepositoryError, "cannot read"):
            self.fail_with(error)

    def test_timeout(self):
        with self.assertRaisesRegex(RepositoryError, "timed out"):
            self.fail_with(TimeoutError("timed out"))


if __name__ == "__main__":
    unittest.main()
