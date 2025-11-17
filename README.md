<div align=center>
<img alt="PiWave image" src="https://piwave.xyz/static/img/logo.png"/>
<h1>PiWave</h1>
</div>

**PiWave** is a Python module designed to manage and control your Raspberry Pi radio using multiple FM transmission backends. It provides a unified interface for broadcasting audio files with multiple backends support and RDS (Radio Data System) support.

## Features

- **Multi-Backend Architecture**: Supports multiple backends for different actions
- **Wide Frequency Support**: 1-250 MHz coverage through different backends
- **RDS Support**: Program Service, Radio Text, and Program Identifier broadcasting
- **Live Stream Support**: Broadcast live from a stream source.
- **Smart Backend Selection**: Automatically chooses the best backend to suit your needs
- **Audio Format Support**: Converts most audio formats (MP3, FLAC, M4A, etc.) to WAV
- **Real-time Settings Updates**: Change frequency, RDS data, and settings without restart
- **Advanced Playback Control**: Play, pause, resume, stop, and loop functionality
- **CLI Interface**: Command-line tools for backend management and broadcasting
- **Detailed Logging**: Debug mode with comprehensive error handling
- **Event Callbacks**: Custom handlers for track changes and errors
- **Non-blocking Operation**: Threading-based playback with status monitoring

## Supported Backends

