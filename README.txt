# 🎧 Gesture-Based Music Controller

Control your music with just your hands — no keyboard, no mouse, just gestures!  
Built using Python, PyQt5, MediaPipe, and OpenCV, this desktop app lets you play, pause, control volume, adjust speed, and even mix two songs using real-time hand tracking.

---

## 🚀 Features

- 🎶 **Play One Song** — Control volume and playback speed using pinch gestures.
- 🎵 **Mix Two Songs** — Adjust individual volume levels of each track with your hands.
- ✋ **Gesture-Based Controls**:
  - Pinch Index + Thumb to scale Volume/Speed
  - Tap both hands together (Middle Fingers) to Play/Pause
- 📸 Embedded **Webcam Feed** with real-time hand visuals
- 📊 UI includes:
  - Live volume/speed bars
  - Song title and mode
  - Playback progress bar

---

## 🧰 Built With

- **Python 3.11+**
- [PyQt5](https://pypi.org/project/PyQt5/)
- [MediaPipe](https://google.github.io/mediapipe/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- [Pygame](https://www.pygame.org/)
- [Sounddevice](https://pypi.org/project/sounddevice/)
- [Soundfile](https://pypi.org/project/soundfile/)
- [PyAutoGUI](https://pypi.org/project/PyAutoGUI/)

---

## 📦 Installation

### 🔧 Prerequisites

- Python 3.11+
- A webcam
- A virtual environment (recommended)

### 🧪 Setup

```bash
git clone https://github.com/yourusername/gesture-music-controller.git
cd gesture-music-controller
python -m music_venv venv
music_venv\Scripts\activate  # On Windows
pip install -r requirements.txt
python music_control_ui.py
