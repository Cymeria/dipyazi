from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QSpinBox, QPushButton, QColorDialog, QLineEdit,
    QCheckBox, QSlider, QTabWidget, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Altyazı Stil Ayarları")
        self.setMinimumSize(500, 450)

        self.settings = current_settings or self.get_default_settings()
        self.setup_ui()

    def get_default_settings(self) -> dict:
        return {
            "font": "Arial",
            "size": 24,
            "color": "#FFFFFF",
            "outline_color": "#000000",
            "outline": 2,
            "shadow": 1,
            "bold": False,
            "italic": False,
            "underline": False,
            "alignment": 2,
            "margin_v": 30,
            "background_opacity": 0,
            "background_color": "#000000"
        }

    def setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        font_tab = QWidget()
        font_layout = QFormLayout(font_tab)

        self.font_combo = QComboBox()
        fonts = [
            "Arial", "Calibri", "Comic Sans MS", "Courier New", "Georgia",
            "Impact", "Lucida Console", "Microsoft Sans Serif", "Palatino Linotype",
            "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"
        ]
        self.font_combo.addItems(fonts)
        idx = self.font_combo.findText(self.settings["font"])
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        font_layout.addRow("Font:", self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self.settings["size"])
        font_layout.addRow("Boyut:", self.size_spin)

        self.bold_check = QCheckBox("Kalın")
        self.bold_check.setChecked(self.settings["bold"])
        font_layout.addRow(self.bold_check)

        self.italic_check = QCheckBox("İtalik")
        self.italic_check.setChecked(self.settings["italic"])
        font_layout.addRow(self.italic_check)

        self.underline_check = QCheckBox("Altı Çizili")
        self.underline_check.setChecked(self.settings["underline"])
        font_layout.addRow(self.underline_check)

        tabs.addTab(font_tab, "Font")

        color_tab = QWidget()
        color_layout = QFormLayout(color_tab)

        color_row = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(40, 24)
        self.color_preview.setStyleSheet(
            f"background-color: {self.settings['color']}; border: 1px solid #3d3d3d; border-radius: 4px;"
        )
        color_row.addWidget(self.color_preview)

        self.color_btn = QPushButton("Renk Seç")
        self.color_btn.clicked.connect(self.choose_color)
        color_row.addWidget(self.color_btn)
        color_row.addStretch()

        color_layout.addRow("Yazı Rengi:", color_row)

        outline_row = QHBoxLayout()
        self.outline_preview = QLabel()
        self.outline_preview.setFixedSize(40, 24)
        self.outline_preview.setStyleSheet(
            f"background-color: {self.settings['outline_color']}; border: 1px solid #3d3d3d; border-radius: 4px;"
        )
        outline_row.addWidget(self.outline_preview)

        self.outline_color_btn = QPushButton("Kenarlık Rengi")
        self.outline_color_btn.clicked.connect(self.choose_outline_color)
        outline_row.addWidget(self.outline_color_btn)
        outline_row.addStretch()

        color_layout.addRow("Kenarlık:", outline_row)

        tabs.addTab(color_tab, "Renk")

        effect_tab = QWidget()
        effect_layout = QFormLayout(effect_tab)

        self.outline_spin = QSpinBox()
        self.outline_spin.setRange(0, 10)
        self.outline_spin.setValue(self.settings["outline"])
        effect_layout.addRow("Kenarlık Kalınlığı:", self.outline_spin)

        self.shadow_spin = QSpinBox()
        self.shadow_spin.setRange(0, 5)
        self.shadow_spin.setValue(self.settings["shadow"])
        effect_layout.addRow("Gölge:", self.shadow_spin)

        alignment_group = QGroupBox("Hizalama")
        alignment_layout = QHBoxLayout(alignment_group)

        self.align_left = QPushButton("Sol")
        self.align_left.setCheckable(True)
        self.align_left.setChecked(self.settings["alignment"] == 1)
        alignment_layout.addWidget(self.align_left)

        self.align_center = QPushButton("Orta")
        self.align_center.setCheckable(True)
        self.align_center.setChecked(self.settings["alignment"] == 2)
        alignment_layout.addWidget(self.align_center)

        self.align_right = QPushButton("Sağ")
        self.align_right.setCheckable(True)
        self.align_right.setChecked(self.settings["alignment"] == 3)
        alignment_layout.addWidget(self.align_right)

        effect_layout.addRow(alignment_group)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        self.margin_spin.setValue(self.settings["margin_v"])
        self.margin_spin.setSuffix(" px")
        effect_layout.addRow("Dikey Kenar Boşluğu:", self.margin_spin)

        tabs.addTab(effect_tab, "Efekt")

        layout.addWidget(tabs)

        preview_group = QGroupBox("Önizleme (1920x1080 Video Üzerinde)")
        preview_layout = QVBoxLayout(preview_group)

        # Video karesi benzeri arka plan
        preview_frame = QWidget()
        preview_frame.setStyleSheet("""
            background-color: #1a1a2e;
            border: 2px solid #3d3d3d;
            border-radius: 8px;
        """)
        preview_frame.setMinimumHeight(150)
        preview_frame_layout = QVBoxLayout(preview_frame)
        preview_frame_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.preview_label = QLabel("Bu bir örnek altyazı satırıdır.\nİkinci satır burada görünebilir.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(60)
        self.preview_label.setStyleSheet("""
            background-color: transparent;
            padding: 10px;
        """)
        preview_frame_layout.addWidget(self.preview_label)

        # Alt bilgi etiketi
        info_hint = QLabel("Önizleme: Altyazı stili gerçek video çıktısına benzer şekilde gösterilir")
        info_hint.setStyleSheet("color: #666666; font-size: 10px; background: transparent;")
        info_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_frame_layout.addWidget(info_hint)

        preview_layout.addWidget(preview_frame)

        layout.addWidget(preview_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("Tamam")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

        self.font_combo.currentTextChanged.connect(self.update_preview)
        self.size_spin.valueChanged.connect(self.update_preview)
        self.bold_check.stateChanged.connect(self.update_preview)
        self.italic_check.stateChanged.connect(self.update_preview)
        self.underline_check.stateChanged.connect(self.update_preview)
        self.outline_spin.valueChanged.connect(self.update_preview)
        self.shadow_spin.valueChanged.connect(self.update_preview)

    def choose_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings["color"]),
            self, "Yazı Rengi Seç"
        )
        if color.isValid():
            self.settings["color"] = color.name()
            self.color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #3d3d3d; border-radius: 4px;"
            )
            self.update_preview()

    def choose_outline_color(self):
        color = QColorDialog.getColor(
            QColor(self.settings["outline_color"]),
            self, "Kenarlık Rengi Seç"
        )
        if color.isValid():
            self.settings["outline_color"] = color.name()
            self.outline_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #3d3d3d; border-radius: 4px;"
            )
            self.update_preview()

    def update_preview(self):
        font = self.font_combo.currentText()
        size = self.size_spin.value()
        color = self.settings["color"]
        outline_color = self.settings["outline_color"]
        outline = self.outline_spin.value()
        bold = "font-weight: bold;" if self.bold_check.isChecked() else ""
        italic = "font-style: italic;" if self.italic_check.isChecked() else ""
        underline = "text-decoration: underline;" if self.underline_check.isChecked() else ""

        # Hizalama ayarını uygula
        alignment = 2 if self.align_center.isChecked() else (1 if self.align_left.isChecked() else 3)
        alignment_map = {
            1: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            2: Qt.AlignmentFlag.AlignCenter,
            3: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        }
        self.preview_label.setAlignment(alignment_map.get(alignment, Qt.AlignmentFlag.AlignCenter))

        # Kenarlık rengini rgba'ya çevir (daha iyi gölge efekti için)
        outline_rgba = self._hex_to_rgba(outline_color, 0.8)

        style = f"""
            background-color: transparent;
            color: {color};
            font-family: '{font}';
            font-size: {size}px;
            {bold}
            {italic}
            {underline}
            padding: 10px;
            border: none;
            text-shadow: {outline}px {outline}px {outline_rgba},
                         -{outline}px -{outline}px {outline_rgba},
                         {outline}px -{outline}px {outline_rgba},
                         -{outline}px {outline}px {outline_rgba};
        """
        self.preview_label.setStyleSheet(style)

    def _hex_to_rgba(self, hex_color: str, alpha: float = 1.0) -> str:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        return "rgba(0, 0, 0, 0.8)"

    def get_settings(self) -> dict:
        return {
            "font": self.font_combo.currentText(),
            "size": self.size_spin.value(),
            "color": self.settings["color"],
            "outline_color": self.settings["outline_color"],
            "outline": self.outline_spin.value(),
            "shadow": self.shadow_spin.value(),
            "bold": self.bold_check.isChecked(),
            "italic": self.italic_check.isChecked(),
            "underline": self.underline_check.isChecked(),
            "alignment": 2 if self.align_center.isChecked() else (1 if self.align_left.isChecked() else 3),
            "margin_v": self.margin_spin.value(),
            "background_opacity": 0,
            "background_color": "#000000"
        }
