import pygame

class AudioMixer:
    def __init__(self):
        pygame.mixer.init()
        self.channel1 = None
        self.channel2 = None

    def start_mixing(self, songs):
        """Load and play two songs on separate channels."""
        if len(songs) != 2:
            print("❌ Error: Please select exactly two songs for mixing.")
            return

        pygame.mixer.quit()
        pygame.mixer.init()
        
        self.channel1 = pygame.mixer.Channel(0)
        self.channel2 = pygame.mixer.Channel(1)

        song1 = pygame.mixer.Sound(songs[0])
        song2 = pygame.mixer.Sound(songs[1])

        self.channel1.play(song1, loops=-1)
        self.channel2.play(song2, loops=-1)
        print("🎵 Mixing started!")

    def update_mixing(self, left_volume, right_volume):
        """Update volume levels for each track."""
        if self.channel1 and self.channel2:
            self.channel1.set_volume(left_volume)
            self.channel2.set_volume(right_volume)

    def stop_mixing(self):
        """Stop mixing playback."""
        pygame.mixer.quit()
        print("🛑 Mixing stopped.")

# Global instance for simplicity
mixer = AudioMixer()

def start_mixing(songs):
    mixer.start_mixing(songs)

def update_mixing(left_volume, right_volume):
    mixer.update_mixing(left_volume, right_volume)

def stop_mixing():
    mixer.stop_mixing()
