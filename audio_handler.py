import pygame

class AudioHandler:
    def __init__(self):
        self.mode = None
        self.songs = None
        self.channel1 = None
        self.channel2 = None
        self.speed_states = [0.8, 1.0, 1.2]
        self.current_speed = 1.0
        pygame.mixer.init()

    def start_audio(self, mode, songs):
        """Start audio playback based on mode."""
        self.mode = mode
        self.songs = songs
        if mode == "mix" and len(songs) == 2:
            song1 = pygame.mixer.Sound(songs[0])
            song2 = pygame.mixer.Sound(songs[1])
            self.channel1 = pygame.mixer.Channel(0)
            self.channel2 = pygame.mixer.Channel(1)
            self.channel1.play(song1, loops=-1)
            self.channel2.play(song2, loops=-1)
        elif mode == "play" and len(songs) == 1:
            pygame.mixer.music.load(songs[0])
            pygame.mixer.music.play(loops=-1)

    def update_audio(self, mode, left_volume, right_value):
        """Update audio parameters based on hand distances."""
        if mode == "mix":
            if left_volume is not None and self.channel1:
                self.channel1.set_volume(left_volume)
            if right_value is not None and self.channel2:
                self.channel2.set_volume(right_value)
        elif mode == "play":
            if left_volume is not None:
                pygame.mixer.music.set_volume(left_volume)
            if right_value is not None:
                speed_index = int(right_value * (len(self.speed_states) - 1))
                new_speed = self.speed_states[speed_index]
                if new_speed != self.current_speed:
                    self.current_speed = new_speed
                    print(f"Speed set to {self.current_speed}x (requires preprocessing for true effect)")

    def stop_audio(self):
        """Stop all audio playback."""
        pygame.mixer.quit()

# Global instance for simplicity
audio = AudioHandler()

def start_audio(mode, songs):
    audio.start_audio(mode, songs)

def update_audio(mode, left_volume, right_value):
    audio.update_audio(mode, left_volume, right_value)

def stop_audio():
    audio.stop_audio()
