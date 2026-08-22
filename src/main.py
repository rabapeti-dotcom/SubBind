import csv
import json
import os
import re
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QDir, QUrl
from PySide6.QtGui import QFont, QAction, QPalette, QColor, QIcon, QPixmap, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QMessageBox, QFileDialog,
    QGroupBox, QGridLayout, QDialog, QDialogButtonBox, QMenu, QFrame,
    QAbstractItemView, QHeaderView, QProgressBar, QListView, QTreeView, QFileSystemModel
)

from version import APP_NAME, APP_VERSION, AUTHOR
from renamer_engine import (
    parse_item, ALL_EXTS, common_title, render_template,
    disambiguate_subtitle_target_names, apply_pair_group_status,
    apply_item_target_names, NamingContext,
    apply_destination_conflicts, apply_completion_status,
    destination_matches_output, copy_to_destination,
    rollback_copied_files, rollback_renamed_files,
    verify_copy_undo, apply_copy_undo,
    verify_inplace_undo, apply_inplace_undo,
)

DATA_DIR_ENV = "SERIESRENAMER_DATA"


def resolve_data_dir():
    """Portable adatmappa: exe/projekt mellett data/, teszthez SERIESRENAMER_DATA.

    Frozen: <exe mappa>/data
    Fejlesztés: <projekt gyökér>/data
    Nem %APPDATA%.
    """
    override = str(os.environ.get(DATA_DIR_ENV, "") or "").strip()
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parent.parent / "data"


RELEASE_ENV = "SERIESRENAMER_RELEASE"


