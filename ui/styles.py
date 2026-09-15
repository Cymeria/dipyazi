# Modern tasarım sistemi - renk paleti
BG_COLOR = "#0d1017"          # Ana pencere arka planı
SURFACE_COLOR = "#151a23"     # Kart yüzeyi
SURFACE_ALT = "#1b2130"       # İkincil yüzey (input, tablo)
SURFACE_HOVER = "#222a3d"     # Hover yüzeyi
BORDER_COLOR = "#262e3f"      # Kart kenarlığı
BORDER_LIGHT = "#36405a"      # Vurgulu kenarlık
TEXT_COLOR = "#e8eaf0"        # Ana metin
TEXT_MUTED = "#8a93a6"        # İkincil metin
TEXT_DIM = "#5c6579"          # Soluk metin

ACCENT_COLOR = "#6c8cff"      # Ana vurgu (mavi-mor)
ACCENT_2 = "#8b5cf6"          # Gradyan ikinci renk (mor)
HOVER_COLOR = "#829dff"
PRESSED_COLOR = "#5675e0"
DANGER_COLOR = "#ef4444"
SUCCESS_COLOR = "#34d399"
WARNING_COLOR = "#fbbf24"
INFO_COLOR = "#38bdf8"

DARK_THEME = f"""
/* ===================== Genel ===================== */
QMainWindow {{
    background-color: {BG_COLOR};
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}

QWidget#CentralWidget {{
    background-color: {BG_COLOR};
}}

QLabel {{
    color: {TEXT_COLOR};
    background-color: transparent;
}}

QLabel.muted {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QLabel.cardTitle {{
    color: {TEXT_COLOR};
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
}}

/* ===================== Üst Bar ===================== */
QFrame#HeaderBar {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
}}

QLabel#AppTitle {{
    font-size: 17px;
    font-weight: 700;
    color: {TEXT_COLOR};
}}

QLabel#AppSubtitle {{
    font-size: 11px;
    color: {TEXT_MUTED};
}}

QLabel#AppLogo {{
    font-size: 20px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_2});
    border-radius: 10px;
    padding: 4px;
}}

/* Durum çipleri */
QLabel.chip {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 11px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: {TEXT_MUTED};
}}

QLabel.chipOk {{
    background-color: rgba(52, 211, 153, 0.12);
    border: 1px solid rgba(52, 211, 153, 0.35);
    border-radius: 11px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: {SUCCESS_COLOR};
}}

QLabel.chipOff {{
    background-color: rgba(239, 68, 68, 0.10);
    border: 1px solid rgba(239, 68, 68, 0.30);
    border-radius: 11px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
    color: #f87171;
}}

/* ===================== Kartlar ===================== */
QFrame.card {{
    background-color: {SURFACE_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 14px;
}}

QFrame.card:hover {{
    border: 1px solid {BORDER_LIGHT};
}}

/* ===================== Butonlar ===================== */
QPushButton {{
    background-color: {SURFACE_ALT};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {SURFACE_HOVER};
    border: 1px solid {BORDER_LIGHT};
}}

QPushButton:pressed {{
    background-color: {SURFACE_COLOR};
}}

QPushButton:disabled {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_COLOR};
}}

QPushButton.primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_2});
    color: #ffffff;
    border: none;
}}

QPushButton.primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {HOVER_COLOR}, stop:1 #9d74f8);
}}

QPushButton.primary:pressed {{
    background: {PRESSED_COLOR};
}}

QPushButton.primary:disabled {{
    background: {SURFACE_ALT};
    color: {TEXT_DIM};
}}

QPushButton.success {{
    background-color: rgba(52, 211, 153, 0.15);
    color: {SUCCESS_COLOR};
    border: 1px solid rgba(52, 211, 153, 0.4);
}}

QPushButton.success:hover {{
    background-color: rgba(52, 211, 153, 0.25);
}}

QPushButton.success:disabled {{
    background-color: {SURFACE_COLOR};
    color: {TEXT_DIM};
    border: 1px solid {BORDER_COLOR};
}}

QPushButton.danger {{
    background-color: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
}}

QPushButton.danger:hover {{
    background-color: rgba(239, 68, 68, 0.22);
}}

QPushButton.ghost {{
    background-color: transparent;
    border: 1px solid transparent;
    color: {TEXT_MUTED};
}}

QPushButton.ghost:hover {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_COLOR};
}}

QPushButton.iconBtn {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 17px;
    padding: 0px;
    font-size: 14px;
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
}}

QPushButton.iconBtn:hover {{
    background-color: {SURFACE_HOVER};
    border: 1px solid {ACCENT_COLOR};
}}

QPushButton.playBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_2});
    color: #ffffff;
    border: none;
    border-radius: 21px;
    font-size: 15px;
    min-width: 42px;
    max-width: 42px;
    min-height: 42px;
    max-height: 42px;
    padding: 0px;
}}

QPushButton.playBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {HOVER_COLOR}, stop:1 #9d74f8);
}}

QPushButton.playBtn:disabled {{
    background: {SURFACE_ALT};
    color: {TEXT_DIM};
}}

/* ===================== Girdiler ===================== */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 9px;
    padding: 8px 12px;
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT_COLOR};
}}

QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border: 1px solid {BORDER_LIGHT};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {ACCENT_COLOR};
    background-color: {SURFACE_HOVER};
}}

QComboBox {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 9px;
    padding: 8px 12px;
    color: {TEXT_COLOR};
    min-height: 20px;
}}

QComboBox:hover {{
    border: 1px solid {BORDER_LIGHT};
    background-color: {SURFACE_HOVER};
}}

QComboBox:focus {{
    border: 1px solid {ACCENT_COLOR};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT_MUTED};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 9px;
    selection-background-color: {ACCENT_COLOR};
    selection-color: #ffffff;
    color: {TEXT_COLOR};
    outline: none;
    padding: 4px;
}}

/* ===================== İlerleme ===================== */
QProgressBar {{
    border: none;
    border-radius: 5px;
    text-align: center;
    background-color: {SURFACE_ALT};
    min-height: 10px;
    max-height: 10px;
    font-size: 1px;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_2});
    border-radius: 5px;
}}

/* ===================== Tablo ===================== */
QTableWidget {{
    background-color: {SURFACE_COLOR};
    alternate-background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: rgba(108, 140, 255, 0.18);
    selection-color: {TEXT_COLOR};
    color: {TEXT_COLOR};
    outline: none;
}}

QTableWidget::item {{
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
}}

QTableWidget::item:selected {{
    background-color: rgba(108, 140, 255, 0.18);
    color: {TEXT_COLOR};
}}

QTableWidget::item:hover {{
    background-color: rgba(108, 140, 255, 0.08);
}}

QHeaderView::section {{
    background-color: {SURFACE_ALT};
    color: {TEXT_MUTED};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {BORDER_COLOR};
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
}}

QTableCornerButton::section {{
    background-color: {SURFACE_ALT};
    border: none;
}}

/* ===================== Kaydırma Çubukları ===================== */
QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background-color: {BORDER_LIGHT};
    min-height: 30px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT_COLOR};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 10px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background-color: {BORDER_LIGHT};
    min-width: 30px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {ACCENT_COLOR};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ===================== Ayırıcı ===================== */
QSplitter::handle {{
    background-color: transparent;
}}

QSplitter::handle:horizontal {{
    width: 6px;
}}

QSplitter::handle:vertical {{
    height: 6px;
}}

QSplitter::handle:hover {{
    background-color: rgba(108, 140, 255, 0.25);
    border-radius: 3px;
}}

/* ===================== Sekmeler ===================== */
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    background-color: {SURFACE_COLOR};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: none;
    padding: 9px 18px;
    font-weight: 600;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}

QTabBar::tab:selected {{
    color: {ACCENT_COLOR};
    border-bottom: 2px solid {ACCENT_COLOR};
}}

QTabBar::tab:hover {{
    color: {TEXT_COLOR};
}}

/* ===================== Metin Alanları ===================== */
QTextEdit, QPlainTextEdit {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 9px;
    color: {TEXT_COLOR};
    padding: 8px;
    selection-background-color: {ACCENT_COLOR};
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_COLOR};
}}

/* ===================== Kaydırıcılar ===================== */
QSlider::groove:horizontal {{
    border: none;
    height: 5px;
    background: {SURFACE_ALT};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_COLOR}, stop:1 {ACCENT_2});
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: #ffffff;
    border: 2px solid {ACCENT_COLOR};
    width: 14px;
    height: 14px;
    margin: -6px 0;
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: {ACCENT_COLOR};
    border: 2px solid #ffffff;
}}

/* ===================== Onay Kutuları ===================== */
QCheckBox {{
    spacing: 8px;
    color: {TEXT_MUTED};
}}

QCheckBox:hover {{
    color: {TEXT_COLOR};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {BORDER_LIGHT};
    border-radius: 5px;
    background-color: {SURFACE_ALT};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT_COLOR};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_COLOR};
    border-color: {ACCENT_COLOR};
}}

QRadioButton {{
    spacing: 8px;
    color: {TEXT_MUTED};
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {BORDER_LIGHT};
    border-radius: 10px;
    background-color: {SURFACE_ALT};
}}

QRadioButton::indicator:checked {{
    background-color: {ACCENT_COLOR};
    border-color: {ACCENT_COLOR};
}}

/* ===================== GroupBox (dialoglar için) ===================== */
QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    margin-top: 1em;
    padding-top: 12px;
    font-weight: 600;
    color: {ACCENT_COLOR};
    background-color: {SURFACE_COLOR};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

/* ===================== Menü ===================== */
QMenu {{
    background-color: {SURFACE_ALT};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 6px;
    color: {TEXT_COLOR};
}}

QMenu::item:selected {{
    background-color: {ACCENT_COLOR};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {BORDER_COLOR};
    margin: 6px 8px;
}}

/* ===================== Araç İpucu ===================== */
QToolTip {{
    background-color: {SURFACE_HOVER};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_LIGHT};
    padding: 8px 10px;
    border-radius: 4px;
    font-size: 12px;
}}

/* ===================== Mesaj Kutuları / Dialoglar ===================== */
QMessageBox, QDialog {{
    background-color: {SURFACE_COLOR};
}}

QMessageBox QLabel, QDialog QLabel {{
    color: {TEXT_COLOR};
}}
"""

# Eski açık tema (geriye dönük uyumluluk için korunuyor)
LIGHT_THEME = DARK_THEME
