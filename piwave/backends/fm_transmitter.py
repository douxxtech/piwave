# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/backends/fm_transmitter.py : fm_transmitter backend, doesn't supports RDS, can broadcast on freqs 1 to 250
# needs https://github.com/markondej/fm_transmitter installed on the system to work !

from .base import Backend

class FmTransmitterBackend(Backend):
    
    @property
    def name(self):
        return "fm_transmitter"
    
    @property
    def frequency_range(self):
        return (1.0, 250.0)  # fm transmitter supports a pretty good range, tho be aware of performance issues
    
    @property
    def supports_rds(self):
        return False
    
    @property
    def supports_live_streaming(self):
        return True
    
    @property
    def supports_loop(self):
        return False
    
    def _get_executable_name(self):
        return "fm_transmitter"
    
    def _get_search_paths(self):
        return ["/opt/PiWave/fm_transmitter", "/opt", "/usr/local/bin", "/usr/bin", "/bin", "/home"]
    
    def build_command(self, wav_file: str, loop: bool):
        return [
            'sudo', self.required_executable,
            '-f', str(self.frequency),
            wav_file
        ]
    
    def build_live_command(self):
        return [
            'sudo', self.required_executable,
            '-f', str(self.frequency),
            '-'
        ]