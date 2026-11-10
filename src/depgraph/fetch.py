"""Download of repository files by URL (http, https and file)."""
import errno
import urllib.error
import urllib.request

from .errors import PackageNotFoundError, RepositoryError

TIMEOUT_SECONDS = 15
NOT_FOUND_CODES = (404, 410)
USER_AGENT = "depgraph/1.0"


def is_missing_file(reason):
    """Return True if a URL error reason means that a file is absent."""
    return isinstance(reason, OSError) and reason.errno == errno.ENOENT


def fetch_bytes(url, timeout=TIMEOUT_SECONDS):
    """Download the resource and return its content as bytes.

    Raises PackageNotFoundError if the resource does not exist and
    RepositoryError for any other failure.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code in NOT_FOUND_CODES:
            raise PackageNotFoundError(f"not found: {url}") from error
        raise RepositoryError(f"HTTP {error.code} for {url}") from error
    except urllib.error.URLError as error:
        if is_missing_file(error.reason):
            raise PackageNotFoundError(f"not found: {url}") from error
        raise RepositoryError(f"cannot read {url}: {error.reason}") from error
    except (OSError, ValueError) as error:
        raise RepositoryError(f"cannot read {url}: {error}") from error
