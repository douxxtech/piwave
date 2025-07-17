# piwave/piwave.py
# Improved version by Claude - fixes blocking issues, adds stream support, better error handling
# pi_fm_rds is required !!! Check https://github.com/ChristopheJacquet/PiFmRds

import os
import subprocess
import signal
import threading
import time
import asyncio
import tempfile
import shutil
import sys
from typing import List, Optional, Callable
from pathlib import Path
from urllib.parse import urlparse

class Log:
    COLORS = { # absolutely not taken from stackoverflow trust
        'reset': '\033[0m',
        'bold': '\033[1m',
        'underline': '\033[4m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bright_red': '\033[91m',
        'bright_green': '\033[92m',
        'bright_yellow': '\033[93m',
        'bright_blue': '\033[94m',
        'bright_magenta': '\033[95m',
        'bright_cyan': '\033[96m',
        'bright_white': '\033[97m',
    }

    ICONS = {
        'success': 'OK',
        'error': 'ERR',
        'warning': 'WARN',
        'info': 'INFO',
        'client': 'CLIENT',
        'server': 'SERVER',
        'file': 'FILE',
        'broadcast': 'BCAST',
        'version': 'VER',
        'update': 'UPD',
    }

    @classmethod
    def print(cls, message: str, style: str = '', icon: str = '', end: str = '\n'):
        color = cls.COLORS.get(style, '')
        icon_char = cls.ICONS.get(icon, '')
        if icon_char:
            if color:
                print(f"{color}[{icon_char}]\033[0m {message}", end=end)
            else:
                print(f"[{icon_char}] {message}", end=end)
        else:
            if color:
                print(f"{color}{message}\033[0m", end=end)
            else:
                print(f"{message}", end=end)
        sys.stdout.flush()

    @classmethod
    def header(cls, text: str):
        cls.print(text, 'bright_blue', end='\n\n')
        sys.stdout.flush()

    @classmethod
    def section(cls, text: str):
        cls.print(f" {text} ", 'bright_blue', end='')
        cls.print("─" * (len(text) + 2), 'blue', end='\n\n')
        sys.stdout.flush()

    @classmethod
    def success(cls, message: str):
        cls.print(message, 'bright_green', 'success')

    @classmethod
    def error(cls, message: str):
        cls.print(message, 'bright_red', 'error')

    @classmethod
    def warning(cls, message: str):
        cls.print(message, 'bright_yellow', 'warning')

    @classmethod
    def info(cls, message: str):
        cls.print(message, 'bright_cyan', 'info')

    @classmethod
    def file_message(cls, message: str):
        cls.print(message, 'yellow', 'file')

    @classmethod
    def broadcast_message(cls, message: str):
        cls.print(message, 'bright_magenta', 'broadcast')

class PiWaveError(Exception):
    pass

