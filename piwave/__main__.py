# PiWave is available at https://piwave.xyz
# Licensed under GPLv3.0, main GitHub repository at https://github.com/douxxtech/piwave/
# piwave/__main__.py : handles cli inputs

import sys
import argparse
from .backends import search_backends, list_backends, backends, discover_backends
from .logger import Log
from .piwave import PiWave, PiWaveError

def main():
    if len(sys.argv) < 2:
        Log.header("PiWave CLI")
        Log.info("Usage: python3 -m piwave <command> [args]\n")
        Log.info("Available commands:")
        Log.info("  search       - Search for available backends")
        Log.info("  list         - List cached backends")
        Log.info("  add <name> <path> - Manually add backend executable path")
        Log.info("  info         - Show package info")
        Log.info("  broadcast <file>  - Broadcast a file over FM")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "search":
        search_backends()

    elif cmd == "list":
        discover_backends()
        list_backends()

    elif cmd == "add":
        if len(sys.argv) < 4:
            Log.error("Usage: python3 -m piwave add <backend_name> <path>")
            sys.exit(1)

        backend_name = sys.argv[2]
        backend_path = sys.argv[3]

        discover_backends()
        if backend_name not in backends:
            Log.error(f"Unknown backend '{backend_name}'. Run `python3 -m piwave search` first.")
            sys.exit(1)

        backend_class = backends[backend_name]
        try:
            backend = backend_class()
            backend.cache_file.write_text(backend_path)
            Log.success(f"Backend '{backend_name}' path set to {backend_path}")
        except Exception as e:
            Log.error(f"Failed to add backend '{backend_name}': {e}")

    elif cmd == "info":
        Log.header("PiWave Module Info")
        Log.info("Python-based FM transmitter manager for Raspberry Pi")
        Log.info("Commands: search, list, add, info, broadcast")

    elif cmd == "broadcast":
        parser = argparse.ArgumentParser(
            prog="python3 -m piwave broadcast",
            description="Broadcast a file using PiWave"
        )
        parser.add_argument("file", help="Path to the audio file to broadcast")
        parser.add_argument("--frequency", type=float, default=90.0, help="FM frequency (MHz)")
        parser.add_argument("--ps", type=str, default="PiWave", help="Program Service name (max 8 chars)")
        parser.add_argument("--rt", type=str, default="PiWave: The best python module for managing your pi radio", help="Radio Text (max 64 chars)")
        parser.add_argument("--pi", type=str, default="FFFF", help="Program Identification code (4 hex digits)")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        parser.add_argument("--silent", action="store_true", help="Suppress logs")
        parser.add_argument("--loop", action="store_true", help="Loop playback")
        parser.add_argument("--backend", type=str, default="auto", help="Choose a specific backend")

        args = parser.parse_args(sys.argv[2:])

        pw = None
        try:
            pw = PiWave(
                frequency=args.frequency,
                ps=args.ps,
                rt=args.rt,
                pi=args.pi,
                debug=args.debug,
                silent=args.silent,
                loop=args.loop,
                backend=args.backend
            )
            pw.play(args.file)

            Log.info("Press Ctrl+C to stop broadcasting...")
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                pw.stop()
                Log.info("Broadcast stopped")
                raise

        except PiWaveError as e:
            Log.error(f"PiWaveError: {e}")
            sys.exit(1)
        except Exception:
            pass
        finally:
            if pw is not None:
                pw.cleanup()


    else:
        Log.error(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
