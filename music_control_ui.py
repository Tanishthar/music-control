from PyQt5 import QtWidgets, QtCore
import hand_tracking
import os

class MusicControlApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Music Control App")

        # Set window size to 1920x1080 and center it
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        window_width = 1920
        window_height = 1080
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2

        self.setGeometry(x, y, window_width, window_height)
        self.show()

        self.setStyleSheet("background-color: #2C2F33; color: white;")
        layout = QtWidgets.QVBoxLayout()

        # Title Label
        self.label = QtWidgets.QLabel("Select Mode", self)
        self.label.setStyleSheet("font-size: 22px; font-weight: bold; padding: 10px;")
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignCenter)

        self.mix_button = QtWidgets.QPushButton("🎵 Mix Two Songs")
        self.play_button = QtWidgets.QPushButton("🎶 Play One Song")

        button_style = """
            QPushButton {
                background-color: #7289DA;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #5B6EAE;
            }
        """
        self.mix_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)

        layout.addWidget(self.mix_button)
        layout.addWidget(self.play_button)

        self.mix_button.clicked.connect(lambda: self.select_songs("mix"))
        self.play_button.clicked.connect(lambda: self.select_songs("play"))

        self.setLayout(layout)
        self.show()

    def select_songs(self, mode):
        """Open file dialog and start hand tracking."""
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setNameFilter("Audio Files (*.mp3 *.wav)")
        
        if dialog.exec_():
            songs = [os.path.abspath(song) for song in dialog.selectedFiles()]
            
            # Validate number of songs selected
            if mode == "mix" and len(songs) != 2:
                QtWidgets.QMessageBox.warning(self, "Error", "Please select exactly two songs for mixing.")
                return
            if mode == "play" and len(songs) != 1:
                QtWidgets.QMessageBox.warning(self, "Error", "Please select exactly one song for playback.")
                return

            print(f"🎵 Mode: {mode}, Selected Songs: {songs}")  # Debugging print
            self.label.setText(f"Selected {len(songs)} Song(s)")
            hand_tracking.start_hand_tracking(mode, songs, window_size=(1920,1080))

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MusicControlApp()
    app.exec_()
