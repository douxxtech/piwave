# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/Logger.py : Main logging manage

from dlogger import DLogger

class Logger(DLogger):
    
    ICONS = {
        'success': 'OK',
        'error': 'ERR',
        'warning': 'WARN',
        'info': 'INFO',
        'file': 'FILE',
        'broadcast': 'BCAST'
    }
    
    STYLES = {
        'success': 'bright_green',
        'error': 'bright_red',
        'warning': 'bright_yellow',
        'info': 'bright_cyan',
        'file': 'yellow',
        'broadcast': 'bright_magenta'
    }
    
    SILENT = False
    
    def __init__(self):
        # Initialize with prebuilt icons & styles and silent support.
        
        super().__init__(
            icons=self.ICONS,
            styles=self.STYLES
        )
    
    @classmethod
    def config(self, silent: bool = False):
        self.SILENT = silent
    
    def print(self, message: str, style: str = '', icon: str = '', end: str = '\n'):
        if self.SILENT:
            return
        super().print(message, style, icon, end)

Log = Logger()