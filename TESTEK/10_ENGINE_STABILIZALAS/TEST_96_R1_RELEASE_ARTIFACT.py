"""
R1/H: frozen portable artifact — data/ az exe mellett, nem APPDATA.
A teszt a projekt dist\\SorozatEsFilmAtnevezo mappáját másolja izolált tempbe.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = PROJECT_ROOT / "dist" / "SorozatEsFilmAtnevezo"
EXE_NAME = "SorozatEsFilmAtnevezo.exe"


class TestR1HPortableArtifact(unittest.TestCase):
    def test_frozen_exe_uses_sidecar_data_not_appdata(self):
        exe_src = DIST_DIR / EXE_NAME
        self.assertTrue(
            exe_src.is_file(),
            f"Nincs release exe: {exe_src}. Először futtasd a build_exe.bat-ot.",
        )
        self.assertTrue((DIST_DIR / "_internal").is_dir())
        self.assertFalse((DIST_DIR / "TESTEK").exists())
        self.assertFalse((DIST_DIR / "src" / "testing").exists())

        iso = Path(tempfile.mkdtemp(prefix="sr_r1h_iso_"))
        fake_appdata = Path(tempfile.mkdtemp(prefix="sr_r1h_appdata_"))
        proc = None
        try:
            dest = iso / "SorozatEsFilmAtnevezo"
            shutil.copytree(DIST_DIR, dest)
            exe = dest / EXE_NAME
            data_dir = dest / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "settings.json").write_text(
                json.dumps(
                    {
                        "template": "{CIM}.{SZEZON}{EPIZOD}",
                        "mode": "Sorozat",
                        "normalize": True,
                        "include_subdirs": True,
                        "check_conflicts": True,
                        "preserve_selection": True,
                        "sort_mode": "Név",
                        "show_welcome": False,
                        "language": "hu",
                        "output_mode": "Helyben átnevezés",
                        "output_dir": "",
                        "appearance": "Világos",
                        "version": "0.6.1",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["QT_QPA_PLATFORM"] = "offscreen"
            env["APPDATA"] = str(fake_appdata)
            env.pop("SERIESRENAMER_DATA", None)

            proc = subprocess.Popen(
                [str(exe)],
                cwd=str(dest),
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(4)
            self.assertIsNone(proc.poll(), "A frozen exe azonnal kilépett.")

            settings_path = data_dir / "settings.json"
            self.assertTrue(settings_path.is_file())
            cfg = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(cfg.get("version"), "0.6.1")
            self.assertNotIn("TEST", str(cfg.get("version")))

            leaked = list(fake_appdata.rglob("settings.json"))
            self.assertEqual(
                leaked,
                [],
                f"A frozen build APPDATA-ba írt: {leaked}",
            )
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            shutil.rmtree(iso, ignore_errors=True)
            shutil.rmtree(fake_appdata, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
