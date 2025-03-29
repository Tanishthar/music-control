import cv2
import mediapipe as mp
import math
import threading
import time
import logging
import sys
import audio_mixer
import audio_editor
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)

class HandTracker:
    def __init__(self, mode, songs, window_size):
        self.mode = mode
        self.songs = songs
        self.mp_hands = mp.solutions.hands
        self.last_tap_time = 0  # Cooldown timer for play/pause

        self.window_width, self.window_height = window_size
        screen_width, screen_height = 1920, 1080
        self.window_x = (screen_width - self.window_width) // 2
        self.window_y = (screen_height - self.window_height) // 2

        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.left_min, self.left_max = None, None
        self.right_min, self.right_max = None, None
        self.audio_thread = None
        self.should_quit = False  

        # Define colors and thickness
        self.silver_gray = (192, 192, 192)  # Silvery gray
        self.line_thickness = 1  # Thin lines
        self.circle_radius = 5  # Size of fingertip circles

        # Define finger tip landmarks
        self.fingertips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

    def calculate_distance(self, point1, point2):
        return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)

    def calibrate_distances(self):
        """Calibrate min/max distances with on-screen instructions, waiting for hands first."""
        hands_detected = False
        while not hands_detected:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)
            
            if result.multi_hand_landmarks:
                hands_detected = True
                for hand_landmarks in result.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            cv2.putText(frame, "Please show your hands to start calibration", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            # Resize camera window to match the app size
            frame = cv2.resize(frame, (self.window_width, self.window_height))

            # Show the camera window and move it to overlay the app
            cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Hand Tracking", self.window_width, self.window_height)
            cv2.moveWindow("Hand Tracking", self.window_x, self.window_y)

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                break
        
        if self.should_quit:
            return
        
        # Pinch phase
        start_time = time.time()
        left_min = float('inf')
        right_min = float('inf')
        while time.time() - start_time < 3:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)
            
            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    dist = self.calculate_distance(index_tip, thumb_tip)
                    
                    if handedness.classification[0].label == "Left":
                        left_min = min(left_min, dist)
                    else:
                        right_min = min(right_min, dist)
            
            cv2.putText(frame, "Pinch your fingers (Min Distance)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Resize camera window to match the app size
            frame = cv2.resize(frame, (self.window_width, self.window_height))

            # Show the camera window and move it to overlay the app
            cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Hand Tracking", self.window_width, self.window_height)
            cv2.moveWindow("Hand Tracking", self.window_x, self.window_y)

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                break
        
        if self.should_quit:
            return
        
        # Extend phase
        start_time = time.time()
        left_max = 0
        right_max = 0
        while time.time() - start_time < 3:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)
            
            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    dist = self.calculate_distance(index_tip, thumb_tip)
                    
                    if handedness.classification[0].label == "Left":
                        left_max = max(left_max, dist)
                    else:
                        right_max = max(right_max, dist)
            
            cv2.putText(frame, "Extend your fingers (Max Distance)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # Resize camera window to match the app size
            frame = cv2.resize(frame, (self.window_width, self.window_height))

            # Show the camera window and move it to overlay the app
            cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Hand Tracking", self.window_width, self.window_height)
            cv2.moveWindow("Hand Tracking", self.window_x, self.window_y)

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                break
        
        self.left_min, self.left_max = left_min, left_max
        self.right_min, self.right_max = right_min, right_max
        logging.info(f"Calibration: Left min={left_min:.3f}, max={left_max:.3f}, Right min={right_min:.3f}, max={right_max:.3f}")

    def draw_hand_annotations(self, frame, hand_landmarks):
        """Custom function to draw hands with thin silvery-gray lines and circles on fingertips."""
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (5, 9), (9, 13), (13, 17)  # Palm structure
        ]

        # Draw thin silvery-gray lines for the palm and fingers
        for connection in connections:
            start_idx, end_idx = connection
            start = hand_landmarks.landmark[start_idx]
            end = hand_landmarks.landmark[end_idx]
            h, w, _ = frame.shape
            start_pos = (int(start.x * w), int(start.y * h))
            end_pos = (int(end.x * w), int(end.y * h))
            cv2.line(frame, start_pos, end_pos, self.silver_gray, self.line_thickness)

        # Draw circles on the fingertips
        for idx in self.fingertips:
            tip = hand_landmarks.landmark[idx]
            tip_pos = (int(tip.x * frame.shape[1]), int(tip.y * frame.shape[0]))
            cv2.circle(frame, tip_pos, self.circle_radius, self.silver_gray, -1)

    def track_hands(self):
        """Continuously track hands and update audio settings in real time."""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb_frame)

            left_dist = None
            right_dist = None

            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    dist = self.calculate_distance(index_tip, thumb_tip)

                    if handedness.classification[0].label == "Left":
                        left_dist = dist
                    else:
                        right_dist = dist

            left_volume = 0.0
            if left_dist and self.left_max > self.left_min:
                normalized_left = max(0.0, min(1.0, (left_dist - self.left_min) / (self.left_max - self.left_min)))
                left_volume = np.log10(1 + normalized_left * 9)  # Logarithmic scaling

            right_value = 0.0
            if right_dist and self.right_max > self.right_min:
                normalized_right = max(0.0, min(1.0, (right_dist - self.right_min) / (self.right_max - self.right_min)))
                right_value = np.log10(1 + normalized_right * 9)  # Logarithmic scaling

            left_middle = None
            right_middle = None

            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get middle finger tips (Landmark 12)
                    middle_tip = hand_landmarks.landmark[12]

                    if handedness.classification[0].label == "Left":
                        left_middle = middle_tip
                    else:
                        right_middle = middle_tip

            # Detect tap gesture (middle fingers close together)
            if left_middle and right_middle:
                tap_distance = self.calculate_distance(left_middle, right_middle)
                if tap_distance < 0.03:  # Small distance means fingers tapped
                    current_time = time.time()
                    if current_time - self.last_tap_time > 1:  # 1-second cooldown
                        self.last_tap_time = current_time
                        audio_editor.toggle_play_pause()  # Call function to toggle play/pause
                        print("🎵 Play/Pause Toggled!")

            if self.mode == "mix":
                audio_mixer.update_mixing(left_volume, right_value)
            else:
                audio_editor.update_audio(left_volume, right_value)

            cv2.putText(frame, f"Mode: {self.mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if left_dist:
                cv2.putText(frame, f"Left: {left_volume:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if right_dist:
                cv2.putText(frame, f"Right: {right_value:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Resize camera window to match the app size
            frame = cv2.resize(frame, (self.window_width, self.window_height))

            # Show the camera window and move it to overlay the app
            cv2.namedWindow("Hand Tracking", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("Hand Tracking", self.window_width, self.window_height)
            cv2.moveWindow("Hand Tracking", self.window_x, self.window_y)

            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                break

        self.cleanup_and_exit()

    
    def start_audio(self):
        if self.mode == "mix":
            audio_mixer.start_mixing(self.songs)
        else:
            audio_editor.start_playback(self.songs[0])

    def cleanup_and_exit(self):
        self.cap.release()
        cv2.destroyAllWindows()
        if self.mode == "mix":
            audio_mixer.stop_mixing()
        else:
            audio_editor.stop_playback()
        logging.info("Exiting program")
        sys.exit(0)

def start_hand_tracking(mode, songs, window_size):
    tracker = HandTracker(mode, songs, window_size)
    tracker.calibrate_distances()
    if not tracker.should_quit:
        tracker.start_audio()
        tracker.track_hands()  # Start real-time hand tracking
    tracker.cleanup_and_exit()
