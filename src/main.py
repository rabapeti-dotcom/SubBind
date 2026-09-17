import csv
import ctypes
import json
import os
import re
import shutil
import sys
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QSize, QDir, QUrl, QRect, QEvent
from PySide6.QtGui import (
    QFont, QAction, QPalette, QColor, QIcon, QPixmap, QPainter, QPen, QBrush,
    QPainterPath,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QCheckBox, QTextEdit, QMessageBox, QFileDialog,
    QGroupBox, QGridLayout, QDialog, QDialogButtonBox, QMenu, QFrame,
    QAbstractItemView, QHeaderView, QProgressBar, QListView, QTreeView,
    QFileSystemModel, QToolTip, QSizePolicy, QTabBar,
)

from version import APP_NAME, APP_VERSION, AUTHOR
from i18n import (
    MODE_IDS, MODE_KEYS, OUTPUT_IDS, OUTPUT_KEYS, SORT_IDS, SORT_KEYS,
    SUBTITLE_PREF_KEYS,
    t, set_active_language, fill_combo, combo_id, set_combo_id, status_text,
    note_text, hist_op_text, hist_status_text,
    STATUS_DISPLAY_KEYS, STRINGS,
)
from ui_theme import (
    theme_tokens, build_app_stylesheet, copy_state_colors,
    primary_button_stylesheet, filled_button_stylesheet,
    rename_button_stylesheet, plain_button_stylesheet,
    review_button_stylesheet,
)
from renamer_engine import (
    parse_item, ALL_EXTS, common_title, render_template,
    disambiguate_subtitle_target_names, apply_pair_group_status,
    apply_item_target_names, NamingContext,
    apply_destination_conflicts, apply_completion_status,
    destination_matches_output, copy_to_destination,
    rollback_copied_files, rollback_renamed_files,
    verify_copy_undo, apply_copy_undo,
    verify_inplace_undo, apply_inplace_undo,
    DEFAULT_SUBTITLE_PREF, SUBTITLE_PREF_CHOICES, normalize_subtitle_pref,
    is_preferred_plain_sub,
)

DATA_DIR_ENV = "SERIESRENAMER_DATA"

# Fájlok tábla: elsődleges oszlopok elöl, másodlagosak hátul. 10 oszlop marad.
COL_CHECK = 0
COL_ORIG = 1
COL_NEW = 2
COL_STATUS = 3
COL_SERIES = 4
COL_SEASON = 5
COL_EPISODE = 6
COL_TYPE = 7
COL_SIZE = 8
COL_PROGRESS = 9
TABLE_COLS = 10
# Gombfelirat i18n; a beszúrt token a dict kulcsa, változatlan.
TOKEN_BUTTON_KEYS = {
    "{CIM}": ("var.cim", "var.cim_tip"),
    "{SZEZON}": ("var.szezon", "var.szezon_tip"),
    "{EPIZOD}": ("var.epizod", "var.epizod_tip"),
}
COPY_ACTIVE_STATES = {
    "Másolás...", "Átnevezés...", "Átmásolva", "Kész",
    "Már létezik", "Névütközés", "Nem egyező pár", "Hiba",
    "Nem fért el", "Megszakítva",
}


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
DEV_ENV = "SERIESRENAMER_DEV"


