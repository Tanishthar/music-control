import sys
import cv2
import mediapipe as mp
import math
import time
import logging
import numpy as np
import audio_mixer
import audio_editor

logging.basicConfig(level=logging.INFO)

class HandTracker:
    def __init__(self, mode, songs, window_size):
        self.mode = mode
        self.songs = songs
        self.window_width, self.window_height = window_size
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.cap = cv2.VideoCapture(0)

        self.left_min = self.left_max = None
        self.right_min = self.right_max = None
        self.should_quit = False
        self.last_tap_time = 0

    def calculate_distance(self, point1, point2):
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def calibrate_distances(self):
        hands_detected = False
        while not hands_detected:
            ret, frame = self.cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)
            hands_detected = bool(result.multi_hand_landmarks)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                return

        # Pinch Phase
        left_min, right_min = float('inf'), float('inf')
        start_time = time.time()
        while time.time() - start_time < 3:
            ret, frame = self.cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)
            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    dist = self.calculate_distance(
                        hand_landmarks.landmark[8],  # Index
                        hand_landmarks.landmark[4])  # Thumb
                    if handedness.classification[0].label == "Left":
                        left_min = min(left_min, dist)
                    else:
                        right_min = min(right_min, dist)

        # Extend Phase
        left_max, right_max = 0, 0
        start_time = time.time()
        while time.time() - start_time < 3:
            ret, frame = self.cap.read()
            if not ret:
                break
            rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)
            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    dist = self.calculate_distance(
                        hand_landmarks.landmark[8],
                        hand_landmarks.landmark[4])
                    if handedness.classification[0].label == "Left":
                        left_max = max(left_max, dist)
                    else:
                        right_max = max(right_max, dist)

        self.left_min, self.left_max = left_min, left_max
        self.right_min, self.right_max = right_min, right_max
        logging.info(f"Calibration Done — Left: min={left_min:.3f}, max={left_max:.3f} | Right: min={right_min:.3f}, max={right_max:.3f}")

    def start_audio(self):
        if self.mode == "mix":
            audio_mixer.start_mixing(self.songs)
        else:
            audio_editor.start_playback(self.songs[0])

    def cleanup_and_exit(self):
        self.cap.release()
        if self.mode == "mix":
            audio_mixer.stop_mixing()
        else:
            audio_editor.stop_playback()
        logging.info("Exited successfully.")
        sys.exit(0)

    def process_frame(self, frame):
        """Used by update_frame() in PyQt UI."""
        left_volume = right_value = 0.0
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        left_middle = right_middle = None

        if result.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                label = handedness.classification[0].label
                index_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]
                dist = self.calculate_distance(index_tip, thumb_tip)

                # Draw landmarks (only index and thumb with a connecting line)
                self.draw_index_thumb_line(frame, index_tip, thumb_tip)

                if label == "Left" and self.left_min is not None and self.left_max is not None:
                    norm = max(0.0, min(1.0, (dist - self.left_min) / (self.left_max - self.left_min)))
                    left_volume = np.log10(1 + norm * 9)
                    left_middle = hand_landmarks.landmark[12]

                elif label == "Right" and self.right_min is not None and self.right_max is not None:
                    norm = max(0.0, min(1.0, (dist - self.right_min) / (self.right_max - self.right_min)))
                    right_value = np.log10(1 + norm * 9)
                    right_middle = hand_landmarks.landmark[12]

        # Detect tap gesture (middle fingers close)
        if left_middle and right_middle:
            tap_distance = self.calculate_distance(left_middle, right_middle)
            if tap_distance < 0.03:
                current_time = time.time()
                if current_time - self.last_tap_time > 1:
                    self.last_tap_time = current_time
                    audio_editor.toggle_play_pause()

        # Apply audio controls
        if self.mode == "mix":
            audio_mixer.update_mixing(left_volume, right_value)
        else:
            audio_editor.update_audio(left_volume, right_value)

        return frame, left_volume, right_value

    def draw_index_thumb_line(self, frame, index_tip, thumb_tip):
        h, w, _ = frame.shape
        index_pos = (int(index_tip.x * w), int(index_tip.y * h))
        thumb_pos = (int(thumb_tip.x * w), int(thumb_tip.y * h))
        color = (255, 255, 255)

        # Draw fingertip outlines
        cv2.circle(frame, index_pos, 16, color, 2)
        cv2.circle(frame, thumb_pos, 16, color, 2)

        # Draw line connecting them
        cv2.line(frame, index_pos, thumb_pos, color, 2)