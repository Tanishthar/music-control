import sys
import os
import pyautogui
import cv2
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
import hand_tracking
import audio_editor
import audio_mixer

class MusicControlApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Gesture Music Control")
        self.showFullScreen()
        self.setStyleSheet("background-color: #2C2F33; color: white;")

        # 🧱 Main vertical layout (center everything)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setAlignment(QtCore.Qt.AlignCenter)

        # 🟦 Top block: Title + description
        top_block = QtWidgets.QVBoxLayout()
        top_block.setAlignment(QtCore.Qt.AlignHCenter)

        title = QtWidgets.QLabel("🎧 Gesture-Based Music Controller")
        title.setStyleSheet("font-size: 36px; font-weight: bold; color: #7289DA;")
        title.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Control your music with just your hands!")
        subtitle.setStyleSheet("font-size: 20px; color: #99AAB5;")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)

        description = QtWidgets.QLabel(
            "Use finger gestures to play/pause music, adjust volume and tempo, or mix two songs in real-time."
        )
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 16px; color: #BBB; padding: 0 60px;")
        description.setAlignment(QtCore.Qt.AlignCenter)

        top_block.addWidget(title)
        top_block.addWidget(subtitle)
        top_block.addWidget(description)

        # 🟪 Bottom block: buttons
        bottom_block = QtWidgets.QVBoxLayout()
        bottom_block.setSpacing(10)
        bottom_block.setAlignment(QtCore.Qt.AlignHCenter)

        self.label = QtWidgets.QLabel("Select Mode")
        self.label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.mix_button = QtWidgets.QPushButton("🎵 Mix Two Songs")
        self.play_button = QtWidgets.QPushButton("🎶 Play One Song")

        button_style = """
            QPushButton {
                background-color: #7289DA;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #5B6EAE;
            }
        """
        self.mix_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)

        self.mix_button.clicked.connect(lambda: self.select_songs("mix"))
        self.play_button.clicked.connect(lambda: self.select_songs("play"))

        bottom_block.addWidget(self.label)
        bottom_block.addWidget(self.mix_button)
        bottom_block.addWidget(self.play_button)

        # Combine all in main layout with spacers to center
        main_layout.addStretch(1)
        main_layout.addLayout(top_block)
        main_layout.addStretch(1)
        main_layout.addLayout(bottom_block)
        main_layout.addStretch(2)

        self.setLayout(main_layout)

    def select_songs(self, mode):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setNameFilter("Audio Files (*.mp3 *.wav)")
        if dialog.exec_():
            songs = [os.path.abspath(song) for song in dialog.selectedFiles()]
            if mode == "mix" and len(songs) != 2:
                QtWidgets.QMessageBox.warning(self, "Error", "Please select exactly two songs for mixing.")
                return
            if mode == "play" and len(songs) != 1:
                QtWidgets.QMessageBox.warning(self, "Error", "Please select exactly one song for playback.")
                return
            self.hide()
            self.window = HandTrackingWindow(mode, songs)
            self.window.show()


class HandTrackingWindow(QtWidgets.QWidget):
    def __init__(self, mode, songs):
        super().__init__()
        self.mode = mode
        self.songs = songs
        self.tracker = hand_tracking.HandTracker(mode, songs, pyautogui.size())
        self.init_ui()
        self.start_tracking()

    def init_ui(self):
        self.setWindowTitle("Gesture Music Controller")
        screen_width, screen_height = pyautogui.size()
        # self.setGeometry(0, 0, screen_width, screen_height)
        self.showFullScreen()

        self.setStyleSheet("""
            background-color: #000000;
            color: white;
            QLabel {
                font-family: 'Segoe UI', sans-serif;
                font-size: 16px;
            }
        """)

        self.mode_label = QtWidgets.QLabel(f"Mode: {self.mode}")
        self.mode_label.setStyleSheet("font-size: 20px; color: lightgreen; font-weight: bold;")
        self.song_label = QtWidgets.QLabel(f"Song: {' & '.join(os.path.basename(song) for song in self.songs)}")
        self.song_label.setStyleSheet("font-size: 18px; color: white;")

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(self.mode_label)
        top_layout.addStretch()
        top_layout.addWidget(self.song_label)

        self.video_label = QtWidgets.QLabel()
        self.video_label.setFixedSize(int(screen_width * 0.6), int(screen_height * 0.8))
        self.video_label.setStyleSheet("background-color: black;")

        self.left_bar = QtWidgets.QProgressBar()
        self.left_bar.setOrientation(QtCore.Qt.Vertical)
        self.left_bar.setMaximum(100)
        self.left_bar.setStyleSheet("QProgressBar::chunk { background-color: #7289DA; } QProgressBar { background-color: #555; color: white; }")

        self.right_bar = QtWidgets.QProgressBar()
        self.right_bar.setOrientation(QtCore.Qt.Vertical)
        self.right_bar.setMaximum(100)
        self.right_bar.setStyleSheet("QProgressBar::chunk { background-color: #7289DA; } QProgressBar { background-color: #555; color: white; }")

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m sec")
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #7289DA; } QProgressBar { background-color: #555; color: white; }")

        self.status_label = QtWidgets.QLabel("🖐️ Waiting for hands...")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        self.exit_button = QtWidgets.QPushButton("❌ Exit")
        self.exit_button.setStyleSheet("font-size: 14px; padding: 6px; background-color: red; color: white; border-radius: 8px;")
        self.exit_button.clicked.connect(self.exit_app)

        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(QtWidgets.QLabel("Volume"))
        left_layout.addWidget(self.left_bar)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(QtWidgets.QLabel("Speed" if self.mode == "play" else "Volume"))
        right_layout.addWidget(self.right_bar)

        center_layout = QtWidgets.QHBoxLayout()
        center_layout.addLayout(left_layout)
        center_layout.addWidget(self.video_label)
        center_layout.addLayout(right_layout)

        bottom_layout = QtWidgets.QVBoxLayout()
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.exit_button)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addLayout(center_layout)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def start_tracking(self):
        QtCore.QTimer.singleShot(500, self.run_calibration)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def run_calibration(self):
        self.status_label.setText("🖐️ Calibrating... please pinch and extend")
        self.tracker.calibrate_distances()
        self.tracker.start_audio()
        self.status_label.setText("✅ Calibration complete. Gesture control active!")

    def update_frame(self):
        ret, frame = self.tracker.cap.read()
        if not ret:
            return

        frame, left_volume, right_value = self.tracker.process_frame(frame)

        self.left_bar.setValue(int(left_volume * 100))
        self.right_bar.setValue(int(right_value * 100))

        if self.mode == "play":
            elapsed, total = audio_editor.get_progress()
        else:
            (pos1, pos2), (dur1, dur2) = audio_mixer.get_progress()
            elapsed, total = (pos1 + pos2) / 2, (dur1 + dur2) / 2

        self.progress_bar.setMaximum(int(total))
        self.progress_bar.setValue(int(elapsed))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = QtGui.QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(img).scaled(self.video_label.size(), QtCore.Qt.KeepAspectRatio)
        self.video_label.setPixmap(pixmap)

    def exit_app(self):
        self.tracker.cleanup_and_exit()
        QtWidgets.QApplication.quit()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MusicControlApp()
    window.show()
    sys.exit(app.exec_())