def _env_flag_on(name):
    flag = str(os.environ.get(name, "") or "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def dev_tools_enabled():
    """Tesztlabor / Patch: csak explicit DEV mód (run_dev.bat / SERIESRENAMER_DEV).

    Normál GUI, frozen exe és SERIESRENAMER_RELEASE=1: rejtve. A funkció megmarad.
    """
    if getattr(sys, "frozen", False):
        return False
    if _env_flag_on(RELEASE_ENV):
        return False
    return _env_flag_on(DEV_ENV)


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


def _win_pick_folders(hwnd, title, start_dir):
    """Natív Windows mappaválasztó: egy vagy több mappa (IFileOpenDialog).

    Sikeres választás: Path lista. Mégsem: üres lista. COM-hiba: None (Qt tartalék).
    """
    if sys.platform != "win32":
        return None
    ole32 = ctypes.WinDLL("ole32")
    shell32 = ctypes.WinDLL("shell32")
    ole32.CoInitialize.restype = ctypes.HRESULT
    ole32.CoInitialize(None)

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    def _guid(text):
        value = GUID()
        ole32.CLSIDFromString.restype = ctypes.HRESULT
        hr = ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(value))
        if hr:
            raise OSError(hr)
        return value

    try:
        clsid = _guid("{DC1C5A9C-E88A-4DDE-A5A1-60F82A20AEF7}")
        iid_dlg = _guid("{D57C7288-D4AD-4768-BE02-9D969532D960}")
        iid_item = _guid("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
    except OSError:
        return None

    HRESULT = ctypes.HRESULT
    LPVOID = ctypes.c_void_p
    ULONG = ctypes.c_ulong
    dialog = LPVOID()
    ole32.CoCreateInstance.restype = HRESULT
    hr = ole32.CoCreateInstance(
        ctypes.byref(clsid), None, 1, ctypes.byref(iid_dlg), ctypes.byref(dialog)
    )
    if hr or not dialog.value:
        return None

    vtbl = ctypes.cast(dialog, ctypes.POINTER(ctypes.POINTER(LPVOID))).contents

    def _fn(index, restype, *argtypes):
        proto = ctypes.WINFUNCTYPE(restype, LPVOID, *argtypes)
        return proto(vtbl[index])

    FOS_PICKFOLDERS = 0x20
    FOS_ALLOWMULTISELECT = 0x200
    FOS_FORCEFILESYSTEM = 0x40
    SIGDN_FILESYSPATH = 0x80058000
    ERROR_CANCELLED = 0x800704C7

    try:
        _fn(17, HRESULT, ctypes.c_wchar_p)(dialog, title or "")
        options = ULONG(0)
        _fn(10, HRESULT, ctypes.POINTER(ULONG))(dialog, ctypes.byref(options))
        options.value |= FOS_PICKFOLDERS | FOS_ALLOWMULTISELECT | FOS_FORCEFILESYSTEM
        _fn(9, HRESULT, ULONG)(dialog, options)
        if start_dir and Path(start_dir).is_dir():
            folder_item = LPVOID()
            shell32.SHCreateItemFromParsingName.restype = HRESULT
            shr = shell32.SHCreateItemFromParsingName(
                ctypes.c_wchar_p(str(Path(start_dir))),
                None,
                ctypes.byref(iid_item),
                ctypes.byref(folder_item),
            )
            if not shr and folder_item.value:
                _fn(12, HRESULT, LPVOID)(dialog, folder_item)
                _fn(2, ULONG)(folder_item)
        hr = _fn(3, HRESULT, LPVOID)(dialog, LPVOID(hwnd or 0))
        unsigned = ctypes.c_ulong(hr).value if not isinstance(hr, int) else (hr & 0xFFFFFFFF)
        if unsigned == ERROR_CANCELLED:
            return []
        if hr:
            return None
        results = LPVOID()
        hr = _fn(27, HRESULT, ctypes.POINTER(LPVOID))(dialog, ctypes.byref(results))
        if hr or not results.value:
            return []
        arr_vtbl = ctypes.cast(results, ctypes.POINTER(ctypes.POINTER(LPVOID))).contents

        def _arr(index, restype, *argtypes):
            proto = ctypes.WINFUNCTYPE(restype, LPVOID, *argtypes)
            return proto(arr_vtbl[index])

        count = ULONG(0)
        _arr(7, HRESULT, ctypes.POINTER(ULONG))(results, ctypes.byref(count))
        folders = []
        for i in range(count.value):
            item = LPVOID()
            if _arr(8, HRESULT, ULONG, ctypes.POINTER(LPVOID))(
                results, i, ctypes.byref(item)
            ) or not item.value:
                continue
            item_vtbl = ctypes.cast(item, ctypes.POINTER(ctypes.POINTER(LPVOID))).contents
            get_name = ctypes.WINFUNCTYPE(
                HRESULT, LPVOID, ctypes.c_int, ctypes.POINTER(ctypes.c_wchar_p)
            )(item_vtbl[5])
            name_ptr = ctypes.c_wchar_p()
            if not get_name(item, SIGDN_FILESYSPATH, ctypes.byref(name_ptr)) and name_ptr.value:
                folders.append(Path(name_ptr.value))
                ole32.CoTaskMemFree(name_ptr)
            ctypes.WINFUNCTYPE(ULONG, LPVOID)(item_vtbl[2])(item)
        ctypes.WINFUNCTYPE(ULONG, LPVOID)(arr_vtbl[2])(results)
        return folders
    except (OSError, ValueError, AttributeError):
        return None
    finally:
        ctypes.WINFUNCTYPE(ULONG, LPVOID)(vtbl[2])(dialog)


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


def show_test_version_mark():
    """Test Version 2 jelölés: frozen / release buildben nem jelenik meg."""
    if getattr(sys, "frozen", False):
        return False
    if _env_flag_on(RELEASE_ENV):
        return False
    return True


def _set_qss_state(widget, name, value):
    if widget is None:
        return
    widget.setProperty(name, value)
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _i18n_max_px(fm, *keys):
    """Legszélesebb HU/EN felirat pixelben. Layout-ugrás elkerülésére."""
    widest = 0
    for key in keys:
        found = False
        for lang in ("hu", "en"):
            text = (STRINGS.get(lang) or {}).get(key)
            if text is None:
                continue
            found = True
            widest = max(widest, fm.horizontalAdvance(str(text)))
        if not found:
            widest = max(widest, fm.horizontalAdvance(str(key)))
    return widest


def _i18n_map_max_px(fm, key_map):
    return _i18n_max_px(fm, *key_map.values())


class _StableTabBar(QTabBar):
    """Tab szélesség a hosszabb HU/EN felirathoz igazodik, nyelvváltáskor nem ugrik."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min_widths = {}

    def set_min_widths(self, widths):
        self._min_widths = dict(widths or {})
        self.updateGeometry()

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        minimum = self._min_widths.get(index, 0)
        if minimum:
            size.setWidth(max(size.width(), int(minimum)))
        return size


def make_theme_toggle_icon(dark=False):
    """Kompakt fél-világos / fél-sötét kör. Nincs nap, hold, kapcsoló vagy felirat."""
    light_tok = theme_tokens(False)
    dark_tok = theme_tokens(True)
    pix = QPixmap(28, 26)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    cx, cy, r = 14, 13, 11
    disc = QRect(cx - r, cy - r, r * 2, r * 2)

    clip = QPainterPath()
    clip.addEllipse(disc)
    painter.setClipPath(clip)
    painter.fillRect(cx - r, cy - r, r, r * 2, QColor(light_tok["surface"]))
    painter.fillRect(cx, cy - r, r, r * 2, QColor(dark_tok["window"]))
    painter.setClipping(False)

    rim = QColor(dark_tok["window_rim"] if dark else light_tok["border_strong"])
    painter.setPen(QPen(rim, 1))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(disc)
    painter.end()
    return QIcon(pix)


def format_confirm_preview_text(changes, copy_mode):
    """Megerősítő lista: névváltás vs. másolás azonos néven. Nem indít I/O-t."""
    blocks = []
    shown = changes[:12]
    for _item, old_path, new_path in shown:
        old_name = Path(old_path).name
        new_name = Path(new_path).name
        if copy_mode and old_name == new_name:
            blocks.append(t("confirm.copy_same", name=old_name))
        else:
            blocks.append(t("confirm.rename_pair", old=old_name, new=new_name))
    extra = len(changes) - len(shown)
    if extra > 0:
        blocks.append(t("confirm.more", n=extra))
    return "\n\n".join(blocks)


def subtitle_ext_label(ext):
    return (ext or "").lstrip(".").upper()


def is_ui_primary_sub(item, pref="hu"):
    """Csak megjelenítés. Nem nyúl selected / pairing / feldolgozáshoz."""
    return is_preferred_plain_sub(item, pref)


def lang_ui_name(code):
    if not code:
        return t("sub.lang_none")
    return t(f"lang.{code}")


def subtitle_meta_text(item, pref="hu"):
    parts = [
        lang_ui_name(getattr(item, "lang", None)),
        subtitle_ext_label(getattr(item, "ext", "")),
    ]
    variant = str(getattr(item, "variant", None) or "").strip()
    if variant:
        parts.append(variant)
    if is_ui_primary_sub(item, pref):
        parts.append(t("sub.primary"))
    return " · ".join(parts)


def type_cell_text(item, pref="hu"):
    kind = getattr(item, "kind", "")
    if kind == "video":
        return t("kind.video")
    if kind == "sub":
        return subtitle_meta_text(item, pref)
    return t("kind.other")


def item_search_extra(item, pref="hu"):
    """GUI szűrő-haystack. A parser/motor keresését nem érinti."""
    parts = [type_cell_text(item, pref)]
    if getattr(item, "kind", "") != "sub":
        return " ".join(parts)
    ext = subtitle_ext_label(getattr(item, "ext", ""))
    if ext:
        parts.append(ext)
        parts.append(ext.lower())
    code = getattr(item, "lang", None)
    if code:
        parts.append(code)
        for table in STRINGS.values():
            name = table.get(f"lang.{code}")
            if name:
                parts.append(name)
    else:
        parts.append("—")
    variant = str(getattr(item, "variant", None) or "").strip()
    if variant:
        parts.append(variant)
    if is_ui_primary_sub(item, pref):
        parts.append(STRINGS["hu"].get("sub.primary", ""))
        parts.append(STRINGS["en"].get("sub.primary", ""))
    return " ".join(p for p in parts if p)


class StartConfirmDialog(QDialog):
    """Átnevezés előtti összefoglaló. Nem indít műveletet, csak megerősít."""

    def __init__(self, parent, changes, copy_mode, destination):
        super().__init__(parent)
        self.setWindowTitle(t("confirm.title"))
        self.setModal(True)
        self.setMinimumWidth(520)
        self.resize(560, 460)

        videos = sum(1 for item, _, _ in changes if item.kind == "video")
        subs = sum(1 for item, _, _ in changes if item.kind == "sub")

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(10)

        title = QLabel(t("confirm.title"))
        title.setObjectName("welcomeHeadline")
        title.setStyleSheet("font-size: 14pt; font-weight: 700;")
        title.setWordWrap(True)
        root.addWidget(title)

        counts = QLabel(
            t("confirm.files", n=len(changes))
            + "\n"
            + t("meta.av_counts", videos=videos, subs=subs)
        )
        counts.setStyleSheet("font-size: 11pt;")
        root.addWidget(counts)
        self.counts_label = counts

        preview_box = QGroupBox(t("confirm.preview"))
        preview_layout = QVBoxLayout(preview_box)
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setMinimumHeight(140)
        preview.setPlainText(format_confirm_preview_text(changes, copy_mode))
        preview_layout.addWidget(preview)
        self.preview = preview
        self.preview = preview
        root.addWidget(preview_box)

        op = QLabel(t("confirm.op_copy" if copy_mode else "confirm.op_inplace"))
        op.setStyleSheet("font-weight: 600;")
        op.setWordWrap(True)
        root.addWidget(op)

        if copy_mode and destination:
            folder = QLabel(t("confirm.target", path=str(destination)))
            folder.setWordWrap(True)
            root.addWidget(folder)

        note = QLabel(t("confirm.keep" if copy_mode else "confirm.change"))
        parent_win = parent if parent is not None else None
        dark = bool(
            parent_win is not None
            and getattr(parent_win, "appearance", "Világos") == "Sötét"
        )
        tok = theme_tokens(dark)
        if copy_mode:
            note.setStyleSheet(
                f"color: {tok['success']}; font-weight: 600;"
            )
        else:
            note.setStyleSheet(
                f"color: {tok['danger']}; font-weight: 600; padding: 8px; "
                f"background: {tok['danger_soft']}; border: 1px solid {tok['danger']}; "
                f"border-radius: 6px;"
            )
        note.setWordWrap(True)
        root.addWidget(note)
        self.note_label = note

        buttons = QDialogButtonBox()
        cancel_btn = buttons.addButton(
            t("confirm.cancel"), QDialogButtonBox.ButtonRole.RejectRole
        )
        start_btn = buttons.addButton(
            t("confirm.start"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        start_btn.setDefault(True)
        start_btn.setObjectName("btnSuccess")
        start_btn.setStyleSheet(filled_button_stylesheet(tok, "success"))
        cancel_btn.clicked.connect(self.reject)
        start_btn.clicked.connect(self.accept)
        root.addWidget(buttons)


class WelcomeDialog(QDialog):
    def __init__(self, parent=None, language="hu", show_again=True):
        super().__init__(parent)
        self.setMinimumSize(780, 600)
        self.resize(800, 620)
        self.setModal(True)
        self.selected_language = language

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 20)
        root.setSpacing(12)

        top = QHBoxLayout()
        self.kicker = QLabel()
        self.kicker.setObjectName("welcomeKicker")
        top.addWidget(self.kicker)
        top.addStretch(1)
        self.language_label = QLabel()
        top.addWidget(self.language_label)
        self.hu_btn = QPushButton()
        self.en_btn = QPushButton()
        self.hu_btn.setIcon(make_flag_icon("hu"))
        self.en_btn.setIcon(make_flag_icon("en"))
        self.hu_btn.setIconSize(QSize(28, 20))
        self.en_btn.setIconSize(QSize(28, 20))
        for btn in (self.hu_btn, self.en_btn):
            btn.setCheckable(True)
            btn.setFixedSize(42, 32)
            top.addWidget(btn)
        self.hu_btn.clicked.connect(lambda: self.select_language("hu"))
        self.en_btn.clicked.connect(lambda: self.select_language("en"))
        root.addLayout(top)

        self.headline = QLabel()
        self.headline.setObjectName("welcomeHeadline")
        self.headline.setWordWrap(True)
        root.addWidget(self.headline)

        self.intro = QLabel()
        self.intro.setObjectName("welcomeIntro")
        self.intro.setWordWrap(True)
        root.addWidget(self.intro)

        self.example = QGroupBox()
        self.example.setObjectName("exampleCard")
        ex_layout = QHBoxLayout(self.example)
        ex_layout.setContentsMargins(14, 16, 14, 12)
        ex_layout.setSpacing(12)

        orig_col = QVBoxLayout()
        orig_col.setSpacing(4)
        self.example_original = QLabel()
        self.example_original.setObjectName("exampleHeading")
        orig_col.addWidget(self.example_original)
        self.ex_orig_video = QLabel()
        self.ex_orig_sub = QLabel()
        for lab in (self.ex_orig_video, self.ex_orig_sub):
            lab.setObjectName("monoSample")
            lab.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            orig_col.addWidget(lab)
        orig_col.addStretch(1)
        ex_layout.addLayout(orig_col, 1)

        arrow = QLabel("→")
        arrow.setObjectName("arrowLabel")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ex_layout.addWidget(arrow)

        new_col = QVBoxLayout()
        new_col.setSpacing(4)
        self.example_new = QLabel()
        self.example_new.setObjectName("exampleHeading")
        new_col.addWidget(self.example_new)
        self.ex_new_video = QLabel()
        self.ex_new_sub = QLabel()
        for lab in (self.ex_new_video, self.ex_new_sub):
            lab.setObjectName("monoSample")
            lab.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            new_col.addWidget(lab)
        new_col.addStretch(1)
        ex_layout.addLayout(new_col, 1)
        root.addWidget(self.example)

        self.note = QLabel()
        self.note.setObjectName("welcomeNote")
        self.note.setWordWrap(True)
        root.addWidget(self.note)

        root.addStretch(1)

        bottom = QHBoxLayout()
        self.dont_show = QCheckBox()
        bottom.addWidget(self.dont_show)
        bottom.addStretch(1)

        self.first_btn = QPushButton()
        self.first_btn.clicked.connect(self.open_help)
        bottom.addWidget(self.first_btn)

        self.ok_btn = QPushButton()
        self.ok_btn.setObjectName("btnPrimary")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept)
        dark = (
            parent is not None
            and getattr(parent, "appearance", "Világos") == "Sötét"
        )
        self.ok_btn.setStyleSheet(primary_button_stylesheet(theme_tokens(dark)))
        bottom.addWidget(self.ok_btn)

        root.addLayout(bottom)
        self.select_language(language)

    def retranslate(self):
        self.setWindowTitle(t("welcome.title"))
        self.kicker.setText(t("welcome.kicker"))
        self.headline.setText(t("welcome.headline"))
        self.intro.setText(t("welcome.intro"))
        self.example.setTitle(t("welcome.example"))
        self.example_original.setText(t("welcome.original"))
        self.example_new.setText(t("welcome.new_name"))
        self.ex_orig_video.setText(t("welcome.ex_orig_video"))
        self.ex_orig_sub.setText(t("welcome.ex_orig_sub"))
        self.ex_new_video.setText(t("welcome.ex_new_video"))
        self.ex_new_sub.setText(t("welcome.ex_new_sub"))
        self.note.setText(t("welcome.note"))
        self.language_label.setText(t("welcome.language"))
        self.hu_btn.setToolTip(t("tip.hu"))
        self.en_btn.setToolTip(t("tip.en"))
        self.dont_show.setText(t("welcome.dont_show"))
        self.first_btn.setText(t("welcome.first"))
        self.ok_btn.setText(t("welcome.ok"))

    def select_language(self, language):
        self.selected_language = language
        set_active_language(language)
        self.hu_btn.setChecked(language == "hu")
        self.en_btn.setChecked(language == "en")
        self.retranslate()

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
        self.setWindowTitle(t("patch.title"))
        self.resize(760, 520)
        self.setModal(True)

        self.base_dir = Path(__file__).resolve().parent.parent
        self.patch_dir = self.base_dir / "patches"
        self.patch_dir.mkdir(parents=True, exist_ok=True)

        root = QVBoxLayout(self)

        title = QLabel(t("patch.heading"))
        title.setStyleSheet("font-size: 15pt; font-weight: 700;")
        root.addWidget(title)

        info = QLabel(t("patch.info"))
        info.setWordWrap(True)
        root.addWidget(info)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel(t("patch.folder")))
        self.path_edit = QLineEdit(str(self.patch_dir))
        self.path_edit.setReadOnly(True)
        path_row.addWidget(self.path_edit, 1)
        open_folder = QPushButton(t("patch.open_folder"))
        open_folder.clicked.connect(self.open_patch_folder)
        path_row.addWidget(open_folder)
        root.addLayout(path_row)

        self.list = QTableWidget(0, 3)
        self.list.setHorizontalHeaderLabels([
            t("patch.col_name"), t("patch.col_size"), t("patch.col_status"),
        ])
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
        self.log.setPlaceholderText(t("patch.log_ph"))
        self.log.setMinimumHeight(130)
        root.addWidget(self.log)

        buttons = QHBoxLayout()
        refresh = QPushButton(t("patch.scan"))
        refresh.clicked.connect(self.scan_patches)
        buttons.addWidget(refresh)

        self.run_btn = QPushButton(t("patch.run"))
        self.run_btn.setEnabled(False)
        self.run_btn.setStyleSheet(
            "QPushButton { background: #6a1b9a; color: white; "
            "font-weight: bold; padding: 7px 12px; }"
            "QPushButton:hover { background: #4a126d; }"
            "QPushButton:disabled { background: #bdbdbd; color: #666; }"
        )
        self.run_btn.clicked.connect(self.run_selected_patch)
        buttons.addWidget(self.run_btn)

        close = QPushButton(t("help.close"))
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
            self.log.setPlainText(t("patch.none", path=self.patch_dir))
            self.update_buttons()
            return

        for path in files:
            row = self.list.rowCount()
            self.list.insertRow(row)

            name = QTableWidgetItem(path.name)
            size = QTableWidgetItem(f"{path.stat().st_size / 1024:.1f} KB")
            status = QTableWidgetItem(t("patch.available"))

            self.list.setItem(row, 0, name)
            self.list.setItem(row, 1, size)
            self.list.setItem(row, 2, status)

        self.log.setPlainText(t("patch.found", n=len(files)))
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
            QMessageBox.warning(self, t("patch.no_sel_title"), t("patch.no_sel"))
            return

        answer = QMessageBox.question(
            self,
            t("patch.run_title"),
            t("patch.run_body", name=patch_path.name),
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
            self.log.setPlainText(t("patch.timeout", name=patch_path.name))
            self.run_btn.setEnabled(True)
            return
        except OSError as exc:
            self.log.setPlainText(t("patch.start_fail", exc=exc))
            self.run_btn.setEnabled(True)
            return

        output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
        self.log.setPlainText(output.strip() or t("patch.no_output"))

        if completed.returncode != 0:
            QMessageBox.critical(
                self,
                t("patch.err_title"),
                t("patch.err_body", code=completed.returncode, output=output[-3000:]),
            )
            self.scan_patches()
            return

        self.scan_patches()

        answer = QMessageBox.question(
            self,
            t("patch.ok_title"),
            t("patch.ok_body"),
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
                t("patch.restart_title"),
                t("patch.restart_fail", exc=exc)
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
        self._rename_busy = False
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
        self.show_review_only = False
        self._last_folder = str(Path.home())
        self.sort_mode_value = "Évad → epizód"
        self.language = "hu"
        self.subtitle_pref = DEFAULT_SUBTITLE_PREF
        self.show_welcome = True
        self.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.output_dir = ""
        self.appearance = "Világos"
        self.advanced_mode = False

        self._load_ui_preferences()
        set_active_language(self.language)
        self.title_value = ""
        self.title_manual = False

        intended_template = self.template_value

        self.build_ui()
        self.apply_ui_language()
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
        self.subtitle_pref = normalize_subtitle_pref(
            config.get("subtitle_pref", DEFAULT_SUBTITLE_PREF)
        )
        self.show_welcome = config.get("show_welcome", True)
        self.output_mode = config.get(
            "output_mode",
            "Másolás kimeneti mappába és átnevezés"
        )
        self.output_dir = config.get("output_dir", "")
        self.appearance = config.get("appearance", "Világos")
        if "advanced_mode" in config:
            # Régi settings kulcs: ne okozzon hibát; a UI-t nem vezérli.
            self.advanced_mode = bool(config.get("advanced_mode"))

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
        central.setObjectName("centralRoot")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 8, 10, 6)
        root.setSpacing(8)

        accent = QFrame()
        accent.setObjectName("accentBar")

        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar_layout = QVBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        top_bar_layout.addWidget(accent)

        top = QHBoxLayout()
        top.setContentsMargins(8, 6, 8, 6)
        top.setSpacing(8)
        top_bar_layout.addLayout(top)

        self.add_btn = QPushButton(t("btn.add"))
        self.add_btn.setObjectName("btnPrimary")
        self.add_btn.setMinimumHeight(36)
        self.add_menu = QMenu(self)
        self.add_files_act = self.add_menu.addAction(t("menu.add_files"))
        self.add_files_act.triggered.connect(self.add_files)
        self.add_folder_act = self.add_menu.addAction(t("menu.add_folder"))
        self.add_folder_act.triggered.connect(self.add_folder_native)
        self.add_btn.setMenu(self.add_menu)
        top.addWidget(self.add_btn)

        self.clear_btn = QPushButton(t("btn.clear_list"))
        self.clear_btn.clicked.connect(self.clear_list)
        self.check_btn = QPushButton(t("btn.check"))
        self.check_btn.clicked.connect(self.check)
        self.refresh_preview_btn = QPushButton(t("btn.refresh_preview"))
        self.refresh_preview_btn.clicked.connect(lambda: self.refresh(reanalyze=True))

        file_cluster = QFrame()
        file_cluster.setObjectName("toolbarCluster")
        file_cluster_layout = QHBoxLayout(file_cluster)
        file_cluster_layout.setContentsMargins(4, 3, 4, 3)
        file_cluster_layout.setSpacing(4)
        file_cluster_layout.addWidget(self.clear_btn)
        file_cluster_layout.addWidget(self.check_btn)
        file_cluster_layout.addWidget(self.refresh_preview_btn)
        top.addWidget(file_cluster)

        if dev_tools_enabled():
            # 0.6.0-TEST: ideiglenes Tesztlabor — csak DEV / teszt futtatás.
            self.test_lab_btn = QPushButton(t("btn.testlab"))
            self.test_lab_btn.setObjectName("btnDev")
            self.test_lab_btn.setToolTip(t("tip.testlab"))
            self.test_lab_btn.clicked.connect(self.open_test_lab)
            top.addWidget(self.test_lab_btn)

            # 0.6.1-TEST: helyi Patch Center — csak DEV / teszt futtatás.
            self.patch_btn = QPushButton(t("btn.patch"))
            self.patch_btn.setObjectName("btnMuted")
            self.patch_btn.setToolTip(t("tip.patch"))
            self.patch_btn.clicked.connect(self.open_patch_center)
            top.addWidget(self.patch_btn)

        self.help_btn = QPushButton(t("btn.help"))
        help_menu = QMenu(self)

        self.help_guide_act = help_menu.addAction(t("menu.help"))
        self.help_guide_act.triggered.connect(self.show_help)
        self.first_steps_act = help_menu.addAction(t("menu.first_steps"))
        self.first_steps_act.triggered.connect(self.show_first_steps)
        self.template_help_act = help_menu.addAction(t("menu.template_vars"))
        self.template_help_act.triggered.connect(self.show_template_help)

        help_menu.addSeparator()

        self.updates_act = help_menu.addAction(t("menu.updates"))
        self.updates_act.triggered.connect(self.check_updates)
        self.bug_act = help_menu.addAction(t("menu.bug"))
        self.bug_act.triggered.connect(self.report_bug)
        self.donate_act = help_menu.addAction(t("menu.donate"))
        self.donate_act.triggered.connect(self.donate)

        help_menu.addSeparator()

        self.about_act = help_menu.addAction(t("menu.about"))
        self.about_act.triggered.connect(self.show_about)

        self.help_btn.setMenu(help_menu)
        top.addWidget(self.help_btn)

        for btn in (
            self.clear_btn, self.check_btn, self.refresh_preview_btn, self.help_btn
        ):
            btn.setMinimumHeight(32)

        action_frame = QFrame()
        action_frame.setObjectName("renameFrame")
        action_frame.setFrameShape(QFrame.Shape.StyledPanel)
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(4, 4, 4, 4)

        self.rename_btn = QPushButton(t("btn.rename"))
        self.rename_btn.setObjectName("btnRename")
        self.rename_btn.setMinimumSize(150, 38)
        self.rename_btn.clicked.connect(self.rename)
        action_layout.addWidget(self.rename_btn)
        self.rename_frame = action_frame
        self.rename_btn.installEventFilter(self)
        self.rename_frame.installEventFilter(self)
        top.addWidget(action_frame)

        # Jobb felső sarok: téma-kapcsoló és nyelv. A feliratok tooltipként jelennek meg.
        top.addStretch(1)

        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeToggle")
        self.theme_btn.setIconSize(QSize(28, 26))
        self.theme_btn.setFixedSize(34, 30)
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_appearance)
        top.addWidget(self.theme_btn)
        self.update_appearance_buttons()

        self.hu_main_btn = QPushButton()
        self.en_main_btn = QPushButton()
        self.hu_main_btn.setIcon(make_flag_icon("hu"))
        self.en_main_btn.setIcon(make_flag_icon("en"))
        self.hu_main_btn.setToolTip(t("tip.hu"))
        self.en_main_btn.setToolTip(t("tip.en"))
        lang_cluster = QFrame()
        lang_cluster.setObjectName("iconCluster")
        lang_cluster.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        lang_cluster.setFixedHeight(30)
        lang_layout = QHBoxLayout(lang_cluster)
        lang_layout.setContentsMargins(2, 0, 2, 0)
        lang_layout.setSpacing(2)
        for btn in (self.hu_main_btn, self.en_main_btn):
            btn.setCheckable(True)
            btn.setFixedSize(30, 28)
            btn.setIconSize(QSize(22, 16))
            lang_layout.addWidget(btn)
        top.addWidget(lang_cluster)
        top.setAlignment(self.theme_btn, Qt.AlignmentFlag.AlignVCenter)
        top.setAlignment(lang_cluster, Qt.AlignmentFlag.AlignVCenter)
        self.hu_main_btn.clicked.connect(lambda: self.set_language("hu"))
        self.en_main_btn.clicked.connect(lambda: self.set_language("en"))
        self.update_language_buttons()

        root.addWidget(top_bar)

        self.tabs = QTabWidget()
        self.tabs.setTabBar(_StableTabBar())
        root.addWidget(self.tabs, 1)

        self.files_tab = QWidget()
        self.settings_tab = QWidget()
        self.preview_tab = QWidget()
        self.history_tab = QWidget()

        self.tabs.addTab(self.files_tab, t("tab.files"))
        self.tabs.addTab(self.settings_tab, t("tab.settings"))
        self.tabs.addTab(self.preview_tab, t("tab.preview"))
        self.tabs.addTab(self.history_tab, t("tab.history"))

        self.build_files()
        self.build_settings()
        self.build_preview()
        self.build_history()
        self.tabs.currentChanged.connect(self._on_main_tab_changed)

        footer = QFrame()
        footer.setObjectName("footerBar")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 4, 10, 4)
        self.footer_name = QLabel(APP_NAME)
        footer_layout.addWidget(self.footer_name)
        self.footer_badge = QLabel(t("footer.test_version"))
        self.footer_badge.setObjectName("testBadge")
        self.footer_badge.setVisible(show_test_version_mark())
        footer_layout.addWidget(self.footer_badge)
        footer_layout.addStretch(1)
        self.footer_meta = QLabel(f"v{APP_VERSION}  •  {AUTHOR}")
        self.footer_meta.setObjectName("mutedLabel")
        footer_layout.addWidget(self.footer_meta)
        footer_layout.addSpacing(18)

        self.footer_bug_btn = QPushButton(t("btn.bug"))
        self.footer_bug_btn.setFlat(True)
        self.footer_bug_btn.clicked.connect(self.report_bug)
        footer_layout.addWidget(self.footer_bug_btn)

        self.footer_donate_btn = QPushButton(t("btn.donate"))
        self.footer_donate_btn.setFlat(True)
        self.footer_donate_btn.clicked.connect(self.donate)
        footer_layout.addWidget(self.footer_donate_btn)

        root.addWidget(footer)

        status_row = QHBoxLayout()

        self.status_label = QLabel(t("status.zero"))
        self.status_label.setObjectName("mutedLabel")
        self.status_label.setFrameShape(QFrame.Shape.NoFrame)
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

        self.cancel_btn = QPushButton(t("btn.cancel"))
        self.cancel_btn.setObjectName("btnDanger")
        self.cancel_btn.setMinimumHeight(30)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.request_cancel)
        status_row.addWidget(self.cancel_btn)

        root.addLayout(status_row)
        self.set_appearance(self.appearance)
        self._stabilize_i18n_geometry()

    def build_files(self):
        layout = QVBoxLayout(self.files_tab)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(8)

        self.guide_banner = QLabel()
        self.guide_banner.setWordWrap(True)
        self.guide_banner.setTextFormat(Qt.TextFormat.RichText)
        self.guide_banner.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.guide_banner)

        tools = QHBoxLayout()
        tools.setSpacing(6)

        self.filter_edit = QLineEdit()
        self.filter_edit.setObjectName("searchField")
        self.filter_edit.setPlaceholderText(t("files.search_ph"))
        self.filter_edit.setMinimumWidth(180)
        self.filter_edit.textChanged.connect(
            lambda *_: self.refresh(reanalyze=False)
        )
        tools.addWidget(self.filter_edit, 1)

        self.search_btn = QPushButton(t("files.search"))
        self.search_btn.clicked.connect(lambda: self.refresh(reanalyze=False))
        tools.addWidget(self.search_btn)

        self.sort_label = QLabel(t("files.sort"))
        tools.addWidget(self.sort_label)

        self.sort_combo = QComboBox()
        for ident in SORT_IDS:
            self.sort_combo.addItem(ident, ident)
        set_combo_id(self.sort_combo, self.sort_mode_value)
        self.sort_combo.currentIndexChanged.connect(
            lambda *_: self.refresh(reanalyze=False)
        )
        tools.addWidget(self.sort_combo)

        self.select_all_files_btn = QPushButton(t("files.select_all"))
        self.select_all_files_btn.clicked.connect(lambda: self.set_all(True))
        tools.addWidget(self.select_all_files_btn)

        self.deselect_files_btn = QPushButton(t("files.deselect"))
        self.deselect_files_btn.clicked.connect(lambda: self.set_all(False))
        tools.addWidget(self.deselect_files_btn)

        self.remove_selected_btn = QPushButton(t("files.remove_selected"))
        self.remove_selected_btn.clicked.connect(self.remove_selected)
        self.remove_selected_btn.setToolTip(t("tip.remove_selected"))
        tools.addWidget(self.remove_selected_btn)

        self.select_review_btn = QPushButton(t("files.select_review"))
        self.select_review_btn.setToolTip(t("tip.select_review"))
        self.select_review_btn.clicked.connect(self.select_review_items)
        tools.addWidget(self.select_review_btn)
        self.show_review_only_btn = QPushButton(t("files.show_review_only"))
        self.show_review_only_btn.setObjectName("showReviewOnly")
        self.show_review_only_btn.setCheckable(True)
        self.show_review_only_btn.setChecked(False)
        self.show_review_only_btn.setToolTip(t("tip.show_review_only"))
        self.show_review_only_btn.toggled.connect(self._on_show_review_only_toggled)
        tools.addWidget(self.show_review_only_btn)
        for btn in (
            self.search_btn, self.select_all_files_btn, self.deselect_files_btn,
            self.remove_selected_btn, self.select_review_btn,
            self.show_review_only_btn,
        ):
            btn.setMinimumHeight(30)

        layout.addLayout(tools)

        self.detect_banner = QLabel()
        self.detect_banner.setObjectName("detectBanner")
        self.detect_banner.setWordWrap(True)
        self.detect_banner.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self.detect_banner)

        self.empty_panel = QWidget()
        empty_layout = QVBoxLayout(self.empty_panel)
        empty_layout.setContentsMargins(0, 8, 0, 8)
        self.empty_state = QLabel(t("files.empty"))
        self.empty_state.setObjectName("emptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setWordWrap(True)
        self.empty_state.setMinimumHeight(88)
        empty_layout.addWidget(self.empty_state)
        self.empty_add_btn = QPushButton(t("btn.add_folder_cta"))
        self.empty_add_btn.setObjectName("btnPrimary")
        self.empty_add_btn.setMinimumHeight(40)
        self.empty_add_btn.clicked.connect(self.add_folder_native)
        empty_layout.addWidget(self.empty_add_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_panel)

        self.output_box = QGroupBox(t("output.box"))
        output_layout = QGridLayout(self.output_box)
        self.output_grid = output_layout

        self.output_action_label = QLabel(t("output.action"))
        output_layout.addWidget(self.output_action_label, 0, 0)

        self.output_mode_combo = QComboBox()
        for ident in OUTPUT_IDS:
            self.output_mode_combo.addItem(ident, ident)
        if self.output_mode in OUTPUT_IDS:
            set_combo_id(self.output_mode_combo, self.output_mode)
        self.output_mode_combo.currentIndexChanged.connect(self.on_output_mode_changed)
        output_layout.addWidget(self.output_mode_combo, 0, 1, 1, 2)

        self.output_folder_label = QLabel(t("output.folder"))
        output_layout.addWidget(self.output_folder_label, 1, 0)

        self.output_edit = QLineEdit(self.output_dir)
        self.output_edit.setPlaceholderText(t("output.folder_ph"))
        self.output_edit.textChanged.connect(self.on_output_dir_changed)
        output_layout.addWidget(self.output_edit, 1, 1)

        self.output_browse_btn = QPushButton(t("output.browse"))
        self.output_browse_btn.clicked.connect(self.choose_output_dir)
        output_layout.addWidget(self.output_browse_btn, 1, 2)

        self.output_hint = QLabel()
        self.output_hint.setWordWrap(True)
        self.output_hint.setTextFormat(Qt.TextFormat.RichText)
        self.output_hint.setMinimumHeight(42)
        output_layout.addWidget(self.output_hint, 2, 0, 1, 3)

        layout.addWidget(self.output_box)

        self.table = QTableWidget(0, TABLE_COLS)
        self.table.setHorizontalHeaderLabels(self._table_headers())
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
        header.setToolTip(t("tip.table_check"))
        header.setSectionResizeMode(COL_CHECK, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(COL_ORIG, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_NEW, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        for col in (COL_SERIES, COL_SEASON, COL_EPISODE, COL_TYPE, COL_SIZE, COL_PROGRESS):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(40)
        self.table.setColumnWidth(COL_ORIG, 280)
        self.table.setColumnWidth(COL_NEW, 240)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)

        layout.addWidget(self.table)
        self.table.setVisible(False)
        self.empty_panel.setVisible(True)

        self.on_output_mode_changed(self.output_mode_combo.currentText())


    def build_settings(self):
        layout = QVBoxLayout(self.settings_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.settings_intro = QLabel(t("settings.intro"))
        self.settings_intro.setObjectName("settingsIntro")
        self.settings_intro.setWordWrap(True)
        layout.addWidget(self.settings_intro)

        self.naming_heading = QLabel(t("settings.naming_box"))
        self.naming_heading.setObjectName("sectionHeading")
        layout.addWidget(self.naming_heading)

        left = QWidget()
        grid = QGridLayout(left)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        self.settings_grid = grid

        self.mode_label = QLabel(t("mode.label"))
        grid.addWidget(self.mode_label, 0, 0)

        self.mode_combo = QComboBox()
        fill_combo(self.mode_combo, MODE_IDS, MODE_KEYS)
        set_combo_id(self.mode_combo, self.mode_value)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        grid.addWidget(self.mode_combo, 0, 1)

        self.name_label = QLabel(t("name.series"))
        grid.addWidget(self.name_label, 1, 0)

        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._title_changed)
        grid.addWidget(self.title_edit, 1, 1)

        self.detected_box = QGroupBox(t("detect.box"))
        detected_layout = QVBoxLayout(self.detected_box)
        self.detected_series_label = QLabel(t("detect.none"))
        self.detected_series_label.setObjectName("mutedLabel")
        self.detected_series_label.setWordWrap(True)
        detected_layout.addWidget(self.detected_series_label)
        grid.addWidget(self.detected_box, 1, 2, 2, 1)

        self.template_label = QLabel(t("template.label"))
        grid.addWidget(self.template_label, 2, 0)

        self.template_edit = QLineEdit(self.template_value)
        self.template_edit.textChanged.connect(self._template_changed)
        grid.addWidget(self.template_edit, 2, 1)

        self.base_vars_label = QLabel(t("vars.base"))
        grid.addWidget(self.base_vars_label, 3, 0)

        var_frame = QWidget()
        var_layout = QHBoxLayout(var_frame)
        var_layout.setContentsMargins(0, 0, 0, 0)

        self.var_buttons = {}
        for value, (text_key, tip_key) in TOKEN_BUTTON_KEYS.items():
            b = QPushButton(t(text_key))
            b.setToolTip(t(tip_key))
            b.clicked.connect(lambda checked=False, x=value: self.insert_var(x))
            var_layout.addWidget(b)
            self.var_buttons[value] = b

        grid.addWidget(var_frame, 3, 1)

        self.default_template_label = QLabel(t("tpl.series"))
        self.default_template_label.setObjectName("mutedLabel")
        grid.addWidget(self.default_template_label, 4, 1)

        self.subtitle_pref_label = QLabel(t("pref.label"))
        grid.addWidget(self.subtitle_pref_label, 5, 0)
        self.subtitle_pref_combo = QComboBox()
        fill_combo(self.subtitle_pref_combo, SUBTITLE_PREF_CHOICES, SUBTITLE_PREF_KEYS)
        set_combo_id(self.subtitle_pref_combo, self.subtitle_pref)
        self.subtitle_pref_combo.currentIndexChanged.connect(self._on_subtitle_pref_changed)
        grid.addWidget(self.subtitle_pref_combo, 5, 1)

        self.advanced_box = QGroupBox()
        self.advanced_box.setCheckable(False)
        self.advanced_box.setFlat(False)
        adv_layout = QVBoxLayout(self.advanced_box)

        self.normalize_cb = QCheckBox(t("adv.normalize"))
        self.lang_norm_cb = QCheckBox(t("adv.lang_norm"))
        self.subdirs_cb = QCheckBox(t("adv.subdirs"))
        self.conflicts_cb = QCheckBox(t("adv.conflicts"))
        self.preserve_cb = QCheckBox(t("adv.preserve"))

        self.normalize_cb.setChecked(bool(self.normalize_value))
        self.subdirs_cb.setChecked(bool(self.include_subdirs_value))
        self.conflicts_cb.setChecked(bool(self.check_conflicts_value))
        self.preserve_cb.setChecked(True)

        for cb in [
            self.normalize_cb, self.lang_norm_cb, self.subdirs_cb,
            self.conflicts_cb, self.preserve_cb
        ]:
            adv_layout.addWidget(cb)

        self.adv_vars_label = QLabel(t("adv.vars"))
        self.adv_vars_label.setObjectName("mutedLabel")
        self.adv_vars_label.setWordWrap(True)
        adv_layout.addWidget(self.adv_vars_label)
        grid.addWidget(self.advanced_box, 6, 0, 1, 2)

        button_row = QHBoxLayout()
        self.save_settings_btn = QPushButton(t("btn.save_settings"))
        self.save_settings_btn.clicked.connect(self.save_settings)
        button_row.addWidget(self.save_settings_btn)

        self.refresh_list_btn = QPushButton(t("btn.refresh_list"))
        self.refresh_list_btn.setToolTip(t("tip.refresh_list"))
        self.refresh_list_btn.clicked.connect(self.refresh)
        button_row.addWidget(self.refresh_list_btn)

        self.reset_settings_btn = QPushButton(t("btn.reset_settings"))
        self.reset_settings_btn.clicked.connect(self.reset_settings)
        button_row.addWidget(self.reset_settings_btn)
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
        self.select_all_btn = QPushButton(t("preview.select_all"))
        self.select_none_btn = QPushButton(t("preview.select_none"))
        self.select_missing_btn = QPushButton(t("preview.select_missing"))
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

        self.history_info = QLabel()
        self.history_info.setWordWrap(True)
        layout.addWidget(self.history_info)

        self.hist = QTableWidget(0, 7)
        self.hist.setHorizontalHeaderLabels([
            t("hist.check"), t("hist.num"), t("hist.time"), t("hist.op"),
            t("hist.title"), t("hist.files"), t("hist.place"),
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
        self.hist_select_all_btn = QPushButton(t("hist.select_all"))
        self.hist_select_all_btn.clicked.connect(self.history_select_all)
        buttons.addWidget(self.hist_select_all_btn)
        self.hist_deselect_btn = QPushButton(t("hist.deselect"))
        self.hist_deselect_btn.clicked.connect(self.history_clear_selection)
        buttons.addWidget(self.hist_deselect_btn)
        self.hist_delete_btn = QPushButton(t("hist.delete"))
        self.hist_delete_btn.clicked.connect(self.delete_selected_history)
        buttons.addWidget(self.hist_delete_btn)
        buttons.addSpacing(12)
        self.hist_undo_btn = QPushButton(t("hist.undo"))
        self.hist_undo_btn.setObjectName("btnDanger")
        self.hist_undo_btn.clicked.connect(self.undo_selected)
        buttons.addWidget(self.hist_undo_btn)
        self.hist_failed_btn = QPushButton(t("hist.failed"))
        self.hist_failed_btn.clicked.connect(self.show_selected_history_failures)
        buttons.addWidget(self.hist_failed_btn)
        self.hist_export_btn = QPushButton(t("hist.export"))
        self.hist_export_btn.clicked.connect(self.export_history)
        buttons.addWidget(self.hist_export_btn)
        buttons.addStretch(1)
        self.hist_clear_btn = QPushButton(t("hist.clear"))
        self.hist_clear_btn.clicked.connect(self.clear_history)
        buttons.addWidget(self.hist_clear_btn)
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
            self.mode_value = combo_id(self.mode_combo) or self.mode_value

        film_only = self.mode_value == "Film"
        mixed = self.mode_value == "Automatikus / Vegyes"

        if film_only:
            self.name_label.setText(t("name.movie"))
            self.base_vars_label.setText(t("vars.base"))
            self.default_template_label.setText(t("tpl.movie"))
            self.var_buttons["{SZEZON}"].setVisible(False)
            self.var_buttons["{EPIZOD}"].setVisible(False)
            if self.template_value == "{CIM}.{SZEZON}{EPIZOD}":
                self.template_edit.setText("{CIM}")
        elif mixed:
            self.name_label.setText(t("name.mixed"))
            self.base_vars_label.setText(t("vars.series"))
            self.default_template_label.setText(t("tpl.mixed"))
            self.var_buttons["{SZEZON}"].setVisible(True)
            self.var_buttons["{EPIZOD}"].setVisible(True)
            if self.template_value == "{CIM}":
                self.template_edit.setText("{CIM}.{SZEZON}{EPIZOD}")
        else:
            self.name_label.setText(t("name.series"))
            self.base_vars_label.setText(t("vars.base"))
            self.default_template_label.setText(t("tpl.series"))
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
        dialog.setWindowTitle(t("dlg.add_folders_title"))
        dialog.resize(760, 560)

        root = QVBoxLayout(dialog)
        info = QLabel(t("dlg.add_folders_info"))
        info.setWordWrap(True)
        root.addWidget(info)

        path_row = QHBoxLayout()
        path_row.addWidget(QLabel(t("dlg.location")))
        start = self._last_folder if Path(self._last_folder).is_dir() else str(Path.home())
        path_edit = QLineEdit(start)
        path_edit.setPlaceholderText(t("dlg.path_ph"))
        path_row.addWidget(path_edit, 1)
        go_btn = QPushButton(t("dlg.open"))
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

        selected_label = QLabel(t("dlg.selected_folders", n=0))
        root.addWidget(selected_label)

        def update_count():
            count = len(tree.selectionModel().selectedRows(0))
            selected_label.setText(t("dlg.selected_folders", n=count))

        tree.selectionModel().selectionChanged.connect(lambda *_: update_count())

        def navigate():
            path = Path(path_edit.text().strip().strip('"'))
            if path.is_dir():
                tree.setRootIndex(model.index(str(path)))
            else:
                QMessageBox.warning(
                    dialog, t("dlg.invalid_folder_title"),
                    t("dlg.invalid_folder", path=path),
                )

        go_btn.clicked.connect(navigate)
        path_edit.returnPressed.connect(navigate)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=dialog
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("dlg.add"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("dlg.cancel"))
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
                QMessageBox.information(
                    dialog, t("dlg.none_selected_title"), t("dlg.none_selected_folders")
                )
                return
            dialog.selected_folders = folders
            dialog.accept()

        buttons.accepted.connect(accept_selection)
        buttons.rejected.connect(dialog.reject)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._add_folders_from_list(getattr(dialog, "selected_folders", []))

    def _add_folders_from_list(self, folders):
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
                t("msg.no_files_title"),
                t("msg.no_files_folders"),
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
        dialog.setWindowTitle(t("dlg.add_folder_title"))
        dialog.resize(560, 140)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(t("dlg.add_folder_info")))
        row = QHBoxLayout()
        start = self._last_folder if Path(self._last_folder).is_dir() else str(Path.home())
        path_edit = QLineEdit(start)
        path_edit.setPlaceholderText(t("dlg.path_example"))
        row.addWidget(path_edit, 1)
        browse = QPushButton(t("dlg.browse"))
        row.addWidget(browse)
        layout.addLayout(row)

        def browse_native():
            chosen = QFileDialog.getExistingDirectory(
                dialog, t("dlg.pick_folder"), path_edit.text().strip() or start
            )
            if chosen:
                path_edit.setText(chosen)

        browse.clicked.connect(browse_native)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok,
            parent=dialog
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(t("dlg.add"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("dlg.cancel"))
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
                self, t("dlg.invalid_folder_title"),
                t("dlg.invalid_folder", path=folder),
            )
            return None
        self._last_folder = str(folder)
        return folder

    def _pick_source_folders(self):
        """Natív Windows mappaválasztó; Mégsem: üres lista."""
        start = self._last_folder if Path(self._last_folder).is_dir() else str(Path.home())
        title = t("dlg.pick_folder")
        hwnd = int(self.winId()) if self.winId() else 0
        picked = _win_pick_folders(hwnd, title, start)
        if picked is None:
            chosen = QFileDialog.getExistingDirectory(self, title, start)
            if not chosen:
                return []
            return [Path(chosen)]
        return [path for path in picked if path.is_dir()]

    def add_folder_native(self):
        """Üres CTA és menü: közvetlenül a natív mappaválasztó, köztes ablak nélkül."""
        folders = self._pick_source_folders()
        if not folders:
            return
        self._last_folder = str(folders[-1])
        if len(folders) == 1:
            self._add_folder_from_path(folders[0])
            return
        self._add_folders_from_list(folders)

    def add_folder(self):
        self.add_folder_native()

    def _add_folder_from_path(self, root):
        recursive = self.subdirs_cb.isChecked()
        paths = list(self._iter_folder_files(root, recursive))

        if not paths and not recursive:
            answer = QMessageBox.question(
                self,
                t("msg.no_direct_title"),
                t("msg.no_direct"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                paths = list(self._iter_folder_files(root, True))

        if not paths:
            QMessageBox.information(
                self,
                t("msg.no_files_title"),
                t("msg.no_files_folder", path=root),
            )
            return

        self.add_paths(paths)

    def add_files(self):
        start = self._last_folder if Path(self._last_folder).is_dir() else ""
        extensions = " ".join("*" + x for x in sorted(ALL_EXTS))
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            t("dlg.pick_files"),
            start,
            f"{t('dlg.files_filter', exts=extensions)};;{t('dlg.all_files')}"
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
                t("msg.path_missing_title"),
                t("msg.path_missing", paths="\n".join(str(x) for x in missing[:8])),
            )
            return
        if not collected:
            QMessageBox.information(
                self,
                t("msg.no_files_title"),
                t("msg.no_files_drop"),
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
                self._set_status(t("status.added", added=added, total=len(self.items)))
            elif paths:
                self._set_status(t("status.none_added"))

    # ---------- output ----------

    def on_output_mode_changed(self, mode=None):
        ident = combo_id(self.output_mode_combo) if hasattr(self, "output_mode_combo") else ""
        if ident:
            self.output_mode = ident
        copy_mode = self.output_mode == "Másolás kimeneti mappába és átnevezés"

        self.output_edit.setEnabled(copy_mode)
        self.output_browse_btn.setEnabled(copy_mode)

        if copy_mode:
            self.output_hint.setText(t("output.hint_copy"))
        else:
            self.output_hint.setText(t("output.hint_inplace"))
        self._style_output_hint()

        # A build során ez a jelzés már lefuthat azelőtt, hogy
        # a beállítási vezérlők létrejönnének.
        if hasattr(self, "normalize_cb"):
            self.save_settings(silent=True)
        self.update_action_state()

    def _theme(self):
        return theme_tokens(getattr(self, "appearance", "Világos") == "Sötét")

    def _style_output_hint(self):
        """Kimeneti súgó stílusa. A helyben-figyelmeztetés szövege változatlan,
        vizuálisan a vezető sáv alatt marad."""
        if not hasattr(self, "output_hint"):
            return
        tok = self._theme()
        copy_mode = self.output_mode == "Másolás kimeneti mappába és átnevezés"
        ready = (
            hasattr(self, "guide_banner")
            and getattr(self, "items", None)
            and self._guided_state() == "ready"
        )
        if copy_mode:
            self.output_hint.setStyleSheet(
                f"QLabel {{ border: 1px solid {tok['success']}; border-radius: 8px; "
                f"padding: 8px 11px; background: {tok['success_soft']}; "
                f"color: {tok['success']}; font-weight: 400; }}"
            )
            return
        if ready:
            self.output_hint.setStyleSheet(
                f"QLabel {{ border: 1px solid {tok['danger']}; border-radius: 8px; "
                f"padding: 6px 10px; background: {tok['danger_soft']}; "
                f"color: {tok['text_secondary']}; font-weight: 400; font-size: 9.5pt; }}"
            )
            return
        self.output_hint.setStyleSheet(
            f"QLabel {{ border: 1px solid {tok['danger']}; border-radius: 8px; "
            f"padding: 6px 10px; background: {tok['danger_soft']}; "
            f"color: {tok['danger']}; font-weight: 400; font-size: 9.5pt; }}"
        )

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
            return t("msg.output_empty")

        try:
            destination = Path(self.output_dir).resolve()
        except OSError:
            return t("msg.output_invalid")

        if destination.exists() and not destination.is_dir():
            return t("msg.output_not_dir")

        source_parents = {self._source_path(i).resolve().parent for i in selected}
        if destination in source_parents:
            return t("msg.output_same")

        return ""

    def _table_headers(self):
        return [
            t("table.check"), t("table.original"), t("table.new_name"),
            t("table.status"), t("table.series"), t("table.season"),
            t("table.episode"), t("table.type"), t("table.size"),
            t("table.progress"),
        ]

    def _status_cell_text(self, item):
        """Állapot oszlop: felhasználói szöveg. item.status nem változik."""
        copy_state = self._copy_state(item)
        if copy_state in COPY_ACTIVE_STATES and copy_state not in STATUS_DISPLAY_KEYS:
            return status_text(copy_state)
        display_key = STATUS_DISPLAY_KEYS.get(item.status or "")
        if display_key:
            return t(display_key)
        if copy_state in COPY_ACTIVE_STATES:
            return status_text(copy_state)
        review = self._review_kind(item)
        return t(
            "review.ok" if review == "ok"
            else "review.blocked" if review == "blocked"
            else "review.needs"
        )

    def _row_tooltip(self, item, orig_name, src_path):
        mark = self._status_cell_text(item)
        size_text = format_size_bytes(getattr(item, "size_bytes", None))
        exact = getattr(item, "size_bytes", None)
        size_line = f"{size_text}" + (f" ({exact} B)" if exact is not None else "")
        ep = "—"
        if item.season is not None and item.episode is not None:
            ep = f"S{item.season:02d}E{item.episode:02d}"
        copy_state = status_text(self._copy_state(item))
        note = self._visible_note(item)
        lines = [
            mark,
            orig_name,
            src_path,
            f"{item.title.strip() or '—'}  {ep}",
            size_line,
            f"{t('table.copy_state')}: {copy_state}",
        ]
        if item.kind == "sub":
            variant = str(getattr(item, "variant", None) or "").strip()
            lines.extend([
                t("tip.lang", lang=lang_ui_name(getattr(item, "lang", None))),
                t("tip.format", fmt=subtitle_ext_label(item.ext)),
                t("tip.variant", variant=variant or t("tip.variant_none")),
                t("tip.primary_yes" if is_ui_primary_sub(item, self.subtitle_pref) else "tip.primary_no"),
            ])
        if note:
            lines.append(note)
        return "\n".join(lines)

    def _visible_note(self, item):
        """Felhasználói note. OK/Kész mellett nem mutat hiányt/problémát.

        A motor `item.note` mezője változatlan (pl. „Nincs sima HU felirat”).
        """
        if (item.status or "") in {"OK", "Kész"}:
            return ""
        return note_text(item.note)

    def _review_kind(self, item):
        """UI-only grouping of existing item.status values. Does not change them."""
        status = item.status or ""
        if item.kind not in ("video", "sub") or status == "Nem támogatott":
            return "blocked"
        if status in {"OK", "Kész"}:
            return "ok"
        return "review"

    def _review_counts(self):
        ok = issues = blocked = 0
        for item in self.items:
            kind = self._review_kind(item)
            if kind == "ok":
                ok += 1
            elif kind == "blocked":
                blocked += 1
            else:
                issues += 1
        return ok, issues, blocked

    def _has_processable_ok(self):
        return any(
            item.selected and item.status == "OK"
            for item in self.items
        )

    def _rename_output_ok(self):
        """A Rename gomb másolásnál kimeneti mappát igényel; helyben nem."""
        return (
            self.output_mode == "Helyben átnevezés"
            or bool(str(getattr(self, "output_dir", "") or "").strip())
        )

    def _is_busy(self):
        if getattr(self, "_rename_busy", False) or getattr(self, "cancel_requested", False):
            return True
        return any(
            getattr(item, "copy_status", "") in {"Másolás...", "Átnevezés..."}
            for item in self.items
        )

    def _all_processed(self):
        media = [i for i in self.items if i.kind in ("video", "sub")]
        if not media:
            return False
        return all(
            i.status == "Kész"
            or getattr(i, "copy_status", "") in {"Átmásolva", "Kész"}
            for i in media
        )

    def _guided_state(self):
        if self._is_busy():
            return "busy"
        if not self.items:
            return "empty"
        if self._all_processed():
            return "done"
        ok, issues, blocked = self._review_counts()
        has_name = any(getattr(i, "new_name", "") for i in self.items)
        if not has_name and ok == 0:
            return "added"
        if issues or blocked:
            return "review"
        if self._has_processable_ok() and self._rename_output_ok():
            return "ready"
        return "preview"

    def _update_guided_workflow(self):
        if not hasattr(self, "guide_banner"):
            return
        state = self._guided_state()
        empty = state == "empty"
        busy = state == "busy"
        primary = state == "ready" and not empty

        self.guide_banner.setText(self._guide_banner_html(state))
        tok = self._theme()
        colors = {
            "empty": (tok["accent_soft"], tok["accent"], tok["accent"]),
            "added": (tok["success_soft"], tok["success"], tok["success"]),
            "preview": (tok["success_soft"], tok["success"], tok["success"]),
            "ready": (tok["success_soft"], tok["success_fill"], tok["success"]),
            "review": (tok["warning_soft"], tok["warning"], tok["warning"]),
            "busy": (tok["surface_alt"], tok["border_strong"], tok["text_secondary"]),
            "done": (tok["success_soft"], tok["success"], tok["success"]),
        }
        bg, border, fg = colors.get(state, colors["empty"])
        if state == "ready":
            self.guide_banner.setStyleSheet(
                f"QLabel {{ padding: 12px 14px; border: 2px solid {border}; "
                f"border-radius: 8px; background: {bg}; color: {fg}; "
                f"font-size: 12pt; font-weight: 600; }}"
            )
        else:
            self.guide_banner.setStyleSheet(
                f"QLabel {{ padding: 10px 12px; border: 1px solid {border}; "
                f"border-radius: 8px; background: {bg}; color: {fg}; "
                f"font-size: 11pt; font-weight: 600; }}"
            )

        has_files = not empty
        for widget in (
            getattr(self, "filter_edit", None),
            getattr(self, "search_btn", None),
            getattr(self, "sort_label", None),
            getattr(self, "sort_combo", None),
            getattr(self, "select_all_files_btn", None),
            getattr(self, "deselect_files_btn", None),
            getattr(self, "remove_selected_btn", None),
        ):
            if widget is not None:
                widget.setEnabled(has_files)
        self._style_output_hint()

        if hasattr(self, "empty_panel"):
            self.empty_panel.setVisible(empty)
        if hasattr(self, "detect_banner"):
            self.detect_banner.setVisible(not empty)
            if not empty:
                self.detect_banner.setText(self._detect_summary_html())
                _set_qss_state(
                    self.detect_banner,
                    "ok",
                    "true" if self._detect_all_pairs_ok() else "false",
                )
        if hasattr(self, "output_box"):
            self.output_box.setVisible(not empty)

        if hasattr(self, "clear_btn"):
            self.clear_btn.setEnabled(not empty)
        if hasattr(self, "check_btn"):
            self.check_btn.setEnabled(not empty)
        if hasattr(self, "select_review_btn"):
            _ok, issues, blocked = self._review_counts()
            has_review = not empty and (issues + blocked) > 0
            self.select_review_btn.setEnabled(has_review)
            self._sync_show_review_only_control(has_review)
        if hasattr(self, "refresh_preview_btn"):
            self.refresh_preview_btn.setEnabled(not empty)
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setVisible(busy or self.cancel_btn.isEnabled())

        copy_ok = self._rename_output_ok()
        can_rename = (not empty) and (not busy) and self._has_processable_ok() and copy_ok
        if hasattr(self, "rename_btn"):
            self.rename_btn.setEnabled(can_rename)
            ready = bool(can_rename and primary)
            _set_qss_state(self.rename_btn, "ready", "true" if ready else "false")
            self.rename_btn.setStyleSheet(rename_button_stylesheet(self._theme(), ready))
            if hasattr(self, "rename_frame"):
                _set_qss_state(self.rename_frame, "ready", "true" if ready else "false")
            self._apply_rename_next_step_tooltip(
                can_rename=can_rename, empty=empty, busy=busy, copy_ok=copy_ok
            )

    def _apply_rename_next_step_tooltip(
        self, can_rename=None, empty=None, busy=None, copy_ok=None
    ):
        """Inaktív Átnevezés: a következő lépést mondja, nem a belső logikát."""
        if not hasattr(self, "rename_btn"):
            return
        if empty is None:
            empty = not self.items
        if busy is None:
            busy = self._is_busy()
        if copy_ok is None:
            copy_ok = self._rename_output_ok()
        if can_rename is None:
            can_rename = (
                (not empty) and (not busy)
                and self._has_processable_ok() and copy_ok
            )
        if can_rename:
            tip = t("tip.rename_ready")
        elif empty:
            tip = t("tip.rename_empty")
        elif busy:
            tip = t("tip.rename_busy")
        elif not copy_ok:
            tip = t("tip.rename_output")
        elif self._all_processed():
            tip = t("tip.rename_done")
        elif not self._has_processable_ok():
            state = self._guided_state()
            if state == "added":
                tip = t("tip.rename_added")
            elif state == "review":
                tip = t("tip.rename_review")
            else:
                tip = t("tip.rename_select")
        else:
            tip = t("tip.rename_output")
        self.rename_btn.setToolTip(tip)
        if hasattr(self, "rename_frame"):
            self.rename_frame.setToolTip(tip)

    def eventFilter(self, obj, event):
        # Disabled QPushButton nem mutat tooltipet; a keret/gomb hoverét itt pótoljuk.
        if event.type() == QEvent.Type.ToolTip and obj in (
            getattr(self, "rename_btn", None),
            getattr(self, "rename_frame", None),
        ):
            tip = self.rename_btn.toolTip() if hasattr(self, "rename_btn") else ""
            if tip:
                QToolTip.showText(event.globalPos(), tip, obj)
                return True
        return super().eventFilter(obj, event)

    def _guide_banner_html(self, state):
        head = t(f"guide.{state}")
        ok, issues, blocked = self._review_counts()
        extra = ""
        if self.items and state not in {"empty", "busy"}:
            issue_n = issues + blocked
            if ok and issue_n:
                extra = (
                    t("guide.counts", ok=ok, issues=issue_n)
                    + " "
                    + t("guide.rename_only_ok")
                )
            elif ok:
                extra = t("guide.counts_ok", ok=ok)
            elif issue_n:
                extra = t("guide.counts_issues", issues=issue_n)
        if extra:
            return f"{head}<br><span style='font-weight:500; font-size:10pt'>{extra}</span>"
        return head

    def _detect_missing_pairs(self):
        videos = [i for i in self.items if i.kind == "video"]
        subs = [i for i in self.items if i.kind == "sub"]
        missing_videos = sum(
            1 for i in videos
            if i.status in {"Felirat nélkül", "Nem egyező pár"}
        )
        missing_subs = sum(
            1 for i in subs
            if i.status in {"Videó nélkül", "Nem egyező pár"}
        )
        return videos, subs, max(missing_videos, missing_subs)

    def _detect_all_pairs_ok(self):
        videos, subs, missing = self._detect_missing_pairs()
        return missing == 0 and bool(videos or subs)

    def _detect_summary_html(self):
        videos, subs, missing = self._detect_missing_pairs()
        episodes = {
            (i.title.strip().lower(), i.season, i.episode)
            for i in videos
            if i.season is not None and i.episode is not None
        }
        names = []
        for item in videos:
            name = item.title.strip()
            if name and name not in names:
                names.append(name)
        title = names[0] if names else (
            self.title_value.strip() if getattr(self, "title_value", "") else t("detect.summary_unknown")
        )
        if len(names) > 1:
            title = ", ".join(names[:3])
            if len(names) > 3:
                title += "…"
        if episodes:
            key = "detect.summary_line_missing" if missing else "detect.summary_line"
            detail = t(
                key,
                episodes=len(episodes),
                videos=len(videos),
                subs=len(subs),
                missing=missing,
            )
        else:
            key = "detect.summary_line_movie_missing" if missing else "detect.summary_line_movie"
            detail = t(key, videos=len(videos), subs=len(subs), missing=missing)
        return f"<b>{title}</b><br>{detail}"

    def update_action_state(self):
        self._update_guided_workflow()

    def clear_list(self):
        if not self.items:
            return

        if QMessageBox.question(
            self, t("msg.clear_title"), t("msg.clear")
        ) == QMessageBox.StandardButton.Yes:
            self.items = []
            self._set_title_programmatic("", manual=False)
            self.detected_series_label.setText(t("detect.none"))
            self.refresh()

    def remove_selected(self):
        selected_count = sum(1 for item in self.items if item.selected)
        if not selected_count:
            QMessageBox.information(
                self, t("msg.no_sel_title"), t("msg.no_sel")
            )
            return

        answer = QMessageBox.question(
            self,
            t("msg.remove_title"),
            t("msg.remove", n=selected_count),
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
            self.cancel_btn.setText(t("btn.cancel_busy"))
        self.update_action_state()

    def _set_cancel_enabled(self, enabled):
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setEnabled(enabled)
            self.cancel_btn.setText(t("btn.cancel"))
        self.update_action_state()

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

        sort_id = combo_id(self.sort_combo)
        if sort_id == "Név":
            order.sort(
                key=lambda x: Path(self.items[x].path).name.lower()
            )
        elif sort_id == "Fájltípus":
            order.sort(
                key=lambda x: (
                    self.items[x].ext,
                    Path(self.items[x].path).name.lower()
                )
            )
        elif sort_id == "Módosítás dátuma":
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
            if getattr(self, "show_review_only", False) and self._review_kind(item) == "ok":
                continue
            if filt and filt not in (
                Path(item.path).name + " " +
                str(self._source_path(item)) + " " +
                item.status + " " + item.group + " " +
                item_search_extra(item, self.subtitle_pref)
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

        open_action = menu.addAction(t("ctx.open"))
        folder_action = menu.addAction(t("ctx.folder"))
        copy_path_action = menu.addAction(t("ctx.copy_path"))
        menu.addSeparator()
        select_action = menu.addAction(t("ctx.select"))
        deselect_action = menu.addAction(t("ctx.deselect"))

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
            self._set_status(t("status.selected", selected=selected, n=len(self.items)))

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

    def select_review_items(self):
        """UI-only: select rows that need review or cannot be processed."""
        for item in self.items:
            kind = self._review_kind(item)
            item.selected = kind != "ok" and item.kind in ("video", "sub")
        self._refresh_selection_status()
        self._scroll_to_first_review()

    def _on_show_review_only_toggled(self, checked):
        """Nézetszűrő: csak a táblázat látható sorait változtatja."""
        self.show_review_only = bool(checked)
        self.refresh(reanalyze=False)

    def _sync_show_review_only_control(self, has_review):
        if not hasattr(self, "show_review_only_btn"):
            return
        if not has_review:
            self.show_review_only = False
        btn = self.show_review_only_btn
        btn.blockSignals(True)
        btn.setEnabled(bool(has_review))
        btn.setChecked(bool(self.show_review_only) and bool(has_review))
        btn.blockSignals(False)
        _set_qss_state(btn, "active", "true" if self.show_review_only else "false")

    def _scroll_to_first_review(self):
        if not hasattr(self, "table"):
            return
        visible = self._visible_items()
        for row, item in enumerate(visible):
            if self._review_kind(item) != "ok":
                cell = self.table.item(row, COL_ORIG)
                if cell is not None:
                    self.table.scrollToItem(cell)
                    self.table.selectRow(row)
                return

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
            detected_parts.append(t("detect.series", names=", ".join(sorted(series_titles.values(), key=str.lower))))
        if film_titles:
            detected_parts.append(t("detect.movies", names=", ".join(sorted(film_titles.values(), key=str.lower))))
        if hasattr(self, "detected_series_label"):
            self.detected_series_label.setText("\n".join(detected_parts) if detected_parts else t("detect.fail"))

        apply_item_target_names(
            self.items,
            NamingContext(
                mode=self.mode_value,
                template=self.template_value,
                normalize=self.normalize_cb.isChecked(),
                title_manual=self.title_manual,
                global_title=global_title,
                subtitle_pref=self.subtitle_pref,
            ),
        )

        disambiguate_subtitle_target_names(self.items)
        apply_pair_group_status(self.items, self.subtitle_pref)

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
            # A videó + pontosan 1 preferált sima felirat automatikusan együtt kijelölhető.
            # 0 vagy 2+ preferált: nincs automatikus subtitle partner, nincs fallback.
            group_items = [x for x in self.items if x.group == item.group]
            videos = [x for x in group_items if x.kind == "video"]
            preferred = [
                x for x in group_items
                if is_preferred_plain_sub(x, self.subtitle_pref)
            ]
            pair = []
            if videos:
                pair.append(videos[0])
            if len(preferred) == 1:
                pair.append(preferred[0])
            for member in pair:
                member.selected = True
        self._set_status(t(
            "status.files",
            n=len(self.items),
            selected=sum(i.selected for i in self.items),
        ))
        self.refresh(reanalyze=False)

    def _copy_state(self, item):
        return getattr(item, "copy_status", "Várakozik")

    def _copy_percent(self, item):
        return int(getattr(item, "copy_percent", 0) or 0)

    def _set_progress_cell(self, row, item, state):
        """Folyamat: szöveg, amíg nincs aktív másolás — nagy listánál nincs 1000 QProgressBar."""
        self.table.removeCellWidget(row, COL_PROGRESS)
        if state == "Másolás...":
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(self._copy_percent(item))
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            self.table.setCellWidget(row, COL_PROGRESS, bar)
            return
        text = "100%" if state in {"Átmásolva", "Kész"} else "—"
        # Kész/Átmásolva: a folyamat oszlop 100%, az állapot oszlop viseli a státuszt.
        # Hiba/megszakítás: ne írjon hamis 100%-ot, maradjon a státuszszöveg.
        if (
            state in COPY_ACTIVE_STATES
            and state not in {"Másolás...", "Átnevezés...", "Átmásolva", "Kész"}
        ):
            text = status_text(state)
        cell = QTableWidgetItem(text)
        src = str(self._source_path(item))
        cell.setToolTip(f"{status_text(state)}\n{src}")
        cell.setForeground(QColor(self._theme()["text_muted"]))
        self.table.setItem(row, COL_PROGRESS, cell)

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
        styles = copy_state_colors(self._theme())
        if state in styles:
            fg, bg = styles[state]
            state_item.setForeground(QColor(fg))
            state_item.setBackground(QColor(bg))
            state_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.table.setItem(row, COL_STATUS, state_item)
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
        _ok, issues, blocked = self._review_counts()
        self._sync_show_review_only_control(bool(self.items) and (issues + blocked) > 0)
        visible=self._visible_items()
        has_list = bool(self.items)
        self.empty_panel.setVisible(not has_list)
        self.table.setVisible(has_list)
        if hasattr(self, "output_box"):
            self.output_box.setVisible(has_list)

        self._syncing_table = True
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(visible))
            for row, item in enumerate(visible):
                series=item.title.strip() or t("preview.unknown")
                season=f"S{item.season:02d}" if item.season is not None else "—"
                episode=f"E{item.episode:02d}" if item.episode is not None else "—"
                # Valódi, kattintható kijelölő a sorhoz.
                check = QCheckBox()
                check.setChecked(bool(item.selected))
                check.setToolTip(t("tip.row_check"))
                check.stateChanged.connect(
                    lambda state, obj=item: self._checkbox_changed(obj, state)
                )
                holder = QWidget()
                holder_layout = QHBoxLayout(holder)
                holder_layout.setContentsMargins(0, 0, 0, 0)
                holder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                holder_layout.addWidget(check)
                self.table.setCellWidget(row, 0, holder)

                orig_name = Path(item.path).name
                src_path = str(self._source_path(item))
                size_text = format_size_bytes(getattr(item, "size_bytes", None))
                copy_state = self._copy_state(item)
                tip = self._row_tooltip(item, orig_name, src_path)
                kind_label = type_cell_text(item, self.subtitle_pref)
                values = {
                    COL_ORIG: orig_name,
                    COL_NEW: item.new_name or "—",
                    COL_STATUS: self._status_cell_text(item),
                    COL_SERIES: series,
                    COL_SEASON: season,
                    COL_EPISODE: episode,
                    COL_TYPE: kind_label,
                    COL_SIZE: size_text,
                }
                review = self._review_kind(item)
                tok = self._theme()
                primary_font = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
                secondary_fg = QColor(tok["text_secondary"])
                row_bg = {
                    "ok": tok["row_ok"],
                    "blocked": tok["row_blocked"],
                }.get(review, tok["row_review"])
                for col, value in values.items():
                    cell = QTableWidgetItem(value)
                    cell.setToolTip(tip)
                    cell.setBackground(QColor(row_bg))
                    if col in (COL_ORIG, COL_NEW, COL_STATUS):
                        cell.setFont(primary_font)
                    else:
                        cell.setForeground(secondary_fg)
                    if col == COL_STATUS:
                        state = copy_state
                        styles = copy_state_colors(tok)
                        if state in styles:
                            fg, bg = styles[state]
                            cell.setForeground(QColor(fg))
                            cell.setBackground(QColor(bg))
                            cell.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    self.table.setItem(row, col, cell)
                self._set_progress_cell(row, item, self._copy_state(item))
        finally:
            self.table.setUpdatesEnabled(True)
            self._syncing_table = False
            self.table.resizeColumnToContents(COL_TYPE)
            if self.table.columnWidth(COL_TYPE) < 158:
                self.table.setColumnWidth(COL_TYPE, 158)

        self._set_status(t(
            "status.files",
            n=len(self.items),
            selected=sum(i.selected for i in self.items),
        ))
        self.update_action_state()

        summary=self._batch_summary()
        self.preview_text.clear()
        self.preview_text.append(t(
            "preview.head",
            series=summary["series_count"],
            movies=summary["film_count"],
            seasons=summary["season_count"],
            files=summary["file_count"],
            ok=summary["ok_count"],
            issues=summary["issue_count"],
        ) + "\n")
        groups = []
        buckets = {}
        for item in visible:
            key = item.group or f"#{id(item)}"
            if key not in buckets:
                buckets[key] = []
                groups.append(key)
            buckets[key].append(item)
        for key in groups:
            members = buckets[key]
            videos_n = sum(1 for i in members if i.kind == "video")
            subs_n = sum(1 for i in members if i.kind == "sub")
            first = members[0]
            season_text = (
                f"S{first.season:02d}E{first.episode:02d}"
                if first.season is not None and first.episode is not None
                else "—"
            )
            self.preview_text.append(t(
                "preview.group_head",
                title=first.title.strip() or t("preview.unknown"),
                episode=season_text,
            ))
            self.preview_text.append(t(
                "preview.group_counts",
                videos=videos_n,
                subs=subs_n,
            ))
            for item in members:
                selected_mark = "✓" if item.selected else " "
                note = self._visible_note(item)
                common = dict(
                    mark=selected_mark,
                    original=Path(item.path).name,
                    new_name=item.new_name or "—",
                    status=self._status_cell_text(item),
                    note=note,
                    copy=status_text(self._copy_state(item)),
                )
                if item.kind == "sub":
                    self.preview_text.append(t(
                        "preview.file_sub",
                        kind=t("kind.sub"),
                        meta=subtitle_meta_text(item, self.subtitle_pref),
                        **common,
                    ))
                else:
                    self.preview_text.append(t(
                        "preview.file_video",
                        kind=t("kind.video") if item.kind == "video" else t("kind.other"),
                        **common,
                    ))

    # ---------- actions ----------

    def check(self):
        self.analyze()
        if hasattr(self, "files_tab"):
            self.tabs.setCurrentWidget(self.files_tab)
        self.refresh(reanalyze=False)
        self._scroll_to_first_review()

        ok = sum(i.status in {"OK", "Kész"} for i in self.items)
        bad = len(self.items) - ok

        summary = self._batch_summary()
        names = ", ".join(summary["series_names"][:8])
        if len(summary["series_names"]) > 8:
            names += f", ... (+{len(summary['series_names']) - 8})"

        issue_items = [i for i in self.items if i.status not in {"OK", "Kész"}]

        mixed_mode_note = ""
        if self.mode_value == "Sorozat" and summary["film_count"]:
            mixed_mode_note = t("check.mixed_note", mode=t("mode.mixed"))

        issue_lines = []
        for item in issue_items[:8]:
            if item.season is not None and item.episode is not None:
                label = f"{item.title.strip() or t('preview.unknown')} S{item.season:02d}E{item.episode:02d}"
            else:
                label = item.title.strip() or t("check.unknown_movie")
            reason = self._visible_note(item) or self._status_cell_text(item)
            issue_lines.append(f"• {label} — {self._source_path(item).name}: {reason}")
        if len(issue_items) > 8:
            issue_lines.append(t("check.more_files", n=len(issue_items) - 8))

        details = "\n".join(issue_lines) if issue_lines else t("check.no_issues")

        videos_n = sum(1 for i in self.items if i.kind == "video")
        subs_n = sum(1 for i in self.items if i.kind == "sub")
        av_line = t("meta.av_counts", videos=videos_n, subs=subs_n)

        QMessageBox.information(
            self,
            t("check.title"),
            t(
                "check.body",
                series=summary["series_count"],
                movies=summary["film_count"],
                seasons=summary["season_count"],
                files=summary["file_count"],
                selected=summary["selected_count"],
                ok=summary["ok_count"],
                issues=summary["issue_count"],
                series_names=names or "—",
                movie_names=", ".join(summary["film_names"][:8]) or "—",
                details=details,
            ) + mixed_mode_note + "\n\n" + av_line
        )

    def _progress_start(self, total, label=None):
        if not hasattr(self, "progress_bar"):
            return
        total = max(1, total)
        if label is None:
            label = t("progress.work")
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(t("progress.fmt", label=label, current=0, total=total, percent=0))
        self.progress_bar.setVisible(True)
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText("")
            self.progress_file_label.setToolTip("")
        QApplication.processEvents()

    def _progress_step(self, current, total, label=None, filename=""):
        if not hasattr(self, "progress_bar"):
            return
        total = max(1, total)
        if label is None:
            label = t("progress.work")
        percent = round(current * 100 / total)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(t(
            "progress.fmt", label=label, current=current, total=total, percent=percent
        ))
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText(
                t("progress.file", name=filename) if filename else ""
            )
            self.progress_file_label.setToolTip(filename or "")
        QApplication.processEvents()

    def _progress_finish(self):
        if not hasattr(self, "progress_bar"):
            return
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.progress_bar.setFormat(t("progress.done"))
        if hasattr(self, "progress_file_label"):
            self.progress_file_label.setText("")
            self.progress_file_label.setToolTip("")
        QApplication.processEvents()
        QTimer.singleShot(1200, self.progress_bar.hide)

    def _apply_progress_bar_language(self):
        """A látható folyamatcsík szövege kövesse az aktív nyelvet."""
        if not hasattr(self, "progress_bar"):
            return
        bar = self.progress_bar
        if not bar.isVisible():
            return
        if bar.maximum() > 0 and bar.value() >= bar.maximum():
            bar.setFormat(t("progress.done"))
            return
        total = max(1, bar.maximum())
        current = bar.value()
        percent = round(current * 100 / total)
        bar.setFormat(t(
            "progress.fmt",
            label=t("progress.work"),
            current=current,
            total=total,
            percent=percent,
        ))

    def _confirm_rename(self, changes, copy_mode, destination):
        """Felhasználói megerősítés az átnevezés előtt. True = Indítás."""
        dialog = StartConfirmDialog(self, changes, copy_mode, destination)
        return dialog.exec() == QDialog.DialogCode.Accepted

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
                t("msg.nothing_title"),
                t("msg.nothing")
            )
            return

        output_error = self._output_path_error(selected)
        if output_error:
            QMessageBox.warning(self, t("msg.output_title"), output_error)
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
            preferred = [x for x in subs if is_preferred_plain_sub(x, self.subtitle_pref)]
            required = []
            if vids:
                required.append(vids[0])
            if len(preferred) == 1:
                required.append(preferred[0])
            required_ids = {id(x) for x in required}
            selected_required = {id(x) for x in selected_here}
            if required_ids and not required_ids.issubset(selected_required):
                incomplete_pairs.append(group)

        if incomplete_pairs:
            QMessageBox.warning(
                self, t("msg.pair_title"),
                t("msg.pair")
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
            QMessageBox.information(self, t("msg.idle_title"), t("msg.idle"))
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
                self, t("msg.idle_title"), t("msg.idle_left")
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
                    self, t("msg.nospace_title"),
                    t(
                        "msg.nospace",
                        needed=f"{total_bytes / (1024**3):.1f}",
                        free=f"{free_bytes / (1024**3):.1f}",
                    ),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if ans != QMessageBox.StandardButton.Yes:
                    return

        if copy_mode:
            operation_text = "Másolás és átnevezés"
        else:
            operation_text = "Helyben átnevezés"

        if not self._confirm_rename(changes, copy_mode, destination):
            return

        if copy_mode:
            # A nem létező kimeneti mappát automatikusan létrehozzuk.
            try:
                destination.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                QMessageBox.critical(
                    self,
                    t("msg.output_mkdir_title"),
                    t("msg.output_mkdir", path=destination, exc=exc),
                )
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
        progress_label = t("progress.copy") if copy_mode else t("progress.rename")
        self.cancel_requested = False
        self._rename_busy = True
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
                        self._progress_step(current, total_changes, progress_label, t("progress.nospace_next"))
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
                    copy_rollback_failures = rollback_copied_files(pair_created)
                    # Helyben átnevezésnél visszanevezzük az addig elkészült tagokat.
                    rename_rollback_failures = rollback_renamed_files(pair_renames)
                    copy_rollback_errors = {
                        file_identity_key(entry["path"]): entry["error"]
                        for entry in copy_rollback_failures
                    }
                    rename_rollback_errors = {
                        file_identity_key(entry["new"]): entry["error"]
                        for entry in rename_rollback_failures
                    }
                    rollback_errors = copy_rollback_errors | rename_rollback_errors

                    for change in pending_history:
                        if file_identity_key(change["new"]) in rollback_errors:
                            record["changes"].append(change)

                    for pair_item, old_path, new_path in pair:
                        rollback_error = rollback_errors.get(file_identity_key(new_path))
                        if rollback_error:
                            pair_item.copy_status = "Hiba"
                            pair_item.copy_percent = 0
                            pair_item.note = (
                                "A pár rollbackje sikertelen; a célfájl megmaradt: "
                                f"{new_path} — {rollback_error}"
                            )
                            pair_item.path = str(new_path)
                        elif pair_item.copy_status == "Másolás..." or pair_item.copy_status == "Átnevezés...":
                            pair_item.copy_status = "Hiba"
                            pair_item.copy_percent = 0
                            pair_item.note = "A videó + felirat pár visszaállítva"
                            pair_item.path = str(old_path)
                        else:
                            pair_item.path = str(old_path)
                        failed.append((pair_item, pair_item.note or "A teljes pár visszaállítva"))
                    current += len(pair)
                    self._progress_step(current, total_changes, progress_label, t("progress.pair_restored"))
                    continue

                # A pár csak most tekinthető késznek: előzmény + belső állapot egyszerre frissül.
                record["changes"].extend(pending_history)
                for pair_item, old_path, new_path in pair:
                    pair_item.path = str(new_path)
                    pair_item.copy_percent = 100
                    if copy_mode:
                        self._update_copy_row(pair_item)
                    pair_item.status = "Kész"
                    pair_item.copy_status = "Átmásolva" if copy_mode else "Kész"
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
                self._progress_step(current, total_changes, progress_label, t("progress.remaining"))

        except Exception as exc:
            self._set_cancel_enabled(False)
            self.cancel_requested = False
            if hasattr(self, "progress_bar"):
                self.progress_bar.hide()
            if record["changes"] or failed:
                record["failed"] = [
                    {"file": str(self._source_path(item)), "reason": reason}
                    for item, reason in failed
                ]
                if failed or current < total_changes:
                    record["status"] = "Részben elkészült"
                else:
                    record["status"] = "Sikeres"
                self.history.append(record)
                self.save_history()
                self.update_history_view()
            QMessageBox.critical(
                self, t("msg.op_error_title"),
                t("msg.op_error", exc=exc)
            )
            return
        finally:
            self._rename_busy = False
            self.update_action_state()

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

        message = t("msg.done_files", n=len(record["changes"]))
        if failed:
            message += "\n\n" + t("msg.done_failed", n=len(failed))
        if was_cancelled:
            message = t("msg.done_cancelled") + "\n\n" + message
        if copy_mode:
            message += "\n\n" + t("msg.done_copy", path=destination)
        if failed and any("már létezett" in reason for _, reason in failed):
            message += "\n" + t("msg.done_exists")

        QMessageBox.information(self, t("msg.done_title"), message)

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
                t("hist.save_title"),
                t("hist.save", exc=exc),
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

            operation = hist_op_text(record.get("operation", "Átnevezés"))
            title = record.get("title", "") or t("hist.unknown")
            destination = record.get("destination", "")
            count = len(record.get("changes", []))
            failed_count = len(record.get("failed", []))
            status = record.get("status", "")
            result_text = (
                t("hist.result_ok", n=count) if failed_count == 0
                else t("hist.result_partial", n=count, failed=failed_count)
            )
            if status:
                result_text += f" — {hist_status_text(status)}"

            values = [
                str(index), record.get("time", ""), operation, title,
                result_text, destination
            ]
            for column, value in enumerate(values, start=1):
                cell = QTableWidgetItem(value)
                if status in {"Visszavonva", "Megszakítva", "Hiba"} and column == 3:
                    cell.setForeground(QColor(self._theme()["danger"]))
                    cell.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                if column == 5 and failed_count:
                    cell.setToolTip(t("hist.failed_tip"))
                self.hist.setItem(row, column, cell)
        self.hist.resizeRowsToContents()

    def _format_history_failed_text(self, record):
        """failed lista olvasható szövege; a rekordot nem módosítja."""
        items = []
        for entry in record.get("failed") or []:
            if not isinstance(entry, dict):
                continue
            file_text = str(entry.get("file") or "")
            reason_text = note_text(str(entry.get("reason") or ""))
            items.append(t("hist.failed_item", file=file_text, reason=reason_text))
        return t("hist.failed_body", n=len(items), list="\n\n".join(items))

    def show_selected_history_failures(self):
        """A kijelölt előzmény failed elemeinek file/reason listája. Undo-t nem érinti."""
        indices = self._selected_history_indices()
        if len(indices) != 1:
            QMessageBox.information(
                self, t("hist.failed_title"), t("hist.failed_need_one")
            )
            return
        record = self.history[indices[0]]
        failed = record.get("failed") or []
        if not failed:
            QMessageBox.information(
                self, t("hist.failed_title"), t("hist.failed_none")
            )
            return
        QMessageBox.information(
            self, t("hist.failed_title"), self._format_history_failed_text(record)
        )

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
            QMessageBox.information(self, t("hist.none_title"), t("hist.none"))
            return
        if QMessageBox.question(
            self, t("hist.delete_sel_title"),
            t("hist.delete_sel", n=len(indices)),
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
                self, t("undo.need_one_title"), t("undo.need_one")
            )
            return
        row = indices[0]
        if row >= len(self.history):
            return
        record = self.history[row]
        operation = record.get("operation", "Átnevezés")
        changes = record.get("changes", [])

        if record.get("status") == "Visszavonva":
            QMessageBox.information(self, t("undo.already_title"), t("undo.already"))
            return

        if operation == "Másolás és átnevezés":
            copy_check = verify_copy_undo(changes)
            if copy_check is not None:
                kind, path = copy_check
                if kind == "missing":
                    QMessageBox.critical(self, t("undo.unsafe_title"), t("undo.unsafe_missing"))
                else:
                    QMessageBox.critical(
                        self, t("undo.unsafe_title"),
                        t("undo.unsafe_changed", path=path),
                    )
                return
            if QMessageBox.question(
                self, t("undo.copy_title"), t("undo.copy_body", n=len(changes))
            ) != QMessageBox.StandardButton.Yes:
                return
            undo_failures = apply_copy_undo(changes)
            failed_keys = {
                file_identity_key(entry["path"]) for entry in undo_failures
            }
        else:
            if not verify_inplace_undo(changes):
                QMessageBox.critical(self, t("undo.unsafe_title"), t("undo.unsafe_state"))
                return
            undo_failures = apply_inplace_undo(changes)
            failed_keys = {
                file_identity_key(entry["new"]) for entry in undo_failures
            }

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
                if file_identity_key(change["new"]) in failed_keys:
                    continue
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

        if undo_failures:
            remaining = [
                change for change in changes
                if file_identity_key(change["new"]) in failed_keys
            ]
            record["changes"] = remaining
            extra_failed = []
            for entry in undo_failures:
                path = entry.get("path") or entry.get("new")
                extra_failed.append({
                    "file": str(path),
                    "reason": f"Visszaállítás sikertelen: {entry['error']}",
                })
            record["failed"] = list(record.get("failed") or []) + extra_failed
            record["status"] = "Részben elkészült"
            self.save_history()
            self.update_history_view()
            self.refresh()
            QMessageBox.critical(
                self,
                t("undo.unsafe_title"),
                t("undo.partial"),
            )
            return

        record["status"] = "Visszavonva"
        self.save_history()
        self.update_history_view()
        self.refresh()
        QMessageBox.information(self, t("undo.done_title"), t("undo.done"))

    def clear_history(self):
        if QMessageBox.question(
            self, t("hist.clear_confirm_title"), t("hist.clear_confirm")
        ) == QMessageBox.StandardButton.Yes:
            self.history = []
            self.history_selected_keys.clear()
            self.save_history()
            self.update_history_view()

    def export_history(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            t("hist.export_title"),
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
                    f"{t('hist.export_txt_time')}: {record.get('time', '')}\n"
                    f"{t('hist.export_txt_op')}: {hist_op_text(record.get('operation', ''))}\n"
                    f"{t('hist.export_txt_title')}: {record.get('title', '')}\n"
                    f"{t('hist.export_txt_place')}: {record.get('destination', '')}\n"
                    f"{t('hist.export_txt_files')}: {len(record.get('changes', []))}\n"
                    f"{t('hist.export_txt_failed')}: {len(record.get('failed', []))}\n"
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

        self.show_welcome = not dialog.dont_show.isChecked()
        self.set_language(dialog.selected_language)

        if result == 2:
            self.show_help()

    def show_help(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(t("help.title", name=APP_NAME, version=APP_VERSION))
        dialog.resize(780, 620)

        layout = QVBoxLayout(dialog)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(
            t("help.body", name=APP_NAME, version=APP_VERSION)
        )
        layout.addWidget(text)

        close = QPushButton(t("help.close"))
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

        dialog.exec()

    # ---------- appearance / help menu ----------

    def set_appearance(self, value):
        if value not in ("Világos", "Sötét"):
            value = "Világos"

        self.appearance = value
        dark = value == "Sötét"
        tok = theme_tokens(dark)
        app = QApplication.instance()

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(tok["window"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(tok["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(tok["surface"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tok["surface_alt"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(tok["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(tok["raised"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(tok["text"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(tok["selected"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tok["text"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tok["raised"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tok["text"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(tok["text_muted"]))
        palette.setColor(QPalette.ColorRole.Light, QColor(tok["surface"]))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(tok["surface_alt"]))
        palette.setColor(QPalette.ColorRole.Mid, QColor(tok["border"]))
        palette.setColor(QPalette.ColorRole.Dark, QColor(tok["border_strong"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(tok["white"]))
        app.setStyle("Fusion")
        app.setPalette(palette)
        app.setStyleSheet(build_app_stylesheet(dark))
        self._apply_cta_styles()

        self.update_appearance_buttons()
        if hasattr(self, "guide_banner"):
            self._update_guided_workflow()
        if hasattr(self, "table") and getattr(self, "items", None):
            self.refresh(reanalyze=False)
        if hasattr(self, "hist"):
            self.update_history_view()
        if hasattr(self, "sort_combo"):
            self.save_settings(silent=True)

    def _apply_cta_styles(self):
        """CTA + sima gombok: widget-level QSS, Fusion ne fesse felül a kontúrt."""
        tok = self._theme()
        plain = plain_button_stylesheet(tok)
        if hasattr(self, "add_btn"):
            self.add_btn.setStyleSheet(primary_button_stylesheet(tok))
        if hasattr(self, "empty_add_btn"):
            self.empty_add_btn.setStyleSheet(primary_button_stylesheet(tok))
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setStyleSheet(filled_button_stylesheet(tok, "danger"))
        if hasattr(self, "hist_undo_btn"):
            self.hist_undo_btn.setStyleSheet(filled_button_stylesheet(tok, "danger"))
        if hasattr(self, "test_lab_btn"):
            self.test_lab_btn.setStyleSheet(filled_button_stylesheet(tok, "dev"))
        if hasattr(self, "patch_btn"):
            self.patch_btn.setStyleSheet(filled_button_stylesheet(tok, "muted"))
        if hasattr(self, "rename_btn"):
            ready = self.rename_btn.property("ready") == "true"
            self.rename_btn.setStyleSheet(rename_button_stylesheet(tok, ready))
        for name in (
            "clear_btn", "check_btn", "refresh_preview_btn", "help_btn",
            "search_btn", "select_all_files_btn", "deselect_files_btn",
            "remove_selected_btn", "select_review_btn", "output_browse_btn",
            "save_settings_btn", "refresh_list_btn", "reset_settings_btn",
            "select_all_btn", "select_none_btn", "select_missing_btn",
            "hist_select_all_btn", "hist_deselect_btn", "hist_delete_btn",
            "hist_failed_btn", "hist_export_btn", "hist_clear_btn",
        ):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.setStyleSheet(plain)
        if hasattr(self, "var_buttons"):
            for button in self.var_buttons.values():
                button.setStyleSheet(plain)
        if hasattr(self, "show_review_only_btn"):
            self.show_review_only_btn.setStyleSheet(review_button_stylesheet(tok))

    def _freeze_caption_width(self, widget, *keys):
        """Egyszeres szélesség: a hosszabb HU/EN sizeHint. A gomb nem zsugorodik."""
        if widget is None or getattr(widget, "_sr_width_frozen", False):
            return
        original = widget.text() if hasattr(widget, "text") else ""
        previous_min = widget.minimumWidth()
        widget.setMinimumWidth(0)
        widget.setMaximumWidth(16777215)
        widest = 0
        for key in keys:
            for lang in ("hu", "en"):
                text = (STRINGS.get(lang) or {}).get(key)
                if text is None:
                    continue
                widget.setText(text)
                widest = max(widest, widget.sizeHint().width())
        if keys:
            widget.setText(t(keys[0]))
        else:
            widget.setText(original)
        width = max(widest, previous_min)
        if isinstance(widget, QPushButton):
            widget.setFixedWidth(width)
        else:
            widget.setMinimumWidth(width)
        widget._sr_width_frozen = True

    def _freeze_combo_width(self, combo, key_map):
        if combo is None or getattr(combo, "_sr_width_frozen", False):
            return
        fm = combo.fontMetrics()
        previous_min = combo.minimumWidth()
        combo.setMinimumWidth(0)
        chrome = max(combo.sizeHint().width() - fm.horizontalAdvance(combo.currentText()), 0)
        combo.setMinimumWidth(max(previous_min, _i18n_map_max_px(fm, key_map) + chrome))
        combo.setFixedWidth(combo.minimumWidth())
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        combo._sr_width_frozen = True

    def _stabilize_i18n_geometry(self):
        """HU/EN feliratcsere a widgeten belül maradjon, a pozíció ne ugorjon."""
        fm = self.fontMetrics()
        if hasattr(self, "add_btn"):
            self._freeze_caption_width(self.add_btn, "btn.add")
            self._freeze_caption_width(self.clear_btn, "btn.clear_list")
            self._freeze_caption_width(self.check_btn, "btn.check")
            self._freeze_caption_width(self.refresh_preview_btn, "btn.refresh_preview")
        if hasattr(self, "help_btn"):
            self._freeze_caption_width(self.help_btn, "btn.help")
        if hasattr(self, "test_lab_btn"):
            self._freeze_caption_width(self.test_lab_btn, "btn.testlab")
        if hasattr(self, "patch_btn"):
            self._freeze_caption_width(self.patch_btn, "btn.patch")
        if hasattr(self, "rename_btn"):
            self._freeze_caption_width(self.rename_btn, "btn.rename")
            self.rename_btn.setMinimumWidth(max(150, self.rename_btn.minimumWidth()))
        if hasattr(self, "search_btn"):
            self._freeze_caption_width(self.search_btn, "files.search")
            self._freeze_caption_width(self.sort_label, "files.sort")
            self._freeze_combo_width(self.sort_combo, SORT_KEYS)
            self._freeze_caption_width(self.select_all_files_btn, "files.select_all")
            self._freeze_caption_width(self.deselect_files_btn, "files.deselect")
            self._freeze_caption_width(self.remove_selected_btn, "files.remove_selected")
            self._freeze_caption_width(self.select_review_btn, "files.select_review")
            if hasattr(self, "show_review_only_btn"):
                self._freeze_caption_width(self.show_review_only_btn, "files.show_review_only")
            self._freeze_caption_width(self.output_browse_btn, "output.browse")
        if hasattr(self, "output_grid"):
            out_label = _i18n_max_px(fm, "output.action", "output.folder") + 6
            self.output_grid.setColumnMinimumWidth(0, out_label)
            self.output_grid.setColumnStretch(0, 0)
            self.output_grid.setColumnStretch(1, 1)
            expanding = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.output_mode_combo.setSizePolicy(expanding)
            self.output_mode_combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            self.output_edit.setSizePolicy(expanding)
            self.output_action_label.setMinimumWidth(out_label)
            self.output_folder_label.setMinimumWidth(out_label)
        if hasattr(self, "settings_grid"):
            label_w = _i18n_max_px(
                fm,
                "mode.label", "name.series", "name.movie", "name.mixed",
                "template.label", "vars.base", "vars.series", "pref.label",
            ) + 6
            self.settings_grid.setColumnMinimumWidth(0, label_w)
            self.settings_grid.setColumnStretch(0, 0)
            self.settings_grid.setColumnStretch(1, 1)
            expanding = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            for widget in (
                self.mode_combo, self.title_edit, self.template_edit,
                self.subtitle_pref_combo,
            ):
                widget.setSizePolicy(expanding)
            for combo in (self.mode_combo, self.subtitle_pref_combo):
                combo.setSizeAdjustPolicy(
                    QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
                )
            for label in (
                self.mode_label, self.name_label, self.template_label,
                self.base_vars_label, self.subtitle_pref_label,
            ):
                label.setMinimumWidth(label_w)
            if not getattr(self.detected_box, "_sr_width_frozen", False):
                detect_need = _i18n_max_px(fm, "detect.box", "detect.none", "detect.fail")
                self.detected_box.setMinimumWidth(
                    max(self.detected_box.sizeHint().width(), detect_need)
                )
                self.detected_box._sr_width_frozen = True
        if hasattr(self, "var_buttons"):
            for value, (text_key, _tip_key) in TOKEN_BUTTON_KEYS.items():
                button = self.var_buttons.get(value)
                if button is not None:
                    self._freeze_caption_width(button, text_key)
        if hasattr(self, "save_settings_btn"):
            self._freeze_caption_width(self.save_settings_btn, "btn.save_settings")
            self._freeze_caption_width(self.refresh_list_btn, "btn.refresh_list")
            self._freeze_caption_width(self.reset_settings_btn, "btn.reset_settings")
        bar = self.tabs.tabBar() if hasattr(self, "tabs") else None
        if isinstance(bar, _StableTabBar) and not bar._min_widths:
            keys = ("tab.files", "tab.settings", "tab.preview", "tab.history")
            tab_fm = bar.fontMetrics()
            pad = 40
            bar.set_min_widths({
                i: _i18n_max_px(tab_fm, key) + pad for i, key in enumerate(keys)
            })

    def _toggle_appearance(self):
        self.set_appearance("Sötét" if self.appearance != "Sötét" else "Világos")

    def update_appearance_buttons(self):
        if not hasattr(self, "theme_btn"):
            return
        dark = self.appearance == "Sötét"
        self.theme_btn.setIcon(make_theme_toggle_icon(dark))
        self.theme_btn.setToolTip(
            t("tip.theme_toggle_dark" if dark else "tip.theme_toggle_light")
        )
        _set_qss_state(self.theme_btn, "dark", "true" if dark else "false")


    def show_first_steps(self):
        QMessageBox.information(
            self, t("msg.first_steps_title"),
            t("msg.first_steps")
        )

    def show_template_help(self):
        QMessageBox.information(
            self, t("msg.template_title"),
            t("msg.template")
        )

    def check_updates(self):
        QMessageBox.information(
            self, t("msg.updates_title"),
            t("msg.updates", version=APP_VERSION)
        )

    def report_bug(self):
        QMessageBox.information(
            self, t("msg.bug_title"),
            t("msg.bug")
        )

    def donate(self):
        QMessageBox.information(
            self, t("msg.donate_title"),
            t("msg.donate")
        )

    def show_about(self):
        QMessageBox.about(
            self, t("msg.about_title"),
            t("msg.about", name=APP_NAME, version=APP_VERSION, author=AUTHOR)
        )

    # ---------- settings ----------

    def update_language_buttons(self):
        if not hasattr(self, "hu_main_btn"):
            return
        self.hu_main_btn.setChecked(self.language == "hu")
        self.en_main_btn.setChecked(self.language == "en")

    def _set_status(self, text):
        label = getattr(self, "status_label", None) or getattr(self, "status_label", None)
        if label is not None:
            label.setText(text)

    def _on_main_tab_changed(self, index):
        if getattr(self, "settings_tab", None) is self.tabs.widget(index):
            self._apply_settings_tab_language()

    def _apply_settings_tab_language(self):
        """Haladó beállítások fül: mindig az aktív nyelv látható szövegei.

        A QTabWidget rejtett oldala Windowson nem mindig veszi a setText-et;
        ezért nyelvváltáskor és a fül előhozásakor is újra kell tölteni.
        """
        if not hasattr(self, "mode_combo"):
            return
        if hasattr(self, "settings_intro"):
            self.settings_intro.setText(t("settings.intro"))
        if hasattr(self, "naming_heading"):
            self.naming_heading.setText(t("settings.naming_box"))
        self.mode_label.setText(t("mode.label"))
        fill_combo(self.mode_combo, MODE_IDS, MODE_KEYS)
        self.detected_box.setTitle(t("detect.box"))
        if not self.items:
            self.detected_series_label.setText(t("detect.none"))
        self.template_label.setText(t("template.label"))
        self.subtitle_pref_label.setText(t("pref.label"))
        self.subtitle_pref_label.setToolTip(t("pref.tip"))
        self.subtitle_pref_combo.setToolTip(t("pref.tip"))
        fill_combo(self.subtitle_pref_combo, SUBTITLE_PREF_CHOICES, SUBTITLE_PREF_KEYS)
        self.subtitle_pref_combo.blockSignals(True)
        set_combo_id(self.subtitle_pref_combo, self.subtitle_pref)
        self.subtitle_pref_combo.blockSignals(False)
        self.normalize_cb.setText(t("adv.normalize"))
        self.lang_norm_cb.setText(t("adv.lang_norm"))
        self.subdirs_cb.setText(t("adv.subdirs"))
        self.conflicts_cb.setText(t("adv.conflicts"))
        self.preserve_cb.setText(t("adv.preserve"))
        self.adv_vars_label.setText(t("adv.vars"))
        if hasattr(self, "var_buttons"):
            for value, (text_key, tip_key) in TOKEN_BUTTON_KEYS.items():
                button = self.var_buttons.get(value)
                if button is None:
                    continue
                button.setText(t(text_key))
                button.setToolTip(t(tip_key))
        self.save_settings_btn.setText(t("btn.save_settings"))
        self.refresh_list_btn.setText(t("btn.refresh_list"))
        self.refresh_list_btn.setToolTip(t("tip.refresh_list"))
        self.reset_settings_btn.setText(t("btn.reset_settings"))
        film_only = self.mode_value == "Film"
        mixed = self.mode_value == "Automatikus / Vegyes"
        if film_only:
            self.name_label.setText(t("name.movie"))
            self.base_vars_label.setText(t("vars.base"))
            self.default_template_label.setText(t("tpl.movie"))
        elif mixed:
            self.name_label.setText(t("name.mixed"))
            self.base_vars_label.setText(t("vars.series"))
            self.default_template_label.setText(t("tpl.mixed"))
        else:
            self.name_label.setText(t("name.series"))
            self.base_vars_label.setText(t("vars.base"))
            self.default_template_label.setText(t("tpl.series"))

    def apply_ui_language(self):
        """Reload visible widget text from the active language table."""
        self.setWindowTitle(t("win.title", name=APP_NAME, version=APP_VERSION))
        if hasattr(self, "add_btn"):
            self.add_btn.setText(t("btn.add"))
            self.add_files_act.setText(t("menu.add_files"))
            self.add_folder_act.setText(t("menu.add_folder"))
            if hasattr(self, "add_folders_act"):
                self.add_folders_act.setText(t("menu.add_folders"))
            self.clear_btn.setText(t("btn.clear_list"))
            self.check_btn.setText(t("btn.check"))
            self.refresh_preview_btn.setText(t("btn.refresh_preview"))
        if hasattr(self, "test_lab_btn"):
            self.test_lab_btn.setText(t("btn.testlab"))
            self.test_lab_btn.setToolTip(t("tip.testlab"))
        if hasattr(self, "patch_btn"):
            self.patch_btn.setText(t("btn.patch"))
            self.patch_btn.setToolTip(t("tip.patch"))
        if hasattr(self, "help_btn"):
            self.help_btn.setText(t("btn.help"))
            self.help_guide_act.setText(t("menu.help"))
            self.first_steps_act.setText(t("menu.first_steps"))
            self.template_help_act.setText(t("menu.template_vars"))
            self.updates_act.setText(t("menu.updates"))
            self.bug_act.setText(t("menu.bug"))
            self.donate_act.setText(t("menu.donate"))
            self.about_act.setText(t("menu.about"))
        if hasattr(self, "rename_btn"):
            self.rename_btn.setText(t("btn.rename"))
            self._apply_rename_next_step_tooltip()
        if hasattr(self, "theme_btn"):
            self.theme_btn.setToolTip(
                t("tip.theme_toggle_dark" if self.appearance == "Sötét"
                  else "tip.theme_toggle_light")
            )
            self.hu_main_btn.setToolTip(t("tip.hu"))
            self.en_main_btn.setToolTip(t("tip.en"))
        if hasattr(self, "tabs"):
            self.tabs.setTabText(0, t("tab.files"))
            self.tabs.setTabText(1, t("tab.settings"))
            self.tabs.setTabText(2, t("tab.preview"))
            self.tabs.setTabText(3, t("tab.history"))
        if hasattr(self, "footer_bug_btn"):
            self.footer_bug_btn.setText(t("btn.bug"))
            self.footer_donate_btn.setText(t("btn.donate"))
        if hasattr(self, "footer_badge"):
            self.footer_badge.setText(t("footer.test_version"))
            self.footer_badge.setVisible(show_test_version_mark())
        self._apply_settings_tab_language()
        if hasattr(self, "cancel_btn"):
            busy = self.cancel_btn.isEnabled() and getattr(self, "cancel_requested", False)
            self.cancel_btn.setText(t("btn.cancel_busy" if busy else "btn.cancel"))
        if hasattr(self, "filter_edit"):
            self.filter_edit.setPlaceholderText(t("files.search_ph"))
            self.search_btn.setText(t("files.search"))
            self.sort_label.setText(t("files.sort"))
            fill_combo(self.sort_combo, SORT_IDS, SORT_KEYS)
            self.select_all_files_btn.setText(t("files.select_all"))
            self.deselect_files_btn.setText(t("files.deselect"))
            self.remove_selected_btn.setText(t("files.remove_selected"))
            self.remove_selected_btn.setToolTip(t("tip.remove_selected"))
            self.select_review_btn.setText(t("files.select_review"))
            self.select_review_btn.setToolTip(t("tip.select_review"))
            if hasattr(self, "show_review_only_btn"):
                self.show_review_only_btn.setText(t("files.show_review_only"))
                self.show_review_only_btn.setToolTip(t("tip.show_review_only"))
            self.empty_state.setText(t("files.empty"))
            self.empty_add_btn.setText(t("btn.add_folder_cta"))
            self.output_box.setTitle(t("output.box"))
            self.output_action_label.setText(t("output.action"))
            fill_combo(self.output_mode_combo, OUTPUT_IDS, OUTPUT_KEYS)
            self.output_folder_label.setText(t("output.folder"))
            self.output_edit.setPlaceholderText(t("output.folder_ph"))
            self.output_browse_btn.setText(t("output.browse"))
            self.table.setHorizontalHeaderLabels(self._table_headers())
            self.table.horizontalHeader().setToolTip(t("tip.table_check"))
        if hasattr(self, "select_all_btn"):
            self.select_all_btn.setText(t("preview.select_all"))
            self.select_none_btn.setText(t("preview.select_none"))
            self.select_missing_btn.setText(t("preview.select_missing"))
        if hasattr(self, "history_info"):
            self.history_info.setText(t("history.info"))
            self.hist.setHorizontalHeaderLabels([
                t("hist.check"), t("hist.num"), t("hist.time"), t("hist.op"),
                t("hist.title"), t("hist.files"), t("hist.place"),
            ])
            self.hist_select_all_btn.setText(t("hist.select_all"))
            self.hist_deselect_btn.setText(t("hist.deselect"))
            self.hist_delete_btn.setText(t("hist.delete"))
            self.hist_undo_btn.setText(t("hist.undo"))
            self.hist_failed_btn.setText(t("hist.failed"))
            self.hist_export_btn.setText(t("hist.export"))
            self.hist_clear_btn.setText(t("hist.clear"))
            self.update_history_view()
        if hasattr(self, "output_mode_combo"):
            self.on_output_mode_changed()
        if hasattr(self, "table"):
            self.refresh(reanalyze=False)
        else:
            self._set_status(t("status.zero"))
        self._apply_progress_bar_language()
        self._stabilize_i18n_geometry()

    def set_language(self, language):
        self.language = set_active_language(language)
        self.save_settings(silent=True)
        self.update_language_buttons()
        self.apply_ui_language()

    def _on_subtitle_pref_changed(self):
        self.set_subtitle_pref(combo_id(self.subtitle_pref_combo))

    def set_subtitle_pref(self, code):
        """L2.3: setting + pair-status + C.1 + checkbox/rename partner. Naming még HU."""
        self.subtitle_pref = normalize_subtitle_pref(code)
        combo = getattr(self, "subtitle_pref_combo", None)
        if combo is not None:
            combo.blockSignals(True)
            set_combo_id(combo, self.subtitle_pref)
            combo.blockSignals(False)
        if hasattr(self, "normalize_cb"):
            self.save_settings(silent=True)
        if getattr(self, "items", None):
            self.analyze()
            if hasattr(self, "table"):
                self.refresh(reanalyze=False)

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
            "sort_mode": combo_id(self.sort_combo),
            "show_welcome": self.show_welcome,
            "language": self.language,
            "subtitle_pref": normalize_subtitle_pref(self.subtitle_pref),
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
                self, t("msg.saved_title"),
                t("msg.saved")
            )

    def reset_settings(self):
        self.template_edit.setText(
            "{CIM}.{SZEZON}{EPIZOD}"
        )
        self._set_title_programmatic("", manual=False)
        set_combo_id(self.mode_combo, "Sorozat")
        self.normalize_cb.setChecked(True)
        self.lang_norm_cb.setChecked(True)
        self.subdirs_cb.setChecked(False)
        self.conflicts_cb.setChecked(True)
        self.preserve_cb.setChecked(True)
        set_combo_id(self.sort_combo, "Évad → epizód")
        self.subtitle_pref = DEFAULT_SUBTITLE_PREF
        self.subtitle_pref_combo.blockSignals(True)
        set_combo_id(self.subtitle_pref_combo, self.subtitle_pref)
        self.subtitle_pref_combo.blockSignals(False)
        self.on_mode_changed()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    window.center_window()

    sys.exit(app.exec())
