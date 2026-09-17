"""Test Version 2 — GUI appearance tokens and stylesheets.

Visual only. No engine, pairing, rename, or settings logic.
"""

LIGHT = {
    "chrome": "#b7c2d0",
    "window": "#eef2f7",
    "surface": "#ffffff",
    "surface_alt": "#e6edf4",
    "raised": "#ffffff",
    "sunken": "#d5dde6",
    "border": "#8a97a8",
    "border_strong": "#5d6d80",
    "text": "#121c2b",
    "text_secondary": "#3a4658",
    "text_muted": "#5a6573",
    "accent": "#1a5fd4",
    "accent_hover": "#144db0",
    "accent_fill": "#1a5fd4",
    "accent_soft": "#e6f0fc",
    "success": "#186338",
    "success_hover": "#145530",
    "success_fill": "#1c7340",
    "success_soft": "#e6f5ec",
    "warning": "#8a5800",
    "warning_fill": "#c48610",
    "warning_soft": "#fff6df",
    "danger": "#b71c1c",
    "danger_hover": "#931616",
    "danger_fill": "#c62828",
    "danger_soft": "#fbeaea",
    "selected": "#d4e4fb",
    "hover": "#e7edf5",
    "row_line": "#d7dee6",
    "row_ok": "#e8f6ee",
    "row_review": "#fff7e6",
    "row_blocked": "#fbecee",
    "handle": "#8b97a8",
    "handle_hover": "#6d7a8c",
    "white": "#ffffff",
    "window_rim": "#3f5168",
    "field": "#ffffff",
    "overlay": "#ffffff",
}

DARK = {
    "chrome": "#10141c",
    "window": "#161b26",
    "surface": "#1e2533",
    "surface_alt": "#252d3e",
    "raised": "#2a3346",
    "sunken": "#141924",
    "border": "#3a455c",
    "border_strong": "#5a6880",
    "text": "#e8eef8",
    "text_secondary": "#a8b4c8",
    "text_muted": "#7d8aa0",
    "accent": "#7aa7ff",
    "accent_hover": "#95baff",
    "accent_fill": "#3d6fd6",
    "accent_soft": "#243656",
    "success": "#7dcea0",
    "success_hover": "#93d9b0",
    "success_fill": "#2f8f5b",
    "success_soft": "#1c3a2c",
    "warning": "#e0b34d",
    "warning_fill": "#b88920",
    "warning_soft": "#3a3118",
    "danger": "#e06b6b",
    "danger_hover": "#ef8585",
    "danger_fill": "#c44545",
    "danger_soft": "#3a2226",
    "selected": "#2a4570",
    "hover": "#2c3548",
    "row_line": "#2c3448",
    "row_ok": "#1c3328",
    "row_review": "#3a321c",
    "row_blocked": "#3a2428",
    "handle": "#5a6880",
    "handle_hover": "#7d8aa0",
    "white": "#ffffff",
    "window_rim": "#7a889e",
    "field": "#303a4e",
    "overlay": "#3d4860",
}


def theme_tokens(dark):
    return dict(DARK if dark else LIGHT)


def copy_state_colors(tok):
    """Status-cell colors for copy/rename outcomes. Keys match engine copy_status."""
    danger = (tok["danger"], tok["danger_soft"])
    return {
        "Már létezik": danger,
        "Névütközés": danger,
        "Nem egyező pár": danger,
        "Hiba": danger,
        "Nem fért el": (tok["warning"], tok["warning_soft"]),
        "Megszakítva": (tok["danger"], tok["danger_soft"]),
        "Átmásolva": (tok["success"], tok["success_soft"]),
    }


def _fill(template, tok):
    """Replace $tokens. Longer names first so $window_rim is not eaten by $window."""
    out = template
    for key in sorted(tok, key=len, reverse=True):
        out = out.replace("$" + key, tok[key])
    return out


def filled_button_stylesheet(tok, role="primary"):
    """Kitöltött CTA: fehér felirat mindig a kitöltött háttéren."""
    roles = {
        "primary": (tok["accent_fill"], tok["accent_hover"]),
        "success": (tok["success_fill"], tok["success_hover"]),
        "danger": (tok["danger_fill"], tok["danger_hover"]),
        "dev": ("#6a1b9a", "#4a126d"),
        "muted": ("#455a64", "#37474f"),
    }
    bg, hover = roles[role]
    fg = tok["white"]
    return (
        f"QPushButton {{ background-color: {bg}; color: {fg}; font-weight: 600; "
        f"padding: 6px 14px; border: 1px solid {bg}; border-radius: 6px; }}"
        f"QPushButton:hover {{ background-color: {hover}; border-color: {hover}; "
        f"color: {fg}; }}"
        f"QPushButton:pressed, QPushButton:open {{ background-color: {bg}; "
        f"color: {fg}; border-color: {bg}; }}"
        f"QPushButton:disabled {{ background-color: {tok['sunken']}; "
        f"color: {tok['text_muted']}; border-color: {tok['border']}; }}"
        "QPushButton::menu-indicator { subcontrol-origin: padding; "
        "subcontrol-position: center right; left: -4px; }"
    )