### PiFmRds Backend
- **Frequency Range**: 80.0 - 108.0 MHz (Standard FM band)
- **RDS Support**: ✅ Full support (PS, RT, PI)
- **Live Support**: ❌ No live support
- **Repository**: [ChristopheJacquet/PiFmRds](https://github.com/ChristopheJacquet/PiFmRds)
- **Best For**: Standard FM broadcasting with RDS features

### FmTransmitter Backend  
- **Frequency Range**: 1.0 - 250.0 MHz (Extended range)
- **RDS Support**: ❌ No RDS support
- **Live Support**: ✅ Experimental support
- **Repository**: [markondej/fm_transmitter](https://github.com/markondej/fm_transmitter)
- **Best For**: Non-standard frequencies and experimental broadcasting

## Hardware Installation

To use PiWave for broadcasting, you need to set up the hardware correctly:

1. **Connect the Antenna**:
   - Attach a cable or antenna to GPIO 4 (Pin 7) on the Raspberry Pi
   - Ensure secure connection for optimal signal quality
   - Use appropriate antenna length for your target frequency

2. **GPIO Configuration**:
   - GPIO 4 (Pin 7) is used for FM signal output
   - No additional hardware modifications required

## Installation

> [!WARNING]
> **Legal Disclaimer**: Broadcasting radio signals may be subject to local regulations and laws. It is your responsibility to ensure compliance with all applicable legal requirements in your area. Unauthorized broadcasting may result in legal consequences, including fines or penalties.
>
> **Liability**: The author is not responsible for any damage, loss, or legal issues arising from the use of this software. Users accept all risks and liabilities associated with operation and broadcasting capabilities.

### Quick Installation (Recommended)

Use the automated installer script:

```bash
curl -sL https://setup.piwave.xyz/ | sudo bash
```

This installs PiWave dependencies and the PiFmRds backend automatically.

#### Advanced Installation Options

```bash
# Install with fm_transmitter backend (may affect system stability)
curl -sL https://setup.piwave.xyz/ | sudo bash -s -- --install_fmt

# Skip confirmation prompts
curl -sL https://setup.piwave.xyz/ | sudo bash -s -- --install_fmt --no-wait
```

#### Uninstallation

```bash
curl -sL https://setup.piwave.xyz/uninstall | sudo bash
```

### Manual Installation

1. **Install Dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip ffmpeg git make libsndfile1-dev
   ```

2. **Install PiWave**:
   ```bash
   # Create virtual environment (recommended)
   python3 -m venv ~/piwave-env
   source ~/piwave-env/bin/activate
   
   # Install PiWave
   pip install git+https://github.com/douxxtech/piwave.git
   ```

3. **Install Backends**:

   **PiFmRds** (Recommended):
   ```bash
   git clone https://github.com/ChristopheJacquet/PiFmRds /opt/PiWave/PiFmRds
   cd /opt/PiWave/PiFmRds/src
   make
   ```

   **FmTransmitter** (Optional):
   ```bash
   sudo apt install -y libraspberrypi-dev
   git clone https://github.com/markondej/fm_transmitter /opt/PiWave/fm_transmitter
   cd /opt/PiWave/fm_transmitter
   make
   ```

## Quick Start

### Basic Usage

```python
from piwave import PiWave

# Initialize with automatic backend selection
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

### Backend Selection

```python
from piwave import PiWave

# Automatic selection (recommended)
pw = PiWave(frequency=95.0, backend="auto")

# Force specific backend
pw = PiWave(frequency=95.0, backend="pi_fm_rds")

# Extended frequency range with fm_transmitter
pw = PiWave(frequency=150.0, backend="fm_transmitter")
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

# Individual setting updates
pw.update(frequency=102.1)
pw.update(ps="Radio2024")
```

### Advanced Playback Control

```python
from piwave import PiWave

pw = PiWave(frequency=95.0, loop=True)

# Playback control
pw.play("music.mp3")
pw.pause()
pw.resume()
pw.stop()

# Status monitoring
status = pw.get_status()
print(f"Playing: {status['is_playing']}")
print(f"Current backend: {status['current_backend']}")
print(f"Backend supports RDS: {status['backend_supports_rds']}")
print(f"Frequency range: {status['backend_frequency_range']}")
```


## Backend Management

### CLI Commands

```bash
# Search for available backends on system
python3 -m piwave search

# List cached backends
python3 -m piwave list

# Manually add backend executable path
python3 -m piwave add pi_fm_rds /path/to/pi_fm_rds

# Show package information
python3 -m piwave info

# Broadcast a file directly
python3 -m piwave broadcast song.mp3 --frequency 101.5 --ps "MyRadio"
```

### Programmatic Backend Discovery

```python
from piwave.backends import discover_backends, list_backends, search_backends

# Load cached backends
discover_backends()

# Search for new backends (ignores cache)
search_backends()

# List available backends with details
backends_info = list_backends()
```


## Complete Examples

<details>
    <summary>Click to expand examples</summary>

### Multi-Backend Radio Station

```python
from piwave import PiWave
import os
import time

def smart_radio_station():
    """Automatically selects best backend for each frequency"""
    
    stations = [
        {"freq": 88.5, "name": "Jazz FM", "file": "jazz.mp3"},
        {"freq": 101.5, "name": "Rock Radio", "file": "rock.mp3"},
        {"freq": 150.0, "name": "Experimental", "file": "experimental.wav"}
    ]
    
    for station in stations:
        try:
            # PiWave automatically selects the best backend
            pw = PiWave(
                frequency=station["freq"],
                ps=station["name"][:8],  # Max 8 chars
                rt=f"Broadcasting {station['name']}",
                backend="auto"  # Let PiWave choose
            )
            
            print(f"Starting {station['name']} on {station['freq']}MHz")
            print(f"Using backend: {pw.get_status()['current_backend']}")
            
            if os.path.exists(station["file"]):
                pw.play(station["file"])
                
                # Wait for completion or user interrupt
                while pw.get_status()['is_playing']:
                    time.sleep(1)
                    
                print(f"{station['name']} completed")
            else:
                print(f"File {station['file']} not found")
                
            pw.cleanup()
            
        except Exception as e:
            print(f"Error with {station['name']}: {e}")

if __name__ == "__main__":
    smart_radio_station()
```

### Text-to-Speech Radio with Backend Selection

```python
from gtts import gTTS
from piwave import PiWave
from pydub import AudioSegment
import os
import sys
import time

def tts_radio():
    """Text-to-speech radio with automatic backend selection using update() method"""
    
    print("=" * 50)
    print("TTS Radio, original: https://git.new/SEdemCA")
    print("=" * 50)
    
    pw = None
    wav_file = "tts_radio.wav"
    
    try:
        # Initialize PiWave once with default settings
        print("Initializing PiWave...")
        pw = PiWave(
            frequency=90.0,  # Default frequency
            ps="TTS-FM",
            rt="Text-to-Speech Radio",
            backend="auto",
            silent=False
        )
        
        print("PiWave initialized successfully!")
        print(f"Initial backend: {pw.get_status()['current_backend']}")
        print("=" * 50)
        
        while True:
            print("\n" + "=" * 30)
            text = input("Text to broadcast: ").strip()
            if not text:
                print("No text entered, skipping...\n")
                continue

            try:
                freq = float(input("Frequency (MHz): "))
            except ValueError:
                print("Invalid frequency, please enter a number.\n")
                continue
            
            # Let user choose backend or use auto
            backend_choice = input("Backend (auto/pi_fm_rds/fm_transmitter) [auto]: ").strip()
            if not backend_choice:
                backend_choice = "auto"
            
            # Generate TTS
            print("Generating speech...")
            mp3_file = "temp_tts.mp3"
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(mp3_file)
            
            # Convert to WAV
            sound = AudioSegment.from_mp3(mp3_file)
            sound.export(wav_file, format="wav")
            os.remove(mp3_file)

            try:
                # update pw settings

                update_params = {
                    'frequency': freq,
                    'rt': text[:64]
                }
                
                update_params['backend'] = backend_choice
                
                print("Updating broadcast settings...")
                pw.update(**update_params)
                
                status = pw.get_status()
                print(f"\nBroadcast Configuration:")
                print(f"Frequency: {freq}MHz")
                print(f"Backend: {status['current_backend']}")
                print(f"RDS Support: {'Yes' if status['backend_supports_rds'] else 'No'}")
                print(f"Text: {text}")
                print("=" * 50)

                pw.play(wav_file)
                print("Broadcasting! Press Ctrl+C to stop...\n")
                
                # Wait for completion
                while pw.get_status()['is_playing']:
                    time.sleep(0.5)
                
                print("Broadcast completed!\n")
                
            except Exception as e:
                print(f"Update/Broadcast error: {e}")
                print("Continuing with current settings...\n")
                continue

    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Initialization error: {e}")
        print("Make sure you're running on a Raspberry Pi as root with PiWave dependencies installed.")
    finally:
        if pw:
            pw.cleanup()
        
        # Cleanup temp files
        for temp_file in [wav_file, "temp_tts.mp3"]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        print("Cleanup completed.")

if __name__ == "__main__":
    tts_radio()
```

</details>

## API Reference

<details>
    <summary>Click to expand API reference</summary>


### PiWave Class

#### Initialization

```python
PiWave(
    frequency=90.0,            # Broadcast frequency (1.0-250.0 MHz)
    ps="PiWave",               # Program Service name (max 8 chars)
    rt="PiWave: ...",          # Radio Text (max 64 chars)
    pi="FFFF",                 # Program Identifier (4 hex digits)
    debug=False,               # Enable debug logging
    silent=False,              # Disable all logging
    loop=False,                # Loop current track continuously
    backend="auto",            # Backend selection ("auto", "pi_fm_rds", "fm_transmitter")
    used_for="file_broadcast", # Backend main purpose, used if backend = auto ("file_broadcast", "live_broadcast")
    on_track_change=None,      # Callback for track changes
    on_error=None              # Callback for errors
)
```

#### Core Methods

##### `play(file_path: str) -> bool`
Start playing an audio file with automatic format conversion.

```python
pw.play("song.mp3")  # Returns True if started successfully
```

##### `stop()`
Stop all playback and clean up processes.

```python
pw.stop()
```

##### `pause()` / `resume()`
Pause and resume playback control.

```python
pw.pause()
pw.resume()
```

##### `update(**kwargs)`
Update settings in real-time. Accepts any initialization parameter.

```python
pw.update(frequency=101.5, ps="NewName", backend="fm_transmitter")
```

##### `get_status() -> dict`
Get comprehensive status information.

```python
status = pw.get_status()
# Returns:
{
    'is_playing': bool,
    'is_live_streaming': bool,
    'frequency': float,
    'current_file': str|None,
    'current_backend': str,
    'backend_frequency_range': str,
    'backend_supports_rds': bool,
    'available_backends': list,
    'ps': str,
    'rt': str, 
    'pi': str,
    'loop': bool
}
```

##### `cleanup()`
Clean up resources and temporary files.

> [!WARNING]
> Always clean up behind you! Dropped support of auto-cleanup on version > 2.1.2

```python
pw.cleanup()
```

### Backend Management

#### Discovery Functions

```python
from piwave.backends import discover_backends, search_backends, list_backends

# Load cached backend availability
discover_backends()

# Perform fresh search (updates cache)
search_backends()

# List available backends with details
backend_info = list_backends()
```

#### Backend Selection

```python
from piwave.backends import get_best_backend

# Get best backend for specific frequency
backend_name = get_best_backend("file_broadcast", 95.0)
```

### Command Line Interface

```bash
# Backend management
python3 -m piwave search                    # Search for backends
python3 -m piwave list                      # List cached backends
python3 -m piwave add pi_fm_rds /path/exe   # Add backend path
python3 -m piwave info                      # Package information

# Direct broadcasting
python3 -m piwave broadcast file.mp3 \
    --frequency 101.5 \
    --ps "MyRadio" \
    --rt "Great Music" \
    --pi "ABCD" \
    --backend auto \
    --loop \
    --debug
```

## Error Handling

PiWave includes comprehensive error handling:

- **Environment Validation**: Raspberry Pi and root access checks
- **Backend Validation**: Automatic detection and compatibility verification
- **Frequency Validation**: Ensures frequency is within backend's supported range
- **File Validation**: Checks file existence and format compatibility
- **Process Management**: Clean process termination and resource cleanup
- **Exception Callbacks**: Custom error handlers for applications

### Common Error Scenarios

```python
from piwave import PiWave, PiWaveError

try:
    pw = PiWave(frequency=50.0, backend="pi_fm_rds")  # Outside range
except PiWaveError as e:
    print(f"Configuration error: {e}")
    # Try with auto backend selection
    pw = PiWave(frequency=50.0, backend="auto")
```

## Backend Development

### Creating Custom Backends

```python
from piwave.backends.base import Backend

class CustomBackend(Backend):
    @property
    def name(self):
        return "custom_backend"
    
    @property
    def frequency_range(self):
        return (50.0, 200.0)  # MHz range
    
    @property
    def supports_rds(self):
        return True  # RDS capability

    @property
    def supports_loop(self):
        return True  # loop support capability
    
    def _get_executable_name(self):
        return "my_transmitter"
    
    def _get_search_paths(self):
        return ["/opt", "/usr/local/bin", "/usr/bin"]
    
    def build_command(self, wav_file: str, loop: bool):
        cmd = ['sudo', self.required_executable, '-f', str(self.frequency)]
        if self.supports_rds and self.ps:
            cmd.extend(['-ps', self.ps])

        if self.supports_rds and loop:
            cmd.extend(['-loop'])
        cmd.append(wav_file)
        return cmd
```

### Backend Registration

```python
from piwave.backends import backend_classes

# Register custom backend
backend_classes["custom_backend"] = CustomBackend

# Re-discover backends
from piwave.backends import discover_backends
discover_backends()
```

</details>

## Troubleshooting

### Common Issues

1. **"No suitable backend found"**
   ```bash
   python3 -m piwave search  # Refresh backend cache
   ```

2. **"Backend doesn't support frequency"**
   ```python
   # Check supported ranges
   python3 -m piwave list
   
   # Use auto selection
   pw = PiWave(frequency=your_freq, backend="auto")
   ```

3. **"Process failed to start"**
   - Ensure running as root: `sudo python3 your_script.py`
   - Verify backend installation: `python3 -m piwave list`
   - Check executable permissions

4. **Audio conversion issues**
   - Install FFmpeg: `sudo apt install ffmpeg`
   - Check file format support
   - Verify file permissions

### Debug Mode

Enable comprehensive logging:

```python
pw = PiWave(debug=True)
# or
pw.update(debug=True)
```

### Backend Path Issues

Manually specify backend paths:

```bash
# Find backend executable
sudo find /opt -name "pi_fm_rds" -type f

# Add to PiWave
python3 -m piwave add pi_fm_rds /opt/PiWave/PiFmRds/src/pi_fm_rds
```

## Performance Notes

- **Backend Selection**: `pi_fm_rds` generally provides better stability for standard FM frequencies
- **Audio Conversion**: WAV files play immediately; other formats require conversion time
- **Memory Usage**: Large audio files are streamed, not loaded entirely into memory
- **CPU Impact**: FM transmission is CPU-intensive; avoid other heavy processes during broadcast

## Requirements

- Raspberry Pi (any model with GPIO)
- Root access (`sudo`)
- Python 3.7+
- FFmpeg for audio conversion
- At least one backend installed (PiFmRds or fm_transmitter)

### System Dependencies

```bash
sudo apt install -y python3 python3-pip ffmpeg git make libsndfile1-dev
```

### Optional Dependencies

```bash
# For extended frequency range
sudo apt install -y libraspberrypi-dev

# For Python virtual environment (recommended)
sudo apt install -y python3-venv
```

## License

PiWave is licensed under the GNU General Public License (GPL) v3.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Areas for contribution:

- Additional backend implementations
- Improved frequency range detection
- Enhanced RDS functionality
- Performance optimizations
- Documentation improvements

Please submit pull requests or open issues on [GitHub](https://github.com/douxxtech/piwave/issues).

## Acknowledgments

- [ChristopheJacquet/PiFmRds](https://github.com/ChristopheJacquet/PiFmRds) - Primary FM/RDS backend
- [markondej/fm_transmitter](https://github.com/markondej/fm_transmitter) - Extended frequency backend

---

**PiWave** - FM Broadcasting module for Raspberry Pi

![Made by Douxx](https://madeby.douxx.tech)