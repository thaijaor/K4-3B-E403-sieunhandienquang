"""Explicit UI fixture preview: no real AI, no production Persona logic."""
import tempfile
from pathlib import Path
from server import create_app
from tests.fixtures import FakeServices


def create_preview():
    folder = Path(tempfile.mkdtemp(prefix="tutor-ui-fixture-"))
    return create_app(folder / "preview.sqlite", FakeServices())