def primary_button_stylesheet(tok):
    """Widget-level CTA style. Menu-buttons ignore app QSS background on Windows."""
    return filled_button_stylesheet(tok, "primary")


def plain_button_stylesheet(tok):
    """Teljes widget-level gomb QSS. Fusion app-QSS border nélkül natívan fest."""
    return (
        f"QPushButton {{ background-color: {tok['raised']}; color: {tok['text']}; "
        f"font-weight: 400; padding: 6px 12px; "
        f"border: 1px solid {tok['border_strong']}; border-radius: 6px; }}"
        f"QPushButton:hover {{ background-color: {tok['hover']}; "
        f"border: 1px solid {tok['window_rim']}; color: {tok['text']}; }}"
        f"QPushButton:pressed, QPushButton:open {{ background-color: {tok['sunken']}; "
        f"border: 1px solid {tok['border_strong']}; color: {tok['text']}; }}"
        f"QPushButton:focus {{ border: 1px solid {tok['accent']}; }}"
        f"QPushButton:disabled {{ background-color: {tok['sunken']}; "
        f"color: {tok['text_muted']}; border: 1px solid {tok['border']}; }}"
        "QPushButton::menu-indicator { subcontrol-origin: padding; "
        "subcontrol-position: center right; left: -4px; }"
    )


def review_button_stylesheet(tok):
    """Checkable files-tab gomb: aktív állapot megmarad a widget-level QSS mellett."""
    return plain_button_stylesheet(tok) + (
        f"QPushButton:checked, QPushButton[active=\"true\"] {{ "
        f"background-color: {tok['warning_soft']}; border: 1px solid {tok['warning']}; "
        f"color: {tok['text']}; font-weight: 600; }}"
    )


def rename_button_stylesheet(tok, ready):
    """Átnevezés: inaktív visszafogott, ready = zöld CTA fehér felirattal."""
    if ready:
        qss = filled_button_stylesheet(tok, "success")
        return qss.replace("padding: 6px 14px", "padding: 8px 18px; font-size: 11pt")
    fg = tok["text_secondary"]
    bg = tok["sunken"]
    return (
        f"QPushButton {{ background-color: {bg}; color: {fg}; font-weight: 600; "
        f"font-size: 11pt; padding: 8px 18px; border: 1px solid {tok['border_strong']}; "
        f"border-radius: 6px; }}"
        f"QPushButton:disabled {{ background-color: {bg}; color: {tok['text_muted']}; "
        f"border: 1px solid {tok['border']}; }}"
    )


def build_app_stylesheet(dark):
    tok = theme_tokens(dark)
    qss = _fill(_APP_QSS, tok)
    if dark:
        qss += _fill(_DARK_EXTRAS, tok)
    else:
        qss += _fill(_LIGHT_EXTRAS, tok)
    return qss


