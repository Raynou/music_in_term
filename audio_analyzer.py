import wave
import numpy as np

# ChatGPT generated, verify this stuff
class AudioAnalyzer:
    """Analyzes audio in real-time using FFT."""
    
    def __init__(self, wav_path, chunk_size=1024):
        self.wav_path = wav_path
        self.chunk_size = chunk_size
        self.frequencies = []
        self.running = False
        self.current_pos = 0
        
        # Open WAV file
        self.wf = wave.open(wav_path, 'rb')
        self.sample_rate = self.wf.getframerate()
        
    def get_audio_data(self):
        """Get current audio chunk and perform FFT."""
        data = self.wf.readframes(self.chunk_size)
        
        if len(data) < self.chunk_size * 2:
            return None
        
        # Convert to numpy array
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Perform FFT
        fft = np.fft.fft(audio_data)
        fft_magnitude = np.abs(fft[:len(fft)//2])
        
        # Normalize
        if np.max(fft_magnitude) > 0:
            fft_magnitude = fft_magnitude / np.max(fft_magnitude)
        
        return fft_magnitude
    
    def sync_to_ms(self, pos_ms):
        """Seek WAV reader to match current pygame playback position."""
        target_frame = int((pos_ms / 1000.0) * self.sample_rate)
        total_frames = self.wf.getnframes()
        self.wf.setpos(min(target_frame, total_frames))

    def get_frequency_bands(self, num_bands=40):
        """Split FFT into logarithmically spaced frequency bands."""
        data = self.get_audio_data()

        if data is None:
            return [0] * num_bands

        num_bins = len(data)
        # Logarithmic edges: low freqs get more bars, matching human hearing
        edges = np.geomspace(1, num_bins, num=num_bands + 1, dtype=int)
        edges = np.clip(edges, 0, num_bins - 1)

        bands = []
        for i in range(num_bands):
            start = edges[i]
            end = max(edges[i + 1], start + 1)
            bands.append(float(np.mean(data[start:end])))

        return bands
    
    def close(self):
        self.wf.close()
