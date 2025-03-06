import cv2
import mediapipe as mp
import math
import threading
import time
import audio_handler
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO)

class HandTracker:
    def __init__(self, mode, songs):
        self.mode = mode
        self.songs = songs
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)
        self.left_min, self.left_max = None, None
        self.right_min, self.right_max = None, None
        self.audio_thread = None
        self.should_quit = False  # Flag to signal program exit

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
            
            cv2.putText(frame, "Please show your hands to start calibration", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                return
        
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
            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                return
        
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
            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                return
        
        if self.should_quit:
            return
        
        # Ensure valid ranges
        if left_max <= left_min:
            left_max = left_min + 0.1
        if right_max <= right_min:
            right_max = right_min + 0.1
        
        self.left_min, self.left_max = left_min, left_max
        self.right_min, self.right_max = right_min, right_max
        logging.info(f"Calibration: Left min={left_min:.3f}, max={left_max:.3f}, Right min={right_min:.3f}, max={right_max:.3f}")

    def track_hands(self):
        """Main tracking loop after calibration."""
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
                left_volume = max(0.0, min(1.0, (left_dist - self.left_min) / (self.left_max - self.left_min)))
                logging.debug(f"Left: raw={left_dist:.3f}, normalized={left_volume:.3f}")
            
            right_value = 0.0
            if right_dist and self.right_max > self.right_min:
                right_value = max(0.0, min(1.0, (right_dist - self.right_min) / (self.right_max - self.right_min)))
                logging.debug(f"Right: raw={right_dist:.3f}, normalized={right_value:.3f}")
            
            audio_handler.update_audio(self.mode, left_volume, right_value)
            
            cv2.putText(frame, f"Mode: {self.mode}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if left_dist:
                cv2.putText(frame, f"Left: {left_volume:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if right_dist:
                cv2.putText(frame, f"Right: {right_value:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow("Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.should_quit = True
                break
    
    def start(self):
        self.calibrate_distances()
        if self.should_quit:
            self.cleanup_and_exit()
            return
        
        self.audio_thread = threading.Thread(target=audio_handler.start_audio, args=(self.mode, self.songs))
        self.audio_thread.start()
        self.track_hands()
        self.cleanup_and_exit()

    def cleanup_and_exit(self):
        """Clean up resources and exit the program."""
        self.cap.release()
        cv2.destroyAllWindows()
        audio_handler.stop_audio()
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join()
        if self.should_quit:
            logging.info("Exiting program due to 'q' press")
            sys.exit(0)  # Terminate the entire program

def start_hand_tracking(mode, songs):
    tracker = HandTracker(mode, songs)
    tracker.start()

if __name__ == "__main__":
    start_hand_tracking("play", ["test.mp3"])