def dev_tools_enabled():
    """Tesztlabor / Patch Center: csak fejlesztői futtatás, nem frozen release."""
    flag = str(os.environ.get(RELEASE_ENV, "") or "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        return False
    if getattr(sys, "frozen", False):
        return False
    return True


def format_size_bytes(n):
    """Emberi méret; a nyers bájt a hívónál marad."""
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        n = 0
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    if n < 1024 ** 3:
        return f"{n / (1024 ** 2):.1f} MB"
    return f"{n / (1024 ** 3):.2f} GB"


def file_identity_key(path):
    """Ugyanaz a fájl: feloldott, Windows-on kis-nagybetű független útvonal."""
    p = Path(path)
    try:
        return os.path.normcase(str(p.resolve()))
    except OSError:
        return os.path.normcase(str(p))



def make_flag_icon(language):
    """Kis, rajzolt zászlóikonok – külső képfájl nélkül."""
    pix = QPixmap(28, 20)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Lekerekített zászlófelület.
    rect = pix.rect().adjusted(1, 1, -1, -1)

    if language == "hu":
        # Magyar trikolór.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ce2939")))
        painter.drawRoundedRect(rect, 3, 3)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRect(1, 8, 26, 6)
        painter.setBrush(QBrush(QColor("#477050")))
        painter.drawRect(1, 14, 26, 5)
    else:
        # Egyszerű, jól felismerhető Union Jack.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#012169")))
        painter.drawRoundedRect(rect, 3, 3)

        # Fehér átlók.
        pen = QPen(QColor("#ffffff"), 4)
        painter.setPen(pen)
        painter.drawLine(2, 3, 26, 17)
        painter.drawLine(26, 3, 2, 17)

        # Piros átlók.
        pen = QPen(QColor("#c8102e"), 2)
        painter.setPen(pen)
        painter.drawLine(3, 3, 25, 17)
        painter.drawLine(25, 3, 3, 17)

        # Fehér kereszt.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawRect(1, 7, 26, 6)
        painter.drawRect(11, 1, 6, 18)

        # Piros kereszt.
        painter.setBrush(QBrush(QColor("#c8102e")))
        painter.drawRect(1, 9, 26, 2)
        painter.drawRect(13, 1, 2, 18)

    painter.end()
    return QIcon(pix)


def make_theme_icon(dark=False):
    """Modern, kör alakú világos/sötét ikon."""
    pix = QPixmap(26, 26)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor("#171717") if dark else QColor("#f4f4f4")
    painter.setPen(QPen(QColor("#777777"), 1))
    painter.setBrush(QBrush(color))
    painter.drawEllipse(3, 3, 20, 20)
    painter.end()
    return QIcon(pix)


class WelcomeDialog(QDialog):
    def __init__(self, parent=None, language="hu", show_again=True):
        super().__init__(parent)
        self.setWindowTitle("Üdvözöl a Sorozat & film átnevező")
        self.setFixedSize(760, 570)
        self.setModal(True)
        self.selected_language = language

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 18)

        title = QLabel("Eleged van abból, hogy a felirat nem működik?")
        title.setStyleSheet("font-size: 16pt; font-weight: 700;")
        root.addWidget(title)

        intro = QLabel(
            "Biztos jártál már úgy, hogy egy filmet vagy sorozatot pendrive-ról "
            "vagy külső merevlemezről szerettél volna megnézni a tévén, de a "
            "felirat nem jelent meg.\n\n"
            "A feliratfájl ott van a videó mellett, mégsem találja meg a tévé, "
            "mert a két fájl neve nem egyezik.\n\n"
            "Egy egész sorozatnál pedig elég kellemetlen lehet ezeket egyenként "
            "átnevezni.\n\n"
            "Ezt a programot éppen erre készítettük: néhány kattintással "
            "felismeri a videókat és a hozzájuk tartozó feliratokat, megmutatja "
            "a tervezett új neveket, majd csak a jóváhagyásod után nevezi át a fájlokat."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        example = QGroupBox("Példa")
        ex_layout = QVBoxLayout(example)
        for label, value in [
            ("Eredeti:", "film.cime.s01e01.web-dl.aac2.0.h.264-tdi.mkv"),
            ("", "FILM.CIME.S01E01.The.Eyes.ATV.WEB-DL.hu.srt"),
            ("Új név:", "film.cime.S01E01.mkv"),
            ("", "film.cime.S01E01.srt"),
        ]:
            if label:
                l = QLabel(label)
                l.setStyleSheet("font-weight: 700;")
                ex_layout.addWidget(l)
            v = QLabel(value)
            v.setFont(QFont("Consolas", 9))
            ex_layout.addWidget(v)
        root.addWidget(example)

        note = QLabel(
            "A program alapfunkcióihoz nincs szükség internetkapcsolatra. "
            "A program a kiválasztott fájlokkal és mappákkal dolgozik."
        )
        note.setWordWrap(True)
        root.addWidget(note)

        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Nyelv:"))
        self.hu_btn = QPushButton()
        self.en_btn = QPushButton()
        self.hu_btn.setIcon(make_flag_icon("hu"))
        self.en_btn.setIcon(make_flag_icon("en"))
        self.hu_btn.setIconSize(QSize(28, 20))
        self.en_btn.setIconSize(QSize(28, 20))
        self.hu_btn.setToolTip("Magyar")
        self.en_btn.setToolTip("English")
        for btn in (self.hu_btn, self.en_btn):
            btn.setCheckable(True)
            btn.setFixedSize(42, 32)
            lang_row.addWidget(btn)
        lang_row.addStretch(1)
        self.hu_btn.clicked.connect(lambda: self.select_language("hu"))
        self.en_btn.clicked.connect(lambda: self.select_language("en"))
        root.addLayout(lang_row)
        self.select_language(language)

        root.addStretch(1)

        bottom = QHBoxLayout()
        self.dont_show = QCheckBox(
            "Ne jelenjen meg ez az ablak a következő indításkor"
        )
        bottom.addWidget(self.dont_show)
        bottom.addStretch(1)

        first = QPushButton("Első lépések")
        first.clicked.connect(self.open_help)
        bottom.addWidget(first)

        ok = QPushButton("Rendben, kezdjük")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        bottom.addWidget(ok)

        root.addLayout(bottom)

    def select_language(self, language):
        self.selected_language = language
        self.hu_btn.setChecked(language == "hu")
        self.en_btn.setChecked(language == "en")
        style = (
            "QPushButton { background: transparent; border: 1px solid transparent; "
            "border-radius: 6px; padding: 1px; }"
            "QPushButton:hover { background: rgba(128,128,128,35); }"
            "QPushButton:checked { border: 2px solid #666666; "
            "background: rgba(128,128,128,45); }"
        )
        self.hu_btn.setStyleSheet(style)
        self.en_btn.setStyleSheet(style)

    def open_help(self):
        self.done(2)


class PatchCenterDialog(QDialog):
    """Tesztfázisú helyi Patch Center.

    A jelenlegi tesztverzió kizárólag a program melletti 'patches' mappában
    található Python patchokat kínálja fel. A patch külön Python folyamatban
    fut, így a GUI folyamatát nem blokkolja végig és a patch saját hibakódja
    visszajelezhető.

    A későbbi nyilvános kiadásban ugyanennek a felületnek a backendje lecserélhető
    online frissítőre anélkül, hogy a fő UI-t újra kellene tervezni.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patch Center – tesztfázis")
        self.resize(760, 520)
        self.setModal(True)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.patch_dir = self.base_dir / "patches"
        self.patch_dir.mkdir(parents=True, exist_ok=True)

        root = QVBoxLayout(self)

        title = QLabel("Patch Center")
        title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        root.addWidget(title)

        info = QLabel(
            "Tesztfázisban a program csak a helyi „patches” mappából futtat patchokat. "
            "A patch külön folyamatban indul, és siker esetén a program újraindítható. "
            "Nyilvános verzióban ez a felület később online Upgrade központra cserélhető."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Patch mappa:"))
        self.path_edit = QLineEdit(str(self.patch_dir))
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit, 1)
        open_folder = QPushButton("Mappa megnyitása")
        open_folder.clicked.connect(self.open_patch_folder)
        path_row.addWidget(open_folder)
        root.addLayout(path_row)

        self.list = QTableWidget(0, 3)
        self.list.setHorizontalHeaderLabels(["Patch", "Méret", "Állapot"])
        self.list.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.list.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.list.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.list.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.list.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        root.addWidget(self.list, 1)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setPlaceholderText("Patch napló...")
        self.log.setMinimumHeight(130)
        root.addWidget(self.log)

        buttons = QHBoxLayout()
        refresh = QPushButton("Patchok keresése")
        refresh.clicked.connect(self.scan_patches)
        buttons.addWidget(refresh)

        self.run_btn = QPushButton("Kijelölt patch futtatása")
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet(
            "QPushButton { background: #6a1b9a; color: white; "
            "font-weight: bold; padding: 7px 12px; }"
            "QPushButton:hover { background: #4a126d; }"
            "QPushButton:disabled { background: #bdbdbd; color: #666; }"
        )
        self.run_btn.clicked.connect(self.run_selected_patch)
        buttons.addWidget(self.run_btn)

        close = QPushButton("Bezárás")
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.list.itemSelectionChanged.connect(self.update_buttons)
        self.scan_patches()

    def _patch_files(self):
        if not self.patch_dir.exists():
            return []
        return sorted(
            [
                p for p in self.patch_dir.iterdir()
                if p.is_file()
                and p.suffix.lower() == ".py"
                and not p.name.startswith("_")
            ],
            key=lambda p: p.name.lower()
        )

    def scan_patches(self):
        self.list.setRowCount(0)
        files = self._patch_files()

        if not files:
            self.log.setPlainText(
                "Nincs helyi patch.\n\n"
                f"Helyezd a saját .py patchokat ide:\n{self.patch_dir}"
            )
            self.update_buttons()
            return

        for path in files:
            row = self.list.rowCount()
            self.list.insertRow(row)

            name = QTableWidgetItem(path.name)
            size = QTableWidgetItem(f"{path.stat().st_size / 1024:.1f} KB")
            status = QTableWidgetItem("Elérhető")

            self.list.setItem(row, 0, name)
            self.list.setItem(row, 1, size)
            self.list.setItem(row, 2, status)

        self.log.setPlainText(
            f"{len(files)} helyi patch található.\n"
            "A program csak a kiválasztott patchot futtatja."
        )
        self.update_buttons()

    def update_buttons(self):
        self.run_btn.setEnabled(bool(self.list.currentRow() >= 0))

    def open_patch_folder(self):
        folder = self.patch_dir
        folder.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(folder)
        else:
            os.system(f'xdg-open "{folder}"')

    def _selected_patch(self):
        row = self.list.currentRow()
        if row < 0:
            return None
        item = self.list.item(row, 0)
        if not item:
            return None
        path = self.patch_dir / item.text()
        return path if path.is_file() else None

    def run_selected_patch(self):
        patch_path = self._selected_patch()
        if not patch_path:
            QMessageBox.warning(self, "Patch", "Nincs kijelölt patch.")
            return

        answer = QMessageBox.question(
            self,
            "Patch futtatása",
            f"Futtassam ezt a helyi patchot?\n\n"
            f"{patch_path.name}\n\n"
            "A patch módosíthatja a program fájljait. "
            "A futtatás előtt a patchnek saját biztonsági mentést kell készítenie.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.run_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            completed = subprocess.run(
                [sys.executable, str(patch_path)],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            self.log.setPlainText(
                f"A patch időtúllépés miatt leállt:\n{patch_path.name}"
            )
            self.run_btn.setEnabled(True)
            return
        except OSError as exc:
            self.log.setPlainText(f"Nem sikerült elindítani a patchot:\n{exc}")
            self.run_btn.setEnabled(True)
            return

        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
        self.log.setPlainText(output.strip() or "A patch nem adott szöveges kimenetet.")

        if completed.returncode != 0:
            QMessageBox.critical(
                self,
                "Patch hiba",
                f"A patch sikertelenül futott le.\n\n"
                f"Visszatérési kód: {completed.returncode}\n\n"
                f"{output[-3000:]}"
            )
            self.scan_patches()
            return

        self.scan_patches()

        answer = QMessageBox.question(
            self,
            "Patch sikeres",
            "A patch sikeresen lefutott.\n\n"
            "Újraindítsam most a programot?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if answer == QMessageBox.StandardButton.Yes:
            self._restart_application()

    def _restart_application(self):
        executable = sys.executable
        args = sys.argv[:]

        try:
            subprocess.Popen(
                [executable] + args,
                cwd=str(self.base_dir),
                close_fds=True
            )
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Újraindítás",
                f"A programot nem sikerült újraindítani:\n{exc}"
            )
            return

        QApplication.instance().quit()



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1250, 800)
        self.setMinimumSize(1050, 680)

        self.items = []
        self.history = []
        self.history_selected_keys = set()
        self.cancel_requested = False
        self.data_dir = resolve_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Tesztfázisú helyi patch könyvtár (csak DEV; release buildben nincs Patch UI).
        self.patch_dir = Path(__file__).resolve().parent.parent / "patches"
        if dev_tools_enabled():
            self.patch_dir.mkdir(parents=True, exist_ok=True)

        self.template_value = "{CIM}.{SZEZON}{EPIZOD}"
        self.title_value = ""
        self.title_manual = False
        self.mode_value = "Sorozat"
        self.normalize_value = True
        self.lang_norm_value = True
        self.include_subdirs_value = True
        self.check_conflicts_value = True
        self.preserve_selection_value = True
        self._syncing_table = False
        self._last_folder = str(Path.home())
        self.sort_mode_value = "Évad → epizód"
        self.language = "hu"
        self.show_welcome = True
        self.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.output_dir = ""
        self.appearance = "Világos"

        self._load_ui_preferences()
        self.title_value = ""
        self.title_manual = False

        intended_template = self.template_value

        self.build_ui()
        self.setAcceptDrops(True)
        self.load_history()
        self.on_mode_changed()
        if hasattr(self, "template_edit"):
            self.template_edit.setText(intended_template)
        self.refresh()

        QTimer.singleShot(150, self.first_run_welcome)

    def center_window(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        available = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(available.center())
        self.move(frame.topLeft())

    def _load_ui_preferences(self):
        path = self.data_dir / "settings.json"
        if not path.exists():
            return
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.language = config.get("language", "hu")
        self.show_welcome = config.get("show_welcome", True)
        self.output_mode = config.get(
            "output_mode",
            "Másolás kimeneti mappába és átnevezés"
        )
        self.output_dir = config.get("output_dir", "")
        self.appearance = config.get("appearance", "Világos")

        modes = {"Automatikus / Vegyes", "Sorozat", "Film"}
        sorts = {"Név", "Évad → epizód", "Fájltípus", "Módosítás dátuma"}
        saved_mode = config.get("mode")
        if saved_mode in modes:
            self.mode_value = saved_mode
        saved_template = str(config.get("template") or "").strip()
        if saved_template:
            self.template_value = saved_template
        if "normalize" in config:
            self.normalize_value = bool(config.get("normalize"))
        if "include_subdirs" in config:
            self.include_subdirs_value = bool(config.get("include_subdirs"))
        if "check_conflicts" in config:
            self.check_conflicts_value = bool(config.get("check_conflicts"))
        saved_sort = config.get("sort_mode")
        if saved_sort in sorts:
            self.sort_mode_value = saved_sort
        # title_var, lang_norm, preserve_selection szándékosan nem töltődik.

        # Új verzióra frissítéskor a bemutatóablak egyszer ismét jelenjen meg.
        # Ha a felhasználó ezt már ebben a verzióban letiltja, az állapot mentésre kerül.
        stored_version = str(config.get("version", "0.0.0"))
        if stored_version != APP_VERSION:
            self.show_welcome = True

    # ---------- UI ----------

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 4)

        top = QHBoxLayout()
        top.setSpacing(4)

        self.add_btn = QPushButton("＋ Hozzáadás")
        self.add_btn.setMinimumHeight(34)
        self.add_btn.setStyleSheet(
            "QPushButton { background: #1976d2; color: white; "
            "font-weight: bold; padding: 6px 12px; border: 1px solid #125ca3; }"
            "QPushButton:hover { background: #1565c0; }"
        )
        add_menu = QMenu(self)
        action = add_menu.addAction("Fájlok hozzáadása")
        action.triggered.connect(self.add_files)
        action = add_menu.addAction("Mappák hozzáadása")
        action.triggered.connect(self.add_folders)
        action = add_menu.addAction("Egy mappa hozzáadása")
        action.triggered.connect(self.add_folder)
        self.add_btn.setMenu(add_menu)
        top.addWidget(self.add_btn)

        for text, callback in [
            ("Lista ürítése", self.clear_list),
            ("Ellenőrzés", self.check),
            ("Előnézet frissítése", lambda: self.refresh(reanalyze=True)),
        ]:
            b = QPushButton(text)
            b.clicked.connect(callback)
            top.addWidget(b)

        if dev_tools_enabled():
            # 0.6.0-TEST: ideiglenes Tesztlabor — csak DEV / teszt futtatás.
            self.test_lab_btn = QPushButton("Tesztlabor")
            self.test_lab_btn.setStyleSheet(
                "QPushButton { background:#6a1b9a; color:white; "
                "font-weight:bold; padding:6px 12px; border:1px solid #4a126d; }"
                "QPushButton:hover { background:#4a126d; }"
            )
            self.test_lab_btn.setToolTip("Ideiglenes automata tesztlabor — 0.6.0-TEST")
            self.test_lab_btn.clicked.connect(self.open_test_lab)
            top.addWidget(self.test_lab_btn)

            # 0.6.1-TEST: helyi Patch Center — csak DEV / teszt futtatás.
            self.patch_btn = QPushButton("Patch")
            self.patch_btn.setStyleSheet(
                "QPushButton { background:#455a64; color:white; "
                "font-weight:bold; padding:6px 12px; border:1px solid #263238; }"
                "QPushButton:hover { background:#37474f; }"
            )
            self.patch_btn.setToolTip(
                "Tesztfázis: helyi patchok futtatása. "
                "Később online Upgrade központ használhatja ugyanezt a gombot."
            )
            self.patch_btn.clicked.connect(self.open_patch_center)
            top.addWidget(self.patch_btn)

        self.help_btn = QPushButton("Súgó ▾")
        help_menu = QMenu(self)

        a = help_menu.addAction("Súgó és használati útmutató")
        a.triggered.connect(self.show_help)
        a = help_menu.addAction("Első lépések")
        a.triggered.connect(self.show_first_steps)
        a = help_menu.addAction("Sablonváltozók")
        a.triggered.connect(self.show_template_help)

        help_menu.addSeparator()

        a = help_menu.addAction("Frissítések keresése")
        a.triggered.connect(self.check_updates)
        a = help_menu.addAction("Hibajelentés")
        a.triggered.connect(self.report_bug)
        a = help_menu.addAction("Adományozás / Donate")
        a.triggered.connect(self.donate)

        help_menu.addSeparator()

        a = help_menu.addAction("Névjegy")
        a.triggered.connect(self.show_about)

        self.help_btn.setMenu(help_menu)
        top.addWidget(self.help_btn)

        action_frame = QFrame()
        action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        action_frame.setStyleSheet(
            "QFrame { background: #e8f5e9; border: 1px solid #bdbdbd; }"
        )
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(2, 2, 2, 2)

        self.rename_btn = QPushButton("Átnevezés")
        self.rename_btn.setMinimumSize(150, 46)
        self.rename_btn.setStyleSheet(
            "QPushButton { background: #2e7d32; color: white; "
            "font-size: 11pt; font-weight: bold; padding: 8px 18px; }"
            "QPushButton:hover { background: #256628; }"
        )
        self.rename_btn.clicked.connect(self.rename)
        action_layout.addWidget(self.rename_btn)
        top.addWidget(action_frame)

        # Jobb felső sarok: csak ikonok, a feliratok tooltipként jelennek meg.
        top.addStretch(1)

        self.light_btn = QPushButton()
        self.dark_btn = QPushButton()
        self.light_btn.setIcon(make_theme_icon(False))
        self.dark_btn.setIcon(make_theme_icon(True))
        self.light_btn.setIconSize(QSize(26, 26))
        self.dark_btn.setIconSize(QSize(26, 26))
        self.light_btn.setToolTip("Világos mód")
        self.dark_btn.setToolTip("Sötét mód")
        for btn in (self.light_btn, self.dark_btn):
            btn.setCheckable(True)
            btn.setFixedSize(34, 30)
            top.addWidget(btn)
        self.light_btn.clicked.connect(lambda: self.set_appearance("Világos"))
        self.dark_btn.clicked.connect(lambda: self.set_appearance("Sötét"))
        self.update_appearance_buttons()

        top.addSpacing(8)

        self.hu_main_btn = QPushButton()
        self.en_main_btn = QPushButton()
        self.hu_main_btn.setIcon(make_flag_icon("hu"))
        self.en_main_btn.setIcon(make_flag_icon("en"))
        self.hu_main_btn.setIconSize(QSize(28, 20))
        self.en_main_btn.setIconSize(QSize(28, 20))
        self.hu_main_btn.setToolTip("Magyar")
        self.en_main_btn.setToolTip("English")
        for btn in (self.hu_main_btn, self.en_main_btn):
            btn.setCheckable(True)
            btn.setFixedSize(34, 30)
            top.addWidget(btn)
        self.hu_main_btn.clicked.connect(lambda: self.set_language("hu"))
        self.en_main_btn.clicked.connect(lambda: self.set_language("en"))
        self.update_language_buttons()

        root.addLayout(top)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        self.files_tab = QWidget()
        self.settings_tab = QWidget()
        self.preview_tab = QWidget()
        self.history_tab = QWidget()

        self.tabs.addTab(self.files_tab, "Fájlok")
        self.tabs.addTab(self.settings_tab, "Sablon és beállítások")
        self.tabs.addTab(self.preview_tab, "Előnézet")
        self.tabs.addTab(self.history_tab, "Előzmények")

        self.build_files()
        self.build_settings()
        self.build_preview()
        self.build_history()
        self.set_appearance(self.appearance)

        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f3f3f3; }")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 3, 8, 3)
        footer_layout.addWidget(QLabel(APP_NAME))
        footer_layout.addStretch(1)
        footer_layout.addWidget(QLabel(f"v{APP_VERSION}  •  {AUTHOR}"))
        footer_layout.addSpacing(18)

        bug = QPushButton("Hibajelentés")
        bug.setFlat(True)
        bug.clicked.connect(self.report_bug)
        footer_layout.addWidget(bug)

        donate = QPushButton("Donate")
        donate.setFlat(True)
        donate.clicked.connect(self.donate)
        footer_layout.addWidget(donate)

        root.addWidget(footer)

        status_row = QHBoxLayout()

        self.status_label = QLabel("0 fájl")
        self.status_label.setFrameStyle(
            QFrame.Shape.Panel | QFrame.Shadow.Sunken
        )
        status_row.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(360)
        self.progress_bar.setMinimumHeight(24)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("")
        status_row.addWidget(self.progress_bar)
        self.progress_file_label = QLabel("")
        self.progress_file_label.setMinimumWidth(220)
        self.progress_file_label.setMaximumWidth(420)
        self.progress_file_label.setToolTip("")
        status_row.addWidget(self.progress_file_label)

        self.cancel_btn = QPushButton("⛔  Feladat megszakítása")
        self.cancel_btn.setMinimumHeight(30)
        self.cancel_btn.setStyleSheet(
            "QPushButton { background: #c62828; color: white; border: 1px solid #8e1b1b; "
            "border-radius: 5px; padding: 5px 10px; font-weight: 700; }"
            "QPushButton:hover { background: #a51f1f; }"
            "QPushButton:disabled { background: #ead0d0; color: #8a6a6a; border-color: #c9aaaa; }"
        )
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.request_cancel)
        status_row.addWidget(self.cancel_btn)

        root.addLayout(status_row)

    def build_files(self):
        layout = QVBoxLayout(self.files_tab)

        tools = QHBoxLayout()

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Keresés...")
        self.filter_edit.textChanged.connect(
            lambda *_: self.refresh(reanalyze=False)
        )
        tools.addWidget(self.filter_edit, 1)

        search = QPushButton("Keresés")
        search.clicked.connect(lambda: self.refresh(reanalyze=False))
        tools.addWidget(search)

        tools.addWidget(QLabel("Rendezés:"))

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Név", "Évad → epizód", "Fájltípus", "Módosítás dátuma"
        ])
        self.sort_combo.setCurrentText(self.sort_mode_value)
        self.sort_combo.currentTextChanged.connect(
            lambda *_: self.refresh(reanalyze=False)
        )
        tools.addWidget(self.sort_combo)

        select_all = QPushButton("Minden kiválasztása")
        select_all.clicked.connect(lambda: self.set_all(True))
        tools.addWidget(select_all)

        deselect = QPushButton("Kijelölés törlése")
        deselect.clicked.connect(lambda: self.set_all(False))
        tools.addWidget(deselect)

        remove_selected = QPushButton("Kijelöltek törlése")
        remove_selected.clicked.connect(self.remove_selected)
        remove_selected.setToolTip("Csak a bepipált sorokat távolítja el a listából.")
        tools.addWidget(remove_selected)

        layout.addLayout(tools)

        self.empty_state = QLabel("<b>Nincsenek betöltött fájlok</b><br>Húzz ide videókat és feliratokat, vagy kattints a „Hozzáadás” gombra.")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.empty_state.setFixedHeight(90)
        self.empty_state.setStyleSheet("QLabel { color: #666; padding: 24px; border: 1px dashed #bdbdbd; border-radius: 8px; }")
        layout.addWidget(self.empty_state)

        output_box = QGroupBox("Kimenet")
        output_layout = QGridLayout(output_box)

        output_layout.addWidget(QLabel("Művelet:"), 0, 0)

        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems([
            "Másolás kimeneti mappába és átnevezés",
            "Helyben átnevezés"
        ])
        if self.output_mode in [
            "Másolás kimeneti mappába és átnevezés",
            "Helyben átnevezés"
        ]:
            self.output_mode_combo.setCurrentText(self.output_mode)
        self.output_mode_combo.currentTextChanged.connect(self.on_output_mode_changed)
        output_layout.addWidget(self.output_mode_combo, 0, 1, 1, 2)

        output_layout.addWidget(QLabel("Kimeneti mappa:"), 1, 0)

        self.output_edit = QLineEdit(self.output_dir)
        self.output_edit.setPlaceholderText(
            "Válassz egy külön kimeneti mappát..."
        )
        self.output_edit.textChanged.connect(self.on_output_dir_changed)
        output_layout.addWidget(self.output_edit, 1, 1)

        self.output_browse_btn = QPushButton("Mappa kiválasztása…")
        self.output_browse_btn.clicked.connect(self.choose_output_dir)
        output_layout.addWidget(self.output_browse_btn, 1, 2)

        self.output_hint = QLabel()
        self.output_hint.setWordWrap(True)
        self.output_hint.setTextFormat(Qt.TextFormat.RichText)
        self.output_hint.setMinimumHeight(42)
        output_layout.addWidget(self.output_hint, 2, 0, 1, 3)

        layout.addWidget(output_box)

        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([
            "✓", "Sorozat", "Évad", "Epizód", "Típus", "Méret",
            "Eredeti", "Új név", "Másolási állapot", "Folyamat"
        ])
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.table.setHorizontalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.table.setWordWrap(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.context_menu)
        self.table.cellClicked.connect(self._table_cell_clicked)
        self.table.cellDoubleClicked.connect(self._table_double_clicked)
        self.table.horizontalHeader().sectionClicked.connect(self._header_section_clicked)

        header = self.table.horizontalHeader()
        header.setToolTip(
            "Kijelölés: kattintásra mindent kijelöl / újabb kattintásra mindent töröl"
        )
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(48)
        self.table.setColumnWidth(6, 220)
        self.table.setColumnWidth(7, 180)

        layout.addWidget(self.table)
        self.table.setVisible(False)
        self.empty_state.setVisible(True)

        self.on_output_mode_changed(self.output_mode_combo.currentText())


    def build_settings(self):
        layout = QVBoxLayout(self.settings_tab)

        left = QWidget()
        grid = QGridLayout(left)

        grid.addWidget(QLabel("Mód:"), 0, 0)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Automatikus / Vegyes", "Sorozat", "Film"])
        self.mode_combo.setCurrentText(self.mode_value)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        grid.addWidget(self.mode_combo, 0, 1)

        self.name_label = QLabel("Sorozat neve:")
        grid.addWidget(self.name_label, 1, 0)

        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._title_changed)
        grid.addWidget(self.title_edit, 1, 1)

        detected_box = QGroupBox("Felismerés")
        detected_layout = QVBoxLayout(detected_box)
        self.detected_series_label = QLabel("Még nincs elemzés")
        self.detected_series_label.setWordWrap(True)
        self.detected_series_label.setStyleSheet(
            "QLabel { padding: 4px; color: #333; }"
        )
        detected_layout.addWidget(self.detected_series_label)
        grid.addWidget(detected_box, 1, 2, 2, 1)

        grid.addWidget(QLabel("Kívánt név sablon:"), 2, 0)

        self.template_edit = QLineEdit(self.template_value)
        self.template_edit.textChanged.connect(self._template_changed)
        grid.addWidget(self.template_edit, 2, 1)

        self.base_vars_label = QLabel("Alap változók:")
        grid.addWidget(self.base_vars_label, 3, 0)

        var_frame = QWidget()
        var_layout = QHBoxLayout(var_frame)
        var_layout.setContentsMargins(0, 0, 0, 0)

        self.var_buttons = {}
        for value in ["{CIM}", "{SZEZON}", "{EPIZOD}"]:
            b = QPushButton(value)
            b.clicked.connect(lambda checked=False, x=value: self.insert_var(x))
            var_layout.addWidget(b)
            self.var_buttons[value] = b

        grid.addWidget(var_frame, 3, 1)

        self.default_template_label = QLabel(
            "Alapértelmezett sorozatsablon: {CIM}.{SZEZON}{EPIZOD}"
        )
        self.default_template_label.setStyleSheet("color: #444;")
        grid.addWidget(self.default_template_label, 4, 1)

        advanced = QGroupBox("Haladó beállítások")
        adv_layout = QVBoxLayout(advanced)

        self.normalize_cb = QCheckBox("Fájlnév normalizálása")
        self.lang_norm_cb = QCheckBox("Feliratnevek normalizálása")
        self.subdirs_cb = QCheckBox("Almappák bevonása")
        self.conflicts_cb = QCheckBox("Névütközések előzetes ellenőrzése")
        self.preserve_cb = QCheckBox("Kijelölések megőrzése")

        self.normalize_cb.setChecked(bool(self.normalize_value))
        self.subdirs_cb.setChecked(bool(self.include_subdirs_value))
        self.conflicts_cb.setChecked(bool(self.check_conflicts_value))
        self.preserve_cb.setChecked(True)

        for cb in [
            self.normalize_cb, self.lang_norm_cb, self.subdirs_cb,
            self.conflicts_cb, self.preserve_cb
        ]:
            adv_layout.addWidget(cb)

        adv_layout.addWidget(
            QLabel("Haladó sablonváltozók: {NYELV}, {KITERJ}, {EP}, {EXT}")
        )
        grid.addWidget(advanced, 5, 0, 1, 2)

        button_row = QHBoxLayout()
        save = QPushButton("Beállítások mentése")
        save.clicked.connect(self.save_settings)
        button_row.addWidget(save)

        refresh_list = QPushButton("Lista frissítése")
        refresh_list.setToolTip("Újraelemzi a listát és újragenerálja a tervezett neveket.")
        refresh_list.clicked.connect(self.refresh)
        button_row.addWidget(refresh_list)

        reset = QPushButton("Beállítások visszaállítása")
        reset.clicked.connect(self.reset_settings)
        button_row.addWidget(reset)
        button_row.addStretch(1)
        grid.addLayout(button_row, 7, 1)

        layout.addWidget(left)
        layout.addStretch(1)

    def build_preview(self):
        layout = QVBoxLayout(self.preview_tab)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.preview_text)
        self.batch_select_row = QHBoxLayout()
        self.select_all_btn = QPushButton("Összes kijelölése")
        self.select_none_btn = QPushButton("Kijelölés törlése")
        self.select_missing_btn = QPushButton("Csak a hiányzókat")
        self.select_all_btn.clicked.connect(self.select_all_items)
        self.select_none_btn.clicked.connect(self.select_none_items)
        self.select_missing_btn.clicked.connect(self.select_missing_items)
        self.batch_select_row.addWidget(self.select_all_btn)
        self.batch_select_row.addWidget(self.select_none_btn)
        self.batch_select_row.addWidget(self.select_missing_btn)
        self.batch_select_row.addStretch(1)
        layout.addLayout(self.batch_select_row)


    def _history_key(self, record):
        return (
            record.get("time", ""),
            record.get("operation", ""),
            record.get("title", ""),
            record.get("destination", ""),
        )

    def build_history(self):
        layout = QVBoxLayout(self.history_tab)

        info = QLabel(
            "Itt láthatod a korábbi műveleteket. A jelölőnégyzetekkel több előzményt is kiválaszthatsz."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.hist = QTableWidget(0, 7)
        self.hist.setHorizontalHeaderLabels([
            "✓", "#", "Időpont", "Művelet", "Sorozat / film", "Fájlok", "Hely"
        ])
        self.hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.hist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.hist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.hist.setAlternatingRowColors(True)
        self.hist.setColumnWidth(0, 34)
        header = self.hist.horizontalHeader()
        for col in (1, 2, 3, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.hist, 1)

        buttons = QHBoxLayout()
        select_all = QPushButton("Minden kijelölése")
        select_all.clicked.connect(self.history_select_all)
        buttons.addWidget(select_all)
        deselect = QPushButton("Kijelölés törlése")
        deselect.clicked.connect(self.history_clear_selection)
        buttons.addWidget(deselect)
        delete_selected = QPushButton("Kijelöltek törlése")
        delete_selected.clicked.connect(self.delete_selected_history)
        buttons.addWidget(delete_selected)
        buttons.addSpacing(12)
        undo = QPushButton("Kiválasztott művelet visszaállítása")
        undo.setStyleSheet(
            "QPushButton { background: #c62828; color: white; font-weight: bold; }"
            "QPushButton:hover { background: #a51f1f; }"
        )
        undo.clicked.connect(self.undo_selected)
        buttons.addWidget(undo)
        export = QPushButton("Előzmények exportálása")
        export.clicked.connect(self.export_history)
        buttons.addWidget(export)
        buttons.addStretch(1)
        clear = QPushButton("Összes előzmény törlése")
        clear.clicked.connect(self.clear_history)
        buttons.addWidget(clear)
        layout.addLayout(buttons)

    # ---------- state ----------

    def _title_changed(self, value):
        self.title_value = value
        self.title_manual = bool(str(value).strip())

    def _set_title_programmatic(self, text, manual=False):
        text = "" if text is None else str(text)
        if hasattr(self, "title_edit"):
            self.title_edit.blockSignals(True)
            self.title_edit.setText(text)
            self.title_edit.blockSignals(False)
        self.title_value = text
        self.title_manual = bool(manual) and bool(text.strip())

    def _template_changed(self, value):
        self.template_value = value

    def on_mode_changed(self, mode=None):
        if hasattr(self, "mode_combo"):
            self.mode_value = self.mode_combo.currentText()

        film_only = self.mode_value == "Film"
        mixed = self.mode_value == "Automatikus / Vegyes"

        if film_only:
            self.name_label.setText("Film neve:")
            self.base_vars_label.setText("Alap változók:")
            self.default_template_label.setText("Alapértelmezett filmsablon: {CIM}")
            self.var_buttons["{SZEZON}"].setVisible(False)
            self.var_buttons["{EPIZOD}"].setVisible(False)
            if self.template_value == "{CIM}.{SZEZON}{EPIZOD}":
                self.template_edit.setText("{CIM}")
        elif mixed:
            self.name_label.setText("Alapértelmezett cím (opcionális):")
            self.base_vars_label.setText("Sorozatváltozók:")
            self.default_template_label.setText(
                "Vegyes módban az SxxEyy alapján sorozat, egyébként film kerül felismerésre. "
                "A film sablonja: {CIM}"
            )
            self.var_buttons["{SZEZON}"].setVisible(True)
            self.var_buttons["{EPIZOD}"].setVisible(True)
            if self.template_value == "{CIM}":
                self.template_edit.setText("{CIM}.{SZEZON}{EPIZOD}")
        else:
            self.name_label.setText("Sorozat neve:")
            self.base_vars_label.setText("Alap változók:")
            self.default_template_label.setText(
                "Alapértelmezett sorozatsablon: {CIM}.{SZEZON}{EPIZOD}"
            )
            self.var_buttons["{SZEZON}"].setVisible(True)
            self.var_buttons["{EPIZOD}"].setVisible(True)
            if self.template_value == "{CIM}":
                self.template_edit.setText("{CIM}.{SZEZON}{EPIZOD}")

        if hasattr(self, "table"):
            self.refresh()

    def insert_var(self, value):
        self.template_edit.setText(self.template_edit.text() + value)
        self.refresh()

    # ---------- files ----------

    def add_folders(self):
        """Több forráskönyvtár kiválasztása saját, többes kijelölésű ablakkal."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Könyvtárak hozzáadása")
        dialog.resize(760, 560)

        root = QVBoxLayout(dialog)
        info = QLabel(
            "Jelölj ki egy vagy több könyvtárat. Ctrl/Shift segítségével több könyvtár is kiválasztható."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Hely:"))
        start = self._last_folder if Path(self._last_folder).is_dir() else str(Path.home())
        path_edit = QLineEdit(start)
        path_edit.setPlaceholderText("Mappa útvonala – beilleszthető vagy begépelhető")
        path_row.addWidget(path_edit, 1)
        go_btn = QPushButton("Megnyitás")
        path_row.addWidget(go_btn)
        root.addLayout(path_row)

        model = QFileSystemModel(dialog)
        model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        computer_root = ""
        model.setRootPath(computer_root)
        start_index = model.index(start)
        if not start_index.isValid():
            start_index = model.index(str(Path.home()))

        tree = QTreeView(dialog)
        tree.setModel(model)
        tree.setRootIndex(model.index(computer_root) if model.index(computer_root).isValid() else start_index)
        if start_index.isValid():
            tree.setCurrentIndex(start_index)
            tree.scrollTo(start_index)
        tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tree.setColumnWidth(0, 360)
        for col in (1, 2, 3):
            tree.hideColumn(col)
        root.addWidget(tree, 1)

        selected_label = QLabel("Kijelölve: 0 könyvtár")
        root.addWidget(selected_label)

        def update_count():
            count = len(tree.selectionModel().selectedRows(0))
            selected_label.setText(f"Kijelölve: {count} könyvtár")

        tree.selectionModel().selectionChanged.connect(lambda *_: update_count())

        def navigate():
            path = Path(path_edit.text().strip().strip('"'))
            if path.is_dir():
                tree.setRootIndex(model.index(str(path)))
            else:
                QMessageBox.warning(dialog, "Érvénytelen mappa", f"A mappa nem található:\n{path}")

        go_btn.clicked.connect(navigate)
        path_edit.returnPressed.connect(navigate)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=dialog
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Hozzáadás")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Mégsem")
        root.addWidget(buttons)

        def accept_selection():
            indexes = tree.selectionModel().selectedRows(0)
            folders = []
            seen = set()
            for idx in indexes:
                folder = Path(model.filePath(idx))
                key = os.path.normcase(str(folder.resolve()))
                if key not in seen and folder.is_dir():
                    seen.add(key)
                    folders.append(folder)
            if not folders:
                QMessageBox.information(dialog, "Nincs kijelölve", "Jelölj ki legalább egy könyvtárat.")
                return
            dialog.selected_folders = folders
            dialog.accept()

        buttons.accepted.connect(accept_selection)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        folders = getattr(dialog, "selected_folders", [])
        recursive = self.subdirs_cb.isChecked()
        all_paths = []
        seen = set()
        for root_path in folders:
            self._last_folder = str(root_path)
            for pth in self._iter_folder_files(root_path, recursive):
                key = file_identity_key(pth)
                if key not in seen:
                    seen.add(key)
                    all_paths.append(pth)

        if not all_paths:
            QMessageBox.information(
                self,
                "Nincs hozzáadható fájl",
                "A kiválasztott könyvtárakban nem találtam támogatott videó- vagy feliratfájlt."
            )
            return

        self.add_paths(all_paths)

    def _iter_folder_files(self, root, recursive):
        root = Path(root)
        iterator = root.rglob("*") if recursive else root.glob("*")
        for pth in iterator:
            try:
                if pth.is_file() and pth.suffix.lower() in ALL_EXTS:
                    yield pth
            except OSError:
                continue

    def _choose_source_folder(self):
        """Útvonal beillesztése + natív tallózás, a Windows mély fát nem cseréli le."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Mappa hozzáadása")
        dialog.resize(560, 140)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(
            "Illeszd be a mappa útvonalát, vagy tallózz. "
            "Az almappák a beállítások „Almappák bevonása” kapcsolóját követik."
        ))
        row = QHBoxLayout()
        start = self._last_folder if Path(self._last_folder).is_dir() else str(Path.home())
        path_edit = QLineEdit(start)
        path_edit.setPlaceholderText(r"C:\Sorozatok\Show")
        row.addWidget(path_edit, 1)
        browse = QPushButton("Tallózás…")
        row.addWidget(browse)
        layout.addLayout(row)

        def browse_native():
            chosen = QFileDialog.getExistingDirectory(
                dialog, "Mappa kiválasztása", path_edit.text().strip() or start
            )
            if chosen:
                path_edit.setText(chosen)

        browse.clicked.connect(browse_native)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=dialog
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Hozzáadás")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Mégsem")
        layout.addWidget(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        raw = path_edit.text().strip().strip('"')
        if not raw:
            return None
        folder = Path(raw)
        if not folder.is_dir():
            QMessageBox.warning(
                self, "Érvénytelen mappa", f"A mappa nem található:\n{folder}"
            )
            return None
        self._last_folder = str(folder)
        return folder

    def add_folder(self):
        root = self._choose_source_folder()
        if root is None:
            return

        recursive = self.subdirs_cb.isChecked()
        paths = list(self._iter_folder_files(root, recursive))

        if not paths and not recursive:
            answer = QMessageBox.question(
                self,
                "Nincs közvetlenül feldolgozható fájl",
                "A kiválasztott mappában nem találtam támogatott videó- vagy "
                "feliratfájlt közvetlenül.\n\n"
                "Megnézzem az almappákat is?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                paths = list(self._iter_folder_files(root, True))

        if not paths:
            QMessageBox.information(
                self,
                "Nincs hozzáadható fájl",
                f"A kiválasztott mappában nem találtam támogatott fájlt:\n\n"
                f"{root}\n\n"
                "Támogatott videók: MKV, MP4, AVI, M4V, MOV, WMV, WEBM, TS, M2TS\n"
                "Támogatott feliratok: SRT, ASS, SSA, VTT, SUB"
            )
            return

        self.add_paths(paths)

    def add_files(self):
        start = self._last_folder if Path(self._last_folder).is_dir() else ""
        extensions = " ".join("*" + x for x in sorted(ALL_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Videók és feliratok kiválasztása",
            start,
            f"Támogatott fájlok ({extensions});;Minden fájl (*.*)"
        )
        if paths:
            self._last_folder = str(Path(paths[0]).parent)
        self.add_paths([Path(p) for p in paths])

    def dragEnterEvent(self, event):
        if event.mimeData() and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData() and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls() if event.mimeData() else []
        paths = [Path(u.toLocalFile()) for u in urls if u.toLocalFile()]
        if paths:
            self._ingest_user_paths(paths)
            event.acceptProposedAction()

    def _ingest_user_paths(self, paths):
        """Fájlok és mappák (húzás vagy teszt) egységes beléptetése."""
        recursive = self.subdirs_cb.isChecked() if hasattr(self, "subdirs_cb") else True
        collected = []
        seen = set()
        missing = []
        for raw in paths:
            p = Path(raw)
            try:
                exists_file = p.is_file()
                exists_dir = p.is_dir()
            except OSError:
                missing.append(p)
                continue
            if exists_dir:
                self._last_folder = str(p)
                for child in self._iter_folder_files(p, recursive):
                    key = file_identity_key(child)
                    if key not in seen:
                        seen.add(key)
                        collected.append(child)
            elif exists_file:
                key = file_identity_key(p)
                if key not in seen:
                    seen.add(key)
                    collected.append(p)
            else:
                missing.append(p)
        if missing and not collected:
            QMessageBox.warning(
                self,
                "Nem elérhető útvonal",
                "A megadott fájl vagy mappa nem található:\n"
                + "\n".join(str(x) for x in missing[:8])
            )
            return
        if not collected:
            QMessageBox.information(
                self,
                "Nincs hozzáadható fájl",
                "A húzott mappákban nem találtam támogatott videó- vagy feliratfájlt."
            )
            return
        self.add_paths(collected)

    def _source_path(self, item):
        """Az eredeti forrásútvonal, amely másolás után sem változik."""
        raw = getattr(item, "source_path", None)
        if not raw:
            return Path(item.path)
        return Path(raw)

    def add_paths(self, paths):
        existing = set()
        for item in self.items:
            existing.add(file_identity_key(item.path))
            existing.add(file_identity_key(self._source_path(item)))
        added = 0

        for p in paths:
            p = Path(p)
            key = file_identity_key(p)
            if key not in existing:
                item = parse_item(p)
                item.source_path = str(p)
                try:
                    st = p.stat()
                    item.size_bytes = st.st_size
                    item.mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))
                except OSError:
                    item.size_bytes = 0
                    item.mtime_ns = 0
                self.items.append(item)
                existing.add(key)
                added += 1

        if not self.title_value:
            media_names = [
                Path(i.path).name for i in self.items
                if i.kind in ("video", "sub")
            ]
            self._set_title_programmatic(
                common_title(media_names),
                manual=False,
            )

        self.refresh()

        if hasattr(self, "status_label"):
            if added:
                self.status_label.setText(
                    f"{added} új fájl hozzáadva — összesen {len(self.items)} fájl"
                )
            elif paths:
                self.status_label.setText(
                    f"0 új fájl — a kiválasztott fájlok már a listában vannak"
                )

    # ---------- output ----------

    def on_output_mode_changed(self, mode):
        self.output_mode = mode
        copy_mode = mode == "Másolás kimeneti mappába és átnevezés"

        self.output_edit.setEnabled(copy_mode)
        self.output_browse_btn.setEnabled(copy_mode)

        if copy_mode:
            self.output_hint.setStyleSheet(
                "QLabel { border: 1px solid #4a8f5a; border-radius: 6px; "
                "padding: 7px 10px; background: rgba(70, 150, 80, 35); }"
            )
            self.output_hint.setText(
                "<b>Biztonságos másolás</b><br>"
                "Az eredeti fájlok érintetlenek maradnak. A program a kijelölt "
                "videókat és feliratokat a kimeneti mappába másolja az új nevekkel."
            )
        else:
            self.output_hint.setStyleSheet(
                "QLabel { border: 2px solid #b54b4b; border-radius: 6px; "
                "padding: 7px 10px; background: rgba(190, 70, 70, 45); "
                "font-weight: 600; }"
            )
            self.output_hint.setText(
                "<b>⚠ FIGYELEM – az eredeti fájlok neve megváltozik!</b><br>"
                "Ezt csak akkor válaszd, ha az eredeti fájlokat már külön "
                "munkamappába másoltad."
            )

        # A build során ez a jelzés már lefuthat azelőtt, hogy
        # a beállítási vezérlők létrejönnének.
        if hasattr(self, "normalize_cb"):
            self.save_settings(silent=True)
        self.update_action_state()

    def _reset_copy_states_for_destination(self):
        """A célmappa változásakor a korábbi célhoz tartozó állapotok érvénytelenek."""
        for item in self.items:
            if getattr(item, "copy_status", "Várakozik") in {
                "Átmásolva", "Már létezik", "Hiba", "Nem fért el", "Megszakítva"
            }:
                item.copy_status = "Várakozik"
                item.copy_percent = 0
                item.note = ""

    def on_output_dir_changed(self, value):
        old = getattr(self, "output_dir", "")
        self.output_dir = value.strip()
        if old != self.output_dir:
            self._reset_copy_states_for_destination()
            if hasattr(self, "table"):
                self.refresh()
        if hasattr(self, "normalize_cb"):
            self.save_settings(silent=True)
        self.update_action_state()

    def choose_output_dir(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Kimeneti mappa kiválasztása",
            self.output_dir or str(Path.home())
        )
        if folder:
            self.output_edit.setText(folder)

    def _output_path_error(self, selected):
        if self.output_mode != "Másolás kimeneti mappába és átnevezés":
            return ""

        if not self.output_dir:
            return "Nincs kiválasztva kimeneti mappa."

        try:
            destination = Path(self.output_dir).resolve()
        except OSError:
            return "A kimeneti mappa nem érvényes."

        if destination.exists() and not destination.is_dir():
            return "A kimeneti útvonal nem mappa."

        source_parents = {self._source_path(i).resolve().parent for i in selected}
        if destination in source_parents:
            return (
                "A kimeneti mappa nem lehet ugyanaz a mappa, amelyben "
                "az eredeti fájlok találhatók."
            )

        return ""

    def update_action_state(self):
        if not hasattr(self, "rename_btn"):
            return

        has_items = bool(self.items)
        if self.output_mode == "Helyben átnevezés":
            self.rename_btn.setEnabled(has_items)
        else:
            self.rename_btn.setEnabled(
                has_items and bool(self.output_dir.strip())
            )

    def clear_list(self):
        if not self.items:
            return

        if QMessageBox.question(
            self, "Lista ürítése",
            "Biztosan törlöd a teljes feldolgozási listát?\n\n"
            "Ez csak a program listáját üríti ki, az eredeti fájlokat nem törli."
        ) == QMessageBox.StandardButton.Yes:
            self.items = []
            self._set_title_programmatic("", manual=False)
            self.detected_series_label.setText("Még nincs elemzés")
            self.refresh()

    def remove_selected(self):
        selected_count = sum(1 for item in self.items if item.selected)
        if not selected_count:
            QMessageBox.information(
                self, "Nincs kijelölés",
                "Nincs kijelölt sor, amit törölni lehetne a listából."
            )
            return

        answer = QMessageBox.question(
            self,
            "Kijelöltek törlése",
            f"{selected_count} kijelölt fájl eltávolítása a feldolgozási listából?\n\n"
            "Az eredeti fájlokat ez nem törli és nem módosítja.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.items = [item for item in self.items if not item.selected]
            self.refresh()

    def request_cancel(self):
        if getattr(self, "cancel_requested", False):
            return
        self.cancel_requested = True
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("⛔  Megszakítás folyamatban…")

    def _set_cancel_enabled(self, enabled):
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setEnabled(enabled)
            self.cancel_btn.setText(
                "⛔  Feladat megszakítása" if enabled else "⛔  Feladat megszakítása"
            )

    def set_all(self, value):
        for item in self.items:
            if value and item.kind not in ("video", "sub"):
                item.selected = False
                continue
            item.selected = value
        self.refresh(reanalyze=False)

    def _header_section_clicked(self, section):
        # Az első oszlop fejlécére kattintva váltunk:
        # ha van kijelöletlen fájl -> mindent kijelölünk,
        # ha minden kijelölve van -> mindent törlünk.
        if section != 0 or not self.items:
            return
        media = [i for i in self.items if i.kind in ("video", "sub")]
        if not media:
            return
        all_selected = all(i.selected for i in media)
        for item in self.items:
            item.selected = (not all_selected) and item.kind in ("video", "sub")
        self._refresh_selection_status()

    def _table_double_clicked(self, row, column):
        visible = self._visible_items()
        if 0 <= row < len(visible):
            item = visible[row]
            if hasattr(self, "status_label"):
                self.status_label.setText(str(self._source_path(item)))

    def _table_cell_clicked(self, row, column):
        # A 0. oszlop kijelölését kizárólag a checkbox kezeli.
        # A cellClicked + stateChanged együtt dupla váltást okozna.
        return

    def toggle_item(self, row, column):
        visible = self._visible_items()
        if 0 <= row < len(visible):
            item = visible[row]
            if item.kind not in ("video", "sub"):
                item.selected = False
            else:
                item.selected = not item.selected
            self.refresh(reanalyze=False)

    def _visible_items(self):
        filt = self.filter_edit.text().lower().strip()
        order = list(range(len(self.items)))

        if self.sort_combo.currentText() == "Név":
            order.sort(
                key=lambda x: Path(self.items[x].path).name.lower()
            )
        elif self.sort_combo.currentText() == "Fájltípus":
            order.sort(
                key=lambda x: (
                    self.items[x].ext,
                    Path(self.items[x].path).name.lower()
                )
            )
        elif self.sort_combo.currentText() == "Módosítás dátuma":
            order.sort(
                key=lambda x: getattr(self.items[x], "mtime_ns", 0) or 0
            )
        else:
            order.sort(
                key=lambda x: (
                    (self.items[x].title or "").lower(),
                    self.items[x].season if self.items[x].season is not None else 999,
                    self.items[x].episode if self.items[x].episode is not None else 999,
                    0 if self.items[x].kind == "video" else 1,
                    Path(self.items[x].path).name.lower()
                )
            )

        result = []
        for idx in order:
            item = self.items[idx]
            if filt and filt not in (
                Path(item.path).name + " " +
                str(self._source_path(item)) + " " +
                item.status + " " + item.group
            ).lower():
                continue
            result.append(item)

        return result

    # ---------- context menu ----------

    def context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        visible = self._visible_items()
        if row >= len(visible):
            return

        item = visible[row]
        menu = QMenu(self)

        open_action = menu.addAction("Megnyitás")
        folder_action = menu.addAction("Mappa megnyitása")
        copy_path_action = menu.addAction("Forrásútvonal másolása")
        menu.addSeparator()
        select_action = menu.addAction("Kijelölés")
        deselect_action = menu.addAction("Kijelölés megszüntetése")

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))

        if chosen == open_action:
            self.open_file(item.path)
        elif chosen == folder_action:
            self.open_folder(item.path)
        elif chosen == copy_path_action:
            QApplication.clipboard().setText(str(self._source_path(item)))
            if hasattr(self, "status_label"):
                self.status_label.setText(str(self._source_path(item)))
        elif chosen == select_action:
            item.selected = item.kind in ("video", "sub")
            self.refresh(reanalyze=False)
        elif chosen == deselect_action:
            item.selected = False
            self.refresh(reanalyze=False)

    def open_file(self, path):
        if os.name == "nt":
            os.startfile(path)
        else:
            os.system(f'xdg-open "{path}"')

    def open_folder(self, path):
        folder = Path(path).parent
        if os.name == "nt":
            os.startfile(folder)
        else:
            os.system(f'xdg-open "{folder}"')

    # ---------- engine bridge ----------

    def _refresh_selection_status(self):
        self.refresh(reanalyze=False)
        if hasattr(self, "status_label"):
            selected=sum(i.selected for i in self.items)
            self.status_label.setText(f"Kijelölve: {selected} / {len(self.items)} fájl")

    def select_all_items(self):
        for i in self.items:
            i.selected = i.kind in ("video", "sub")
        self._refresh_selection_status()

    def select_none_items(self):
        for i in self.items:
            i.selected = False
        self._refresh_selection_status()

    def select_missing_items(self):
        # Egy epizódot videó + felirat párként kezelünk: ha bármelyik hiányzik,
        # a pár mindkét tagját kijelöljük.
        groups={}
        for item in self.items:
            groups.setdefault(item.group,[]).append(item)

        for arr in groups.values():
            incomplete=False
            for item in arr:
                if not item.new_name:
                    incomplete=True
                    break
                target = self.destination_for(item)
                if target is None:
                    incomplete = True
                    break
                try:
                    complete=target.is_file() and target.stat().st_size==self._source_path(item).stat().st_size
                except OSError:
                    complete=False
                if not complete:
                    incomplete=True
                    break
            for item in arr:
                item.selected = bool(incomplete) and item.kind in ("video", "sub")
        self._refresh_selection_status()

    def analyze(self):
        """A lista teljes újraelemzése sorozat, film vagy vegyes módban."""
        if not self.items:
            return

        if not self.title_value:
            detected_title = common_title([
                Path(i.path).name for i in self.items
                if i.kind in ("video", "sub")
            ])
            if detected_title and self.mode_value != "Automatikus / Vegyes":
                self._set_title_programmatic(detected_title, manual=False)

        global_title = self.title_value.strip()
        video_items = [i for i in self.items if i.kind == "video"]

        series_titles = {}
        film_titles = {}
        for item in video_items:
            key = re.sub(r'[^a-z0-9]+', '.', item.title.lower()).strip('.')
            if item.season is not None and item.episode is not None and item.confidence == "high":
                if key:
                    series_titles[key] = item.title.strip()
            elif key:
                film_titles[key] = item.title.strip()

        detected_parts = []
        if series_titles:
            detected_parts.append("Sorozatok: " + ", ".join(sorted(series_titles.values(), key=str.lower)))
        if film_titles:
            detected_parts.append("Filmek: " + ", ".join(sorted(film_titles.values(), key=str.lower)))
        if hasattr(self, "detected_series_label"):
            self.detected_series_label.setText("\n".join(detected_parts) if detected_parts else "Nem sikerült címet felismerni.")

        apply_item_target_names(
            self.items,
            NamingContext(
                mode=self.mode_value,
                template=self.template_value,
                normalize=self.normalize_cb.isChecked(),
                title_manual=self.title_manual,
                global_title=global_title,
            ),
        )

        disambiguate_subtitle_target_names(self.items)
        apply_pair_group_status(self.items)

        if self.conflicts_cb.isChecked():
            apply_destination_conflicts(
                self.items, self.destination_for, self._source_path
            )

        self._apply_completion_status()

    def destination_for(self, item):
        """Az Item aktuális kimeneti mód szerinti célfájlja, vagy None.

        Másolás: output_dir / new_name
        Helyben: forrásmappa / new_name  (_source_path, nem a másolás utáni path)
        """
        raw = getattr(item, "new_name", None)
        if not raw:
            return None
        name = Path(raw).name
        if not name:
            return None
        if self.output_mode == "Másolás kimeneti mappába és átnevezés":
            if not str(getattr(self, "output_dir", "") or "").strip():
                return None
            try:
                return Path(self.output_dir).resolve() / name
            except OSError:
                return Path(self.output_dir) / name
        return self._source_path(item).parent / name

    def _intended_destination(self, item):
        return self.destination_for(item)

    def _destination_matches_output(self, item):
        return destination_matches_output(
            item, self.destination_for, self._source_path
        )

    def _apply_completion_status(self):
        """A 'Kész' a fizikai célfájl meglétét jelenti, nem a név OK státuszát."""
        apply_completion_status(
            self.items, self.destination_for, self._source_path
        )

    def _batch_summary(self):
        series = {}
        films = {}
        seasons = set()

        for item in self.items:
            if item.kind != "video":
                continue
            title = item.title.strip() or "Ismeretlen"
            key = re.sub(r'[^a-z0-9]+', '.', title.lower()).strip('.')
            if item.season is not None and item.episode is not None and item.confidence == "high":
                series.setdefault(key, title)
                seasons.add((key, item.season))
            else:
                films.setdefault(key, title)

        ok = sum(i.status in {"OK", "Kész"} for i in self.items)
        return {
            "series_count": len(series),
            "film_count": len(films),
            "season_count": len(seasons),
            "file_count": len(self.items),
            "selected_count": sum(i.selected for i in self.items),
            "ok_count": ok,
            "issue_count": len(self.items) - ok,
            "series_names": list(series.values()),
            "film_names": list(films.values()),
        }

    def _checkbox_changed(self, item, state):
        if getattr(self, "_syncing_table", False):
            return
        checked = state == Qt.CheckState.Checked.value
        if item.kind not in ("video", "sub"):
            item.selected = False
            self.refresh(reanalyze=False)
            return
        item.selected = checked
        if checked and item.group:
            # A normál videó/felirat pár automatikusan együtt kijelölhető.
            # Extra (variant) feliratot nem kényszerítünk bele a párba.
            group_items = [x for x in self.items if x.group == item.group]
            videos = [x for x in group_items if x.kind == "video"]
            primary_subs = [x for x in group_items if x.kind == "sub" and x.lang == "hu" and not x.variant]
            if not primary_subs:
                primary_subs = [x for x in group_items if x.kind == "sub"]
            pair = []
            if videos:
                pair.append(videos[0])
            if primary_subs:
                pair.append(primary_subs[0])
            for member in pair:
                member.selected = True
        self.status_label.setText(
            f"{len(self.items)} fájl | kijelölve: "
            f"{sum(i.selected for i in self.items)}"
        )
        self.refresh(reanalyze=False)

    def _copy_state(self, item):
        return getattr(item, "copy_status", "Várakozik")

    def _copy_percent(self, item):
        return int(getattr(item, "copy_percent", 0) or 0)

    def _set_progress_cell(self, row, item, state):
        """Folyamat: szöveg, amíg nincs aktív másolás — nagy listánál nincs 1000 QProgressBar."""
        self.table.removeCellWidget(row, 9)
        if state == "Másolás...":
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(self._copy_percent(item))
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            self.table.setCellWidget(row, 9, bar)
            return
        text = "100%" if state in {"Átmásolva", "Kész"} else "—"
        cell = QTableWidgetItem(text)
        src = str(self._source_path(item))
        cell.setToolTip(src)
        self.table.setItem(row, 9, cell)

    def _update_copy_row(self, item):
        if not hasattr(self, "table"):
            return
        visible=self._visible_items()
        try:
            row=next(i for i,x in enumerate(visible) if x is item)
        except StopIteration:
            return
        state=self._copy_state(item)
        state_item=QTableWidgetItem(state)
        styles = {
            "Már létezik": ("#b71c1c", "#ffebee"),
            "Névütközés": ("#b71c1c", "#ffebee"),
            "Nem egyező pár": ("#b71c1c", "#ffebee"),
            "Hiba": ("#b71c1c", "#ffebee"),
            "Nem fért el": ("#e65100", "#fff3e0"),
            "Megszakítva": ("#8e0000", "#ffebee"),
            "Átmásolva": ("#1b5e20", "#e8f5e9"),
        }
        if state in styles:
            fg, bg = styles[state]
            state_item.setForeground(QColor(fg))
            state_item.setBackground(QColor(bg))
            state_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.table.setItem(row, 8, state_item)
        self._set_progress_cell(row, item, state)
        QApplication.processEvents()

    def refresh(self, reanalyze=True):
        """Táblázat, szűrés, preview. Az analyze csak reanalyze=True esetén fut.

        Alapértelmezés True a kompatibilitás miatt (add_paths, mód, undo, másolás).
        Szűrés, rendezés, kijelölés-újrarajzolás: reanalyze=False.
        """
        if not hasattr(self, "table"):
            return

        if reanalyze:
            self.analyze()
        visible=self._visible_items()
        has_items = bool(visible)
        self.empty_state.setVisible(not has_items)
        self.table.setVisible(has_items)

        self._syncing_table = True
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(visible))
            for row, item in enumerate(visible):
                series=item.title.strip() or "Ismeretlen"
                season=f"S{item.season:02d}" if item.season is not None else "—"
                episode=f"E{item.episode:02d}" if item.episode is not None else "—"
                # Valódi, kattintható kijelölő a sorhoz.
                check = QCheckBox()
                check.setChecked(bool(item.selected))
                check.setToolTip("A sor kijelölése / kijelölés megszüntetése")
                check.stateChanged.connect(
                    lambda state, obj=item: self._checkbox_changed(obj, state)
                )
                holder = QWidget()
                holder_layout = QHBoxLayout(holder)
                holder_layout.setContentsMargins(0, 0, 0, 0)
                holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                holder_layout.addWidget(check)
                self.table.setCellWidget(row, 0, holder)

                if item.kind == "video":
                    kind_label = "videó"
                elif item.kind == "sub":
                    kind_label = "felirat"
                else:
                    kind_label = "egyéb"
                orig_name = Path(item.path).name
                src_path = str(self._source_path(item))
                size_text = format_size_bytes(getattr(item, "size_bytes", None))
                values=[
                    series, season, episode,
                    kind_label,
                    size_text,
                    orig_name,
                    item.new_name or "—",
                    self._copy_state(item)
                ]
                for col,value in enumerate(values, start=1):
                    cell = QTableWidgetItem(value)
                    if col in (6, 7):
                        cell.setToolTip(f"{orig_name}\n{src_path}")
                    elif col == 5:
                        exact = getattr(item, "size_bytes", None)
                        if exact is not None:
                            cell.setToolTip(f"{exact} B")
                    else:
                        cell.setToolTip(src_path)
                    if col == 8:
                        state = self._copy_state(item)
                        styles = {
                            "Már létezik": ("#b71c1c", "#ffebee"),
                            "Névütközés": ("#b71c1c", "#ffebee"),
                            "Hiba": ("#b71c1c", "#ffebee"),
                            "Nem fért el": ("#e65100", "#fff3e0"),
                            "Megszakítva": ("#8e0000", "#ffebee"),
                            "Átmásolva": ("#1b5e20", "#e8f5e9"),
                        }
                        if state in styles:
                            fg, bg = styles[state]
                            cell.setForeground(QColor(fg))
                            cell.setBackground(QColor(bg))
                            cell.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    self.table.setItem(row,col,cell)
                self._set_progress_cell(row, item, self._copy_state(item))
        finally:
            self.table.setUpdatesEnabled(True)
            self._syncing_table = False

        self.status_label.setText(
            f"{len(self.items)} fájl | kijelölve: {sum(i.selected for i in self.items)}"
        )
        self.update_action_state()

        summary=self._batch_summary()
        self.preview_text.clear()
        self.preview_text.append(
            f"Feldolgozási lista: {summary['series_count']} sorozat | "
            f"{summary['film_count']} film | {summary['season_count']} évad | "
            f"{summary['file_count']} fájl | "
            f"Rendben: {summary['ok_count']} | "
            f"Ellenőrzést igényel: {summary['issue_count']}\n"
        )
        for item in visible:
            selected_mark = "✓" if item.selected else " "
            season_text = (
                f"S{item.season:02d}E{item.episode:02d}"
                if item.season is not None and item.episode is not None
                else "—"
            )
            kind_text = (
                "videó" if item.kind == "video"
                else "felirat" if item.kind == "sub"
                else "egyéb"
            )
            self.preview_text.append(
                f"[{selected_mark}] {item.title.strip() or 'Ismeretlen'} — "
                f"{season_text} — "
                f"{kind_text}\n"
                f"    Eredeti: {Path(item.path).name}\n"
                f"    → {item.new_name or '—'}\n"
                f"    [{item.status}] {item.note} | "
                f"{self._copy_state(item)}\n"
            )

    # ---------- actions ----------

    def check(self):
        self.analyze()
        self.tabs.setCurrentWidget(self.preview_tab)
        self.refresh(reanalyze=False)

        ok = sum(i.status in {"OK", "Kész"} for i in self.items)
        bad = len(self.items) - ok

        summary = self._batch_summary()
        names = ", ".join(summary["series_names"][:8])
        if len(summary["series_names"]) > 8:
            names += f", ... (+{len(summary['series_names']) - 8})"

        issue_items = [i for i in self.items if i.status not in {"OK", "Kész"}]

        mixed_mode_note = ""
        if self.mode_value == "Sorozat" and summary["film_count"]:
            mixed_mode_note = (
                "\n\nFigyelem: a lista filmfájlokat is tartalmaz. "
                "Vegyes feldolgozáshoz válaszd az „Automatikus / Vegyes” módot."
            )

        issue_lines = []
        for item in issue_items[:8]:
            if item.season is not None and item.episode is not None:
                label = f"{item.title.strip() or 'Ismeretlen'} S{item.season:02d}E{item.episode:02d}"
            else:
                label = item.title.strip() or "Ismeretlen film"
            reason = item.note or item.status
            issue_lines.append(f"• {label} — {self._source_path(item).name}: {reason}")
        if len(issue_items) > 8:
            issue_lines.append(f"• … és még {len(issue_items) - 8} fájl")

        details = "\n".join(issue_lines) if issue_lines else "Nincs problémás fájl."

        QMessageBox.information(
            self,
            "Ellenőrzés",
            f"Sorozatok: {summary['series_count']}\n"
            f"Filmek: {summary['film_count']}\n"
            f"Évadok: {summary['season_count']}\n"
            f"Fájlok: {summary['file_count']}\n"
            f"Kijelölve: {summary['selected_count']}\n"
            f"Rendben: {summary['ok_count']}\n"
            f"Ellenőrzést igényel: {summary['issue_count']}\n\n"
            f"Sorozatok: {names or '—'}\n"
            f"Filmek: {', '.join(summary['film_names'][:8]) or '—'}\n\n"
            f"Problémás fájlok:\n{details}"
            f"{mixed_mode_note}"
        )

    def _progress_start(self, total, label="Feldolgozás"):
        if not hasattr(self, "progress_bar"):
            return
        total = max(1, total)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"{label}  •  0 / {total}  •  0%")
        self.progress_bar.setVisible(True)
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText("")
            self.progress_file_label.setToolTip("")
        QApplication.processEvents()

    def _progress_step(self, current, total, label="Feldolgozás", filename=""):
        if not hasattr(self, "progress_bar"):
            return
        total = max(1, total)
        percent = round(current * 100 / total)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{label}  •  {current} / {total}  •  {percent}%")
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText(
                f"Fájl: {filename}" if filename else ""
            )
            self.progress_file_label.setToolTip(filename or "")
        QApplication.processEvents()

    def _progress_finish(self):
        if not hasattr(self, "progress_bar"):
            return
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_bar.setFormat("Kész  •  teljes művelet befejezve")
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText("")
            self.progress_file_label.setToolTip("")
        QApplication.processEvents()
        QTimer.singleShot(1200, self.progress_bar.hide)

    def rename(self):
        self.analyze()

        # Meglévő célfájl SOHA nem írható felül.
        allowed_statuses = {"OK"}
        selected = [
            i for i in self.items
            if i.selected and i.status in allowed_statuses
        ]
        selected.sort(
            key=lambda i: (
                (i.title or "").strip().lower(),
                i.season if i.season is not None else 999,
                i.episode if i.episode is not None else 999,
                0 if i.kind == "video" else 1,
                Path(i.path).name.lower()
            )
        )

        if not selected:
            QMessageBox.warning(
                self,
                "Nincs feldolgozható fájl",
                "Nincs kijelölt, feldolgozható videó + felirat csoport."
            )
            return

        output_error = self._output_path_error(selected)
        if output_error:
            QMessageBox.warning(self, "Kimenet", output_error)
            return

        copy_mode = (
            self.output_mode == "Másolás kimeneti mappába és átnevezés"
        )
        destination = Path(self.output_dir).resolve() if copy_mode else None

        # Ellenőrizzük, hogy a kijelölt videó + felirat párok együtt legyenek.
        selected_set = {id(i) for i in selected}
        all_groups = {}
        for item in self.items:
            all_groups.setdefault(item.group, []).append(item)

        incomplete_pairs = []
        for group, arr in all_groups.items():
            vids = [x for x in arr if x.kind == "video"]
            subs = [x for x in arr if x.kind == "sub"]
            if not vids and not subs:
                continue
            selected_here = [x for x in arr if id(x) in selected_set]
            if not selected_here:
                continue
            primary_subs = [x for x in subs if x.lang == "hu" and not x.variant] or subs
            required = []
            if vids:
                required.append(vids[0])
            if primary_subs:
                required.append(primary_subs[0])
            required_ids = {id(x) for x in required}
            selected_required = {id(x) for x in selected_here}
            if required_ids and not required_ids.issubset(selected_required):
                incomplete_pairs.append(group)

        if incomplete_pairs:
            QMessageBox.warning(
                self, "Hiányos epizód kijelölés",
                "Egy vagy több epizódnál csak a videó vagy csak a felirat van kijelölve.\n\n"
                "A videó és a hozzá tartozó felirat csak együtt másolható.\n"
                "Jelöld ki a teljes párt, vagy használd a „Csak a hiányzókat” funkciót."
            )
            return

        # Összeállítjuk a tényleges műveleteket.
        changes = []
        for group, arr in sorted(
            all_groups.items(),
            key=lambda kv: (
                (kv[1][0].title or "").lower(),
                kv[1][0].season if kv[1][0].season is not None else 999,
                kv[1][0].episode if kv[1][0].episode is not None else 999
            )
        ):
            pair = [x for x in arr if id(x) in selected_set and x.status in allowed_statuses]
            if not pair:
                continue
            pair.sort(key=lambda x: 0 if x.kind == "video" else 1)
            for item in pair:
                old = self._source_path(item)
                new = self.destination_for(item)
                if new is None:
                    continue
                try:
                    same = old.resolve() == new.resolve()
                except OSError:
                    same = os.path.normcase(str(old)) == os.path.normcase(str(new))
                if not same:
                    changes.append((item, old, new))

        if not changes:
            QMessageBox.information(self, "Nincs teendő", "Nem maradt végrehajtható művelet.")
            return

        # Célfájlok ellenőrzése:
        # meglévő célfájlt SOHA nem írunk felül, és csak az ütköző fájlt hagyjuk ki.
        existing_targets = [(item, old, new) for item, old, new in changes if new.exists()]
        failed = []

        if existing_targets:
            kept = []
            for change in changes:
                item, old_path, new_path = change
                if new_path.exists():
                    item.status = "Névütközés"
                    item.copy_status = "Névütközés"
                    item.copy_percent = 0
                    item.note = "A célfájl már létezik – a program nem írta felül"
                    failed.append((item, item.note))
                else:
                    kept.append(change)
            changes = kept

        # Biztonsági újraellenőrzés: ugyanaz a cél csak egy forrásból jöhet.
        target_groups = {}
        for change in changes:
            key = os.path.normcase(str(change[2]))
            target_groups.setdefault(key, []).append(change)

        collision_keys = {key for key, arr in target_groups.items() if len(arr) > 1}
        if collision_keys:
            kept = []
            for change in changes:
                key = os.path.normcase(str(change[2]))
                if key in collision_keys:
                    item = change[0]
                    item.copy_status = "Névütközés"
                    item.copy_percent = 0
                    item.note = "Több fájl ugyanarra a célra kerülne"
                    failed.append((item, item.note))
                else:
                    kept.append(change)
            changes = kept

        if not changes:
            self.refresh()
            QMessageBox.information(
                self, "Nincs teendő",
                "Nem maradt végrehajtható művelet. A problémás fájlok a listában maradtak."
            )
            return

        # Csak most kérjük a helyet, amikor már tudjuk, mit fogunk ténylegesen másolni.
        if copy_mode:
            try:
                total_bytes = sum(Path(item.path).stat().st_size for item, _, _ in changes)
                free_bytes = shutil.disk_usage(destination).free
            except OSError:
                total_bytes = free_bytes = 0
            if total_bytes and free_bytes and total_bytes > free_bytes:
                ans = QMessageBox.question(
                    self, "A teljes anyag nem fog elférni",
                    f"Szükséges hely: {total_bytes / (1024**3):.1f} GB\n"
                    f"Szabad hely: {free_bytes / (1024**3):.1f} GB\n\n"
                    "A program a teljes videó + felirat párokat addig másolja, amíg van hely.\n"
                    "A már sikeresen átmásolt párok megmaradnak.\n\nFolytatod?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if ans != QMessageBox.StandardButton.Yes:
                    return

        if copy_mode:
            # A nem létező kimeneti mappát automatikusan létrehozzuk.
            try:
                destination.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    "Kimeneti mappa",
                    f"A kimeneti mappát nem sikerült létrehozni:\n{destination}\n\n{exc}"
                )
                return

            summary = self._batch_summary()
            operation_text = "Másolás és átnevezés"
            question = (
                f"{summary['series_count']} sorozat | "
                f"{summary['film_count']} film | "
                f"{summary['season_count']} évad | "
                f"{len(changes)} fájl készül el.\n\n"
                f"Kimenet:\n{destination}\n\n"
                "Az eredeti fájlok változatlanok maradnak.\n\n"
                "Folytatod?"
            )
        else:
            operation_text = "Helyben átnevezés"
            question = (
                f"{len(changes)} fájl neve közvetlenül megváltozik.\n\n"
                "Ez az eredeti fájlokat módosítja.\n\n"
                "Biztosan folytatod?"
            )

        if QMessageBox.question(self, operation_text, question) != QMessageBox.StandardButton.Yes:
            return

        stamp = datetime.now().isoformat(timespec="seconds")
        titles = []
        for item in selected:
            title = item.title.strip()
            if title and title not in titles:
                titles.append(title)
        if not titles and self.title_value.strip():
            titles = [self.title_value.strip()]
        if not titles:
            for item in selected:
                title = item.title.strip()
                if title and title not in titles:
                    titles.append(title)
        history_title = ", ".join(titles[:3])
        if len(titles) > 3:
            history_title += f" + még {len(titles) - 3}"

        record = {
            "time": stamp,
            "operation": operation_text,
            "title": history_title or "Automatikus / vegyes",
            "destination": str(destination) if destination else str(changes[0][1].parent),
            "changes": [],
            "failed": [],
            "status": ""
        }

        current = 0
        total_changes = len(changes)
        progress_label = "Másolás" if copy_mode else "Átnevezés"
        self.cancel_requested = False
        self._set_cancel_enabled(True)
        self._progress_start(total_changes, progress_label)

        try:
            while current < total_changes:
                if self.cancel_requested:
                    for remaining_item, _, _ in changes[current:]:
                        remaining_item.copy_status = "Megszakítva"
                        remaining_item.copy_percent = 0
                        remaining_item.note = "A felhasználó megszakította a műveletet"
                        failed.append((remaining_item, remaining_item.note))
                    break

                item, _, _ = changes[current]
                pair_key = item.group or f"{item.title}|{item.season}|{item.episode}"
                pair = []
                j = current
                while j < total_changes:
                    other = changes[j][0]
                    other_key = other.group or f"{other.title}|{other.season}|{other.episode}"
                    if other_key != pair_key:
                        break
                    pair.append(changes[j])
                    j += 1

                # Egy pár csak akkor indulhat el, ha mindkét tag elfér.
                if copy_mode:
                    pair_size = sum(p.stat().st_size for _, p, _ in pair if p.exists())
                    free_now = shutil.disk_usage(destination).free
                    if pair_size and free_now < pair_size:
                        for pair_item, _, _ in pair:
                            pair_item.copy_status = "Nem fért el"
                            pair_item.copy_percent = 0
                            pair_item.note = "A teljes videó + felirat pár nem fért el"
                            failed.append((pair_item, pair_item.note))
                        current += len(pair)
                        self._progress_step(current, total_changes, progress_label, "Nem fért el – következő pár")
                        continue

                pair_created = []
                pair_backups = []
                pair_renames = []
                pending_history = []
                pair_failed = False

                for pair_item, old_path, new_path in pair:
                    pair_item.copy_status = "Másolás..." if copy_mode else "Átnevezés..."
                    pair_item.copy_percent = 0
                    self._update_copy_row(pair_item)

                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        if copy_mode:
                            def _on_copy_progress(copied, total_size, _item=pair_item):
                                _item.copy_percent = min(99, int(copied * 100 / total_size))
                                self._update_copy_row(_item)

                            stat = copy_to_destination(
                                old_path, new_path, progress=_on_copy_progress
                            )
                            pending_history.append({
                                "old": str(old_path),
                                "new": str(new_path),
                                "action": "copy",
                                "size": stat.st_size,
                                "mtime_ns": stat.st_mtime_ns
                            })
                            pair_created.append(new_path)
                        else:
                            old_path.rename(new_path)
                            pair_renames.append((old_path, new_path))
                            pending_history.append({
                                "old": str(old_path),
                                "new": str(new_path),
                                "action": "rename"
                            })
                    except OSError as exc:
                        pair_failed = True
                        try:
                            tmp = Path(str(new_path) + ".part")
                            if tmp.exists():
                                tmp.unlink()
                        except OSError:
                            pass
                        pair_item.copy_status = "Nem fért el" if getattr(exc, "winerror", None) == 112 else "Hiba"
                        pair_item.copy_percent = 0
                        pair_item.note = str(exc)
                        self._update_copy_row(pair_item)
                        break

                if pair_failed:
                    # A már létrehozott célfájlokat visszavesszük.
                    rollback_copied_files(pair_created)
                    # Helyben átnevezésnél visszanevezzük az addig elkészült tagokat.
                    rollback_renamed_files(pair_renames)
                    for pair_item, _, _ in pair:
                        if pair_item.copy_status == "Másolás..." or pair_item.copy_status == "Átnevezés...":
                            pair_item.copy_status = "Hiba"
                            pair_item.copy_percent = 0
                            pair_item.note = "A videó + felirat pár visszaállítva"
                        failed.append((pair_item, pair_item.note or "A teljes pár visszaállítva"))
                        pair_item.path = str(next((old for it, old, _ in pair if it is pair_item), Path(pair_item.path)))
                    current += len(pair)
                    self._progress_step(current, total_changes, progress_label, "Pár visszaállítva")
                    continue

                # A pár csak most tekinthető késznek: előzmény + belső állapot egyszerre frissül.
                record["changes"].extend(pending_history)
                for pair_item, old_path, new_path in pair:
                    pair_item.path = str(new_path)
                    pair_item.status = "Kész"
                    pair_item.copy_status = "Átmásolva" if copy_mode else "Kész"
                    pair_item.copy_percent = 100
                    pair_item.note = ""
                    self._update_copy_row(pair_item)

                current += len(pair)
                self._progress_step(current, total_changes, progress_label, Path(pair[-1][2]).name)

                if self.cancel_requested and current < total_changes:
                    for remaining_item, _, _ in changes[current:]:
                        remaining_item.copy_status = "Megszakítva"
                        remaining_item.copy_percent = 0
                        remaining_item.note = "A felhasználó megszakította a műveletet"
                        failed.append((remaining_item, remaining_item.note))
                    break

            if current >= total_changes:
                self._progress_finish()
            else:
                self._progress_step(current, total_changes, progress_label, "Hátralévő fájlok")

        except Exception as exc:
            self._set_cancel_enabled(False)
            self.cancel_requested = False
            if hasattr(self, "progress_bar"):
                self.progress_bar.hide()
            QMessageBox.critical(
                self, "Műveleti hiba",
                f"A művelet nem fejeződött be.\n\n{exc}"
            )
            return

        was_cancelled = self.cancel_requested
        self._set_cancel_enabled(False)
        self.cancel_requested = False

        record["failed"] = [
            {"file": str(self._source_path(item)), "reason": reason}
            for item, reason in failed
        ]
        if was_cancelled:
            record["status"] = "Megszakítva"
        elif failed:
            record["status"] = "Részben elkészült"
        else:
            record["status"] = "Sikeres"
        if record["changes"] or record["failed"]:
            self.history.append(record)
            self.save_history()

        self.refresh()
        self.update_history_view()

        message = f'{len(record["changes"])} fájl elkészült.'
        if failed:
            message += f"\n\n{len(failed)} fájl kimaradt."
        if was_cancelled:
            message = "A feladatot megszakítottad.\n\n" + message
        if copy_mode:
            message += (
                f"\n\nKimenet:\n{destination}"
                "\n\nAz eredeti fájlok változatlanok maradtak."
            )
        if failed and any("már létezett" in reason for _, reason in failed):
            message += "\nA már létező célfájlokat nem módosítottuk."

        QMessageBox.information(self, "Művelet vége", message)

    # ---------- history ----------

    def _history_path(self):
        return self.data_dir / "history.json"

    def load_history(self):
        """Betölti a korábbi műveleteket. Hibás/hiányzó fájl esetén üres előzményből indul."""
        path = self._history_path()
        if not path.exists():
            self.history = []
            self.history_selected_keys.clear()
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.history = data if isinstance(data, list) else []
        except (OSError, ValueError, TypeError):
            self.history = []
        self.history_selected_keys.clear()

    def save_history(self):
        """Elmenti az előzményeket tartósan az alkalmazás adatkönyvtárába."""
        path = self._history_path()
        try:
            path.write_text(
                json.dumps(self.history, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Előzmények mentése",
                f"Az előzményeket nem sikerült elmenteni:\n{exc}"
            )

    def update_history_view(self):
        if not hasattr(self, "hist"):
            return

        self.hist.setRowCount(0)
        for index, record in enumerate(self.history, start=1):
            row = self.hist.rowCount()
            self.hist.insertRow(row)
            key = self._history_key(record)

            check = QCheckBox()
            check.setChecked(key in self.history_selected_keys)
            check.stateChanged.connect(
                lambda state, k=key: self._history_checkbox_changed(k, state)
            )
            holder = QWidget()
            hl = QHBoxLayout(holder)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hl.addWidget(check)
            self.hist.setCellWidget(row, 0, holder)

            operation = record.get("operation", "Átnevezés")
            title = record.get("title", "Ismeretlen")
            destination = record.get("destination", "")
            count = len(record.get("changes", []))
            failed_count = len(record.get("failed", []))
            status = record.get("status", "")
            result_text = f"{count} kész" if failed_count == 0 else f"{count} kész / {failed_count} kimaradt"
            if status:
                result_text += f" — {status}"

            values = [
                str(index), record.get("time", ""), operation, title,
                result_text, destination
            ]
            for column, value in enumerate(values, start=1):
                cell = QTableWidgetItem(value)
                if status in {"Visszavonva", "Megszakítva", "Hiba"} and column == 3:
                    cell.setForeground(QColor("#b71c1c"))
                    cell.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                self.hist.setItem(row, column, cell)
        self.hist.resizeRowsToContents()

    def _history_checkbox_changed(self, key, state):
        if state == Qt.CheckState.Checked.value:
            self.history_selected_keys.add(key)
        else:
            self.history_selected_keys.discard(key)

    def history_select_all(self):
        self.history_selected_keys = {self._history_key(r) for r in self.history}
        self.update_history_view()

    def history_clear_selection(self):
        self.history_selected_keys.clear()
        self.update_history_view()

    def _selected_history_indices(self):
        return [i for i, r in enumerate(self.history) if self._history_key(r) in self.history_selected_keys]

    def delete_selected_history(self):
        indices = self._selected_history_indices()
        if not indices:
            QMessageBox.information(self, "Nincs kijelölve", "Jelölj ki legalább egy előzményt.")
            return
        if QMessageBox.question(
            self, "Kijelölt előzmények törlése",
            f"Biztosan törlöd a kijelölt {len(indices)} előzményt?\n\n"
            "Ez csak az előzménybejegyzéseket törli, a fájlokat nem állítja vissza és nem törli."
        ) != QMessageBox.StandardButton.Yes:
            return
        for idx in reversed(indices):
            del self.history[idx]
        self.history_selected_keys.clear()
        self.save_history()
        self.update_history_view()

    def undo_selected(self):
        indices = self._selected_history_indices()
        if len(indices) != 1:
            QMessageBox.information(
                self, "Egy előzmény szükséges",
                "A visszaállításhoz pontosan egy előzményt jelölj ki."
            )
            return
        row = indices[0]
        if row >= len(self.history):
            return
        record = self.history[row]
        operation = record.get("operation", "Átnevezés")
        changes = record.get("changes", [])

        if record.get("status") == "Visszavonva":
            QMessageBox.information(self, "Már visszavonva", "Ez a művelet már vissza lett állítva.")
            return

        if operation == "Másolás és átnevezés":
            copy_check = verify_copy_undo(changes)
            if copy_check is not None:
                kind, path = copy_check
                if kind == "missing":
                    QMessageBox.critical(self, "Visszaállítás nem biztonságos", "A kimeneti fájlok állapota megváltozott, ezért a műveletet nem hajtottam végre.")
                else:
                    QMessageBox.critical(self, "Visszaállítás nem biztonságos", f"A fájl időközben megváltozott:\n{path}\n\nA program nem törölte.")
                return
            if QMessageBox.question(self, "Kimenet visszaállítása", f"{len(changes)} létrehozott fájl törlésére készülsz.\n\nAz eredeti fájlokat ez nem érinti.\n\nFolytatod?") != QMessageBox.StandardButton.Yes:
                return
            apply_copy_undo(changes)
        else:
            if not verify_inplace_undo(changes):
                QMessageBox.critical(self, "Visszaállítás nem biztonságos", "A fájlállapot megváltozott, ezért a műveletet nem hajtottam végre.")
                return
            apply_inplace_undo(changes)

        def path_key(value):
            try:
                return os.path.normcase(str(Path(value).resolve()))
            except OSError:
                return os.path.normcase(str(Path(value)))

        for item in self.items:
            item_keys = {
                path_key(item.path),
                path_key(self._source_path(item)),
            }
            restored = None
            for change in changes:
                if (
                    path_key(change["new"]) in item_keys
                    or path_key(change["old"]) in item_keys
                ):
                    restored = change["old"]
                    break
            if restored is None:
                src = self._source_path(item)
                if src.is_file() and not Path(item.path).is_file():
                    restored = str(src)
            if restored is None:
                continue
            item.path = restored
            item.copy_status = "Várakozik"
            item.copy_percent = 0
            item.note = ""

        record["status"] = "Visszavonva"
        self.save_history()
        self.update_history_view()
        self.refresh()
        QMessageBox.information(self, "Kész", "A kiválasztott művelet visszaállítva. Az előzmény megmaradt, Visszavonva állapotban.")

    def clear_history(self):
        if QMessageBox.question(self, "Összes előzmény törlése", "Biztosan törlöd az összes előzményt?") == QMessageBox.StandardButton.Yes:
            self.history = []
            self.history_selected_keys.clear()
            self.save_history()
            self.update_history_view()

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Előzmények exportálása",
            "",
            "JSON (*.json);;TXT (*.txt);;CSV (*.csv)"
        )

        if not path:
            return

        ext = Path(path).suffix.lower()

        if ext == ".json":
            Path(path).write_text(
                json.dumps(
                    self.history,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

        elif ext == ".txt":
            blocks = []
            for record in self.history:
                blocks.append(
                    f"Időpont: {record.get('time', '')}\n"
                    f"Művelet: {record.get('operation', '')}\n"
                    f"Sorozat / film: {record.get('title', '')}\n"
                    f"Hely: {record.get('destination', '')}\n"
                    f"Fájlok: {len(record.get('changes', []))}\n"
                    f"Kimaradt: {len(record.get('failed', []))}\n"
                    + "\n".join(
                        f"  {change['old']} -> {change['new']}"
                        for change in record.get("changes", [])
                    )
                )
            Path(path).write_text(
                "\n\n".join(blocks),
                encoding="utf-8"
            )

        else:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow([
                    "time", "operation", "title", "destination",
                    "old", "new"
                ])

                for record in self.history:
                    for change in record.get("changes", []):
                        writer.writerow([
                            record.get("time", ""),
                            record.get("operation", ""),
                            record.get("title", ""),
                            record.get("destination", ""),
                            change.get("old", ""),
                            change.get("new", "")
                        ])


    # ---------- 0.6.0-TEST / Tesztlabor ----------

    def open_test_lab(self):
        """Tesztlabor — csak DEV. Release/frozen buildben no-op."""
        if not dev_tools_enabled():
            return
        from testing.test_runner import TestRunnerDialog
        dialog = TestRunnerDialog(self)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        self._test_lab_dialog = dialog

    def open_patch_center(self):
        """Helyi Patch Center — csak DEV. Release/frozen: nincs Python-futtatás a GUI-ból."""
        if not dev_tools_enabled():
            return
        dialog = PatchCenterDialog(self)
        dialog.exec()

    # ---------- first run / help ----------

    def first_run_welcome(self):
        if not self.show_welcome:
            return

        dialog = WelcomeDialog(
            self,
            language=self.language,
            show_again=self.show_welcome
        )
        result = dialog.exec()

        self.language = dialog.selected_language
        self.show_welcome = not dialog.dont_show.isChecked()
        self.save_settings(silent=True)
        self.update_language_buttons()

        if result == 2:
            self.show_help()

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Súgó – {APP_NAME} v{APP_VERSION}"
        )
        dialog.resize(780, 620)

        layout = QVBoxLayout(dialog)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            f"{APP_NAME} – Súgó\n"
            f"Verzió: {APP_VERSION}\n\n"
            "ELSŐ LÉPÉSEK\n"
            "1. Mappa hozzáadása vagy Fájlok hozzáadása.\n"
            "2. Ellenőrizd az Előnézetet.\n"
            "3. A bizonytalan eseteket a program nem nevezi át automatikusan.\n"
            "4. Az Átnevezés csak a problémamentes, kijelölt elemeket dolgozza fel.\n\n"
            "SOROZAT MÓD\n"
            "A program az S01E01 vagy 1x01 formátumú epizódazonosítókat "
            "biztonságosan felismeri. A puszta E05 formátumot szándékosan "
            "nem fogadja el automatikusan.\n\n"
            "FILM MÓD\n"
            "Film esetén nincs évad- és epizódkövetelmény.\n\n"
            "FONTOS\n"
            "A program nem írja át a fájlok tartalmát, csak a fájlneveket módosítja."
        )
        layout.addWidget(text)

        close = QPushButton("Bezárás")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    # ---------- appearance / help menu ----------

    def set_appearance(self, value):
        if value not in ("Világos", "Sötét"):
            value = "Világos"

        self.appearance = value

        if value == "Sötét":
            palette = QPalette()
            palette.setColor(QPalette.ColorRole.Window, QColor(35, 35, 35))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(235, 235, 235))
            palette.setColor(QPalette.ColorRole.Base, QColor(28, 28, 28))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
            palette.setColor(QPalette.ColorRole.Text, QColor(235, 235, 235))
            palette.setColor(QPalette.ColorRole.Button, QColor(55, 55, 55))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(235, 235, 235))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 110, 180))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
            QApplication.instance().setPalette(palette)
        else:
            QApplication.instance().setPalette(
                QApplication.style().standardPalette()
            )

        self.update_appearance_buttons()
        if hasattr(self, "sort_combo"):
            self.save_settings(silent=True)

    def update_appearance_buttons(self):
        if not hasattr(self, "light_btn"):
            return
        self.light_btn.setChecked(self.appearance == "Világos")
        self.dark_btn.setChecked(self.appearance == "Sötét")
        style = (
            "QPushButton { background: transparent; border: 1px solid transparent; "
            "border-radius: 6px; padding: 1px; }"
            "QPushButton:hover { background: rgba(128,128,128,35); }"
            "QPushButton:checked { border: 2px solid #666666; "
            "background: rgba(128,128,128,45); }"
        )
        self.light_btn.setStyleSheet(style)
        self.dark_btn.setStyleSheet(style)


    def show_first_steps(self):
        QMessageBox.information(
            self, "Első lépések",
            "1. Adj hozzá egy mappát vagy fájlokat.\n"
            "2. Ellenőrizd az előnézetet.\n"
            "3. A bizonytalan eseteket a program nem nevezi át automatikusan.\n"
            "4. Az Átnevezés csak a problémamentes, kijelölt fájlokat dolgozza fel."
        )

    def show_template_help(self):
        QMessageBox.information(
            self, "Sablonváltozók",
            "Alap változók:\n\n"
            "{CIM} – cím\n"
            "{SZEZON} – évad, például S01\n"
            "{EPIZOD} – epizód, például E01\n\n"
            "Haladó változók:\n\n"
            "{EP} – teljes epizódjelölés, például S01E01\n"
            "{NYELV} – felirat nyelve\n"
            "{EXT} – fájlkiterjesztés pont nélkül\n\n"
            "A kapcsos zárójelek a sablon szintaxisának részei."
        )

    def check_updates(self):
        QMessageBox.information(
            self, "Frissítések keresése",
            f"Jelenlegi verzió: {APP_VERSION}\n\n"
            "Online frissítés-ellenőrzés nincs beépítve. "
            "A program hordozható: a beállítások a program melletti data mappában vannak."
        )

    def report_bug(self):
        QMessageBox.information(
            self, "Hibajelentés",
            "Online hibabejelentő nincs a programban.\n\n"
            "Ha hibát tapasztalsz, jegyezd fel a műveletet és a fájlneveket."
        )

    def donate(self):
        QMessageBox.information(
            self, "Donate",
            "Jelenleg nincs beépített támogatási link."
        )

    def show_about(self):
        QMessageBox.about(
            self, "Névjegy",
            f"{APP_NAME}\n"
            f"v{APP_VERSION}\n\n"
            f"Készítette: {AUTHOR}\n\n"
            "Freeware alkalmazás videó- és feliratfájlok nevének "
            "összehangolásához."
        )

    # ---------- settings ----------

    def update_language_buttons(self):
        if not hasattr(self, "hu_main_btn"):
            return
        self.hu_main_btn.setChecked(self.language == "hu")
        self.en_main_btn.setChecked(self.language == "en")
        style = (
            "QPushButton { background: transparent; border: 1px solid transparent; "
            "border-radius: 6px; padding: 1px; }"
            "QPushButton:hover { background: rgba(128,128,128,35); }"
            "QPushButton:checked { border: 2px solid #666666; "
            "background: rgba(128,128,128,45); }"
        )
        self.hu_main_btn.setStyleSheet(style)
        self.en_main_btn.setStyleSheet(style)

    def set_language(self, language):
        self.language = language
        self.save_settings(silent=True)
        self.update_language_buttons()

    def save_settings(self, silent=False):
        config = {
            "template": self.template_value,
            "title_var": self.title_value,
            "mode": self.mode_value,
            "normalize": self.normalize_cb.isChecked(),
            "lang_norm": self.lang_norm_cb.isChecked(),
            "include_subdirs": self.subdirs_cb.isChecked(),
            "check_conflicts": self.conflicts_cb.isChecked(),
            "preserve_selection": self.preserve_cb.isChecked(),
            "sort_mode": self.sort_combo.currentText(),
            "show_welcome": self.show_welcome,
            "language": self.language,
            "output_mode": self.output_mode,
            "output_dir": self.output_dir,
            "appearance": self.appearance,
            "version": APP_VERSION
        }

        (
            self.data_dir / "settings.json"
        ).write_text(
            json.dumps(
                config,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        if not silent:
            QMessageBox.information(
                self, "Mentve",
                "A beállításokat elmentettem."
            )

    def reset_settings(self):
        self.template_edit.setText(
            "{CIM}.{SZEZON}{EPIZOD}"
        )
        self._set_title_programmatic("", manual=False)
        self.mode_combo.setCurrentText("Sorozat")
        self.normalize_cb.setChecked(True)
        self.lang_norm_cb.setChecked(True)
        self.subdirs_cb.setChecked(False)
        self.conflicts_cb.setChecked(True)
        self.preserve_cb.setChecked(True)
        self.sort_combo.setCurrentText("Évad → epizód")
        self.on_mode_changed()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    window.center_window()

    sys.exit(app.exec())
