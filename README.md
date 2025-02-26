# 📻 PiWave

<div align=center>

![PiWave image](https://piwave.xyz/static/img/logo.png)

</div>


**PiWave** is a Python module designed to manage and control your Raspberry Pi radio using the `pi_fm_rds` utility. It allows you to easily convert audio files to WAV format and broadcast them at a specified frequency with RDS (Radio Data System) support.

## Features

- Converts audio files to WAV format.
- Broadcasts WAV files using the `pi_fm_rds` utility.
- Configurable broadcast frequency, PS (Program Service), RT (Radio Text), and PI (Program Identifier).
- Supports looping of playback.
- Detailed logging for debug mode.

> [!NOTE]
> Are you looking for a minimal gui for PiWave?
> Take a look at the [PiWave WebGUI](https://github.com/douxxtech/piwave-webgui)

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
    pip install git+https://github.com/douxxtech/piwave.git --break-system-packages
    ```

2. **Dependencies**:

    PiWave requires the `ffmpeg` and `ffprobe` utilities for file conversion and duration extraction. Install them using:

    ```bash
    sudo apt-get install ffmpeg
    ```
3. **PiFmRds**:

   PiWave uses [PiFmRds](https://github.com/ChristopheJacquet/PiFmRds) to work. Make sure you have installed it before running PiWave

## Usage

### Basic Usage

1. **Importing the module**:

    ```python
    from piwave import PiWave
    ```

2. **Creating an instance**:

    ```python
    piwave = PiWave(frequency=90.0, ps="MyRadio", rt="Playing great music", pi="ABCD", loop=True, debug=True)
    ```

3. **Sending files for playback**:

    ```python
    files = ["path/to/your/audiofile.mp3"]
    piwave.send(files)
    ```

4. **Restarting playback**:

    ```python
    piwave.restart()
    ```

5. **Stopping playback**:

    ```python
    piwave.stop()
    ```

### Configuration

- `frequency`: The broadcast frequency in MHz (default: 90.0).
- `ps`: Program Service name (up to 8 characters, default: "PiWave").
- `rt`: Radio Text (up to 64 characters, default: "PiWave: The best python module for managing your pi radio").
- `pi`: Program Identifier (up to 4 characters, default: "FFFF").
- `loop`: Whether to loop playback of files (default: False).
- `debug`: Enable detailed debug logging (default: False).

## Error Handling

- **Raspberry Pi Check**: The program verifies if it is running on a Raspberry Pi. It exits with an error message if not.
- **Root User Check**: The program requires root privileges to run. It exits with an error message if not run as root.
- **Executable Check**: The program automatically finds the `pi_fm_rds` executable or prompts the user to manually provide its path if it cannot be found.

## License

PiWave is licensed under the GNU General Public License (GPL) v3.0. See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue on [GitHub](https://github.com/douxxtech/piwave/issues) for any bugs or feature requests.

---

Thank you for using PiWave!
Made with <3 by Douxx