_APP_QSS = """
QMainWindow {
    background: $chrome;
    color: $text;
}
QWidget#centralRoot {
    background: $window;
    color: $text;
    border: 2px solid $window_rim;
    border-radius: 8px;
}
QFrame#accentBar {
    background: $accent_fill;
    border: none;
    min-height: 3px;
    max-height: 3px;
}
QFrame#topBar {
    background: $chrome;
    border: none;
    border-bottom: 1px solid $border_strong;
}
QFrame#toolbarCluster {
    background: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
}
QFrame#toolbarCluster QPushButton {
    min-height: 30px;
    background-color: $raised;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 6px;
}
QFrame#toolbarCluster QPushButton:hover {
    background-color: $hover;
    border: 1px solid $window_rim;
    color: $text;
}
QFrame#toolbarCluster QPushButton:pressed,
QFrame#toolbarCluster QPushButton:open {
    background-color: $sunken;
    border: 1px solid $border_strong;
    color: $text;
}
QFrame#toolbarCluster QPushButton:disabled {
    background-color: $sunken;
    color: $text_muted;
    border: 1px solid $border;
}
QFrame#iconCluster {
    background: transparent;
    border: 1px solid $border;
    border-radius: 8px;
}
QFrame#iconCluster QPushButton {
    min-height: 0px;
    padding: 0px;
    border: 1px solid transparent;
    border-radius: 6px;
}
QFrame#iconCluster QPushButton:hover {
    background-color: $hover;
    border: 1px solid $border;
}
QFrame#iconCluster QPushButton:checked {
    border: 1px solid $accent;
    background-color: $accent_soft;
}
QPushButton#themeToggle {
    background-color: transparent;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 1px;
    min-height: 0px;
    font-weight: 400;
}
QPushButton#themeToggle:hover {
    border: 1px solid $border_strong;
    background-color: $hover;
}
QPushButton#themeToggle:pressed {
    background-color: $sunken;
}
QPushButton#themeToggle:focus {
    border: 1px solid $accent;
}
QPushButton#themeToggle[dark="true"] {
    background-color: $raised;
    border-color: $window_rim;
}
QFrame#renameFrame {
    background: $sunken;
    border: 1px solid $border;
    border-radius: 8px;
}
QFrame#renameFrame[ready="true"] {
    background: $success_soft;
    border: 1px solid $success;
}
QFrame#footerBar {
    background: $sunken;
    border: none;
    border-top: 1px solid $border;
}
QLabel {
    color: $text;
    font-weight: 400;
}
QLabel#mutedLabel {
    color: $text_secondary;
}
QLabel#settingsIntro {
    color: $text_secondary;
    padding: 8px 10px;
    background: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
}
QLabel#sectionHeading {
    color: $text_secondary;
    font-size: 10pt;
    font-weight: 600;
    padding: 4px 2px 0 2px;
}
QLabel#testBadge {
    color: $accent;
    font-weight: 600;
    padding: 2px 8px;
    border: 1px solid $accent;
    border-radius: 4px;
    background: $accent_soft;
}
QLabel#emptyState {
    color: $text_secondary;
    padding: 22px;
    border: 1px dashed $border_strong;
    border-radius: 10px;
    background: $surface_alt;
    font-size: 11pt;
}
QLabel#detectBanner {
    padding: 8px 12px;
    border: 1px solid $border;
    border-radius: 8px;
    background: $surface_alt;
    color: $text;
}
QLabel#detectBanner[ok="true"] {
    background: $success_soft;
    border: 1px solid $success;
    color: $text;
}
QLabel#welcomeKicker {
    color: $accent;
    font-size: 9pt;
    font-weight: 600;
    letter-spacing: 0.6px;
}
QLabel#welcomeHeadline {
    font-size: 18pt;
    font-weight: 700;
    color: $text;
}
QLabel#welcomeIntro {
    font-size: 10.5pt;
    color: $text_secondary;
}
QLabel#welcomeNote {
    color: $text_secondary;
    padding: 8px 10px;
    background: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
}
QLabel#monoSample {
    font-family: Consolas, "Cascadia Mono", monospace;
    font-size: 9pt;
    color: $text;
    padding: 3px 0;
}
QLabel#exampleHeading {
    font-weight: 600;
    color: $text_secondary;
    font-size: 9pt;
}
QFrame#exampleCard {
    background: $surface_alt;
    border: 1px solid $border;
    border-radius: 10px;
}
QLabel#arrowLabel {
    color: $accent;
    font-size: 16pt;
    font-weight: 700;
}

QTabWidget::pane {
    border: 1px solid $border_strong;
    border-radius: 8px;
    background: $surface;
    top: -1px;
    padding: 6px;
}
QTabBar::tab {
    background: $sunken;
    color: $text_secondary;
    padding: 8px 16px;
    margin-right: 3px;
    border: 1px solid $border;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 88px;
}
QTabBar::tab:selected {
    background: $surface;
    color: $text;
    font-weight: 600;
    border-color: $border_strong;
}
QTabBar::tab:hover:!selected {
    color: $text;
    background: $hover;
}

QPushButton {
    background-color: $raised;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
    font-weight: 400;
}
QPushButton:hover {
    background-color: $hover;
    color: $text;
    border-color: $window_rim;
}
QPushButton:pressed {
    background-color: $sunken;
    color: $text;
    border-color: $border_strong;
}
QPushButton:focus {
    border: 1px solid $accent;
}
QPushButton:disabled {
    color: $text_muted;
    background-color: $sunken;
    border-color: $border;
}
QPushButton:checked {
    border: 2px solid $accent;
    background-color: $accent_soft;
    color: $text;
}
QPushButton:flat {
    background-color: transparent;
    border: none;
    color: $text_secondary;
    min-height: 22px;
    padding: 2px 8px;
}
QPushButton:flat:hover {
    color: $accent;
    background-color: $accent_soft;
    border-radius: 4px;
}

QPushButton#btnPrimary {
    background-color: $accent_fill;
    color: $white;
    font-weight: 600;
    padding: 6px 14px;
    border: 1px solid $accent_fill;
    border-radius: 6px;
}
QPushButton#btnPrimary:hover,
QPushButton#btnPrimary:pressed,
QPushButton#btnPrimary:open {
    background-color: $accent_hover;
    border-color: $accent_hover;
    color: $white;
}
QPushButton#btnPrimary:pressed,
QPushButton#btnPrimary:open {
    background-color: $accent_fill;
    border-color: $accent_fill;
    color: $white;
}
QPushButton#btnPrimary:disabled {
    background-color: $sunken;
    color: $text_muted;
    border-color: $border;
}

QPushButton#btnRename {
    background-color: $sunken;
    color: $text_muted;
    font-size: 11pt;
    font-weight: 600;
    padding: 8px 18px;
    border: 1px solid $border_strong;
    border-radius: 6px;
}
QPushButton#btnRename[ready="true"] {
    background-color: $success_fill;
    color: $white;
    border: 1px solid $success_fill;
}
QPushButton#btnRename[ready="true"]:hover,
QPushButton#btnRename[ready="true"]:pressed {
    background-color: $success_hover;
    border-color: $success_hover;
    color: $white;
}
QPushButton#btnRename:disabled {
    background-color: $sunken;
    color: $text_muted;
    border: 1px solid $border;
}

QPushButton#btnDanger {
    background-color: $danger_fill;
    color: $white;
    font-weight: 600;
    padding: 5px 10px;
    border: 1px solid $danger_fill;
    border-radius: 6px;
}
QPushButton#btnDanger:hover,
QPushButton#btnDanger:pressed {
    background-color: $danger_hover;
    border-color: $danger_hover;
    color: $white;
}
QPushButton#btnDanger:disabled {
    background-color: $sunken;
    color: $text_muted;
    border-color: $border;
}

QPushButton#btnDev {
    background-color: #6a1b9a;
    color: $white;
    font-weight: 600;
    padding: 6px 12px;
    border: 1px solid #4a126d;
    border-radius: 6px;
}
QPushButton#btnDev:hover,
QPushButton#btnDev:pressed {
    background-color: #4a126d;
    color: $white;
}
QPushButton#btnMuted {
    background-color: #455a64;
    color: $white;
    font-weight: 600;
    padding: 6px 12px;
    border: 1px solid #263238;
    border-radius: 6px;
}
QPushButton#btnMuted:hover,
QPushButton#btnMuted:pressed {
    background-color: #37474f;
    color: $white;
}
QPushButton#btnSuccess {
    background-color: $success_fill;
    color: $white;
    font-weight: 600;
    padding: 6px 18px;
    border: 1px solid $success_fill;
    border-radius: 6px;
}
QPushButton#btnSuccess:hover,
QPushButton#btnSuccess:pressed {
    background-color: $success_hover;
    color: $white;
}

QPushButton#showReviewOnly[active="true"] {
    background-color: $warning_soft;
    border: 1px solid $warning;
    color: $text;
    font-weight: 600;
}

QLineEdit, QTextEdit {
    background-color: $sunken;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 26px;
    selection-background-color: $selected;
    selection-color: $text;
}
QLineEdit#searchField {
    background-color: $sunken;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 26px;
}
QComboBox {
    background-color: $surface;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    min-height: 26px;
    selection-background-color: $selected;
    selection-color: $text;
}
QLineEdit:focus, QLineEdit#searchField:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid $accent;
    color: $text;
}
QLineEdit:disabled, QComboBox:disabled {
    background-color: $sunken;
    color: $text_muted;
}
QComboBox QAbstractItemView {
    background-color: $raised;
    color: $text;
    selection-background-color: $selected;
    selection-color: $text;
    border: 1px solid $border;
    outline: none;
}
QTextEdit {
    min-height: 0px;
}

QGroupBox {
    font-weight: 400;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    background: $surface_alt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: $text_secondary;
    font-weight: 600;
}

QTableWidget, QTableView {
    background: $surface;
    alternate-background-color: $surface_alt;
    color: $text;
    gridline-color: transparent;
    border: 1px solid $border;
    border-radius: 8px;
    selection-background-color: $selected;
    selection-color: $text;
    outline: none;
}
QTableWidget::item {
    padding: 6px 8px;
    border-bottom: 1px solid $row_line;
}
QTableWidget::item:selected, QTableView::item:selected {
    background: $selected;
    color: $text;
}
QHeaderView::section {
    background: $sunken;
    color: $text_secondary;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid $border_strong;
    border-right: 1px solid $row_line;
    font-weight: 600;
}
QTableCornerButton::section {
    background: $sunken;
    border: none;
}

QScrollBar:vertical {
    background: $sunken;
    width: 12px;
    margin: 2px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background: $handle;
    min-height: 32px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: $handle_hover;
}
QScrollBar:horizontal {
    background: $sunken;
    height: 12px;
    margin: 2px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background: $handle;
    min-width: 32px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal:hover {
    background: $handle_hover;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}

QProgressBar {
    background: $sunken;
    border: 1px solid $border;
    border-radius: 6px;
    text-align: center;
    color: $text;
    min-height: 18px;
}
QProgressBar::chunk {
    background: $accent_fill;
    border-radius: 5px;
}

QCheckBox {
    color: $text;
    spacing: 8px;
}

QMenu {
    background-color: $raised;
    color: $text;
    border: 1px solid $border;
    padding: 4px;
}
QMenu::item {
    padding: 6px 22px 6px 12px;
    border-radius: 4px;
    color: $text;
}
QMenu::item:selected {
    background-color: $selected;
    color: $text;
}
QMenu::separator {
    height: 1px;
    background: $border;
    margin: 4px 8px;
}

QToolTip {
    padding: 8px 10px;
    border: 1px solid $border_strong;
    background: $raised;
    color: $text;
    font-size: 10pt;
}

QDialog {
    background-color: $window;
    color: $text;
}
QMessageBox {
    background-color: $window;
}
QMessageBox QLabel {
    color: $text;
}
"""

