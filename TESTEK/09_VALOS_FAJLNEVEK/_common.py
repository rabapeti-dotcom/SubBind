"""
Közös segédmodul – valós fájlnév regressziós tesztek (09_VALOS_FAJLNEVEK).

A tesztek ideiglenes könyvtárban dolgoznak, valódi felhasználói fájlok nélkül.
"""
from pathlib import Path
import hashlib
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from renamer_engine import parse_item, render_template  # noqa: E402

VIDEO = b"VALOS_FAJLNEV_VIDEO_0.6.1"
SUB = b"VALOS_FAJLNEV_SUB_0.6.1"

SERIES_TEMPLATE = "{CIM}.{SZEZON}{EPIZOD}"
FILM_TEMPLATE = "{CIM}"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


def parse(path):
    return parse_item(Path(path))


def render_series(item, title=None):
    title = title if title is not None else item.title
    return render_template(SERIES_TEMPLATE, item, title)


def render_film(item, title=None):
    title = title if title is not None else item.title
    return render_template(FILM_TEMPLATE, item, title)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_valos_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def path_for(self, filename, data=VIDEO):
        return make_case(self.tmp, (filename, data)) / filename

    def assert_renders(self, filename, expected, *, template="series", title=None):
        item = parse(self.path_for(filename))
        render = render_series if template == "series" else render_film
        actual = render(item, title)
        self.assertEqual(
            actual,
            expected,
            f"\nBemenet: {filename}\nElvárt:  {expected}\nKapott:  {actual}",
        )
        return actual
