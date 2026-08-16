from pathlib import Path
import os
import sys
import subprocess
import datetime
import traceback
import shutil

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QTextEdit, QLabel, QMessageBox, QProgressBar, QCheckBox,
    QFileDialog, QLineEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class TestRunnerDialog(QDialog):
    """Teljes 0.6.x Tesztlabor.

    A tesztlista kétféleképpen tölthető:
    - a projekt TESTEK mappájából automatikusan;
    - kézzel hozzáadott .py tesztscriptekkel.

    A futtatás elkülönített TESZT_KORNYEZET alatt történik.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tesztlabor – 0.6.1-TEST")
        self.resize(900, 700)

        self.project_root = Path(__file__).resolve().parents[2]
        self.tests_dir = self.project_root / "TESTEK"
        self.test_root = self.project_root / "Tesztadat_Generator" / "TESZT_KORNYEZET"
        self.last_report_path = None

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        title = QLabel("Automata tesztek")
        title.setStyleSheet("font-weight: bold;")
        root.addWidget(title)

        # Tesztscript-kezelő sor – ezt a korábbi Tesztlaborból megtartjuk.
        list_buttons = QHBoxLayout()

        add = QPushButton("+ Script(ek) hozzáadása")
        add.clicked.connect(self.add_scripts)
        list_buttons.addWidget(add)

        remove = QPushButton("Kijelölt törlése")
        remove.clicked.connect(self.remove_selected)
        list_buttons.addWidget(remove)

        clear = QPushButton("Lista ürítése")
        clear.clicked.connect(self.clear_list)
        list_buttons.addWidget(clear)

        list_buttons.addStretch(1)
        root.addLayout(list_buttons)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list.setAlternatingRowColors(True)
        root.addWidget(self.list, 1)

        # Tesztkörnyezet sor.
        env_row = QHBoxLayout()
        self.cleanup = QCheckBox("Teszt után takarítás")
        self.cleanup.setToolTip(
            "Csak a rögzített TESZT_KORNYEZET tartalmát törli."
        )
        env_row.addWidget(self.cleanup)

        env_row.addWidget(QLabel("Tesztkörnyezet:"))

        self.env_edit = QLineEdit(str(self.test_root))
        self.env_edit.setReadOnly(True)
        env_row.addWidget(self.env_edit, 1)

        root.addLayout(env_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        root.addWidget(self.output, 2)

        action_row = QHBoxLayout()

        self.run = QPushButton("▶ TESZT FUTTATÁSA")
        self.run.setStyleSheet(
            "QPushButton { font-weight:bold; padding:7px 12px; }"
        )
        self.run.clicked.connect(self.run_tests)
        action_row.addWidget(self.run)

        self.stop = QPushButton("■ Teszt megszakítása")
        self.stop.setEnabled(False)
        self.stop.clicked.connect(self.stop_tests)
        action_row.addWidget(self.stop)

        error_btn = QPushButton("Hiba kimenet")
        error_btn.clicked.connect(self.show_error_output)
        action_row.addWidget(error_btn)

        report_btn = QPushButton("Tesztjelentés")
        report_btn.clicked.connect(self.show_report)
        action_row.addWidget(report_btn)

        action_row.addStretch(1)

        close = QPushButton("Bezárás")
        close.clicked.connect(self.close)
        action_row.addWidget(close)

        root.addLayout(action_row)

        self._processes = []
        self._stop_requested = False
        self._last_stderr = ""

        self.scan()

    # ---------- lista ----------

    def scan(self):
        """A TESTEK mappa aktuális scriptjeit betölti, duplikáció nélkül."""
        self.list.clear()
        files = sorted(
            self.tests_dir.glob("*.py"),
            key=lambda p: p.name.lower()
        )
        for p in files:
            if not p.name.startswith("_"):
                self.list.addItem(str(p))

        self.output.setPlainText(
            f"Tesztkönyvtár: {self.tests_dir}\n"
            f"Talált tesztek: {len(files)}\n"
            "A futtatás a TESZT_KORNYEZET alatt dolgozik."
        )

    def add_scripts(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Teszt scriptek kiválasztása",
            str(self.tests_dir),
            "Python tesztek (*.py);;Minden fájl (*.*)",
        )
        if not files:
            return

        existing = {
            str(Path(self.list.item(i).text()).resolve())
            for i in range(self.list.count())
        }
        added = 0

        for raw in files:
            p = Path(raw).resolve()
            if p.suffix.lower() != ".py":
                continue
            if str(p) in existing:
                continue
            self.list.addItem(str(p))
            existing.add(str(p))
            added += 1

        self.output.append(f"\nHozzáadva: {added} tesztscript.")

    def remove_selected(self):
        rows = sorted(
            {idx.row() for idx in self.list.selectedIndexes()},
            reverse=True
        )
        for row in rows:
            self.list.takeItem(row)

    def clear_list(self):
        self.list.clear()
        self.output.setPlainText("Tesztlista kiürítve.")

    # ---------- futtatás ----------

    def run_tests(self):
        files = [
            Path(self.list.item(i).text())
            for i in range(self.list.count())
        ]
        if not files:
            QMessageBox.information(
                self, "Tesztlabor",
                "Nincs teszt a listában."
            )
            return

        self.test_root.mkdir(parents=True, exist_ok=True)

        if self.cleanup.isChecked():
            self._clean_test_root()

        env = os.environ.copy()
        env["SERIES_RENAMER_TEST_ROOT"] = str(self.test_root)
        env["PYTHONPATH"] = (
            str(self.project_root / "src")
            + os.pathsep
            + env.get("PYTHONPATH", "")
        )

        blocks = [
            "Sorozat & film átnevező — Tesztjelentés",
            "Tesztverzió: 0.6.1-TEST",
            f"Indítás: {datetime.datetime.now().isoformat(timespec='seconds')}",
            ""
        ]

        failures = 0
        self._stop_requested = False
        self._last_stderr = ""
        self.run.setEnabled(False)
        self.stop.setEnabled(True)
        self.progress.setValue(0)

        try:
            for idx, script in enumerate(files, 1):
                if self._stop_requested:
                    blocks.append("TESZTFUTTATÁS MEGSZAKÍTVA")
                    failures += 1
                    break

                self.output.append(f"\nFUT: {script.name}")

                try:
                    cp = subprocess.run(
                        [sys.executable, str(script)],
                        cwd=str(self.project_root),
                        env=env,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=300,
                    )
                    out = cp.stdout or ""
                    err = cp.stderr or ""
                except Exception:
                    cp = None
                    out = ""
                    err = traceback.format_exc()
                    failures += 1

                self._last_stderr = err

                blocks += [
                    f"=== SCRIPT {idx}: {script} ===",
                    f"Exit code: {cp.returncode if cp else 1}",
                    "--- STDOUT ---",
                    out,
                    "--- STDERR ---",
                    err,
                    ""
                ]

                if cp is not None and cp.returncode != 0:
                    failures += 1

                self.progress.setValue(int(idx * 100 / len(files)))
                if out:
                    self.output.append(out)
                if err:
                    self.output.append(err)

        finally:
            self.run.setEnabled(True)
            self.stop.setEnabled(False)

        status = "Hibák" if failures else "Sikeres"
        blocks.insert(2, f"Állapot: {status}")
        report = "\n".join(blocks)

        self.test_root.mkdir(parents=True, exist_ok=True)
        report_path = self.test_root / "TESZT_JELENTES_0.6.1-TEST.txt"
        report_path.write_text(report, encoding="utf-8")
        self.last_report_path = report_path

        if self.cleanup.isChecked():
            # A jelentést megőrizzük; csak a tesztadatok ideiglenes tartalmát takarítjuk.
            self._clean_test_root(keep_report=True)

        self.output.setPlainText(report)

        QMessageBox.information(
            self,
            "Tesztlabor",
            f"Tesztfuttatás kész.\n\n"
            f"Állapot: {status}\n"
            f"Jelentés:\n{report_path}"
        )

    def stop_tests(self):
        self._stop_requested = True
        self.output.append("\nMegszakítás kérve...")

    def _clean_test_root(self, keep_report=False):
        self.test_root.mkdir(parents=True, exist_ok=True)
        report = self.test_root / "TESZT_JELENTES_0.6.1-TEST.txt"

        for child in list(self.test_root.iterdir()):
            if keep_report and child == report:
                continue
            try:
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            except OSError as exc:
                self.output.append(
                    f"Takarítási hiba: {child} — {exc}"
                )

    # ---------- eredmény ----------

    def show_error_output(self):
        text = self._last_stderr.strip()
        if not text:
            text = "Az utolsó tesztfuttatásnak nincs STDERR/Hiba kimenete."
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Hiba kimenet")
        dlg.setIcon(QMessageBox.Icon.Information)
        dlg.setText(text)
        dlg.setDetailedText(text)
        dlg.exec()

    def show_report(self):
        if self.last_report_path and self.last_report_path.exists():
            text = self.last_report_path.read_text(
                encoding="utf-8", errors="replace"
            )
            self.output.setPlainText(text)
            return

        report = self.test_root / "TESZT_JELENTES_0.6.1-TEST.txt"
        if report.exists():
            self.last_report_path = report
            self.output.setPlainText(
                report.read_text(encoding="utf-8", errors="replace")
            )
        else:
            QMessageBox.information(
                self, "Tesztjelentés",
                "Még nem készült tesztjelentés."
            )