_LIGHT_EXTRAS = """
QPushButton {
    background-color: $raised;
    color: $text;
    border: 1px solid $border_strong;
}
QPushButton:hover {
    background-color: $hover;
    color: $text;
    border-color: $window_rim;
}
QPushButton:pressed {
    background-color: $sunken;
    color: $text;
    border-color: $border_strong;
}
QPushButton:focus {
    border: 1px solid $accent;
}
QPushButton:disabled {
    background-color: $sunken;
    color: $text_muted;
    border-color: $border;
}
QPushButton:checked {
    background-color: $accent_soft;
    color: $text;
    border: 2px solid $accent;
}
QPushButton#btnPrimary,
QPushButton#btnPrimary:hover,
QPushButton#btnPrimary:pressed,
QPushButton#btnPrimary:open {
    background-color: $accent_fill;
    color: $white;
    border: 1px solid $accent_fill;
}
QPushButton#btnPrimary:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
    color: $white;
}
QTabBar::tab {
    color: $text;
    background-color: $surface_alt;
    border: 1px solid $border_strong;
    border-bottom: none;
}
QTabBar::tab:selected {
    color: $text;
    background-color: $surface;
    border: 1px solid $border_strong;
    border-bottom: 2px solid $accent;
    font-weight: 600;
}
QTabWidget::pane {
    border: 1px solid $border_strong;
}
QHeaderView::section {
    color: $text;
    background-color: $surface_alt;
    border: 1px solid $border_strong;
}
QToolTip {
    background-color: $chrome;
    color: $text;
    border: 1px solid $window_rim;
}
QLineEdit, QTextEdit, QLineEdit#searchField {
    background-color: $field;
    color: $text;
    border: 1px solid $border_strong;
}
QLineEdit:disabled, QTextEdit:disabled, QLineEdit#searchField:disabled,
QComboBox:disabled {
    background-color: $sunken;
    color: $text_muted;
    border: 1px solid $border;
}
QComboBox {
    background-color: $field;
    color: $text;
    border: 1px solid $border_strong;
}
QComboBox QAbstractItemView {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
}
QGroupBox {
    border: 1px solid $border_strong;
}
QTableWidget, QTableView {
    border: 1px solid $border_strong;
}
QFrame#toolbarCluster {
    border: 1px solid $border_strong;
}
QFrame#renameFrame {
    border: 1px solid $border_strong;
}
"""

_DARK_EXTRAS = """
QComboBox {
    background-color: $field;
    color: $text;
    border: 1px solid $border_strong;
}
QComboBox:hover {
    background-color: $field;
    border: 1px solid $window_rim;
    color: $text;
}
QComboBox:focus, QComboBox:on {
    background-color: $field;
    border: 1px solid $accent;
    color: $text;
}
QComboBox:disabled {
    background-color: $sunken;
    color: $text_muted;
    border: 1px solid $border;
}
QComboBox QAbstractItemView {
    background-color: $overlay;
    color: $text;
    border: 1px solid $border_strong;
    selection-background-color: $selected;
    selection-color: $text;
    outline: none;
}
"""
