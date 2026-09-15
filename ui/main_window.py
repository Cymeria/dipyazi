import os
import sys
import json
import hashlib
import base64
import subprocess
import tempfile
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QProgressBar, QFileDialog,
    QSplitter, QFrame, QMessageBox, QApplication, QSlider, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QUrl, QTimer
from PyQt6.QtGui import (
    QDragEnterEvent, QDropEvent, QIcon, QPixmap, QFont, QShortcut, QKeySequence
)

from .subtitle_editor import SubtitleEditor
from .settings_dialog import SettingsDialog
from .style_preview import StylePreviewDialog
from .styles import (
    DARK_THEME, ACCENT_COLOR, SUCCESS_COLOR, DANGER_COLOR,
    TEXT_MUTED, BORDER_LIGHT
)

from core.transcriber import Transcriber
from core.language_detector import LanguageDetector
from core.translator import Translator
from core.subtitle_generator import SubtitleGenerator
from core.video_processor import VideoProcessor
from core.gpu_utils import get_gpu_info

# Video oynatıcı için
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    HAS_MEDIA_PLAYER = True
except ImportError:
    HAS_MEDIA_PLAYER = False


class WorkerThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, task_type: str, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs

    def run(self):
        try:
            if self.task_type == "detect_language":
                detector = LanguageDetector()
                lang, confidence = detector.detect_language(
                    self.kwargs["video_path"],
                    self.kwargs["model_size"],
                    progress_callback=self.progress.emit
                )
                self.finished.emit({"language": lang, "confidence": confidence})

            elif self.task_type == "transcribe":
                transcriber = Transcriber()
                result = transcriber.transcribe(
                    self.kwargs["video_path"],
                    self.kwargs["model_size"],
                    self.kwargs.get("source_language"),
                    progress_callback=self.progress.emit
                )
                self.finished.emit(result)

            elif self.task_type == "translate":
                translator = Translator(
                    self.kwargs["source_lang"],
                    self.kwargs["target_lang"]
                )
                segments = translator.translate_segments(
                    self.kwargs["segments"],
                    self.kwargs["target_lang"],
                    self.kwargs["source_lang"],
                    progress_callback=self.progress.emit
                )
                self.finished.emit({"segments": segments})

            elif self.task_type == "embed_subtitles":
                processor = VideoProcessor()
                output_path = processor.embed_subtitles(
                    self.kwargs["video_path"],
                    self.kwargs["subtitle_path"],
                    self.kwargs["output_path"],
                    self.kwargs.get("style_config"),
                    self.kwargs.get("hard_sub", True),
                    progress_callback=self.progress.emit
                )
                self.finished.emit({"output_path": output_path})

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    SETTINGS_FILE = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(__file__)), "settings.json")
    PROJECTS_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(__file__)), "projects")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dipyazı")
        self.setMinimumSize(1200, 800)
        self.setAcceptDrops(True)

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(__file__))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.video_path = None
        self.subtitle_segments = []
        self.subtitle_generator = SubtitleGenerator()
        self.current_subtitle_path = None

        self.settings = self._load_settings()

        self.worker = None
        self.setup_ui()
        self.apply_theme()
        self._restore_window_geometry()

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(14, 14, 14, 14)
        outer_layout.setSpacing(12)

        outer_layout.addWidget(self.create_header_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.create_left_panel())
        splitter.addWidget(self.create_right_panel())
        splitter.setSizes([420, 820])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        outer_layout.addWidget(splitter, 1)

        outer_layout.addWidget(self.create_footer_bar())

        self._setup_shortcuts()

    def create_header_bar(self) -> QWidget:
        header = QFrame()
        header.setObjectName("HeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        logo = QLabel("\U0001F3AC")
        logo.setObjectName("AppLogo")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title = QLabel("Dipyazı")
        title.setObjectName("AppTitle")
        subtitle = QLabel("Whisper transkripsiyon · çeviri · videoya gömme")
        subtitle.setObjectName("AppSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        layout.addStretch()

        gpu_info = get_gpu_info()

        cuda_text = gpu_info["cuda_device"] or ("Aktif" if gpu_info["cuda_available"] else "Yok")
        cuda_chip = QLabel(f"\u26A1 CUDA · {cuda_text}")
        cuda_chip.setProperty("class", "chipOk" if gpu_info["cuda_available"] else "chipOff")
        cuda_chip.setToolTip("Whisper için GPU hızlandırma durumu")
        layout.addWidget(cuda_chip)

        nvenc_text = "Aktif" if gpu_info["nvenc_available"] else "Yok"
        nvenc_chip = QLabel(f"\U0001F39E NVENC · {nvenc_text}")
        nvenc_chip.setProperty("class", "chipOk" if gpu_info["nvenc_available"] else "chipOff")
        nvenc_chip.setToolTip("FFmpeg için GPU kodlama durumu")
        layout.addWidget(nvenc_chip)

        return header

    def create_footer_bar(self) -> QWidget:
        bar = QFrame()
        bar.setProperty("class", "card")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        self.status_dot = QLabel("\u25CF")
        self.status_dot.setStyleSheet(f"color: {SUCCESS_COLOR}; font-size: 10px;")
        layout.addWidget(self.status_dot)

        self.status_label = QLabel("Hazır")
        self.status_label.setProperty("class", "muted")
        layout.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedWidth(280)
        layout.addWidget(self.progress_bar)

        self.progress_percent = QLabel("%0")
        self.progress_percent.setProperty("class", "muted")
        self.progress_percent.setFixedWidth(42)
        self.progress_percent.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.progress_bar.valueChanged.connect(
            lambda v: self.progress_percent.setText(f"%{v}")
        )
        layout.addWidget(self.progress_percent)

        return bar

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.select_video)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.save_project)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.save_srt)

    def _create_card(self, title: str, icon: str):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel(f"{icon}  {title}")
        title_label.setProperty("class", "cardTitle")
        layout.addWidget(title_label)

        return card, layout

    def _drop_area_style(self, loaded: bool = False) -> str:
        if loaded:
            return f"""
                QLabel#DropArea {{
                    border: 2px solid rgba(52, 211, 153, 0.5);
                    border-radius: 12px;
                    background-color: rgba(52, 211, 153, 0.06);
                    color: {SUCCESS_COLOR};
                    font-size: 13px;
                    font-weight: 600;
                }}
            """
        return f"""
            QLabel#DropArea {{
                border: 2px dashed {BORDER_LIGHT};
                border-radius: 12px;
                background-color: rgba(108, 140, 255, 0.04);
                color: {TEXT_MUTED};
                font-size: 13px;
            }}
            QLabel#DropArea:hover {{
                border-color: {ACCENT_COLOR};
                color: {ACCENT_COLOR};
                background-color: rgba(108, 140, 255, 0.08);
            }}
        """

    def create_left_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(12)

        # ---- Video kartı ----
        video_card, video_layout = self._create_card("Video", "\U0001F4FA")

        self.drop_area = QLabel(
            "\U0001F4E5\n\nVideoyu buraya sürükleyin\nveya tıklayarak seçin\n\nCtrl+O"
        )
        self.drop_area.setObjectName("DropArea")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setMinimumHeight(150)
        self.drop_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drop_area.setStyleSheet(self._drop_area_style())
        self.drop_area.mousePressEvent = self.select_video
        video_layout.addWidget(self.drop_area)

        # Video oynatıcı
        self.media_player = None
        self.video_widget = None
        self.audio_output = None

        if HAS_MEDIA_PLAYER:
            self.video_widget = QVideoWidget()
            self.video_widget.setMinimumHeight(200)
            self.video_widget.setMaximumHeight(400)
            self.video_widget.setStyleSheet("background-color: #000000; border-radius: 10px;")
            self.video_widget.hide()
            video_layout.addWidget(self.video_widget)

            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(0.5)
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)

            # Zaman çubuğu (tıklayarak/sürükleyerek sarma)
            self.seek_slider = QSlider(Qt.Orientation.Horizontal)
            self.seek_slider.setRange(0, 0)
            self.seek_slider.setEnabled(False)
            self.seek_slider.sliderMoved.connect(self.seek_to_position)
            video_layout.addWidget(self.seek_slider)

            player_controls = QHBoxLayout()
            player_controls.setSpacing(10)

            self.play_btn = QPushButton("\u25B6")
            self.play_btn.setProperty("class", "playBtn")
            self.play_btn.setToolTip("Oynat / Duraklat")
            self.play_btn.clicked.connect(self.toggle_playback)
            self.play_btn.setEnabled(False)
            player_controls.addWidget(self.play_btn)

            self.stop_btn = QPushButton("\u23F9")
            self.stop_btn.setProperty("class", "iconBtn")
            self.stop_btn.setToolTip("Durdur")
            self.stop_btn.clicked.connect(self.stop_playback)
            self.stop_btn.setEnabled(False)
            player_controls.addWidget(self.stop_btn)

            self.time_label = QLabel("00:00:00 / 00:00:00")
            self.time_label.setProperty("class", "muted")
            player_controls.addWidget(self.time_label)

            player_controls.addStretch()

            volume_icon = QLabel("\U0001F50A")
            volume_icon.setProperty("class", "muted")
            player_controls.addWidget(volume_icon)

            self.volume_slider = QSlider(Qt.Orientation.Horizontal)
            self.volume_slider.setRange(0, 100)
            self.volume_slider.setValue(50)
            self.volume_slider.setFixedWidth(90)
            self.volume_slider.setToolTip("Ses seviyesi")
            self.volume_slider.valueChanged.connect(
                lambda v: self.audio_output.setVolume(v / 100)
            )
            player_controls.addWidget(self.volume_slider)

            self.player_controls_layout = player_controls
            video_layout.addLayout(player_controls)

            self.media_player.positionChanged.connect(self.on_position_changed)
            self.media_player.durationChanged.connect(self.on_duration_changed)

        self.video_info_label = QLabel("")
        self.video_info_label.setProperty("class", "muted")
        self.video_info_label.setWordWrap(True)
        video_layout.addWidget(self.video_info_label)

        layout.addWidget(video_card)

        # ---- Ayarlar kartı ----
        settings_card, settings_layout = self._create_card("Ayarlar", "\u2699")

        model_caption = QLabel("Whisper Modeli")
        model_caption.setProperty("class", "muted")
        settings_layout.addWidget(model_caption)
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v3"])
        self.model_combo.setCurrentText("medium")
        self.model_combo.setToolTip(
            "tiny: Hızlı, düşük kalite\n"
            "base: Hızlı, orta kalite\n"
            "small: Dengeli\n"
            "medium: İyi kalite (Önerilen)\n"
            "large-v3: En iyi kalite, yavaş"
        )
        settings_layout.addWidget(self.model_combo)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(10)

        source_col = QVBoxLayout()
        source_col.setSpacing(4)
        source_caption = QLabel("Kaynak Dil")
        source_caption.setProperty("class", "muted")
        source_col.addWidget(source_caption)
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.addItem("Otomatik Algıla", "auto")
        detector = LanguageDetector()
        for code, name in sorted(detector.get_supported_languages().items()):
            self.source_lang_combo.addItem(name, code)
        # Varsayılan kaynak dilini İngilizce yap
        english_idx = self.source_lang_combo.findData("en")
        if english_idx >= 0:
            self.source_lang_combo.setCurrentIndex(english_idx)
        source_col.addWidget(self.source_lang_combo)
        lang_row.addLayout(source_col, 1)

        arrow = QLabel("\u2192")
        arrow.setProperty("class", "muted")
        arrow.setAlignment(Qt.AlignmentFlag.AlignBottom)
        lang_row.addWidget(arrow)

        target_col = QVBoxLayout()
        target_col.setSpacing(4)
        target_caption = QLabel("Hedef Dil")
        target_caption.setProperty("class", "muted")
        target_col.addWidget(target_caption)
        self.target_lang_combo = QComboBox()
        translator = Translator()
        for code, name in sorted(translator.get_supported_languages().items()):
            self.target_lang_combo.addItem(name, code)
        turkish_idx = self.target_lang_combo.findData("tr")
        if turkish_idx >= 0:
            self.target_lang_combo.setCurrentIndex(turkish_idx)
        target_col.addWidget(self.target_lang_combo)
        lang_row.addLayout(target_col, 1)

        settings_layout.addLayout(lang_row)
        layout.addWidget(settings_card)

        # ---- İş akışı kartı ----
        actions_card, actions_layout = self._create_card("İş Akışı", "\u26A1")

        self.detect_lang_btn = QPushButton("1 · Dili Algıla")
        self.detect_lang_btn.setMinimumHeight(40)
        self.detect_lang_btn.clicked.connect(self.detect_language)
        self.detect_lang_btn.setEnabled(False)
        actions_layout.addWidget(self.detect_lang_btn)

        self.transcribe_btn = QPushButton("2 · Altyazıyı Oluştur")
        self.transcribe_btn.setProperty("class", "primary")
        self.transcribe_btn.setMinimumHeight(40)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setEnabled(False)
        actions_layout.addWidget(self.transcribe_btn)

        self.translate_btn = QPushButton("3 · Çeviriyi Yap")
        self.translate_btn.setMinimumHeight(40)
        self.translate_btn.clicked.connect(self.start_translation)
        self.translate_btn.setEnabled(False)
        actions_layout.addWidget(self.translate_btn)

        layout.addWidget(actions_card)

        # ---- Mevcut altyazı yükleme kartı ----
        import_card, import_layout = self._create_card("Mevcut Altyazı Yükle", "\U0001F4C2")

        self.import_original_btn = QPushButton("Orijinal Altyazı Yükle")
        self.import_original_btn.setMinimumHeight(36)
        self.import_original_btn.setToolTip("Daha önce oluşturulmuş orijinal dilli altyazı dosyasını yükler")
        self.import_original_btn.clicked.connect(self.import_original_subtitle)
        import_layout.addWidget(self.import_original_btn)

        self.import_translated_btn = QPushButton("Çeviri Altyazı Yükle")
        self.import_translated_btn.setMinimumHeight(36)
        self.import_translated_btn.setToolTip("Daha önce oluşturulmuş çevrilmiş altyazı dosyasını yükler")
        self.import_translated_btn.clicked.connect(self.import_translated_subtitle)
        import_layout.addWidget(self.import_translated_btn)

        layout.addWidget(import_card)

        layout.addStretch()

        scroll.setWidget(panel)
        scroll.setMinimumWidth(380)
        return scroll

    def create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        editor_card = QFrame()
        editor_card.setProperty("class", "card")
        editor_layout = QVBoxLayout(editor_card)
        editor_layout.setContentsMargins(16, 14, 16, 14)

        self.subtitle_editor = SubtitleEditor()
        self.subtitle_editor.row_clicked.connect(self.on_subtitle_row_clicked)
        self.subtitle_editor.segments_changed.connect(self._on_segments_changed)
        editor_layout.addWidget(self.subtitle_editor)

        layout.addWidget(editor_card, 1)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.style_btn = QPushButton("\U0001F3A8  Stil Ayarları")
        self.style_btn.setMinimumHeight(42)
        self.style_btn.clicked.connect(self.open_style_settings)
        bottom_layout.addWidget(self.style_btn)

        self.save_srt_btn = QPushButton("\U0001F4C4  SRT Kaydet")
        self.save_srt_btn.setMinimumHeight(42)
        self.save_srt_btn.setToolTip("Altyazıları SRT/ASS olarak dışa aktar (Ctrl+E)")
        self.save_srt_btn.clicked.connect(self.save_srt)
        self.save_srt_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_srt_btn)

        self.save_project_btn = QPushButton("\U0001F4BE  Kaydet")
        self.save_project_btn.setMinimumHeight(42)
        self.save_project_btn.setToolTip("Projeyi kaydet (Ctrl+S)")
        self.save_project_btn.clicked.connect(self.save_project)
        self.save_project_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_project_btn)

        bottom_layout.addStretch()

        self.embed_btn = QPushButton("\U0001F3AC  Videoya Göm")
        self.embed_btn.setProperty("class", "primary")
        self.embed_btn.setMinimumHeight(42)
        self.embed_btn.setMinimumWidth(170)
        self.embed_btn.clicked.connect(self.embed_subtitles)
        self.embed_btn.setEnabled(False)
        bottom_layout.addWidget(self.embed_btn)

        layout.addLayout(bottom_layout)

        return panel

    def _load_settings(self) -> dict:
        defaults = {
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
            "margin_v": 30
        }
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                defaults.update(saved)
            except (json.JSONDecodeError, OSError):
                pass
        return defaults

    def _save_settings(self):
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _restore_window_geometry(self):
        geo = self.settings.get("window_geometry")
        if geo:
            try:
                self.restoreGeometry(bytes.fromhex(geo))
            except Exception:
                pass

    def _save_window_geometry(self):
        self.settings["window_geometry"] = self.saveGeometry().toHex().data().decode()
        self._save_settings()

    def _get_project_path(self, video_path: str) -> str:
        if not os.path.exists(self.PROJECTS_DIR):
            os.makedirs(self.PROJECTS_DIR, exist_ok=True)
        video_hash = hashlib.md5(video_path.encode()).hexdigest()[:12]
        return os.path.join(self.PROJECTS_DIR, f"{video_hash}.json")

    def _save_project(self):
        if not self.video_path:
            return
        project = {
            "video_path": self.video_path,
            "subtitle_segments": self.subtitle_segments,
            "style_settings": self.settings,
            "source_lang": self.source_lang_combo.currentData(),
            "target_lang": self.target_lang_combo.currentData(),
        }
        try:
            path = self._get_project_path(self.video_path)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(project, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _load_project(self, video_path: str) -> dict | None:
        path = self._get_project_path(video_path)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def apply_theme(self):
        self.setStyleSheet(DARK_THEME)

    def select_video(self, event=None):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Video Seç", "",
            "Video Dosyaları (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;Tüm Dosyalar (*)"
        )
        if file_path:
            self.load_video(file_path)

    def load_video(self, path: str):
        self.video_path = path
        filename = os.path.basename(path)

        try:
            processor = VideoProcessor()
            info = processor.get_video_info(path)

            duration = info["duration"]
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            secs = int(duration % 60)

            size_mb = info["size"] / (1024 * 1024)

            info_text = (
                f"📁 {filename}\n"
                f"⏱️ {hours:02d}:{minutes:02d}:{secs:02d} | "
                f"🎬 {info['width']}x{info['height']} | "
                f"🎞️ {info['fps']:.1f}fps | "
                f"💾 {size_mb:.1f}MB"
            )
            self.video_info_label.setText(info_text)

            self.drop_area.setText(f"\u2705  {filename}")
            self.drop_area.setStyleSheet(self._drop_area_style(loaded=True))
            self.drop_area.setMinimumHeight(48)

            self.detect_lang_btn.setEnabled(True)
            self.transcribe_btn.setEnabled(True)

            # Video oynatıcıya videoyu yükle
            if self.media_player:
                self.drop_area.setMinimumHeight(0)
                self.drop_area.setFixedHeight(42)
                self.video_widget.show()
                self.media_player.setSource(QUrl.fromLocalFile(path))
                self.play_btn.setEnabled(True)
                self.stop_btn.setEnabled(True)
                self.seek_slider.setEnabled(True)
                self.play_btn.setText("\u25B6")

            # Kayıtlı proje varsa geri yükle
            project = self._load_project(path)
            if project:
                self.subtitle_segments = project.get("subtitle_segments", [])
                if project.get("style_settings"):
                    self.settings.update(project["style_settings"])
                if project.get("source_lang"):
                    idx = self.source_lang_combo.findData(project["source_lang"])
                    if idx >= 0:
                        self.source_lang_combo.setCurrentIndex(idx)
                if project.get("target_lang"):
                    idx = self.target_lang_combo.findData(project["target_lang"])
                    if idx >= 0:
                        self.target_lang_combo.setCurrentIndex(idx)
                if self.subtitle_segments:
                    self.subtitle_editor.set_segments(self.subtitle_segments)
                    self.translate_btn.setEnabled(True)
                    self.save_srt_btn.setEnabled(True)
                    self.save_project_btn.setEnabled(True)
                    self.embed_btn.setEnabled(True)
                    self.status_label.setText(
                        f"Proje geri yüklendi: {len(self.subtitle_segments)} altyazı satırı"
                    )

        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Video yüklenirken hata oluştu:\n{str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v')):
                self.load_video(file_path)
                return

        QMessageBox.warning(self, "Uyarı", "Lütfen bir video dosyası sürükleyin.")

    def detect_language(self):
        if not self.video_path:
            return

        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Dil algılanıyor...")

        self.worker = WorkerThread(
            "detect_language",
            video_path=self.video_path,
            model_size=self.model_combo.currentText()
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_language_detected)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_language_detected(self, result: dict):
        lang = result["language"]
        confidence = result["confidence"]

        detector = LanguageDetector()
        lang_name = detector.get_language_name(lang)

        self.source_lang_combo.setCurrentText(lang_name)

        self.status_label.setText(f"Dil: {lang_name} (Güven: %{confidence*100:.0f})")
        self.set_ui_enabled(True)
        self.progress_bar.setValue(100)

    def start_transcription(self):
        if not self.video_path:
            return

        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Transkripsiyon başlıyor...")

        source_lang = self.source_lang_combo.currentData()
        if source_lang == "auto":
            source_lang = None

        self.worker = WorkerThread(
            "transcribe",
            video_path=self.video_path,
            model_size=self.model_combo.currentText(),
            source_language=source_lang
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_transcription_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_transcription_done(self, result: dict):
        self.subtitle_segments = result["segments"]
        detected_lang = result.get("language", "unknown")

        self.source_lang_combo.setCurrentText(
            LanguageDetector().get_language_name(detected_lang)
        )

        self.subtitle_editor.set_segments(self.subtitle_segments)
        self.translate_btn.setEnabled(True)
        self.save_srt_btn.setEnabled(True)
        self.embed_btn.setEnabled(True)

        self.status_label.setText(f"Transkripsiyon tamamlandı! ({len(self.subtitle_segments)} segment)")
        self.set_ui_enabled(True)
        self.progress_bar.setValue(100)
        self._save_project()

    def _on_segments_changed(self, segments):
        self.subtitle_segments = segments

    def start_translation(self):
        if not self.subtitle_segments:
            return

        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Çeviri yapılıyor...")

        source_lang = self.source_lang_combo.currentData() or "auto"
        target_lang = self.target_lang_combo.currentData() or "tr"

        self.worker = WorkerThread(
            "translate",
            segments=self.subtitle_segments,
            source_lang=source_lang,
            target_lang=target_lang
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_translation_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_translation_done(self, result: dict):
        self.subtitle_segments = result["segments"]
        self.subtitle_editor.set_segments(self.subtitle_segments)

        self.status_label.setText("Çeviri tamamlandı!")
        self.set_ui_enabled(True)
        self.progress_bar.setValue(100)
        self._save_project()

    def on_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.status_dot.setStyleSheet(f"color: {ACCENT_COLOR}; font-size: 10px;")

    def on_error(self, message: str):
        QMessageBox.critical(self, "Hata", f"Bir hata oluştu:\n{message}")
        self.status_label.setText("Hata oluştu!")
        self.status_dot.setStyleSheet(f"color: {DANGER_COLOR}; font-size: 10px;")
        self.set_ui_enabled(True)
        self.progress_bar.setValue(0)

    def set_ui_enabled(self, enabled: bool):
        self.detect_lang_btn.setEnabled(enabled and self.video_path is not None)
        self.transcribe_btn.setEnabled(enabled and self.video_path is not None)
        self.translate_btn.setEnabled(enabled and len(self.subtitle_segments) > 0)
        self.save_srt_btn.setEnabled(enabled and len(self.subtitle_segments) > 0)
        self.save_project_btn.setEnabled(enabled and len(self.subtitle_segments) > 0)
        self.embed_btn.setEnabled(enabled and len(self.subtitle_segments) > 0)
        self.model_combo.setEnabled(enabled)
        self.source_lang_combo.setEnabled(enabled)
        self.target_lang_combo.setEnabled(enabled)

    def open_style_settings(self):
        dialog = StylePreviewDialog(
            self,
            video_path=self.video_path,
            subtitle_segments=self.subtitle_segments,
            current_settings=self.settings,
            on_apply=self._apply_style_settings
        )
        if dialog.exec():
            self.settings = dialog.get_current_settings()
            self._save_settings()
            self._save_project()

    def _apply_style_settings(self, new_settings):
        self.settings = new_settings
        self._save_settings()
        self._save_project()

    def save_project(self):
        if not self.video_path:
            return
        self._save_project()
        QMessageBox.information(self, "Kaydedildi", "Proje başarıyla kaydedildi.")

    def save_srt(self):
        if not self.subtitle_segments:
            return

        segments = self.subtitle_editor.get_segments()

        file_path, _ = QFileDialog.getSaveFileName(
            self, "SRT Kaydet", "",
            "SRT Dosyası (*.srt);;ASS Dosyası (*.ass);;Tüm Dosyalar (*)"
        )
        if file_path:
            source_lang = self.source_lang_combo.currentText() or "orijinal"
            target_lang = self.target_lang_combo.currentText() or "cevirilmis"

            if file_path.lower().endswith('.ass'):
                orig_path, trans_path = self.subtitle_generator.generate_both_ass(
                    segments, file_path, self.settings, source_lang, target_lang
                )
            else:
                if not file_path.lower().endswith('.srt'):
                    file_path += '.srt'
                orig_path, trans_path = self.subtitle_generator.generate_both_srt(
                    segments, file_path, source_lang, target_lang
                )

            self.current_subtitle_path = trans_path
            QMessageBox.information(
                self, "Başarılı",
                f"Altyazılar kaydedildi:\n\n"
                f"Orijinal ({source_lang}):\n{orig_path}\n\n"
                f"Çeviri ({target_lang}):\n{trans_path}"
            )

    def embed_subtitles(self):
        if not self.video_path or not self.subtitle_segments:
            return

        segments = self.subtitle_editor.get_segments()

        default_output = os.path.splitext(self.video_path)[0] + "_altyazili" + os.path.splitext(self.video_path)[1]
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Video Kaydet", default_output,
            "MP4 Dosyası (*.mp4);;AVI Dosyası (*.avi);;MKV Dosyası (*.mkv);;Tüm Dosyalar (*)"
        )
        if not output_path:
            return

        # Sadece çevrilmiş altyazı ASS dosyası oluştur
        tmp_dir = tempfile.mkdtemp(prefix="altyazi_embed_")
        subtitle_path = os.path.join(tmp_dir, "subtitle.ass")
        self.subtitle_generator.generate_ass(
            segments, subtitle_path, self.settings, use_translated=True
        )

        self.set_ui_enabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Video işleniyor...")

        self._embed_output_path = output_path
        self._embed_subtitle_path = subtitle_path

        self.worker = WorkerThread(
            "embed_subtitles",
            video_path=self.video_path,
            subtitle_path=subtitle_path,
            output_path=output_path,
            style_config=self.settings,
            hard_sub=True
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_embed_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_embed_done(self, result: dict):
        output_path = result["output_path"]
        self.status_label.setText("Video hazır!")
        self.set_ui_enabled(True)
        self.progress_bar.setValue(100)

        # Geçici ASS dosyasını temizle
        if hasattr(self, '_embed_subtitle_path') and os.path.exists(self._embed_subtitle_path):
            try:
                os.remove(self._embed_subtitle_path)
                os.rmdir(os.path.dirname(self._embed_subtitle_path))
            except OSError:
                pass

        reply = QMessageBox.information(
            self, "Tamamlandı!",
            f"Video kaydedildi:\n{output_path}\n\nKlasörü açmak ister misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            folder = os.path.dirname(os.path.abspath(output_path))
            subprocess.Popen(f'explorer "{folder}"')

    def toggle_playback(self):
        if not self.media_player:
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("\u25B6")
        else:
            self.media_player.play()
            self.play_btn.setText("\u23F8")

    def stop_playback(self):
        if not self.media_player:
            return
        self.media_player.stop()
        self.play_btn.setText("\u25B6")

    def seek_to_position(self, position_ms: int):
        if self.media_player:
            self.media_player.setPosition(position_ms)

    def on_position_changed(self, position):
        duration = self.media_player.duration()
        self.time_label.setText(f"{self._format_time_simple(position)} / {self._format_time_simple(duration)}")
        if not self.seek_slider.isSliderDown():
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(position)
            self.seek_slider.blockSignals(False)
        self.subtitle_editor.highlight_time(position / 1000)

    def on_duration_changed(self, duration):
        self.time_label.setText(f"00:00:00 / {self._format_time_simple(duration)}")
        self.seek_slider.setRange(0, duration)

    def _format_time_simple(self, ms: int) -> str:
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def on_subtitle_row_clicked(self, start_time: float, end_time: float):
        if self.media_player:
            self.seek_to_position(int(start_time * 1000))
            self.media_player.play()
            self.play_btn.setText("\u23F8")
            self._subtitle_end_ms = int(end_time * 1000)
            QTimer.singleShot(100, self._check_subtitle_end)

    def _check_subtitle_end(self):
        if not self.media_player or not hasattr(self, '_subtitle_end_ms'):
            return
        pos = self.media_player.position()
        if pos >= self._subtitle_end_ms:
            self.media_player.pause()
            self.play_btn.setText("\u25B6")
        elif self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            QTimer.singleShot(100, self._check_subtitle_end)

    def import_original_subtitle(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Orijinal Altyazı Yükle", "",
            "SRT Dosyası (*.srt);;ASS Dosyası (*.ass);;Tüm Dosyalar (*)"
        )
        if not file_path:
            return

        try:
            segments = self.subtitle_generator.parse_srt(file_path)
            if not segments:
                QMessageBox.warning(self, "Uyarı", "Altyazı dosyası boş veya geçersiz format.")
                return

            if self.subtitle_segments:
                reply = QMessageBox.question(
                    self, "Altyazı Birleştirme",
                    f"Mevcut {len(self.subtitle_segments)} satır altyazı var.\n"
                    f"Yeni yüklenen {len(segments)} satır ile birleştirmek mi istersiniz?\n\n"
                    "Evet: Birleştir (orijinal metinleri güncelle)\n"
                    "Hayır: Mevcut altyazıları değiştir",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    # Mevcut segmentlere çevirileri koruyarak orijinal metinleri güncelle
                    for i, seg in enumerate(segments):
                        if i < len(self.subtitle_segments):
                            self.subtitle_segments[i]["text"] = seg["text"]
                            if not self.subtitle_segments[i].get("translated"):
                                self.subtitle_segments[i]["translated"] = seg["text"]
                        else:
                            self.subtitle_segments.append(seg)
                else:
                    self.subtitle_segments = segments
            else:
                self.subtitle_segments = segments

            self.subtitle_editor.set_segments(self.subtitle_segments)
            self.translate_btn.setEnabled(True)
            self.save_srt_btn.setEnabled(True)
            self.embed_btn.setEnabled(True)
            self.status_label.setText(f"Orijinal altyazı yüklendi: {len(self.subtitle_segments)} satır")
            self._save_project()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Altyazı yüklenirken hata oluştu:\n{str(e)}")

    def import_translated_subtitle(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Çeviri Altyazı Yükle", "",
            "SRT Dosyası (*.srt);;ASS Dosyası (*.ass);;Tüm Dosyalar (*)"
        )
        if not file_path:
            return

        try:
            translated_segments = self.subtitle_generator.parse_srt(file_path)
            if not translated_segments:
                QMessageBox.warning(self, "Uyarı", "Altyazı dosyası boş veya geçersiz format.")
                return

            if not self.subtitle_segments:
                # Mevcut segment yoksa, yüklenen altyazıları hem orijinal hem çeviri olarak kullan
                self.subtitle_segments = translated_segments
                for seg in self.subtitle_segments:
                    if not seg.get("translated"):
                        seg["translated"] = seg["text"]
            else:
                # Mevcut segmentlere çevirileri ekle/eşleştir
                if len(translated_segments) == len(self.subtitle_segments):
                    # Sayı eşitse doğrudan eşleştir
                    for i, seg in enumerate(translated_segments):
                        self.subtitle_segments[i]["translated"] = seg["text"]
                else:
                    # Sayı farklıysa zamana göre eşleştir
                    for seg in translated_segments:
                        best_match = None
                        best_overlap = 0
                        for existing in self.subtitle_segments:
                            overlap_start = max(seg["start"], existing["start"])
                            overlap_end = min(seg["end"], existing["end"])
                            overlap = max(0, overlap_end - overlap_start)
                            if overlap > best_overlap:
                                best_overlap = overlap
                                best_match = existing
                        if best_match and best_overlap > 0:
                            best_match["translated"] = seg["text"]

            self.subtitle_editor.set_segments(self.subtitle_segments)
            self.translate_btn.setEnabled(True)
            self.save_srt_btn.setEnabled(True)
            self.embed_btn.setEnabled(True)
            self.status_label.setText(f"Çeviri altyazı yüklendi: {len(translated_segments)} satır")
            self._save_project()

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Altyazı yüklenirken hata oluştu:\n{str(e)}")

    def closeEvent(self, event):
        self._save_project()
        self._save_window_geometry()
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()
