<div align=center>
<img alt="PiWave image" src="https://piwave.xyz/static/img/logo.png"/>
<h1>PiWave</h1>
</div>

**PiWave** is a Python module designed to manage and control your Raspberry Pi radio using the `pi_fm_rds` utility. It allows you to easily convert audio files to WAV format and broadcast them at a specified frequency with RDS (Radio Data System) support.

## Features

- Supports most audio file formats (MP3, FLAC, M4A, etc.)
- Configurable broadcast frequency, PS (Program Service), RT (Radio Text), and PI (Program Identifier)
- Real-time settings updates without restart
- Detailed logging with debug mode
- Error handling and event callbacks
- Non-blocking playback with threading
- Simple streaming-focused design

## Hardware Installation

To use PiWave for broadcasting, you need to set up the hardware correctly. This involves connecting an antenna or cable to the Raspberry Pi's GPIO pin.

1. **Connect the Cable or Antenna**:
   - Attach a cable or an antenna to GPIO 4 (Pin 7) on the Raspberry Pi.
   - Ensure the connection is secure to avoid any broadcasting issues.

2. **GPIO Pinout**:
   - GPIO 4 (Pin 7) is used for the broadcasting signal.
   - Ensure that the cable or antenna is properly connected to this pin for optimal performance.

## Installation

> [!WARNING]
> **Warning**: Using PiWave involves broadcasting signals which may be subject to local regulations and laws. It is your responsibility to ensure that your use of PiWave complies with all applicable legal requirements and regulations in your area. Unauthorized use of broadcasting equipment may result in legal consequences, including fines or penalties.
>
> **Liability**: The author of PiWave is not responsible for any damage, loss, or legal issues that may arise from the use of this software. By using PiWave, you agree to accept all risks and liabilities associated with its operation and broadcasting capabilities.
>
> Please exercise caution and ensure you have the proper permissions and knowledge of the regulations before using PiWave for broadcasting purposes.

### Auto Installer

For a quick and easy installation, you can use the auto installer script. Open a terminal and run:

```bash
curl -sL https://setup.piwave.xyz/ | sudo bash
```

This command will download and execute the installation script, setting up PiWave and its dependencies automatically.

> [!NOTE]
> To uninstall, use the following command:
> ```bash
> curl -sL https://setup.piwave.xyz/uninstall | sudo bash
> ```

### Manual Installation

To install PiWave manually, follow these steps:

1. **Clone the repository and install**:

   ```bash
   pip install git+https://github.com/douxxtech/piwave.git
   ```

2. **Dependencies**:

   PiWave requires the `ffmpeg` and `ffprobe` utilities for file conversion and duration extraction. Install them using:

   ```bash
   sudo apt-get install ffmpeg
   ```

