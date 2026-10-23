"""Rogue Compressor For EVO — functional Phase 2 desktop prototype."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parent / "assets"

from PySide6.QtCore import Qt, QUrl, QThread, Signal, QRect
from PySide6.QtWidgets import (
    QApplication, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QProgressBar, QPushButton, QSlider,
    QVBoxLayout, QWidget, QCheckBox, QComboBox, QDialog, QFrame, QScrollArea,
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QDesktopServices, QIcon

from compressor import export_clip

MAX_CLIP_SECONDS = 60.0


class ExportWorker(QThread):
    progress_update = Signal(int)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, source, dest, start, end, blur_faces=False, blur_strength="Strong", manual_box=None, corrections=None, encoder="auto", reviewed=None):
        super().__init__()
        self.source, self.dest = source, dest
        self.start_time, self.end_time = float(start), float(end)
        self.blur_faces, self.blur_strength = blur_faces, "Maximum"
        self.manual_box = manual_box
        self.corrections = corrections or []
        self.encoder = encoder
        self.reviewed = reviewed

    def run(self):
        try:
            result = export_clip(self.source, self.dest, self.start_time, self.end_time, self.progress_update.emit, self.blur_faces, self.blur_strength, self.manual_box, self.corrections, self.encoder, reviewed=self.reviewed)
            self.succeeded.emit(str(result))
        except Exception as exc:
            self.failed.emit(str(exc))



def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 3600:02}:{(seconds // 60) % 60:02}:{seconds % 60:02}"


def get_video_metadata(path):
    """Read video information without modifying the original file."""
    if not shutil.which("ffprobe"):
        raise RuntimeError("FFprobe was not found. Install FFmpeg and add its bin folder to PATH.")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_type,width,height", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    data = json.loads(result.stdout)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("No video stream found in this file.")
    info = data.get("format", {})
    duration = float(info.get("duration", 0))
    if duration <= 0:
        raise ValueError("Video duration could not be determined.")
    return {"duration": duration, "width": video.get("width", 0),
            "height": video.get("height", 0), "size": int(info.get("size", Path(path).stat().st_size))}


class RegionLabel(QLabel):
    """Drag a box around a face on an upright, aspect-preserved preview."""
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.origin = None
        self.rect = QRect()

    def mousePressEvent(self, event):
        self.origin = event.position().toPoint()
        self.rect = QRect(self.origin, self.origin)
        self.update()

    def mouseMoveEvent(self, event):
        if self.origin is not None:
            self.rect = QRect(self.origin, event.position().toPoint()).normalized().intersected(self.contentsRect())
            self.update()

    def mouseReleaseEvent(self, event):
        self.mouseMoveEvent(event)
        self.origin = None

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rect.isNull():
            painter = QPainter(self)
            painter.setPen(QPen(Qt.GlobalColor.red, 3))
            painter.drawRect(self.rect)

    def normalized_box(self):
        if self.rect.width() < 12 or self.rect.height() < 12:
            return None
        return (self.rect.x()/self.width(), self.rect.y()/self.height(),
                self.rect.width()/self.width(), self.rect.height()/self.height())


class VideoCompressorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rogue Compressor For EVO | Rogue Software")
        self.resize(1220, 850)
        self.setMinimumSize(940, 650)
        self.video_path = None
        self.manual_box = None
        self.corrections = []
        self.review_dialog = None
        self.duration = 0.0
        self.exporting = False
        self._previewing = False
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.setStyleSheet("""
        QMainWindow, QWidget#root { background: #101318; color: #E9EDF2; }
        QWidget { color: #E9EDF2; font-family: 'Segoe UI'; font-size: 12px; }
        QFrame#panel { background: #191E26; border: 1px solid #303744; border-radius: 12px; }
        QFrame#previewPanel { background: #0B0E13; border: 1px solid #303744; border-radius: 12px; }
        QLabel#heading { color: #FFFFFF; font-size: 20px; font-weight: 800; }
        QLabel#section { color: #F4F6F8; font-size: 14px; font-weight: 700; }
        QLabel#muted { color: #A7B0BD; }
        QLabel#accent { color: #F08A92; font-weight: 600; }
        QPushButton { background: #292F39; border: 1px solid #434C5B; border-radius: 7px;
                      padding: 10px 13px; font-weight: 600; }
        QPushButton:hover { background: #39414E; border-color: #697689; }
        QPushButton:disabled { color: #69727F; background: #1B2028; border-color: #303743; }
        QPushButton#primary { background: #AF2C3A; color: white; border-color: #CE4655; font-size: 14px; padding: 13px; }
        QPushButton#primary:hover { background: #CA3948; }
        QPushButton#primary:disabled { background: #4B2730; color: #95838A; border-color: #63343D; }
        QDoubleSpinBox, QComboBox { background: #11161D; border: 1px solid #414B59;
                                   border-radius: 6px; padding: 7px; min-height: 23px; }
        QComboBox QAbstractItemView { background: #1A2029; color: white; selection-background-color: #AE3542; }
        QSlider::groove:horizontal { height: 7px; background: #343B46; border-radius: 3px; }
        QSlider::sub-page:horizontal { background: #B43240; border-radius: 3px; }
        QSlider::handle:horizontal { background: #F2F4F7; width: 16px; margin: -5px 0; border-radius: 8px; }
        QProgressBar { background: #0D1117; border: 1px solid #39414C; border-radius: 6px; height: 14px; text-align: center; }
        QProgressBar::chunk { background: #BD3443; border-radius: 5px; }
        QCheckBox { spacing: 9px; }
        QCheckBox::indicator { width: 18px; height: 18px; }
        QCheckBox::indicator:checked { background: #B73544; border: 1px solid #DE5967; border-radius: 4px; }
        QScrollArea { border: none; background: transparent; }
        QPushButton#musclePromo { background: #1A1C28; border: 1px solid #594475;
                                   border-radius: 9px; padding: 6px 11px; text-align: left; }
        QPushButton#musclePromo:hover { background: #272239; border-color: #BD54E8; }

        /* Ensure Windows-native message boxes match the dark application theme. */
        QMessageBox, QDialog { background-color: #191E26; color: #E9EDF2; }
        QMessageBox QLabel, QDialog QLabel { color: #E9EDF2; background-color: transparent; }
        QMessageBox QPushButton, QDialog QPushButton {
            background-color: #292F39; color: #FFFFFF;
            border: 1px solid #434C5B; border-radius: 7px;
            padding: 8px 18px; min-width: 75px;
        }
        QMessageBox QPushButton:hover, QDialog QPushButton:hover {
            background-color: #AF2C3A; border-color: #CE4655;
        }


        """)

        central = QWidget(self)
        central.setObjectName("root")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(14)

        header = QHBoxLayout()
        brand_image = QLabel()
        brand_image.setObjectName("rogueBrand")
        brand_image.setToolTip("Rogue Compressor For EVO")
        header_file = ASSET_DIR / "rogue_header.png"
        if header_file.is_file():
            brand_image.setPixmap(QPixmap(str(header_file)).scaledToWidth(
                510, Qt.TransformationMode.SmoothTransformation))
        else:
            brand_image.setText("ROGUE  /  COMPRESSOR FOR EVO")
        header.addWidget(brand_image)
        header.addStretch()
        promo = QPushButton()
        promo.setObjectName("musclePromo")
        promo.setCursor(Qt.CursorShape.PointingHandCursor)
        promo.setToolTip("Visit Muscle Memory at musclememory.fyi")
        promo.setAccessibleName("Get the Muscle Memory app — opens musclememory.fyi")
        promo.setText("Get Muscle Memory  ↗\nTrack workouts, nutrition && progress")
        logo_path = ASSET_DIR / "muscle_memory_48.png"
        if logo_path.is_file():
            from PySide6.QtGui import QIcon
            promo.setIcon(QIcon(str(logo_path)))
            from PySide6.QtCore import QSize
            promo.setIconSize(QSize(36, 36))
        promo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://musclememory.fyi")))
        header.addWidget(promo)
        outer.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(16)
        outer.addLayout(columns, 1)

        left = QVBoxLayout()
        left.setSpacing(12)
        columns.addLayout(left, 3)

        preview_panel = QFrame()
        preview_panel.setObjectName("previewPanel")
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(10)
        self.video_widget = QVideoWidget(self)
        self.video_widget.setMinimumHeight(270)
        self.player.setVideoOutput(self.video_widget)
        preview_layout.addWidget(self.video_widget, 1)
        self.info = QLabel("NO VIDEO LOADED  •  Import a workout clip to begin")
        self.info.setObjectName("muted")
        self.info.setWordWrap(True)
        preview_layout.addWidget(self.info)
        left.addWidget(preview_panel, 1)

        transport_panel = QFrame()
        transport_panel.setObjectName("panel")
        transport = QVBoxLayout(transport_panel)
        transport.setContentsMargins(16, 14, 16, 14)
        transport.setSpacing(12)
        transport_title = QLabel("PLAYBACK & CLIP SELECTION")
        transport_title.setObjectName("section")
        transport.addWidget(transport_title)
        controls = QHBoxLayout()
        self.play_button = QPushButton("▶  Play")
        self.play_button.clicked.connect(self.toggle_play)
        self.stop_button = QPushButton("■  Stop")
        self.stop_button.clicked.connect(self.player.stop)
        controls.addWidget(self.play_button)
        controls.addWidget(self.stop_button)
        controls.addStretch()
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setObjectName("muted")
        controls.addWidget(self.time_label)
        transport.addLayout(controls)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.sliderMoved.connect(self.player.setPosition)
        transport.addWidget(self.seek)
        trim_row = QHBoxLayout()
        self.start = QDoubleSpinBox()
        self.end = QDoubleSpinBox()
        for widget in (self.start, self.end):
            widget.setDecimals(2)
            widget.setSuffix(" s")
            widget.setSingleStep(0.5)
            widget.valueChanged.connect(self.validate_trim)
            widget.valueChanged.connect(self.clear_corrections_on_trim)
        trim_row.addWidget(QLabel("IN"))
        trim_row.addWidget(self.start)
        trim_row.addSpacing(12)
        trim_row.addWidget(QLabel("OUT"))
        trim_row.addWidget(self.end)
        transport.addLayout(trim_row)
        self.trim_info = QLabel("Select a clip up to 60 seconds")
        self.trim_info.setObjectName("accent")
        transport.addWidget(self.trim_info)
        self.preview_button = QPushButton("▶  Preview Selected Clip")
        self.preview_button.clicked.connect(self.preview_trim)
        transport.addWidget(self.preview_button)
        left.addWidget(transport_panel)

        side_scroll = QScrollArea()
        side_scroll.setWidgetResizable(True)
        side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side_scroll.setMinimumWidth(320)
        columns.addWidget(side_scroll, 2)
        side = QWidget()
        side_scroll.setWidget(side)
        right = QVBoxLayout(side)
        right.setContentsMargins(2, 2, 4, 2)
        right.setSpacing(12)

        import_panel = QFrame()
        import_panel.setObjectName("panel")
        import_layout = QVBoxLayout(import_panel)
        import_layout.setContentsMargins(16, 16, 16, 16)
        import_heading = QLabel("01  /  SOURCE")
        import_heading.setObjectName("section")
        import_layout.addWidget(import_heading)
        self.import_button = QPushButton("＋  Import Video")
        self.import_button.clicked.connect(self.import_video)
        import_layout.addWidget(self.import_button)
        right.addWidget(import_panel)

        privacy_panel = QFrame()
        privacy_panel.setObjectName("panel")
        privacy = QVBoxLayout(privacy_panel)
        privacy.setContentsMargins(16, 16, 16, 16)
        privacy.setSpacing(12)
        privacy_heading = QLabel("02  /  FACE PRIVACY")
        privacy_heading.setObjectName("section")
        privacy.addWidget(privacy_heading)
        self.blur = QCheckBox("Automatically blur detected faces")
        self.blur.setChecked(True)
        privacy.addWidget(self.blur)
        self.manual_button = QPushButton("▣  Select Manual Face Mask")
        self.manual_button.clicked.connect(self.select_manual_mask)
        self.manual_button.setEnabled(False)
        privacy.addWidget(self.manual_button)
        self.manual_info = QLabel("No manual face mask selected")
        self.manual_info.setObjectName("muted")
        self.manual_info.setWordWrap(True)
        privacy.addWidget(self.manual_info)
        self.correction_button = QPushButton("✎  Frame-by-frame Privacy Corrections")
        self.correction_button.clicked.connect(self.edit_corrections)
        privacy.addWidget(self.correction_button)
        self.correction_info = QLabel("0 saved correction ranges")
        privacy.addWidget(self.correction_info)
        self.blur.toggled.connect(self.validate_trim)
        privacy_note = QLabel("PRIVACY CHECK  •  Automatic detection can miss faces. Review the entire exported clip before posting.")
        privacy_note.setObjectName("muted")
        privacy_note.setWordWrap(True)
        privacy.addWidget(privacy_note)
        right.addWidget(privacy_panel)

        export_panel = QFrame()
        export_panel.setObjectName("panel")
        export_layout = QVBoxLayout(export_panel)
        export_layout.setContentsMargins(16, 16, 16, 16)
        export_layout.setSpacing(12)
        export_heading = QLabel("03  /  EXPORT")
        export_heading.setObjectName("section")
        export_layout.addWidget(export_heading)
        export_desc = QLabel("H.264 MP4  •  AAC audio  •  9.5 MB target")
        export_desc.setObjectName("muted")
        export_desc.setWordWrap(True)
        export_layout.addWidget(export_desc)
        export_layout.addWidget(QLabel("Video encoder"))
        self.encoder_choice = QComboBox()
        self.encoder_choice.addItem("Auto — GPU if available, otherwise CPU", "auto")
        self.encoder_choice.addItem("CPU — x264 (two-pass)", "cpu")
        self.encoder_choice.addItem("GPU — first available hardware encoder", "gpu")
        try:
            from compressor import available_encoders
            installed = available_encoders()
            for name, label in (("h264_nvenc", "NVIDIA NVENC"),
                                ("h264_amf", "AMD AMF"),
                                ("h264_qsv", "Intel Quick Sync")):
                if name in installed:
                    self.encoder_choice.addItem(label, name)
        except Exception as exc:
            self.status_encoder_error = str(exc)
        export_layout.addWidget(self.encoder_choice)
        self.encoder_note = QLabel("GPU choices depend on FFmpeg and installed drivers. Auto can fall back to CPU.")
        self.encoder_note.setObjectName("muted")
        self.encoder_note.setWordWrap(True)
        export_layout.addWidget(self.encoder_note)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        export_layout.addWidget(self.progress)
        self.export_button = QPushButton("↓  EXPORT MP4")
        self.export_button.setObjectName("primary")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_video)
        export_layout.addWidget(self.export_button)
        right.addWidget(export_panel)
        right.addStretch()

        self.status = QLabel("●  READY")
        self.status.setObjectName("muted")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)

        self.player.positionChanged.connect(self.on_position)
        self.player.durationChanged.connect(self.on_duration)
        self.player.playbackStateChanged.connect(self.on_playback_state)
        self.player.errorOccurred.connect(self.on_player_error)
        self.start.setEnabled(False)
        self.end.setEnabled(False)
        self.play_button.setEnabled(False)
        self.preview_button.setEnabled(False)

    def import_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose video", "", "Videos (*.mp4 *.mov *.mkv *.avi *.webm)")
        if not path:
            return
        try:
            metadata = get_video_metadata(path)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            QMessageBox.warning(self, "Cannot import video", str(exc))
            self.status.setText("Import failed")
            return
        self.video_path = path
        self.manual_box = None
        self.corrections = []
        self.review_dialog = None
        self.manual_info.setText("No manual face mask selected")
        self.manual_button.setEnabled(True)
        self.duration = metadata["duration"]
        self.player.setSource(QUrl.fromLocalFile(path))
        self.info.setText(
            f"{Path(path).name} | {metadata['width']}×{metadata['height']} | "
            f"{format_time(self.duration)} | {metadata['size'] / 1048576:.2f} MB"
        )
        self.start.blockSignals(True)
        self.end.blockSignals(True)
        self.start.setRange(0, self.duration)
        self.end.setRange(0, self.duration)
        self.start.setValue(0)
        self.end.setValue(min(self.duration, MAX_CLIP_SECONDS))
        self.start.blockSignals(False)
        self.end.blockSignals(False)
        self.start.setEnabled(True)
        self.end.setEnabled(True)
        self.play_button.setEnabled(True)
        self.preview_button.setEnabled(True)
        self.validate_trim()
        self.status.setText("Video loaded. Preview and trim selection available.")

    def clear_corrections_on_trim(self):
        if getattr(self, 'corrections', None):
            self.corrections = []
            self.correction_info.setText('Trim changed — review again')
            self.review_dialog = None

    def validate_trim(self):
        length = self.end.value() - self.start.value()
        valid = 0 < length <= MAX_CLIP_SECONDS
        self.preview_button.setEnabled(valid and self.video_path is not None)
        self.correction_button.setEnabled(valid and self.video_path is not None and self.blur.isChecked() and not getattr(self, "exporting", False))
        self.export_button.setEnabled(valid and self.video_path is not None and not getattr(self, "exporting", False))
        self.trim_info.setText(
            f"Selected: {length:.2f}s / maximum {MAX_CLIP_SECONDS:.0f}s"
            + ("" if valid else " — adjust start/end times")
        )
        return valid

    def toggle_play(self):
        self._previewing = False
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def preview_trim(self):
        if self.validate_trim():
            self._previewing = True
            self.player.setPosition(round(self.start.value() * 1000))
            self.player.play()

    def select_manual_mask(self):
        if not self.video_path:
            return
        try:
            # Decode the *same upright pixels* used by the v11.3 tracking loop.
            # Never run face detection or blur on the selection frame.
            import cv2
            cap = cv2.VideoCapture(str(self.video_path))
            if not cap.isOpened():
                raise RuntimeError('Cannot open source video')
            try:
                cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
                cap.set(cv2.CAP_PROP_POS_MSEC, float(self.start.value()) * 1000)
                ok, frame = cap.read()
            finally:
                cap.release()
            if not ok:
                raise RuntimeError('Cannot read trim start frame')
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h,w,_ = rgb.shape
            image = QImage(rgb.data,w,h,3*w,QImage.Format.Format_RGB888).copy()
            dialog = QDialog(self)
            dialog.setWindowTitle("Drag a rectangle over the face to obscure")
            box = QVBoxLayout(dialog)
            preview = RegionLabel(QPixmap.fromImage(image).scaled(480,720,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            box.addWidget(preview)
            box.addWidget(QLabel("Select face at trim start. Tracking is best-effort; review the full export."))
            actions = QHBoxLayout()
            save = QPushButton("Use this face mask")
            save.clicked.connect(dialog.accept)
            clear = QPushButton("Clear manual mask")
            clear.clicked.connect(lambda: (setattr(self,'manual_box',None),dialog.reject()))
            actions.addWidget(save)
            actions.addWidget(clear)
            box.addLayout(actions)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                chosen = preview.normalized_box()
                if chosen:
                    self.manual_box = chosen
                    self.review_dialog = None
                    self.manual_info.setText("Manual face mask selected (tracks from trim start)")
                else:
                    QMessageBox.warning(self,"No region selected","Drag a rectangle around the face first.")
            elif self.manual_box is None:
                self.manual_info.setText("No manual face mask selected")
        except Exception as exc:
            QMessageBox.warning(self,"Manual mask failed",str(exc))

    def edit_corrections(self):
        if not self.video_path or not self.validate_trim():
            return
        if self.manual_box is None:
            QMessageBox.information(self, 'Select head first', 'Click Select Manual Face Mask first, then review the tracked video.')
            return
        try:
            from v113_review import ReviewDialog
            dialog = ReviewDialog(self.video_path, self.start.value(), self.end.value(), self.manual_box, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.review_dialog = dialog
                self.correction_info.setText(f'v11.3 preview approved — {len(dialog.corrections)} corrected frames')
            else:
                dialog.close()
        except Exception as exc:
            QMessageBox.warning(self, 'Privacy editor failed', str(exc))

    def export_video(self):
        if not self.video_path or not self.validate_trim():
            return
        suggested = str(Path(self.video_path).with_name(Path(self.video_path).stem + '_evo.mp4'))
        destination, _ = QFileDialog.getSaveFileName(self, 'Export MP4', suggested, 'MP4 Video (*.mp4)')
        if not destination:
            return
        if Path(destination).resolve() == Path(self.video_path).resolve():
            QMessageBox.warning(self, 'Invalid destination', 'Choose a different file than the source.')
            return
        if Path(destination).exists():
            QMessageBox.warning(self, 'File exists', 'Choose a filename that does not already exist.')
            return
        reviewed = None
        if self.blur.isChecked():
            d = self.review_dialog
            if d is None or d.start_time != self.start.value() or d.end_time != self.end.value():
                QMessageBox.warning(self, 'Review required', 'Select your head and approve the v11.3 privacy preview before exporting.')
                return
            reviewed = (d.masked, dict(d.corrections))
        self.exporting = True
        self.export_button.setEnabled(False)
        self.import_button.setEnabled(False)
        self.progress.setValue(0)
        self.status.setText('Compressing video — please wait…')
        self.worker = ExportWorker(self.video_path, destination, self.start.value(), self.end.value(), self.blur.isChecked(), "Maximum", self.manual_box, self.corrections, self.encoder_choice.currentData(), reviewed)
        self.worker.progress_update.connect(self.progress.setValue)
        self.worker.succeeded.connect(self.export_success)
        self.worker.failed.connect(self.export_failed)
        self.worker.finished.connect(self.export_finished)
        self.worker.start()

    def export_success(self, path):
        size = Path(path).stat().st_size / 1_000_000
        self.status.setText(f'Export complete: {size:.2f} MB — {path}')
        QMessageBox.information(self, 'Export complete', f'Saved {size:.2f} MB MP4:\n{path}')

    def export_failed(self, error):
        self.status.setText('Export failed')
        QMessageBox.critical(self, 'Export failed', error)

    def export_finished(self):
        self.exporting = False
        self.import_button.setEnabled(True)
        self.validate_trim()

    def on_position(self, milliseconds):
        self.seek.setValue(milliseconds)
        self.time_label.setText(f"{format_time(milliseconds / 1000)} / {format_time(self.duration)}")
        if (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
                and self.video_path and milliseconds >= round(self.end.value() * 1000)
                and getattr(self, '_previewing', False)):
            self.player.pause()
            self._previewing = False

    def on_duration(self, milliseconds):
        self.seek.setRange(0, milliseconds)

    def on_playback_state(self, state):
        self.play_button.setText("Ⅱ  Pause" if state == QMediaPlayer.PlaybackState.PlayingState else "▶  Play")

    def on_player_error(self, error, message):
        if error != QMediaPlayer.Error.NoError:
            self.status.setText(f"Playback error: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_file = ASSET_DIR / "rogue_app_icon.png"
    if icon_file.is_file():
        app.setWindowIcon(QIcon(str(icon_file)))
    window = VideoCompressorWindow()
    window.show()
    sys.exit(app.exec())