class PiWave:
    def __init__(self, 
                 frequency: float = 90.0, 
                 ps: str = "PiWave", 
                 rt: str = "PiWave: The best python module for managing your pi radio", 
                 pi: str = "FFFF", 
                 loop: bool = False, 
                 debug: bool = False,
                 on_track_change: Optional[Callable] = None,
                 on_error: Optional[Callable] = None):
        
        self.debug = debug
        
        self._validate_environment()
        
        self.frequency = frequency
        self.ps = str(ps)[:8]
        self.rt = str(rt)[:64]
        self.pi = str(pi).upper()[:4]
        self.loop = loop
        self.on_track_change = on_track_change
        self.on_error = on_error
        
        self.playlist: List[str] = []
        self.converted_files: dict[str, str] = {}
        self.current_index = 0
        self.is_playing = False
        self.is_stopped = False
        
        self.current_process: Optional[subprocess.Popen] = None
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        self.temp_dir = tempfile.mkdtemp(prefix="piwave_")
        self.stream_process: Optional[subprocess.Popen] = None
        
        self.pi_fm_rds_path = self._find_pi_fm_rds_path()
        
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        
        Log.info(f"PiWave initialized - Frequency: {frequency}MHz, PS: {ps}, Loop: {loop}")

    def _log_debug(self, message: str):
        if self.debug:
            Log.print(f"[DEBUG] {message}", 'blue')


    def _validate_environment(self):

        #validate that we're running on a Raspberry Pi as root

        if not self._is_raspberry_pi():
            raise PiWaveError("This program must be run on a Raspberry Pi")
        
        if not self._is_root():
            raise PiWaveError("This program must be run as root")

    def _is_raspberry_pi(self) -> bool:
        try:
            with open("/sys/firmware/devicetree/base/model", "r") as f:
                model = f.read().strip()
                return "Raspberry Pi" in model
        except FileNotFoundError:
            return False

    def _is_root(self) -> bool:
        return os.geteuid() == 0

    def _find_pi_fm_rds_path(self) -> str:
        current_dir = Path(__file__).parent
        cache_file = current_dir / "pi_fm_rds_path"
        
        if cache_file.exists():
            try:
                cached_path = cache_file.read_text().strip()
                if self._is_valid_executable(cached_path):
                    return cached_path
                else:
                    cache_file.unlink()
            except Exception as e:
                Log.warning(f"Error reading cache file: {e}")
                cache_file.unlink(missing_ok=True)
        
        search_paths = ["/opt", "/usr/local/bin", "/usr/bin", "/bin", "/home"]
        
        for search_path in search_paths:
            if not Path(search_path).exists():
                continue
                
            try:
                for root, dirs, files in os.walk(search_path):
                    if "pi_fm_rds" in files:
                        executable_path = Path(root) / "pi_fm_rds"
                        if self._is_valid_executable(str(executable_path)):
                            cache_file.write_text(str(executable_path))
                            return str(executable_path)
            except (PermissionError, OSError):
                continue
        
        print("Could not automatically find `pi_fm_rds`. Please enter the full path manually.")
        user_path = input("Enter the path to `pi_fm_rds`: ").strip()
        
        if self._is_valid_executable(user_path):
            cache_file.write_text(user_path)
            return user_path
        
        raise PiWaveError("Invalid pi_fm_rds path provided")

    def _is_valid_executable(self, path: str) -> bool:
        try:
            result = subprocess.run(
                [path, "--help"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _is_url(self, path: str) -> bool:
        parsed = urlparse(path)
        return parsed.scheme in ('http', 'https', 'ftp')

    def _is_wav_file(self, filepath: str) -> bool:
        return filepath.lower().endswith('.wav')

    async def _download_stream_chunk(self, url: str, output_file: str, duration: int = 30) -> bool:
        #Download a chunk of stream for specified duration
        try:
            cmd = [
                'ffmpeg', '-i', url, '-t', str(duration), 
                '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
                '-y', output_file
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=duration + 10)
            return process.returncode == 0
            
        except asyncio.TimeoutError:
            Log.error(f"Timeout downloading stream chunk from {url}")
            return False
        except Exception as e:
            Log.error(f"Error downloading stream: {e}")
            return False

    def _convert_to_wav(self, filepath: str) -> Optional[str]:
        if filepath in self.converted_files:
            return self.converted_files[filepath]
        
        if self._is_wav_file(filepath) and not self._is_url(filepath):
            self.converted_files[filepath] = filepath
            return filepath
        
        Log.file_message(f"Converting {filepath} to WAV")
        
        if self._is_url(filepath):
            output_file = os.path.join(self.temp_dir, f"stream_{int(time.time())}.wav")
        else:
            output_file = f"{os.path.splitext(filepath)[0]}_converted.wav"
        
        cmd = [
            'ffmpeg', '-i', filepath, '-acodec', 'pcm_s16le', 
            '-ar', '44100', '-ac', '2', '-y', output_file
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,  # 60 seconds timeout
                check=True
            )
            
            self._log_debug(f"FFmpeg conversion successful for {filepath}")
            
            self.converted_files[filepath] = output_file
            return output_file
            
        except subprocess.TimeoutExpired:
            Log.error(f"Conversion timeout for {filepath}")
            return None
        except subprocess.CalledProcessError as e:
            Log.error(f"Conversion failed for {filepath}: {e.stderr.decode()}")
            return None
        except Exception as e:
            Log.error(f"Unexpected error converting {filepath}: {e}")
            return None

    def _get_file_duration(self, wav_file: str) -> float:
        cmd = [
            'ffprobe', '-i', wav_file, '-show_entries', 'format=duration',
            '-v', 'quiet', '-of', 'csv=p=0'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=True
            )
            return float(result.stdout.decode().strip())
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            return 0.0

    def _play_wav(self, wav_file: str) -> bool:
        if self.stop_event.is_set():
            return False
        
        cmd = [
            'sudo', self.pi_fm_rds_path, 
            '-freq', str(self.frequency),
            '-ps', self.ps,
            '-rt', self.rt,
            '-pi', self.pi,
            '-audio', wav_file
        ]
        
        try:
            Log.broadcast_message(f"Playing {wav_file} at {self.frequency}MHz")
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            if self.on_track_change:
                self.on_track_change(wav_file, self.current_index)
            
            duration = self._get_file_duration(wav_file)
            if duration > 0:
                self.stop_event.wait(duration)
            
            return True
            
        except Exception as e:
            Log.error(f"Error playing {wav_file}: {e}")
            if self.on_error:
                self.on_error(e)
            return False

    def _stop_current_process(self):
        if self.current_process:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                self.current_process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(self.current_process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            finally:
                self.current_process = None

    def _playback_worker(self):
        self._log_debug("Playback worker started")
        
        while not self.stop_event.is_set() and not self.is_stopped:
            if self.current_index >= len(self.playlist):
                if self.loop:
                    self.current_index = 0
                else:
                    break
            
            if self.current_index < len(self.playlist):
                wav_file = self.playlist[self.current_index]
                success = self._play_wav(wav_file)
                
                if not success and not self.stop_event.is_set():
                    Log.error(f"Failed to play {wav_file}")
                
                self._stop_current_process()
                self.current_index += 1
        
        self.is_playing = False
        self._log_debug("Playback worker finished")

    def _handle_interrupt(self, signum, frame):
        Log.warning("Interrupt received, stopping playback...")
        self.stop()
        os._exit(0)

    def add_files(self, files: List[str]) -> bool:
        converted_files = []
        
        for file_path in files:
            if self._is_url(file_path):
                converted_files.append(file_path)
            else:
                wav_file = self._convert_to_wav(file_path)
                if wav_file:
                    converted_files.append(wav_file)
                else:
                    Log.warning(f"Failed to convert {file_path}")
        
        if converted_files:
            self.playlist.extend(converted_files)
            Log.success(f"Added {len(converted_files)} files to playlist")
            return True
        
        return False

    def play(self, files: Optional[List[str]] = None) -> bool:
        if files:
            self.playlist.clear()
            self.current_index = 0
            if not self.add_files(files):
                return False
        
        if not self.playlist:
            Log.warning("No files in playlist")
            return False
        
        if self.is_playing:
            self.stop()
        
        self.stop_event.clear()
        self.is_stopped = False
        self.is_playing = True
        
        self.playback_thread = threading.Thread(target=self._playback_worker)
        self.playback_thread.daemon = True
        self.playback_thread.start()
        
        Log.success("Playback started")
        return True

    def stop(self):
        if not self.is_playing:
            return
        
        Log.warning("Stopping playback")
        self.is_stopped = True
        self.stop_event.set()
        
        self._stop_current_process()
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=5)
        
        self.is_playing = False
        Log.success("Playback stopped")

    def pause(self):
        if self.is_playing:
            self._stop_current_process()
            Log.info("Playback paused")

    def resume(self):
        if not self.is_playing and self.playlist:
            self.play()

    def next_track(self):
        if self.is_playing:
            self._stop_current_process()
            self.current_index += 1

    def previous_track(self):
        if self.is_playing:
            self._stop_current_process()
            self.current_index = max(0, self.current_index - 1)

    def set_frequency(self, frequency: float):
        self.frequency = frequency
        Log.broadcast_message(f"Frequency changed to {frequency}MHz. Will update on next file's broadcast.")

    def get_status(self) -> dict:
        return {
            'is_playing': self.is_playing,
            'current_index': self.current_index,
            'playlist_length': len(self.playlist),
            'frequency': self.frequency,
            'current_file': self.playlist[self.current_index] if self.current_index < len(self.playlist) else None
        }

    def cleanup(self):
        self.stop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        Log.info("Cleanup completed")

    def __del__(self):
        self.cleanup()

    def send(self, files: List[str]):
        return self.play(files)

    def restart(self):
        if self.playlist:
            self.current_index = 0
            self.play()