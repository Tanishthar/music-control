import sounddevice as sd
import soundfile as sf
import numpy as np
import threading

class AudioEditor:
    def __init__(self):
        self.data = None
        self.samplerate = None
        self.stream = None
        self.volume = 1.0
        self.freq_factor = 1.0  # Default = normal frequency
        self.should_stop = False
        self.is_paused = False
        self.playback_position = 0
        self.duration = 0.0

    def load_audio(self, file_path):
        """Load an audio file and ensure it's in mono format."""
        data, samplerate = sf.read(file_path, dtype="float32")
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)  # Convert stereo to mono
        self.duration = len(data) / samplerate
        return data, samplerate

    def start_playback(self, song):
        """Start or resume audio playback."""
        if self.is_paused:
            self.is_paused = False
            self.should_stop = False
            self.thread = threading.Thread(target=self.play_audio)
            self.thread.start()
            print("▶️ Resumed playback!")
            return

        # Load song if it's a new playback
        self.data, self.samplerate = self.load_audio(song)
        if self.data is None:
            print("❌ Error: Failed to load the song.")
            return

        self.should_stop = False
        self.playback_position = 0
        self.thread = threading.Thread(target=self.play_audio)
        self.thread.start()
        print("🎶 Playback started!")

    def play_audio(self):
        """Real-time playback with volume & frequency control."""
        def callback(outdata, frames, time, status):
            if self.should_stop:
                raise sd.CallbackStop()

            total_samples = len(self.data)
            new_indices = np.linspace(
                self.playback_position,
                self.playback_position + (frames * self.freq_factor),
                frames).astype(int)

            new_indices = np.clip(new_indices, 0, total_samples - 1)
            resampled_audio = self.data[new_indices] * self.volume
            outdata[:, 0] = resampled_audio
            self.playback_position += int(frames * self.freq_factor)

            if self.playback_position >= total_samples:
                self.should_stop = True

        self.stream = sd.OutputStream(samplerate=self.samplerate, channels=1, callback=callback)
        self.stream.start()

    def toggle_play_pause(self):
        """Pause or resume playback."""
        if self.is_paused:
            self.start_playback("")
        else:
            self.is_paused = True
            self.should_stop = True
            if self.stream:
                self.stream.abort()
            print("⏸️ Paused playback.")

    def update_audio(self, left_volume, right_value):
        """Update volume & frequency in real-time."""
        self.volume = left_volume
        self.freq_factor = 0.5 + (right_value * 1.0)  # Adjusts frequency between 0.5x and 1.5x

    def get_progress(self):
        """Returns current position and total duration in seconds."""
        elapsed = self.playback_position / self.samplerate if self.samplerate else 0
        return elapsed, self.duration

    def stop_playback(self):
        """Stop audio playback completely."""
        self.should_stop = True
        self.is_paused = False
        self.playback_position = 0
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("🛑 Playback stopped.")

# Global instance
editor = AudioEditor()

def start_playback(song):
    editor.start_playback(song)

def toggle_play_pause():
    editor.toggle_play_pause()

def update_audio(left_volume, right_value):
    editor.update_audio(left_volume, right_value)

def get_progress():
    return editor.get_progress()

def stop_playback():
    editor.stop_playback()