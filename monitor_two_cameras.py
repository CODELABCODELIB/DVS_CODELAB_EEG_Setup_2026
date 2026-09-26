#!/usr/bin/env python3
"""Open the two low-rate recording monitor windows."""

import subprocess
import sys
import time
from pathlib import Path


PORTS = {"DXAS0102": 56102, "DXAS0050": 56050}


def main() -> None:
    viewer = Path(__file__).with_name("monitor_viewer.py")
    processes = [
        subprocess.Popen([sys.executable, str(viewer), serial, "--port", str(port)])
        for serial, port in PORTS.items()
    ]
    try:
        while all(process.poll() is None for process in processes):
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait()


if __name__ == "__main__":
    main()
