from pytubefix import YouTube
from pydub import AudioSegment
from audio_analyzer import AudioAnalyzer
import numpy as np
import os
import sys
import pygame
import time
import math
import threading
import wave
import struct

PATH = "/tmp" # Because we don't want to store this forever

def download_from_yt(link=""):
    yt = YouTube(link)
    audio_stream = yt.streams.filter(only_audio=True).first()
    filename = f"{yt.title}.{audio_stream.subtype}"
    if audio_stream:
        audio_stream.download(output_path=PATH, filename=filename)
    else:
        print("The song couldn't be found :(")
    full_path = os.path.join(PATH, filename)
    return full_path

def transfrom_to_wav(song_path=""):
    path = song_path.rsplit(".", 1)[0]
    extension = song_path.rsplit(".", 1)[1] if "." in song_path else None
    audio = AudioSegment.from_file(song_path, format=extension)
    audio.export(f"{path}.wav", format="wav")
    return f"{path}.wav"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# ChatGPT generated, verify this stuff
def reproduce_song(song_path="", width=80, height=20):
    if not song_path:
        raise ValueError("song_path cannot be empty")
    
    if not os.path.exists(song_path):
        raise FileNotFoundError(f"Audio file not found: {song_path}")
    
    # Convert to WAV for analysis
    wav_path = transfrom_to_wav(song_path)
    
    # Initialize audio analyzer
    analyzer = AudioAnalyzer(wav_path)
    
    # Initialize Pygame mixer
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()
    
    # Catppuccin Frappé palette (24-bit ANSI)
    colors = {
        'mauve':    '\033[38;2;202;158;230m',  # #ca9ee6
        'lavender': '\033[38;2;186;187;241m',  # #babbf1
        'reset': '\033[0m',
        'bold':  '\033[1m',
        'dim':   '\033[2m',
    }
    
    # Hide cursor
    sys.stdout.write('\033[?25l')
    sys.stdout.flush()
    
    try:
        # Each bar occupies 2 chars (█ + gap), so halve the available width
        num_bars = min((width - 4) // 2, 60)
        prev_bands = [0.0] * num_bars
        alpha = 0.3  # EMA factor: lower = smoother decay

        # Catppuccin Frappé Mauve gradient: dim base → vivid tip
        base_rgb  = (100, 79, 115)
        tip_rgb   = (202, 158, 230)

        def bar_color(distance, bar_half):
            t = distance / bar_half if bar_half > 0 else 0
            r = int(base_rgb[0] + t * (tip_rgb[0] - base_rgb[0]))
            g = int(base_rgb[1] + t * (tip_rgb[1] - base_rgb[1]))
            b = int(base_rgb[2] + t * (tip_rgb[2] - base_rgb[2]))
            return f'\033[38;2;{r};{g};{b}m'

        while pygame.mixer.music.get_busy():
            clear_screen()

            # Sync WAV reader to pygame's actual playback position, then analyze
            analyzer.sync_to_ms(pygame.mixer.music.get_pos())
            raw_bands = analyzer.get_frequency_bands(num_bars)

            # Boost higher frequency bands so treble is visible (perceptual compensation)
            boosted = [
                b * (1.0 + (i / num_bars) * 2.5)
                for i, b in enumerate(raw_bands)
            ]

            # Clamp to [0, 1] after boost
            boosted = [min(b, 1.0) for b in boosted]

            # Exponential moving average: fast attack, slow decay
            freq_bands = [
                alpha * cur + (1 - alpha) * prev
                for cur, prev in zip(boosted, prev_bands)
            ]
            prev_bands = freq_bands

            # Title
            title = f"♪ {os.path.basename(song_path)} ♪"
            print(colors['bold'] + colors['lavender'] + title.center(width) + colors['reset'])
            print(colors['dim'] + "─" * width + colors['reset'])
            print()

            # Symmetric spectrum bars: grow from center outward
            max_bar_height = height - 8
            half_height = max_bar_height // 2
            center_row = half_height

            for row in range(max_bar_height, 0, -1):
                line = "  "
                for band in freq_bands:
                    bar_half = int(band * half_height)
                    distance = abs(row - center_row)

                    if distance <= bar_half:
                        line += bar_color(distance, bar_half) + '█' + colors['reset'] + ' '
                    elif distance == 0:
                        line += colors['dim'] + '·' + colors['reset'] + ' '
                    else:
                        line += '  '

                print(line)
            
            # Controls
            print()
            print(colors['dim'] + "─" * width + colors['reset'])
            controls = "ctrl+c to stop"
            print(colors['dim'] + controls.center(width) + colors['reset'])
            
            # time.sleep(0.03)  # ~30 FPS
            time.sleep(0.06)  # ~60 FPS

            
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor again
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
        pygame.mixer.music.stop()
        analyzer.close()
        clear_screen()
        print(colors['green'] + "♪ Playback stopped. Thanks for listening! ♪" + colors['reset'])
        
        # Clean up WAV file if it was converted
        if wav_path != song_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass

# Stuff entrypoint
if __name__ == "__main__":
    # Get url from sys args
    url = sys.argv[1]
    song = download_from_yt(link=url)
    wav_song = transfrom_to_wav(song_path=song)
    reproduce_song(song_path=wav_song) # :)
