"""
R1/A: portable data_dir — nem APPDATA; SERIESRENAMER_DATA felülírás.
"""
from pathlib import Path
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from main import resolve_data_dir, DATA_DIR_ENV


class TestR1PortableDataDir(unittest.TestCase):
    def setUp(self):
        self.original = os.environ.get(DATA_DIR_ENV)

    def tearDown(self):
        if self.original is None:
            os.environ.pop(DATA_DIR_ENV, None)
        else:
            os.environ[DATA_DIR_ENV] = self.original

    def test_override_env_is_used(self):
        tmp = Path(tempfile.mkdtemp(prefix="sr_r1_"))
        os.environ[DATA_DIR_ENV] = str(tmp)
        self.assertEqual(resolve_data_dir(), tmp)

    def test_dev_default_is_project_data_not_appdata(self):
        os.environ.pop(DATA_DIR_ENV, None)
        resolved = resolve_data_dir()
        self.assertEqual(resolved, PROJECT_ROOT / "data")
        appdata = os.environ.get("APPDATA")
        if appdata:
            self.assertFalse(
                str(resolved).lower().startswith(str(Path(appdata)).lower())
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
