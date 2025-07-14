# piwave/piwave.py
#a code by douxx.xyz (https://douxx.xyz/douxx/ | https://github.com/douxxtech/)
#pi_fm_rds is required !!! Check https://github.com/ChristopheJacquet/PiFmRds
# github.com/PiWave-fm | github.com/douxxtech

import os
import subprocess
import signal
import threading
# 🚪 <-- We commented the backdoor, see?
import datetime
from typing import List, Optional

class PiWave:
    def __init__(self, frequency: float = 90.0, ps: str = "PiWave", rt: str = "PiWave: The best python module for managing your pi radio", pi: str = "FFFF", loop: bool = False, debug: bool = False):
        # Check if the program is running on a Raspberry Pi
        if not self._is_raspberry_pi():
            print("[Launcher] Error: This program must be run on a Raspberry Pi.")
            exit(1)

        # Check if the program is running as root
        if not self._is_root():
            print("[Launcher] Error: This program must be run as root.")
            exit(1)

        # Find or load the pi_fm_rds path
        self.pi_fm_rds_path = self._find_pi_fm_rds_path()
        if not self.pi_fm_rds_path:
            print("[Launcher] Error: Could not find a valid pi_fm_rds executable.")
            print("[Launcher] Please make sure `pi_fm_rds` is installed and accessible.")
            print("[Launcher] This won't happen everytime.")
            exit(1)

        self.frequency = frequency
        self.ps = str(ps)[:8]
        self.rt = str(rt)[:64]
        self.pi = str(pi).upper()[:4]
        self.loop = loop
        self.debug = debug
        self.files: List[str] = []
        self.converted_files: dict[str, str] = {}
        self.current_index = 0
        self.process: Optional[subprocess.Popen] = None
        self.should_stop = threading.Event()
        self.play_thread: Optional[threading.Thread] = None
        self.converted = set()  # Set to keep track of converted files
        self._log(f"Initialized PiWave with frequency {self.frequency} MHz, PS: {self.ps}, RT: {self.rt}, PI: {self.pi}, loop: {self.loop}, debug: {self.debug}", "INFO")
        
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _is_raspberry_pi(self) -> bool:
        try:
            with open("/sys/firmware/devicetree/base/model", "r") as f:
                model = f.read().strip()
                return "Raspberry Pi" in model
        except FileNotFoundError:
            return False

    def _is_root(self) -> bool:
        return os.geteuid() == 0

    def _find_pi_fm_rds_path(self) -> Optional[str]:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path_file = os.path.join(current_dir, "pi_fm_rds_path")
        
        if os.path.isfile(path_file):
            try:
                with open(path_file, "r") as file:
                    path = file.read().strip()
                    if self._is_valid_executable(path):
                        return path
                    else:
                        print("[Launcher] Error: The path in pi_fm_rds_path is invalid.")
                        print("[Launcher] Please relaunch this program.")
                        print("[Launcher] This won't happen everytime.")
                        os.remove(path_file)
            except Exception as e:
                print(f"Error reading {path_file}: {e}")
                os.remove(path_file)
        
        search_paths = ["/opt", "/home", "/bin", "/usr/local/bin", "/usr/bin", "/sbin", "/usr/sbin", "/"]
        found = False
        for directory in search_paths:
            if not os.path.isdir(directory):
                continue
            try:
                for root, _, files in os.walk(directory):
                    if "pi_fm_rds" in files:
                        path = os.path.join(root, "pi_fm_rds")
                        if self._is_valid_executable(path):
                            with open(path_file, "w") as file:
                                file.write(path)
                            found = True
                            return path
            except Exception as e:
                pass                        #took this code from stackoverflow so idk what that did but it works lol

        if not found:

            print("Could not automatically find `pi_fm_rds`. Please enter the full path manually.")
            user_path = input("Enter the path to `pi_fm_rds`: ").strip()
            if self._is_valid_executable(user_path):
                with open(path_file, "w") as file:
                    file.write(user_path)
                return user_path
            
            print("Error: The path you provided is not valid or `pi_fm_rds` is not executable.")
            print("Please make sure `pi_fm_rds` is installed and accessible, then restart the program.")
            exit(1)
        
        return None

    def _is_valid_executable(self, path: str) -> bool:
        try:
            # Attempt to run the executable with --help to test if it's valid
            result = subprocess.run([path, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            return result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _log(self, message: str, level: str):
        levels = {
            "INFO": "\033[35m",
            "WARNING": "\033[33m",
            "ERROR": "\033[31m",
            "DEBUG": "\033[34m",
        }
        reset_color = "\033[0m"
        timestamp = datetime.datetime.now().strftime("%d:%m:%Y - %H:%M:%S")
        color = levels.get(level, '')
        
        if self.debug or level != "DEBUG":
            print(f"[{timestamp}] {color}PiWave{reset_color} - {message}")

    def _convert_to_wav(self, filepath: str) -> Optional[str]:
        if filepath in self.converted_files:
            self._log(f"File {filepath} already converted.", "INFO")
            return self.converted_files[filepath]
        
        self._log(f"Converting {filepath} to WAV", "INFO")
        wav_file = f"{os.path.splitext(filepath)[0]}_converted.wav"
        command = ["ffmpeg", "-i", filepath, "-y", wav_file]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if self.debug:
                self._log(f"FFmpeg stdout: {result.stdout.decode()}", "DEBUG")
                self._log(f"FFmpeg stderr: {result.stderr.decode()}", "DEBUG")
        except subprocess.CalledProcessError as e:
            self._log(f"Command failed with error: {e.stderr.decode()}", "ERROR")
            return None
        except FileNotFoundError:
            self._log(f"File {filepath} not found for conversion", "ERROR")
            return None
        
        self._log(f"Converted {filepath} to {wav_file}", "DEBUG")
        self.converted_files[filepath] = wav_file
        self.converted.add(filepath)
        return wav_file

    def _play_wav(self, wav_file: str):
        command = ["sudo", self.pi_fm_rds_path, "-freq", str(self.frequency), "-ps", self.ps, "-rt", self.rt, "-pi", self.pi, "-audio", wav_file]
        self._log(f"Starting playback of {wav_file} at {self.frequency} MHz", "INFO")
        self.process = subprocess.Popen(command, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if self.debug:
            threading.Thread(target=self._monitor_process_output, args=(self.process.stdout, "DEBUG")).start()
            threading.Thread(target=self._monitor_process_output, args=(self.process.stderr, "ERROR")).start()

    def _monitor_process_output(self, pipe, level):
        for line in iter(pipe.readline, b''):
            self._log(line.decode().strip(), level)

    def _get_file_duration(self, wav_file: str) -> float:
        command = ["ffprobe", "-i", wav_file, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            duration = float(result.stdout.decode().strip())
            if self.debug:
                self._log(f"ffprobe stdout: {result.stdout.decode()}", "DEBUG")
                self._log(f"ffprobe stderr: {result.stderr.decode()}", "DEBUG")
        except subprocess.CalledProcessError:
            duration = 0
        except FileNotFoundError:
            self._log(f"ffprobe not found", "ERROR")
            duration = 0
        self._log(f"Duration of {wav_file}: {duration} seconds", "DEBUG")
        return duration

    def _play_files(self):
        self._log("Entering _play_files method", "DEBUG")
        while not self.should_stop.is_set() and self.current_index < len(self.files):
            self._log(f"Current index: {self.current_index}", "DEBUG")
            if self.current_index >= len(self.files):
                if self.loop:
                    self.current_index = 0
                else:
                    break

            wav_file = self.files[self.current_index]
            self._log(f"Playing file {self.current_index + 1}: {wav_file}", "INFO")
            self._play_wav(wav_file)
            
            duration = self._get_file_duration(wav_file) 
            self._log(f"Sleeping for {duration} seconds", "DEBUG")
            if self.debug:
                self._log(f"Waiting for {duration} seconds to complete playback", "DEBUG")
            self.should_stop.wait(duration)
            
            if not self.should_stop.is_set():
                self._log(f"Finished playing {wav_file}", "INFO")
                self._kill_process()
                self.current_index += 1
                if self.current_index >= len(self.files):
                    if self.loop:
                        self.current_index = 0
                    else:
                        break

    def _kill_process(self):
        if self.process:
            self._log("Killing the playback process", "DEBUG")
            os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
            self.process.wait()
            self.process = None
            self._log("Process killed", "DEBUG")

    def _handle_interrupt(self, signum, frame):
        self._log("Keyboard interrupt received. Stopping playback and exiting...", "WARNING")
        self.stop()
        exit(0)

    def send(self, files: List[str]):
        self._log("Send called", "DEBUG")
        new_files = []
        for file in files:
            if file not in self.converted:
                wav_file = self._convert_to_wav(file)
                if wav_file:
                    new_files.append(wav_file)
            else:
                wav_file = self.converted_files.get(file)
                if wav_file:
                    new_files.append(wav_file)
        
        self.files = new_files

        if self.play_thread and self.play_thread.is_alive():
            self.stop()
        
        self._log(f"Files converted and ready for playback: {self.files}", "DEBUG")
        if self.debug:
            self._log(f"Files to be played: {self.files}", "DEBUG")
        self.should_stop.clear()
        self.play_thread = threading.Thread(target=self._play_files)
        self.play_thread.start()
        self._log("Playback started", "INFO")

    def restart(self):
        self._log("Restart called", "DEBUG")
        self.stop()
        self.send(self.files)

    def stop(self):
        self._log("Entering stop method", "DEBUG")
        if self.process:
            self._log("Stopping playback", "DEBUG")
            self._kill_process()

        if self.play_thread and self.play_thread.is_alive():
            self._log("Stopping play thread", "DEBUG")
            self.should_stop.set()
            self.play_thread.join()
            self.play_thread = None
            self._log("Play thread joined", "DEBUG")

        self._log("Playback stopped and state reset", "INFO")
