"""Saving of the Mermaid text and rendering of the PNG image."""
import base64
import os
import shutil
import subprocess
import urllib.error
import urllib.request

from .errors import OutputError

RENDERER_MMDC = "mmdc"
RENDERER_ONLINE = "online"
RENDERER_AUTO = "auto"
ONLINE_URL = "https://mermaid.ink/img/{code}?type=png&bgColor=!white"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MMDC_TIMEOUT = 180
ONLINE_TIMEOUT = 60
MESSAGE_LIMIT = 500


def mermaid_path(image_path):
    """Return the path of the Mermaid text that belongs to the image."""
    return os.path.splitext(image_path)[0] + ".mmd"


def save_text(text, path):
    """Write the Mermaid text into the file."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)
    except OSError as error:
        raise OutputError(f"cannot write '{path}': {error}") from error


def render_with_mmdc(text_path, image_path):
    """Run the Mermaid CLI (mmdc) to turn the text file into a PNG."""
    program = shutil.which("mmdc")
    if program is None:
        raise OutputError(
            "mmdc (Mermaid CLI) is not installed: "
            "npm install -g @mermaid-js/mermaid-cli, "
            "or use --renderer online")
    command = [program, "-i", text_path, "-o", image_path, "-b", "white"]
    try:
        done = subprocess.run(
            command, capture_output=True, text=True, timeout=MMDC_TIMEOUT,
            check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise OutputError(f"mmdc failed: {error}") from error
    if done.returncode != 0:
        details = (done.stderr or done.stdout).strip()[-MESSAGE_LIMIT:]
        raise OutputError(f"mmdc failed: {details}")


def fetch_online(text):
    """Return the PNG bytes of the diagram drawn by mermaid.ink."""
    code = base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
    url = ONLINE_URL.format(code=code)
    try:
        with urllib.request.urlopen(url, timeout=ONLINE_TIMEOUT) as answer:
            data = answer.read()
    except (OSError, urllib.error.URLError) as error:
        raise OutputError(f"mermaid.ink is not available: {error}") from error
    if not data.startswith(PNG_SIGNATURE):
        raise OutputError("mermaid.ink did not return a PNG image")
    return data


def render_online(text, image_path):
    """Draw the diagram with the mermaid.ink service."""
    data = fetch_online(text)
    try:
        with open(image_path, "wb") as file:
            file.write(data)
    except OSError as error:
        raise OutputError(f"cannot write '{image_path}': {error}") from error


def choose_renderer(renderer):
    """Resolve ``auto``: mmdc if it is installed, otherwise mermaid.ink."""
    if renderer != RENDERER_AUTO:
        return renderer
    if shutil.which("mmdc"):
        return RENDERER_MMDC
    return RENDERER_ONLINE


def draw(text, image_path, renderer=RENDERER_AUTO):
    """Save the Mermaid text next to the image and render the PNG.

    Returns the path of the text file. The text is saved first, so it
    stays available even if the image cannot be rendered.
    """
    text_path = mermaid_path(image_path)
    save_text(text, text_path)
    if choose_renderer(renderer) == RENDERER_MMDC:
        render_with_mmdc(text_path, image_path)
    else:
        render_online(text, image_path)
    return text_path
