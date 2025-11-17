# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/piwave.py : main entry

import os
import subprocess
import signal
import threading
import time

import tempfile
import shutil
import queue
from typing import Optional, Callable
from pathlib import Path

from .backends import discover_backends, backends, get_best_backend
from .logger import Log

class PiWaveError(Exception):
    pass

class PiWave:
    def __init__(self, 
                frequency: float = 90.0, 
                ps: str = "PiWave", 
                rt: str = "PiWave: The best python module for managing your pi radio", 
                pi: str = "FFFF", 
                debug: bool = False,
                silent: bool = False,
                loop: bool = False,
                backend: str = "auto",
                used_for: str = "file_broadcast",
                on_track_change: Optional[Callable] = None,
                on_error: Optional[Callable] = None):
        """Initialize PiWave FM transmitter.

        :param frequency: FM frequency to broadcast on (80.0-108.0 MHz)
        :type frequency: float
        :param ps: Program Service name (max 8 characters)
        :type ps: str
        :param rt: Radio Text message (max 64 characters)
        :type rt: str
        :param pi: Program Identification code (4 hex digits)
        :type pi: str
        :param debug: Enable debug logging
        :type debug: bool
        :param silent: Removes every output log
        :type silent: bool
        :param loop: Loop the current track continuously (default: False)
        :type loop: bool
        :param backend: Chose a specific backend to handle the broadcast (default: auto). Supports `pi_fm_rds`, `fm_transmitter` and `auto`
        :type backend: str
        :param backend: Give the main use for the current instance, will be used if backend: auto (default: file_broadcast). Supports `file_broadcast` and `live_broadcast`
        :type backend: str
        :param on_track_change: Callback function called when track changes
        :type on_track_change: Optional[Callable]
        :param on_error: Callback function called when an error occurs
        :type on_error: Optional[Callable]
        :raises PiWaveError: If not running on Raspberry Pi or without root privileges
        
        .. note::
           This class requires pi_fm_rds or fm_transmitter to be installed and accessible.
           Must be run on a Raspberry Pi with root privileges.
        """
        
        self.debug = debug
        self.frequency = frequency
        self.ps = str(ps)[:8]
        self.rt = str(rt)[:64]
        self.pi = str(pi).upper()[:4]
        self.loop = loop
        self.on_track_change = on_track_change
        self.on_error = on_error
        
        self.current_file: Optional[str] = None
        self.is_playing = False
        self.is_stopped = False
        self.current_process: Optional[subprocess.Popen] = None
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.temp_dir = tempfile.mkdtemp(prefix="piwave_")

        self.is_live_streaming = False
        self.live_thread: Optional[threading.Thread] = None
        self.audio_queue: Optional[queue.Queue] = None
        
        Log.config(silent=silent)

        self._validate_environment()
        
        discover_backends()

        self.backend_use = used_for

        if backend == "auto":
            backend_name = get_best_backend(self.backend_use, self.frequency)
            if not backend_name:
                available = list(backends.keys())
                raise PiWaveError(f"No suitable backend found for {self.frequency}MHz and {self.backend_use} mode. Available backends: {available}")
        else:
            if backend not in backends:
                available = list(backends.keys())
                raise PiWaveError(f"Backend '{backend}' not available. Available: {available}. Use 'python3 -m piwave search' to refresh.")
            
            # Validate that the chosen backend supports the frequency
            backend_instance = backends[backend]()
            min_freq, max_freq = backend_instance.frequency_range
            if not (min_freq <= self.frequency <= max_freq):
                raise PiWaveError(f"Backend '{backend}' doesn't support {self.frequency}MHz (supports {min_freq}-{max_freq}MHz)")
            
            backend_name = backend

        self.backend_name = backend_name
        self.backend = backends[backend_name](
            frequency=self.frequency,
            ps=self.ps,
            rt=self.rt,
            pi=self.pi
        )


        min_freq, max_freq = self.backend.frequency_range
        rds_support = "with RDS" if self.backend.supports_rds else "no RDS"
        Log.info(f"Using {self.backend.name} backend ({min_freq}-{max_freq}MHz, {rds_support})")
        
        Log.info(f"PiWave initialized - Frequency: {frequency}MHz, PS: {ps}, Loop: {loop}")

    def _log_debug(self, message: str):
        if self.debug:
            Log.print(f"[DEBUG] {message}", 'bright_cyan')


    def _validate_environment(self):

        #validate that we're running on a Raspberry Pi as root

        if not self._is_raspberry_pi():
            raise PiWaveError("This program must be run on a Raspberry Pi")
        
        if not self._is_root():
            raise PiWaveError("This program must be run as root")

    def _is_raspberry_pi(self) -> bool:
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            return 'raspberry' in cpuinfo.lower()
        except:
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

    def _is_wav_file(self, filepath: str) -> bool:
        return filepath.lower().endswith('.wav')


    def _convert_to_wav(self, filepath: str) -> Optional[str]:
        if self._is_wav_file(filepath):
            return filepath
        
        Log.file(f"Converting {filepath} to WAV")
        
        output_file = f"{os.path.splitext(filepath)[0]}_converted.wav"
        
        cmd = [
            'ffmpeg', '-i', filepath, '-acodec', 'pcm_s16le', 
            '-ar', '44100', '-ac', '2', '-y', output_file
        ]
        
        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,  # 60 seconds timeout
                check=True
            )
            
            self._log_debug(f"FFmpeg conversion successful for {filepath}")
            
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

    def _play_file(self, wav_file: str) -> bool:
        if self.stop_event.is_set():
            return False
        
        duration = self._get_file_duration(wav_file)

        if duration <= 0:
            Log.error(f"Could not determine duration for {wav_file}")
            return False
        
        try:
            # update settings
            self.backend.frequency = self.frequency
            self.backend.ps = self.ps
            self.backend.rt = self.rt
            self.backend.pi = self.pi

            # validate frequency
            min_freq, max_freq = self.backend.frequency_range
            if not (min_freq <= self.frequency <= max_freq):
                raise PiWaveError(f"Current backend '{self.backend.name}' doesn't support {self.frequency}MHz (supports {min_freq}-{max_freq}MHz). Use update() to change backend or frequency.")

            loop_status = "looping" if self.loop else f"Duration: {duration:.1f}s"
            rds_info = f" (PS: {self.ps})" if self.backend.supports_rds and self.ps else ""
            Log.broadcast(f"Playing {wav_file} ({loop_status}) at {self.frequency}MHz{rds_info}")

            self.current_process = self.backend.play_file(wav_file, self.loop)

            if self.on_track_change:
                self.on_track_change(wav_file)

            if self.loop and not self.backend.supports_loop:

                # Only manually loop if the backend does not support it
                while not self.stop_event.is_set():
                    if self.stop_event.wait(timeout=0.1):
                        self._stop_current_process()
                        return False
                    
                    if self.current_process.poll() is not None:
                        Log.error("Process ended unexpectedly while looping")
                        return False
                    
            else:
                # fi backend supports looping or we are not looping, just wait for the process to finish
                while not self.stop_event.is_set():
                    if self.stop_event.wait(timeout=0.1):
                        self._stop_current_process()
                        return False
                    if not self.loop and self.current_process.poll() is not None:
                        break
            return True
        
        except Exception as e:
            Log.error(f"Error playing {wav_file}: {e}")
            if self.on_error:
                self.on_error(e)
            self._stop_current_process()
            return False

        
    def _playback_worker_wrapper(self):
        # wrapper for non-blocking playback
        try:
            wav_file = self._convert_to_wav(self.current_file)
            if not wav_file:
                Log.error(f"Failed to convert {self.current_file}")
                self.is_playing = False
                return

            if not os.path.exists(wav_file):
                Log.error(f"File not found: {wav_file}")
                self.is_playing = False
                return

            self._play_file(wav_file)
        except Exception as e:
            Log.error(f"Playback error: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            self.is_playing = False
        

    def _play_live(self, audio_source, sample_rate: int, channels: int, chunk_size: int) -> bool:
        if self.is_playing or self.is_live_streaming:
            self.stop()
        
        if not self.backend.supports_live_streaming:
            raise PiWaveError(
                f"Backend '{self.backend_name}' doesn't support live streaming. Try using fm_transmitter instead.")

        
        min_freq, max_freq = self.backend.frequency_range
        if not (min_freq <= self.frequency <= max_freq):
            raise PiWaveError(
                f"Backend '{self.backend_name}' doesn't support {self.frequency}MHz"
            )
        
        self.stop_event.clear()
        self.is_live_streaming = True
        self.audio_queue = queue.Queue(maxsize=20)
        
        try:
            cmd = self.backend.build_live_command()
            if not cmd:
                raise PiWaveError(f"Backend doesn't support live streaming") # since we checked before, we shouldnt get this but meh
            
            self.current_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        except Exception as e:
            Log.error(f"Failed to start live stream: {e}")
            self.is_live_streaming = False
            if self.on_error:
                self.on_error(e)
            return False
        
        self.live_thread = threading.Thread(
            target=self._live_producer_worker,
            args=(audio_source, chunk_size)
        )
        self.live_thread.daemon = True
        self.live_thread.start()
        
        consumer_thread = threading.Thread(target=self._live_consumer_worker)
        consumer_thread.daemon = True
        consumer_thread.start()
        
        Log.broadcast(f"Live streaming at {self.frequency}MHz ({sample_rate}Hz, {channels}ch)")
        return True
    
    def _live_producer_worker(self, audio_source, chunk_size: int):
        # producer: reads from audio source, puts in queue; consumer will play it
        try:
            if hasattr(audio_source, '__iter__') and not isinstance(audio_source, (str, bytes)):
                for chunk in audio_source:
                    if self.stop_event.is_set():
                        break
                    if chunk:
                        self.audio_queue.put(chunk, timeout=1)
            
            elif callable(audio_source):
                while not self.stop_event.is_set():
                    chunk = audio_source()
                    if not chunk:
                        break
                    self.audio_queue.put(chunk, timeout=1)
            
            elif hasattr(audio_source, 'read'):
                while not self.stop_event.is_set():
                    chunk = audio_source.read(chunk_size)
                    if not chunk:
                        break
                    self.audio_queue.put(chunk, timeout=1)
            
        except Exception as e:
            Log.error(f"Producer error: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            self.audio_queue.put(None)

    def _live_consumer_worker(self):
        # consumer reads from queue and puts in process
        try:
            while not self.stop_event.is_set():
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                    if chunk is None:
                        break
                    
                    if self.current_process and self.current_process.stdin:
                        self.current_process.stdin.write(chunk)
                        self.current_process.stdin.flush()
                    
                except queue.Empty:
                    continue
                except BrokenPipeError:
                    Log.error(f"Stream process terminated: make sure that the stream you provided compiles with {self.backend_name} stdin support.")
                    break
                except Exception as e:
                    Log.error(f"Write error: {e}")
                    break
        finally:
            if self.current_process and self.current_process.stdin:
                try:
                    self.current_process.stdin.close()
                except:
                    pass
            self.is_live_streaming = False


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

        if not self.current_file:
            Log.error("No file specified for playback")
            self.is_playing = False
            return

        wav_file = self._convert_to_wav(self.current_file)
        if not wav_file:
            Log.error(f"Failed to convert {self.current_file}")
            self.is_playing = False
            return

        if not os.path.exists(wav_file):
            Log.error(f"File not found: {wav_file}")
            self.is_playing = False
            return

        if not self._play_wav(wav_file):
            if not self.stop_event.is_set():
                Log.error(f"Playback failed for {wav_file}")

        self.is_playing = False
        self._log_debug("Playback worker finished")


    def play(self, source, sample_rate: int = 44100, channels: int = 2, chunk_size: int = 4096, blocking: bool = False):
        """Play audio from file or live source.
        
        :param source: Either a file path (str) or live audio source (generator/callable/file-like)
        :param sample_rate: Sample rate for live audio (ignored for files)
        :param channels: Channels for live audio (ignored for files)
        :param chunk_size: Chunk size for live audio (ignored for files)
        :param blocking: If the playback should be blocking or not (ignored for live, always non-blocking)
        :return: True if playback/streaming started successfully
        :rtype: bool
        
        Example:
            >>> pw.play('song.mp3')  # File playback
            >>> pw.play(mic_generator())  # Live streaming
        """

        # autodetect if source is live or file
        if isinstance(source, str):
            # file (string)
            if blocking:
                return self._play_file(source)
            else:
                if self.is_playing:
                    self.stop()
                
                self.current_file = source
                self.is_playing = True
                self.stop_event.clear()
                
                self.playback_thread = threading.Thread(
                    target=self._playback_worker_wrapper,
                    daemon=True
                )
                self.playback_thread.start()
                return True
        
        else:
            # live
            return self._play_live(source, sample_rate, channels, chunk_size)

    def stop(self):
        """Stop all playback and streaming.

        Stops the current playback, kills all related processes, and resets the player state.
        This method is safe to call multiple times.
        
        Example:
            >>> pw.stop()
        """
        
        if not self.is_playing and not self.is_live_streaming and not self.current_process:
            return
        
        Log.warning("Stopping...")
        
        self.is_stopped = True
        self.stop_event.set()
        
        if self.audio_queue:
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
        
        if self.current_process:
            try:
                os.killpg(os.getpgid(self.current_process.pid), signal.SIGTERM)
                self.current_process.wait(timeout=5)
            except Exception:
                pass
            finally:
                self.current_process = None
        
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=5)
        if self.live_thread and self.live_thread.is_alive():
            self.live_thread.join(timeout=3)
        
        self.is_playing = False
        self.is_live_streaming = False
        Log.success("Stopped")

    def pause(self):
        """Pause the current playback.

        Stops the current track but maintains the file reference.
        Use :meth:`resume` to continue playback.
        
        Example:
            >>> pw.pause()
        """
        if self.is_playing:
            self._stop_current_process()
            Log.info("Playback paused")

    def resume(self):
        """Resume playback from the current file.

        Continues playback of the current file.
        
        Example:
            >>> pw.resume()
        """
        if not self.is_playing and self.current_file:
            self.play(self.current_file)

    def update(self, 
                frequency: Optional[float] = None,
                ps: Optional[str] = None,
                rt: Optional[str] = None,
                pi: Optional[str] = None,
                debug: Optional[bool] = None,
                silent: Optional[bool] = None,
                loop: Optional[bool] = None,
                backend: Optional[str] = None,
                used_for: Optional[str] = None,
                on_track_change: Optional[Callable] = None,
                on_error: Optional[Callable] = None):
        """Update PiWave settings.

        :param frequency: FM frequency to broadcast on (80.0-108.0 MHz)
        :type frequency: Optional[float]
        :param ps: Program Service name (max 8 characters)
        :type ps: Optional[str]
        :param rt: Radio Text message (max 64 characters)
        :type rt: Optional[str]
        :param pi: Program Identification code (4 hex digits)
        :type pi: Optional[str]
        :param debug: Enable debug logging
        :type debug: Optional[bool]
        :param silent: Remove every output log
        :type silent: Optional[bool]
        :param loop: Loop the current track continuously
        :type loop: Optional[bool]
        :param backend: Backend used to broadcast
        :type backend: Optional[str]
        :param backend: Give the main use for the current instance, will be used if backend: auto. Supports `file_broadcast` and `live_broadcast`
        :type backend: Optional[str]
        :param on_track_change: Callback function called when track changes
        :type on_track_change: Optional[Callable]
        :param on_error: Callback function called when an error occurs
        :type on_error: Optional[Callable]
        
        .. note::
           Only non-None parameters will be updated. Changes take effect immediately, except for broadcast related changes, where you will have to start a new broadcast to apply them.
        
        Example:
            >>> pw.update(frequency=101.5, ps="NewName")
            >>> pw.update(rt="Updated radio text", debug=True, loop=True)
        """
        updated_settings = []

        freq_to_use = frequency if frequency is not None else self.frequency

        if used_for is not None:
            self.backend_use = used_for

        if backend is not None:
            if backend == "auto":
                backend_name = get_best_backend(self.backend_use, freq_to_use)
                if not backend_name:
                    available = list(backends.keys())
                    raise PiWaveError(f"No suitable backend found for {freq_to_use}MHz. Available: {available}")
            else:
                if backend not in backends:
                    available = list(backends.keys())
                    raise PiWaveError(f"Backend '{backend}' not available. Available: {available}")
                backend_name = backend

            backend_instance = backends[backend_name](
                frequency=freq_to_use,
                ps=ps or self.ps,
                rt=rt or self.rt,
                pi=pi or self.pi
            )

            min_freq, max_freq = backend_instance.frequency_range
            if not (min_freq <= freq_to_use <= max_freq):
                raise PiWaveError(f"Backend '{backend_name}' doesn't support {freq_to_use}MHz (supports {min_freq}-{max_freq}MHz)")

            self.backend_name = backend_name
            self.backend = backend_instance
            updated_settings.append(f"backend: {backend_name}")
        
        if frequency is not None:
            self.frequency = frequency
            updated_settings.append(f"frequency: {frequency}MHz")
        
        if ps is not None:
            self.ps = str(ps)[:8]
            updated_settings.append(f"PS: {self.ps}")
        
        if rt is not None:
            self.rt = str(rt)[:64]
            updated_settings.append(f"RT: {self.rt}")
        
        if pi is not None:
            self.pi = str(pi).upper()[:4]
            updated_settings.append(f"PI: {self.pi}")
        
        if debug is not None:
            self.debug = debug
            updated_settings.append(f"debug: {debug}")
        
        if silent is not None:
            Log.config(silent=silent)
            updated_settings.append(f"silent: {silent}")
        
        if loop is not None:
            self.loop = loop
            updated_settings.append(f"loop: {loop}")
        
        if on_track_change is not None:
            self.on_track_change = on_track_change
            updated_settings.append("on_track_change callback updated")
        
        if on_error is not None:
            self.on_error = on_error
            updated_settings.append("on_error callback updated")
        
        if updated_settings:
            Log.success(f"Updated settings: {', '.join(updated_settings)}")
        else:
            Log.info("No settings updated")

    def set_frequency(self, frequency: float):
        """Change the FM broadcast frequency.

        :param frequency: New frequency in MHz (typically 88.0-108.0)
        :type frequency: float
        
        .. note::
           The frequency change will take effect on the next broadcast.
        
        Example:
            >>> pw.set_frequency(101.5)
        """
        self.frequency = frequency
        Log.broadcast(f"Frequency changed to {frequency}MHz. Will update on next file's broadcast.")

    def set_loop(self, loop: bool):
        """Enable or disable looping for the current track.

        :param loop: True to enable looping, False to disable
        :type loop: bool
        
        .. note::
           The loop setting will take effect on the next broadcast.
        
        Example:
            >>> pw.set_loop(True)   # Enable looping
            >>> pw.set_loop(False)  # Disable looping
        """
        self.loop = loop
        loop_status = "enabled" if loop else "disabled"
        Log.broadcast(f"Looping {loop_status}. Will update on next file's broadcast.")

    def get_status(self) -> dict:
        """Get current status information.

        :return: Dictionary containing current player status
        :rtype: dict
        
        The returned dictionary contains:
        
        - **is_playing** (bool): Whether playback is active
        - **is_live_streaming** (bool): Whether live playback is active
        - **frequency** (float): Current broadcast frequency
        - **current_file** (str|None): Path of currently playing file
        - **current_backend** (str): Currently used backend
        - **backend_frequency_range** (str): Frequency range supported by the backend
        - **backend_supports_rds** (bool): Backend support of Radio Data System
        - **avalible_backends** (list): List of avalible backends
        - **ps** (str): Program Service name
        - **rt** (str): Radio Text message
        - **pi** (str): Program Identification code
        - **loop** (bool): Whether looping is enabled
        
        Example:
            >>> status = pw.get_status()
            >>> print(f"Playing: {status['is_playing']}")
            >>> print(f"Current file: {status['current_file']}")
            >>> print(f"Looping: {status['loop']}")
        """
        return {
            'is_playing': self.is_playing,
            'is_live_streaming': self.is_live_streaming,
            'frequency': self.frequency,
            'current_file': self.current_file,
            'current_backend': self.backend_name,
            'backend_frequency_range': f"{self.backend.frequency_range[0]}-{self.backend.frequency_range[1]}MHz",
            'backend_supports_rds': self.backend.supports_rds,
            'available_backends': list(backends.keys()),
            'ps': self.ps,
            'rt': self.rt,
            'pi': self.pi,
            'loop': self.loop
        }

    def cleanup(self):
        """Clean up resources and temporary files.

        Stops all playback, removes temporary files, and cleans up system resources.
        This method is automatically called when the object is destroyed.
        
        Example:
            >>> pw.cleanup()
        """
        self.stop()
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        Log.info("Cleanup completed")


    def send(self, file_path: str):
        """Alias for the play method.

        :param file_path: Path to local audio file
        :type file_path: str
        :return: True if playback started successfully, False otherwise
        :rtype: bool
        
        .. note::
           This is an alias for :meth:`play` for backward compatibility.
        
        Example:
            >>> pw.send('song.mp3')
        """
        return self.play(file_path)

if __name__ == "__main__":
    Log.header("PiWave Radio Module")
    Log.info("This module is designed to run on a Raspberry Pi with root privileges.")
    Log.info("Please import this module in your main application to use its features.")
    Log.info("Exiting PiWave module")

__all__ = ["PiWave"]