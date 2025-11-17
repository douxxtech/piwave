# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/backend/base.py : backends backbone

from abc import ABC, abstractmethod
from typing import Optional
import subprocess
import os
import signal
import shutil
from pathlib import Path

class BackendError(Exception):
    pass

class Backend(ABC):    
    def __init__(self, frequency: float = 90.0, ps: str = "PiWave", 
                 rt: str = "", pi: str = "FFFF"):
        self.frequency = frequency
        self.ps = ps[:8]  # Max 8 chars
        self.rt = rt[:64]  # Max 64 chars
        self.pi = pi[:4]   # Max 4 chars
        self.current_process: Optional[subprocess.Popen] = None
        self.is_available_cached: Optional[bool] = None
        self._executable_path: Optional[str] = None
    
    @property
    @abstractmethod
    def name(self):
        pass
    
    @property
    @abstractmethod
    def frequency_range(self):
        pass
    
    @property
    @abstractmethod  
    def supports_rds(self):
        pass

    @property
    @abstractmethod
    def supports_live_streaming(self):
        pass

    @property
    @abstractmethod
    def supports_loop(self):
        pass
    
    @property 
    def cache_file(self):
        return Path(__file__).parent.parent / f"{self.name}_path"
    
    @property
    def required_executable(self):
        if self._executable_path:
            return self._executable_path
            
        self._executable_path = self._find_executable()
        return self._executable_path
    
    def _find_executable(self) -> str:
        # Check cache first
        if self.cache_file.exists():
            try:
                cached_path = self.cache_file.read_text().strip()
                if self._is_valid_executable(cached_path):
                    return cached_path
                else:
                    self.cache_file.unlink()
            except Exception:
                self.cache_file.unlink(missing_ok=True)
        
        # Only then search for it
        found_path = self._search_executable()
        if found_path:
            try:
                self.cache_file.write_text(found_path)
            except Exception:
                pass
            return found_path
        
        raise BackendError(f"Could not find path for {self.name}. Please manually add one with python3 -m piwave add {self.name} <path>")
    
    @abstractmethod
    def _get_executable_name(self):
        pass
    
    @abstractmethod  
    def _get_search_paths(self):
        pass
    
    def _search_executable(self):
        executable_name = self._get_executable_name()
        
        # Try at first system $PATH
        system_path = shutil.which(executable_name)
        if system_path and self._is_valid_executable(system_path):
            return system_path
        
        # Then for the dirs
        search_paths = self._get_search_paths()
        
        for search_path in search_paths:
            if not Path(search_path).exists():
                continue
                
            try:
                for root, dirs, files in os.walk(search_path):
                    if executable_name in files:
                        executable_path = Path(root) / executable_name
                        if self._is_valid_executable(str(executable_path)):
                            return str(executable_path)
            except (PermissionError, OSError):
                continue
        
        return None
    
    # valid executable part start

    def _is_valid_executable(self, path: str) -> bool:
        
        path_obj = Path(path)
        if not (path_obj.exists() and path_obj.is_file() and os.access(path, os.X_OK)):
            return False
        
        # test any approach, if only one is valid, its ok
        validation_methods = [
            self._ve_try_help_flag,
            self._ve_try_version_flag,
            self._ve_try_no_args,
            self._ve_try_invalid_flag
        ]
        
        for method in validation_methods:
            try:
                if method(path):
                    return True
            except Exception:
                continue
        
        return False
    
    def _ve_try_help_flag(self, path: str) -> bool:
        try:
            result = subprocess.run(
                [path, "--help"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=3
            )

            return result.returncode in [0, 1, 2]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _ve_try_version_flag(self, path: str) -> bool:
        for flag in ["--version", "-v", "-V"]:
            try:
                result = subprocess.run(
                    [path, flag], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    timeout=3
                )
                if result.returncode in [0, 1]:
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        return False
    
    def _ve_try_no_args(self, path: str) -> bool:
        try:
            result = subprocess.run(
                [path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=1
            )
            return True
        except subprocess.TimeoutExpired:
            return True
        except (FileNotFoundError, PermissionError):
            return False
    
    def _ve_try_invalid_flag(self, path: str) -> bool:
        try:
            result = subprocess.run(
                [path, "--piwave-test-invalid-flag"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=3
            )
            return result.returncode in [1, 2]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
        
    # valid executable part end


    def is_available(self):
        if self.is_available_cached is not None:
            return self.is_available_cached
            
        try:
            self.required_executable
            self.is_available_cached = True
            return True
        except BackendError:
            self.is_available_cached = False
            return False
    
    @abstractmethod
    def build_command(self, wav_file: str, loop: bool):
        pass

    @abstractmethod
    def build_live_command(self):
        pass
    
    def validate_settings(self):
        min_freq, max_freq = self.frequency_range
        return min_freq <= self.frequency <= max_freq
    
    def play_file(self, wav_file: str, loop: bool) -> subprocess.Popen:
        if not self.validate_settings():
            min_freq, max_freq = self.frequency_range
            raise BackendError(f"{self.name} supports {min_freq}-{max_freq}MHz, got {self.frequency}MHz")
            
        cmd = self.build_command(wav_file, loop)
        self.current_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        return self.current_process
    
    def stop(self):
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