3. **PiFmRds**:

   PiWave uses [PiFmRds](https://github.com/ChristopheJacquet/PiFmRds) to work. Make sure you have installed it before running PiWave.

## Quick Start

### Basic Usage

```python
from piwave import PiWave

# Create PiWave instance
pw = PiWave(
    frequency=90.0,
    ps="MyRadio",
    rt="Playing great music",
    pi="ABCD",
    debug=True
)

# Play a single audio file
pw.play("song.mp3")

# Stop playback
pw.stop()
```

### Real-time Settings Updates

```python
from piwave import PiWave

pw = PiWave()

# Update multiple settings at once
pw.update(
    frequency=101.5,
    ps="NewName",
    rt="Updated radio text",
    debug=True
)

# Update individual settings
pw.update(frequency=102.1)
pw.update(ps="Radio2024")
```

### Control Playback

```python
from piwave import PiWave

pw = PiWave(frequency=95.0)

# Play, pause, resume
pw.play("music.mp3")
pw.pause()
pw.resume()

# Check status
status = pw.get_status()
print(f"Playing: {status['is_playing']}")
print(f"Current file: {status['current_file']}")
```

## Examples

### Text-to-Speech Radio

```python
from gtts import gTTS
from piwave import PiWave
from pydub import AudioSegment
import os
import sys
import time

wav_file = sys.argv[1] if len(sys.argv) > 1 else 'tts.wav'

def tts(text, wav_file):
    mp3_file = "tts.mp3"
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(mp3_file)
    sound = AudioSegment.from_mp3(mp3_file)
    sound.export(wav_file, format="wav")
    os.remove(mp3_file)

def main():
    pw = None
    
    print("=" * 50)
    print("Text Broadcast by https://douxx.tech")
    print("""You need PiWave and a raspberry pi with root
access to run this tool !""")
    
    try:
        while True:
            print("=" * 50)
            text = input("Text to broadcast: ").strip()
            if not text:
                print("No text entered, skipping...\n")
                continue

            try:
                freq = float(input("Frequency to broadcast (MHz): "))
            except ValueError:
                print("Invalid frequency, please enter a number.\n")
                continue

            tts(text, wav_file)
            pw = PiWave(silent=True, frequency=freq)

            print("=" * 50)
            print("Ready to play!")
            print(f"Frequency : {freq} MHz")
            print(f"Text      : {text}")
            print(f"WAV file  : {os.path.abspath(wav_file)}")
            print("=" * 50)

            pw.play(wav_file)
            print("Playing! Press Ctrl+C to stop or wait for completion...\n")
            
            # Wait for playback to complete
            while pw.get_status()['is_playing']:
                time.sleep(0.5)
            
            print("Playback completed!\n")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        # Cleanup PiWave
        if pw:
            pw.stop()
            pw.cleanup()
        
        # Remove temp file
        if os.path.exists(wav_file):
            os.remove(wav_file)
        
        print("Cleanup done. Exiting...")

if __name__ == "__main__":
    main()
```

### Music Player with Callbacks

```python
from piwave import PiWave
import os
import time

def on_track_change(filename):
    print(f"🎵 Now playing: {os.path.basename(filename)}")

def on_error(error):
    print(f"❌ Error occurred: {error}")

def main():
    # Create player with callbacks
    pw = PiWave(
        frequency=101.5,
        ps="MyMusic",
        rt="Your favorite tunes",
        on_track_change=on_track_change,
        on_error=on_error
    )
    
    try:
        # Play different formats
        audio_files = ["song1.mp3", "song2.flac", "song3.m4a"]

        for audio_file in audio_files:
            if os.path.exists(audio_file):
                print(f"Playing {audio_file}...")
                pw.play(audio_file)
                
                # Wait for playback to complete
                while pw.get_status()['is_playing']:
                    time.sleep(0.5)
                
                print("Track completed. Press Enter for next song or Ctrl+C to quit...")
                input()
            else:
                print(f"File {audio_file} not found, skipping...")

        print("All tracks completed!")

    except KeyboardInterrupt:
        print("\nPlayback interrupted by user.")
    finally:
        # Cleanup
        pw.stop()
        pw.cleanup()
        print("Cleanup completed.")

if __name__ == "__main__":
    main()
```

### Simple FM Transmitter

```python
from piwave import PiWave
import os
import time

def simple_broadcast():
    pw = None
    
    try:
        # Initialize with custom settings
        pw = PiWave(
            frequency=88.5,
            ps="Pi-FM",
            rt="Broadcasting from Raspberry Pi",
            pi="RAPI"
        )
        
        audio_file = input("Enter audio file path: ")
        
        if not os.path.exists(audio_file):
            print("File not found!")
            return
        
        print(f"Broadcasting {audio_file} on 88.5 MHz")
        print("Press Ctrl+C to stop...")
        
        pw.play(audio_file)
        
        # Keep program running and show status
        while pw.get_status()['is_playing']:
            time.sleep(1)
        
        print("\nPlayback completed!")
            
    except KeyboardInterrupt:
        print("\nStopping broadcast...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if pw:
            pw.stop()
            pw.cleanup()
        print("Broadcast stopped and cleaned up.")

if __name__ == "__main__":
    simple_broadcast()
```

## API Reference

### PiWave Class

#### Initialization

```python
PiWave(
    frequency=90.0,        # Broadcast frequency (80.0-108.0 MHz)
    ps="PiWave",          # Program Service name (max 8 chars)
    rt="PiWave: ...",     # Radio Text (max 64 chars)
    pi="FFFF",            # Program Identifier (4 hex digits)
    debug=False,          # Enable debug logging
    silent=False,         # Disable all logging
    on_track_change=None, # Callback for track changes
    on_error=None         # Callback for errors
)
```

#### Methods

- **`play(file_path)`** - Play an audio file
- **`stop()`** - Stop playback
- **`pause()`** - Pause current playback
- **`resume()`** - Resume playback
- **`update(**kwargs)`** - Update any settings in real-time
- **`set_frequency(freq)`** - Change broadcast frequency
- **`get_status()`** - Get current player status
- **`cleanup()`** - Clean up resources

#### Properties

Access current settings through `get_status()`:
- `is_playing` - Whether audio is currently playing
- `frequency` - Current broadcast frequency
- `current_file` - Currently loaded file
- `ps` - Program Service name
- `rt` - Radio Text
- `pi` - Program Identifier

## Error Handling

- **Raspberry Pi Check**: Verifies the program is running on a Raspberry Pi
- **Root User Check**: Requires root privileges for GPIO access
- **Executable Check**: Automatically finds `pi_fm_rds` or prompts for path
- **File Validation**: Checks file existence and conversion capability
- **Process Management**: Handles cleanup of broadcasting processes

## Requirements

- Raspberry Pi (any model with GPIO)
- Root access (`sudo`)
- Python 3.6+
- FFmpeg for audio conversion
- PiFmRds for FM transmission

## License

PiWave is licensed under the GNU General Public License (GPL) v3.0. See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue on [GitHub](https://github.com/douxxtech/piwave/issues) for any bugs or feature requests.

---

Thank you for using PiWave!

![](https://madeby.douxx.tech)