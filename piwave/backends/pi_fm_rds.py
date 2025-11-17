# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/backends/pi_fm_rds.py : PiFmRds backend, supports RDS on freqs 80 to 108
# needs https://github.com/ChristopheJacquet/PiFmRds installed on the system to work !

from .base import Backend, BackendError

class PiFmRdsBackend(Backend):
    
    @property
    def name(self):
        return "pi_fm_rds"
    
    @property
    def frequency_range(self):
        return (76.0, 108.0)  # taken from pi_fm_rds.c
    
    @property
    def supports_rds(self):
        return True
    
    @property
    def supports_live_streaming(self):
        return False
    
    @property
    def supports_loop(self):
        return False
    
    def _get_executable_name(self):
        return "pi_fm_rds"
    
    def _get_search_paths(self):
        return ["/opt/PiWave/PiFmRds", "/opt", "/usr/local/bin", "/usr/bin", "/bin", "/home"]
    
    def build_command(self, wav_file: str, loop: bool) -> list:
        cmd = [
            'sudo', self.required_executable,
            '-freq', str(self.frequency),
            '-audio', wav_file
        ]
        
        if self.ps:
            cmd.extend(['-ps', self.ps])
        if self.rt:
            cmd.extend(['-rt', self.rt])
        if self.pi:
            cmd.extend(['-pi', self.pi])
            
        return cmd

    def build_live_command(self):
        return None # not supported sadly