# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/backends/__init__.py : some utility funcs for backends

from .pi_fm_rds import PiFmRdsBackend
from .fm_transmitter import FmTransmitterBackend
from ..logger import Log

# auto discover backends
backends = {}
backend_classes = {
    "pi_fm_rds": PiFmRdsBackend,
    "fm_transmitter": FmTransmitterBackend
}


def get_best_backend(mode: str, frequency: float):
    if mode == "file_broadcast":
        if 88.0 <= frequency <= 108.0:
            if "pi_fm_rds" in backends:
                return "pi_fm_rds"
            elif "fm_transmitter" in backends:
                return "fm_transmitter"
        else:
            if "fm_transmitter" in backends:
                return "fm_transmitter"
            elif "pi_fm_rds" in backends:
                return "pi_fm_rds"
    
    elif mode == "live_broadcast":
        if "fm_transmitter" in backends:
            backend = backends["fm_transmitter"]()
            min_freq, max_freq = backend.frequency_range
            if min_freq <= frequency <= max_freq:
                return "fm_transmitter"
        
        return None
    
    return None

def discover_backends():
    """
    Populate `backends` dictionary with available backends.
    Reads cache files first, probes hardware only if no cache exists.
    Stores executable path in cache if available, "None" otherwise.
    """
    backends.clear()

    for name, backend_class in backend_classes.items():
        backend = backend_class()

        if backend.cache_file.exists():
            content = backend.cache_file.read_text().strip()
            if content == "None":
                available = False
            else:
                available = True
                backend._executable_path = content
        else:
            try:
                available = backend.is_available()
            except Exception:
                available = False

            if available:
                backend.cache_file.write_text(backend.required_executable)
            else:
                backend.cache_file.write_text("None")

        if available:
            backends[name] = backend_class

    return backends


def search_backends():
    """
    Probe all backends directly, ignoring any cache.
    Updates the cache files with the actual availability.
    Overwrites existing cache files.
    """
    backends.clear()

    for name, backend_class in backend_classes.items():
        backend = backend_class()

        try:
            available = backend.is_available()
        except Exception:
            available = False

        if available:
            backend.cache_file.write_text(backend.required_executable)
            backends[name] = backend_class
        else:
            backend.cache_file.write_text("None")

    if backends:
        Log.success(f"Found backends: {', '.join(backends.keys())}")
    else:
        Log.warning("No backends found. Please install pi_fm_rds or fm_transmitter")



def list_backends():
    """List every cached backend avalible
    
    .. note::
        You can also use the 'python3 -m piwave list' command.
    """
    if not backends:
        Log.warning("No backends available")
        return {}
    
    backend_info = {}
    for name, backend_class in backends.items():
        backend = backend_class()
        min_freq, max_freq = backend.frequency_range
        rds = "Yes" if backend.supports_rds else "No"
        backend_info[name] = {
            'frequency_range': f"{min_freq}-{max_freq}MHz",
            'rds_support': rds
        }
        Log.info(f"{name}: {min_freq}-{max_freq}MHz, RDS: {rds}")
    
    return backend_info
