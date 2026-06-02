# music_in_term

A CLI that downloads a YouTube video, extracts the audio, and renders a real-time frequency visualizer in the terminal.

## Usage

```bash
python main.py <youtube_url>
```

## How it works

### 1. Audio pipeline

```
YouTube URL → pytubefix → .mp4/webm in /tmp
                               ↓
                          pydub → .wav in /tmp
                               ↓
                     pygame plays the WAV
                     AudioAnalyzer reads the WAV
```

The audio is converted to WAV because it is the only format that allows random-access frame seeking, which is required for synchronization.

### 2. Synchronization

`pygame` and `AudioAnalyzer` read the WAV file with independent pointers. Before each frame, the analyzer is seeked to match pygame's actual playback position:

```python
analyzer.sync_to_ms(pygame.mixer.music.get_pos())
```

This prevents the visualizer from drifting ahead or behind the audio.

### 3. FFT — frequency analysis

The core of the visualizer is the **Discrete Fourier Transform (DFT)**, computed via `numpy`'s FFT algorithm.

Audio is a time-domain signal: a sequence of amplitude values sampled 44,100 times per second. The DFT transforms a chunk of those samples into the **frequency domain** — it answers the question: *which frequencies are present right now, and how loud is each one?*

The formula for each frequency bin `k`:

```
X[k] = Σ x[n] · e^(-i·2π·k·n/N)
```

This works by rotating the signal at each candidate frequency. If the signal contains that frequency, the rotations reinforce and produce a large magnitude. If it does not, they cancel out and produce ~0.

Only the magnitude is needed for visualization — the phase (direction of the complex vector) is discarded:

```python
fft_magnitude = np.abs(np.fft.fft(audio_data)[:N//2])
```

The first half of the FFT output is taken because the second half is a mirror image (redundant for real-valued signals).

#### Chunk size

The FFT is computed on chunks of **1024 samples** (~23ms of audio at 44.1kHz). This is a trade-off:

- Smaller chunks → faster visual response, lower frequency resolution
- Larger chunks → higher frequency resolution, slower visual response

#### Logarithmic band spacing

The 512 FFT bins are grouped into `N` display bands using **logarithmic spacing** (`numpy.geomspace`). Human hearing perceives pitch logarithmically — the perceptual distance between 100Hz and 200Hz is the same as between 1000Hz and 2000Hz (both are one octave). Linear spacing would waste most bars on high frequencies where little musical energy lives.

### 4. Rendering

Each frame:

1. Raw band values are **boosted** at higher frequencies to compensate for the natural energy drop-off in treble.
2. An **exponential moving average** (EMA) is applied so bars decay smoothly instead of snapping:
   ```
   smoothed[i] = α · current[i] + (1 - α) · previous[i]
   ```
3. Bars are drawn **symmetrically from the center** — each bar grows upward and downward proportionally to its band's energy.
4. A **gradient** interpolates from a dim base color (near center) to the full accent color (at the tips), using 24-bit ANSI escape codes with Catppuccin Frappé Mauve (`#ca9ee6`).
