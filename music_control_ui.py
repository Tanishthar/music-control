from PyQt5 import QtWidgets, QtCore
import hand_tracking
import os

class MusicControlApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.songs = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Music Control App")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: #2C2F33; color: white;")

        layout = QtWidgets.QVBoxLayout()
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
        self.songs = []
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        dialog.setNameFilter("Audio Files (*.mp3 *.wav)")

        if mode == "mix":
            self.label.setText("Select Two Songs")
            while len(self.songs) < 2:
                if dialog.exec_():
                    selected = dialog.selectedFiles()
                    if len(selected) > 0:
                        self.songs.append(selected[0])
                        if len(self.songs) == 1:
                            self.label.setText("Select Second Song")
                else:
                    self.label.setText("Select Mode")
                    return
        else:
            self.label.setText("Select One Song")
            if dialog.exec_():
                self.songs = dialog.selectedFiles()

        if self.songs:
            self.label.setText(f"Selected {len(self.songs)} Song(s)")
            hand_tracking.start_hand_tracking(mode, self.songs)

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = MusicControlApp()
    app.exec_()