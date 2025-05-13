import pygame
import soundfile as sf
import time

class AudioMixer:
    def __init__(self):
        pygame.mixer.init()
        self.channel1 = None
        self.channel2 = None
        self.song1_path = None
        self.song2_path = None
        self.song1_start = None
        self.song2_start = None
        self.song1_duration = 0
        self.song2_duration = 0

    def start_mixing(self, songs):
        if len(songs) != 2:
            print("❌ Error: Please select exactly two songs for mixing.")
            return

        pygame.mixer.quit()
        pygame.mixer.init()

        self.channel1 = pygame.mixer.Channel(0)
        self.channel2 = pygame.mixer.Channel(1)

        self.song1_path = songs[0]
        self.song2_path = songs[1]

        song1 = pygame.mixer.Sound(self.song1_path)
        song2 = pygame.mixer.Sound(self.song2_path)

        self.song1_start = time.time()
        self.song2_start = time.time()

        self.song1_duration = self.get_duration(self.song1_path)
        self.song2_duration = self.get_duration(self.song2_path)

        self.channel1.play(song1, loops=-1)
        self.channel2.play(song2, loops=-1)
        print("🎵 Mixing started!")

    def update_mixing(self, left_volume, right_volume):
        if self.channel1 and self.channel2:
            self.channel1.set_volume(left_volume)
            self.channel2.set_volume(right_volume)

    def stop_mixing(self):
        pygame.mixer.quit()
        print("🛑 Mixing stopped.")

    def get_duration(self, path):
        try:
            with sf.SoundFile(path) as f:
                return len(f) / f.samplerate
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return 0

    def get_progress(self):
        """Returns elapsed time and duration for both songs."""
        elapsed1 = time.time() - self.song1_start if self.song1_start else 0
        elapsed2 = time.time() - self.song2_start if self.song2_start else 0
        return (elapsed1, elapsed2), (self.song1_duration, self.song2_duration)

# Global instance
mixer = AudioMixer()

def start_mixing(songs):
    mixer.start_mixing(songs)

def update_mixing(left_volume, right_volume):
    mixer.update_mixing(left_volume, right_volume)

def stop_mixing():
    mixer.stop_mixing()

def get_progress():
    return mixer.get_progress()