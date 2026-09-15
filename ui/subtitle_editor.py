from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QMessageBox,
    QMenu, QSpinBox, QComboBox, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor

from .styles import ACCENT_COLOR, TEXT_MUTED


class SubtitleEditor(QWidget):
    segments_changed = pyqtSignal(list)
    row_clicked = pyqtSignal(float, float)  # başlangıç ve bitiş zamanı

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self._active_row = -1
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        header_label = QLabel("\U0001F4DD  Altyazı Editörü")
        header_label.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {ACCENT_COLOR};"
        )
        header_layout.addWidget(header_label)

        self.row_count_label = QLabel("0 satır")
        self.row_count_label.setProperty("class", "chip")
        header_layout.addWidget(self.row_count_label)

        self.word_count_label = QLabel("0 kelime")
        self.word_count_label.setProperty("class", "chip")
        header_layout.addWidget(self.word_count_label)

        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("\U0001F50D  Altyazılarda ara...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(240)
        self.search_input.textChanged.connect(self.apply_filter)
        header_layout.addWidget(self.search_input)

        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Başlangıç", "Bitiş", "Orijinal Metin", "Çeviri Metni"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.cellClicked.connect(self.on_row_clicked)

        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.add_row_btn = QPushButton("+ Satır Ekle")
        self.add_row_btn.clicked.connect(self.add_row)
        button_layout.addWidget(self.add_row_btn)

        self.delete_row_btn = QPushButton("\U0001F5D1 Sil")
        self.delete_row_btn.setProperty("class", "danger")
        self.delete_row_btn.clicked.connect(self.delete_selected_rows)
        button_layout.addWidget(self.delete_row_btn)

        button_layout.addStretch()

        self.move_up_btn = QPushButton("\u2191 Yukarı")
        self.move_up_btn.clicked.connect(self.move_up)
        button_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("\u2193 Aşağı")
        self.move_down_btn.clicked.connect(self.move_down)
        button_layout.addWidget(self.move_down_btn)

        button_layout.addStretch()

        self.select_all_btn = QPushButton("Tümünü Seç")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        layout.addLayout(button_layout)

        layout_bottom = QHBoxLayout()

        info_label = QLabel("\U0001F4A1 Hücrelere çift tıklayarak düzenleyebilir, satıra tıklayarak videoda o anı oynatabilirsiniz")
        info_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-style: italic;")
        layout_bottom.addWidget(info_label)

        layout_bottom.addStretch()

        self.auto_adjust_check = QCheckBox("Otomatik zamanlama ayarla")
        self.auto_adjust_check.setToolTip("Satır silindiğinde zamanlamayı otomatik ayarlar")
        layout_bottom.addWidget(self.auto_adjust_check)

        layout.addLayout(layout_bottom)

    def set_segments(self, segments: list[dict]):
        self.table.blockSignals(True)
        self.segments = segments
        self._active_row = -1
        self.table.setRowCount(len(segments))

        for i, segment in enumerate(segments):
            self.table.setRowHeight(i, 60)

            start_item = QTableWidgetItem(self.format_time(segment["start"]))
            start_item.setFlags(start_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, start_item)

            end_item = QTableWidgetItem(self.format_time(segment["end"]))
            end_item.setFlags(end_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 1, end_item)

            text_item = QTableWidgetItem(segment.get("text", ""))
            text_item.setToolTip(segment.get("text", ""))
            self.table.setItem(i, 2, text_item)

            translated_item = QTableWidgetItem(segment.get("translated", ""))
            translated_item.setToolTip(segment.get("translated", ""))
            self.table.setItem(i, 3, translated_item)

        self.table.blockSignals(False)
        self.update_word_count()
        if self.search_input.text():
            self.apply_filter(self.search_input.text())

    def apply_filter(self, text: str):
        query = text.strip().lower()
        for row in range(self.table.rowCount()):
            if not query:
                self.table.setRowHidden(row, False)
                continue
            original = self.table.item(row, 2)
            translated = self.table.item(row, 3)
            match = (
                (original and query in original.text().lower()) or
                (translated and query in translated.text().lower())
            )
            self.table.setRowHidden(row, not match)

    def highlight_time(self, seconds: float):
        """Video oynatılırken aktif altyazı satırını vurgular."""
        active = -1
        for i, segment in enumerate(self.segments):
            if segment["start"] <= seconds <= segment["end"]:
                active = i
                break

        if active == self._active_row:
            return

        self.table.blockSignals(True)
        highlight = QColor(108, 140, 255, 45)
        transparent = QColor(0, 0, 0, 0)

        if 0 <= self._active_row < self.table.rowCount():
            for col in range(4):
                item = self.table.item(self._active_row, col)
                if item:
                    item.setBackground(transparent)

        if 0 <= active < self.table.rowCount():
            for col in range(4):
                item = self.table.item(active, col)
                if item:
                    item.setBackground(highlight)
            self.table.scrollToItem(
                self.table.item(active, 0),
                QAbstractItemView.ScrollHint.EnsureVisible
            )

        self._active_row = active
        self.table.blockSignals(False)

    def format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def parse_time(self, time_str: str) -> float:
        parts = time_str.replace(",", ".").split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        return 0.0

    def on_item_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()

        if col == 3 and row < len(self.segments):
            self.segments[row]["translated"] = item.text()
            item.setToolTip(item.text())
            self.update_word_count()
            self.segments_changed.emit(self.segments)

    def on_row_clicked(self, row: int, col: int):
        if row < len(self.segments):
            start_time = self.segments[row]["start"]
            end_time = self.segments[row]["end"]
            self.row_clicked.emit(start_time, end_time)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 40)

        last_end = 0
        if self.segments:
            last_end = self.segments[-1]["end"]

        new_segment = {
            "start": last_end,
            "end": last_end + 2.0,
            "text": "",
            "translated": ""
        }
        self.segments.append(new_segment)

        self.table.setItem(row, 0, QTableWidgetItem(self.format_time(last_end)))
        self.table.setItem(row, 1, QTableWidgetItem(self.format_time(last_end + 2.0)))
        text_item = QTableWidgetItem("")
        text_item.setToolTip("")
        self.table.setItem(row, 2, text_item)
        trans_item = QTableWidgetItem("")
        trans_item.setToolTip("")
        self.table.setItem(row, 3, trans_item)

        self.table.scrollToBottom()
        self.update_word_count()

    def delete_selected_rows(self):
        selected = sorted(self.table.selectionModel().selectedRows(), reverse=True)
        if not selected:
            return

        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"{len(selected)} satır silinecek. Emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for index in selected:
                row = index.row()
                self.table.removeRow(row)
                if row < len(self.segments):
                    self.segments.pop(row)

            if self.auto_adjust_check.isChecked():
                self.auto_adjust_timing()

            self.update_word_count()
            self.segments_changed.emit(self.segments)

    def move_up(self):
        rows = sorted(set(idx.row() for idx in self.table.selectionModel().selectedRows()))
        if not rows or rows[0] == 0:
            return

        for row in rows:
            self._swap_rows(row, row - 1)

        self.table.clearSelection()
        for row in rows:
            self.table.selectRow(row - 1)

    def move_down(self):
        rows = sorted(set(idx.row() for idx in self.table.selectionModel().selectedRows()), reverse=True)
        if not rows or rows[-1] == self.table.rowCount() - 1:
            return

        for row in rows:
            self._swap_rows(row, row + 1)

        self.table.clearSelection()
        for row in rows:
            self.table.selectRow(row + 1)

    def _swap_rows(self, row1: int, row2: int):
        if row1 < 0 or row2 < 0 or row1 >= len(self.segments) or row2 >= len(self.segments):
            return

        self.segments[row1], self.segments[row2] = self.segments[row2], self.segments[row1]

        for col in range(4):
            item1 = self.table.item(row1, col)
            item2 = self.table.item(row2, col)
            if item1 and item2:
                text1 = item1.text()
                text2 = item2.text()
                item1.setText(text2)
                item2.setText(text1)

    def select_all(self):
        self.table.selectAll()

    def auto_adjust_timing(self):
        if not self.segments:
            return

        gap = 0.05
        for i in range(1, len(self.segments)):
            if self.segments[i]["start"] < self.segments[i-1]["end"]:
                self.segments[i]["start"] = self.segments[i-1]["end"] + gap

        for i, segment in enumerate(self.segments):
            self.table.item(i, 0).setText(self.format_time(segment["start"]))
            self.table.item(i, 1).setText(self.format_time(segment["end"]))

    def update_word_count(self):
        total_words = 0
        for segment in self.segments:
            text = segment.get("translated", "") or segment.get("text", "")
            total_words += len(text.split())
        self.word_count_label.setText(f"{total_words} kelime")
        self.row_count_label.setText(f"{len(self.segments)} satır")

    def get_segments(self) -> list[dict]:
        return self.segments.copy()

    def show_context_menu(self, position):
        menu = QMenu(self)

        copy_action = QAction("Kopyala", self)
        copy_action.triggered.connect(self.copy_selected)
        menu.addAction(copy_action)

        paste_action = QAction("Yapıştır", self)
        paste_action.triggered.connect(self.paste_to_selected)
        menu.addAction(paste_action)

        menu.addSeparator()

        delete_action = QAction("Sil", self)
        delete_action.triggered.connect(self.delete_selected_rows)
        menu.addAction(delete_action)

        menu.addSeparator()

        adjust_action = QAction("Zamanlamayı Ayarla", self)
        adjust_action.triggered.connect(self.auto_adjust_timing)
        menu.addAction(adjust_action)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def copy_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        text_parts = []
        for index in selected:
            row = index.row()
            translated_item = self.table.item(row, 3)
            if translated_item:
                text_parts.append(translated_item.text())

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(text_parts))

    def paste_to_selected(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        rows = [idx.row() for idx in selected]
        lines = text.split("\n")

        for i, row in enumerate(rows):
            if i < len(lines):
                self.table.item(row, 3).setText(lines[i])
                self.table.item(row, 3).setToolTip(lines[i])
                if row < len(self.segments):
                    self.segments[row]["translated"] = lines[i]

        self.update_word_count()
