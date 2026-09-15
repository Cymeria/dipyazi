import os
import subprocess
import tempfile
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGroupBox, QFormLayout, QComboBox, QSpinBox, QCheckBox,
    QColorDialog, QMessageBox, QButtonGroup
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics


class StylePreviewDialog(QDialog):
    """Video karesi üzerinde altyazı stilinin gerçek zamanlı önizlemesi."""

    def __init__(self, parent=None, video_path=None, subtitle_segments=None,
                 current_settings=None, on_apply=None):
        super().__init__(parent)
        self.setWindowTitle("Altyazı Stil Önizleme")
        self.setMinimumSize(1100, 650)
        self.video_path = video_path
        self.subtitle_segments = subtitle_segments or []
        self.current_frame = None
        self.current_time = 0.0
        self._on_apply = on_apply

        # Renkleri ayrı tut, paylaşımlı dict ile karışmasın
        self._initial = current_settings or {}
        self._text_color = self._initial.get("color", "#FFFFFF")
        self._outline_color = self._initial.get("outline_color", "#000000")

        self.setup_ui()
        self.load_video_frames()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(8)

        # Sol panel - ayarlar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(280)

        left_layout.addWidget(QLabel("Stil Ayarları"))
        left_layout.addSpacing(4)

        form = QFormLayout()

        self.font_combo = QComboBox()
        fonts = [
            "Arial", "Calibri", "Courier New", "Georgia", "Impact",
            "Segoe UI", "Tahoma", "Times New Roman", "Verdana"
        ]
        self.font_combo.addItems(fonts)
        idx = self.font_combo.findText(self._initial.get("font", "Arial"))
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)
        form.addRow("Font:", self.font_combo)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 72)
        self.size_spin.setValue(self._initial.get("size", 24))
        form.addRow("Boyut:", self.size_spin)

        self.bold_check = QCheckBox("Kalın")
        self.bold_check.setChecked(self._initial.get("bold", False))
        form.addRow(self.bold_check)

        self.italic_check = QCheckBox("İtalik")
        self.italic_check.setChecked(self._initial.get("italic", False))
        form.addRow(self.italic_check)

        self.underline_check = QCheckBox("Altı Çizili")
        self.underline_check.setChecked(self._initial.get("underline", False))
        form.addRow(self.underline_check)

        self.outline_spin = QSpinBox()
        self.outline_spin.setRange(0, 10)
        self.outline_spin.setValue(self._initial.get("outline", 2))
        form.addRow("Kenarlık:", self.outline_spin)

        self.shadow_spin = QSpinBox()
        self.shadow_spin.setRange(0, 5)
        self.shadow_spin.setValue(self._initial.get("shadow", 1))
        form.addRow("Gölge:", self.shadow_spin)

        self.margin_spin = QSpinBox()
        self.margin_spin.setRange(0, 200)
        src = self._initial or {}
        self.margin_spin.setValue(src.get("margin_v", 30))
        self.margin_spin.setSuffix(" px")
        form.addRow("Kenar Boşluğu:", self.margin_spin)

        left_layout.addLayout(form)

        # Renk butonları
        color_group = QGroupBox("Renkler")
        color_layout = QVBoxLayout(color_group)

        self.color_btn = QPushButton("Yazı Rengi")
        self._update_color_btn_style(self.color_btn, self._text_color)
        self.color_btn.clicked.connect(self.pick_text_color)
        color_layout.addWidget(self.color_btn)

        self.outline_color_btn = QPushButton("Kenarlık Rengi")
        self._update_color_btn_style(self.outline_color_btn, self._outline_color)
        self.outline_color_btn.clicked.connect(self.pick_outline_color)
        color_layout.addWidget(self.outline_color_btn)

        left_layout.addWidget(color_group)

        # Hizalama (exclusive grup)
        align_group_box = QGroupBox("Hizalama")
        align_layout = QHBoxLayout(align_group_box)

        self.align_left = QPushButton("Sol")
        self.align_left.setCheckable(True)
        align_layout.addWidget(self.align_left)

        self.align_center = QPushButton("Orta")
        self.align_center.setCheckable(True)
        align_layout.addWidget(self.align_center)

        self.align_right = QPushButton("Sağ")
        self.align_right.setCheckable(True)
        align_layout.addWidget(self.align_right)

        self._align_group = QButtonGroup(self)
        self._align_group.addButton(self.align_left, 1)
        self._align_group.addButton(self.align_center, 2)
        self._align_group.addButton(self.align_right, 3)

        alignment = src.get("alignment", 2)
        if alignment == 1:
            self.align_left.setChecked(True)
        elif alignment == 3:
            self.align_right.setChecked(True)
        else:
            self.align_center.setChecked(True)

        left_layout.addWidget(align_group_box)

        # Zaman seçici
        if self.subtitle_segments:
            time_group = QGroupBox("Zaman Seçimi")
            time_layout = QVBoxLayout(time_group)

            self.time_slider_label = QLabel("İlk altyazı gösteriliyor")
            self.time_slider_label.setStyleSheet("color: #888888;")
            time_layout.addWidget(self.time_slider_label)

            prev_btn = QPushButton("Önceki Altyazı")
            prev_btn.clicked.connect(self.prev_subtitle)
            time_layout.addWidget(prev_btn)

            next_btn = QPushButton("Sonraki Altyazı")
            next_btn.clicked.connect(self.next_subtitle)
            time_layout.addWidget(next_btn)

            left_layout.addWidget(time_group)

        left_layout.addStretch()

        # Sağ panel - video önizleme
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.preview_label = QLabel("Video yükleniyor...")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(640, 360)
        self.preview_label.setStyleSheet("background-color: #000; border-radius: 6px;")
        right_layout.addWidget(self.preview_label)

        self.subtitle_index = 0
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #888888;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.info_label)

        layout.addWidget(left_panel)
        layout.addWidget(right_panel)

        # Alt butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # Sinyaller
        self.font_combo.currentTextChanged.connect(self.update_preview)
        self.size_spin.valueChanged.connect(self.update_preview)
        self.bold_check.stateChanged.connect(self.update_preview)
        self.italic_check.stateChanged.connect(self.update_preview)
        self.underline_check.stateChanged.connect(self.update_preview)
        self.outline_spin.valueChanged.connect(self.update_preview)
        self.shadow_spin.valueChanged.connect(self.update_preview)
        self.margin_spin.valueChanged.connect(self.update_preview)
        self.align_left.clicked.connect(self.update_preview)
        self.align_center.clicked.connect(self.update_preview)
        self.align_right.clicked.connect(self.update_preview)

    def load_video_frames(self):
        if not self.video_path:
            self.preview_label.setText("Video yüklenmedi")
            return

        # Tek bir kare çek, hepsinde kullan
        self._grab_frame(0.5)

    def _grab_frame(self, time_sec):
        tmp_dir = tempfile.mkdtemp(prefix="altyazi_preview_")
        frame_path = os.path.join(tmp_dir, "frame.jpg")
        try:
            cmd = [
                "ffmpeg", "-ss", str(time_sec), "-i", self.video_path,
                "-vframes", "1", "-q:v", "2", "-y", frame_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=5)
            if os.path.exists(frame_path):
                self.current_frame = QPixmap(frame_path)
                self.update_preview()
        except Exception:
            self.preview_label.setText("Video karesi alınamadı")

    def prev_subtitle(self):
        if self.subtitle_segments and self.subtitle_index > 0:
            self.subtitle_index -= 1
            self.update_preview()

    def next_subtitle(self):
        if self.subtitle_segments and self.subtitle_index < len(self.subtitle_segments) - 1:
            self.subtitle_index += 1
            self.update_preview()

    def get_current_settings(self) -> dict:
        alignment = self._align_group.checkedId()

        return {
            "font": self.font_combo.currentText(),
            "size": self.size_spin.value(),
            "color": self._text_color,
            "outline_color": self._outline_color,
            "outline": self.outline_spin.value(),
            "shadow": self.shadow_spin.value(),
            "bold": self.bold_check.isChecked(),
            "italic": self.italic_check.isChecked(),
            "underline": self.underline_check.isChecked(),
            "alignment": alignment if alignment > 0 else 2,
            "margin_v": self.margin_spin.value(),
        }

    def update_preview(self):
        st = self.get_current_settings()

        frame_pixmap = self.current_frame

        if frame_pixmap is None:
            self.preview_label.setText("Kare yükleniyor...")
            if self.video_path:
                QTimer.singleShot(100, lambda: self._grab_frame(0.5))
            return

        # Altyazı metnini al
        subtitle_text = ""
        if self.subtitle_segments and self.subtitle_index < len(self.subtitle_segments):
            seg = self.subtitle_segments[self.subtitle_index]
            subtitle_text = seg.get("translated") or seg.get("text", "")
            start = seg["start"]
            mins = int(start // 60)
            secs = int(start % 60)
            self.time_slider_label.setText(
                f"Altyazı {self.subtitle_index + 1}/{len(self.subtitle_segments)} "
                f"— {mins:02d}:{secs:02d}"
            )
            self.info_label.setText(
                f"Font: {st['font']} | Boyut: {st['size']}px | "
                f"Kenarlık: {st['outline']}px | Gölge: {st['shadow']}px"
            )

        # Kareyi çiz
        scaled = frame_pixmap.scaled(
            960, 540,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        canvas = QPixmap(960, 540)
        canvas.fill(QColor(0, 0, 0))

        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # Video karesini ortala
        x_offset = (960 - scaled.width()) // 2
        y_offset = (540 - scaled.height()) // 2
        painter.drawPixmap(x_offset, y_offset, scaled)

        # Altyazı çiz - ASS formatına uygun
        if subtitle_text:
            # ASS PlayResY=1080, canvas 540px -> ölçek 0.5
            scale = 540 / 1080
            ass_font_size = int(st["size"] * scale)
            ass_outline = max(1, int(st["outline"] * scale))
            ass_shadow = max(1, int(st["shadow"] * scale)) if st["shadow"] > 0 else 0
            ass_margin_v = int(st["margin_v"] * scale)

            font = QFont(st["font"], ass_font_size)
            font.setBold(st["bold"])
            font.setItalic(st["italic"])
            font.setUnderline(st["underline"])
            painter.setFont(font)

            fm = QFontMetrics(font)
            text_width = min(fm.horizontalAdvance(subtitle_text) + 20, 920)
            text_height = fm.height() + 8

            # Hizalama ve konum (ASS: Alignment 1=sol-alt, 2=orta-alt, 3=sağ-alt)
            if st["alignment"] == 1:
                tx = 20
            elif st["alignment"] == 3:
                tx = 940 - text_width
            else:
                tx = (960 - text_width) // 2

            ty = 540 - ass_margin_v - text_height

            outline_color = QColor(self._outline_color)
            text_color = QColor(self._text_color)

            # Gölge (ASS: Shadow offset)
            if ass_shadow > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                shadow_alpha = min(255, 100 + st["shadow"] * 30)
                painter.setBrush(QColor(outline_color.red(), outline_color.green(),
                                        outline_color.blue(), shadow_alpha))
                for offset in range(1, ass_shadow + 1):
                    painter.drawText(tx + offset, ty + offset,
                                     text_width, text_height,
                                     Qt.AlignmentFlag.AlignCenter, subtitle_text)

            # Kenarlık (ASS: Outline - metin etrafında çizgi)
            if ass_outline > 0:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(outline_color)
                for dx in range(-ass_outline, ass_outline + 1):
                    for dy in range(-ass_outline, ass_outline + 1):
                        if dx == 0 and dy == 0:
                            continue
                        painter.drawText(tx + dx, ty + dy,
                                         text_width, text_height,
                                         Qt.AlignmentFlag.AlignCenter, subtitle_text)

            # Ana metin
            painter.setPen(text_color)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawText(tx, ty, text_width, text_height,
                             Qt.AlignmentFlag.AlignCenter, subtitle_text)

        painter.end()
        self.preview_label.setPixmap(canvas)

    def _update_color_btn_style(self, btn, hex_color):
        btn.setStyleSheet(f"background-color: {hex_color}; color: #FFF; padding: 6px;")

    def pick_text_color(self):
        color = QColorDialog.getColor(
            QColor(self._text_color), self, "Yazı Rengi Seç"
        )
        if color.isValid():
            self._text_color = color.name()
            self._update_color_btn_style(self.color_btn, color.name())
            self.update_preview()

    def pick_outline_color(self):
        color = QColorDialog.getColor(
            QColor(self._outline_color), self, "Kenarlık Rengi Seç"
        )
        if color.isValid():
            self._outline_color = color.name()
            self._update_color_btn_style(self.outline_color_btn, color.name())
            self.update_preview()

    def _save_and_close(self):
        if self._on_apply:
            self._on_apply(self.get_current_settings())
        self.accept()

    def closeEvent(self, event):
        event.accept()
