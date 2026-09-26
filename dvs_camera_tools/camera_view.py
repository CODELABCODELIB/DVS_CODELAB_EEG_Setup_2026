#!/usr/bin/env python3
"""Focus preview before recording and low-rate monitoring during recording."""

import argparse
import multiprocessing
import signal
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path

import cv2 as cv
import dv_processing as dv


PORTS = {"DXAS0102": 56102, "DXAS0050": 56050}


def publish_focus_events(serial: str, port: int, stop_event) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    camera = dv.io.camera.openSync(serial)
    stream = dv.io.Stream.EventStream(
        0, "events", camera.getCameraName(), camera.getEventResolution()
    )
    server = dv.io.NetworkWriter("127.0.0.1", port, stream)
    print(f"[{serial}] Focus preview ready on local port {port}.", flush=True)
    while camera.isRunning() and not stop_event.is_set():
        events = camera.getNextEventBatch()
        if events is not None and server.getClientCount() > 0:
            server.writeEvents(events)


def run_focus_source() -> int:
    detected = {device.serialNumber for device in dv.io.camera.discover()}
    missing = [serial for serial in PORTS if serial not in detected]
    if missing:
        print("Missing camera(s): " + ", ".join(missing), file=sys.stderr)
        return 1

    context = multiprocessing.get_context("spawn")
    stop_event = context.Event()
    processes = [
        context.Process(target=publish_focus_events, args=(serial, port, stop_event))
        for serial, port in PORTS.items()
    ]
    for process in processes:
        process.start()

    print("Press Ctrl+C to stop both focus preview streams.", flush=True)
    try:
        while all(process.is_alive() for process in processes):
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping focus preview...", flush=True)
    finally:
        stop_event.set()
        for process in processes:
            process.join()

    if any(process.exitcode != 0 for process in processes):
        print("A camera focus preview process failed.", file=sys.stderr)
        return 1
    return 0


def show_one(serial: str, port: int, mode: str) -> None:
    reader = dv.io.NetworkReader("127.0.0.1", port)
    window = f"{serial}: {'focus' if mode == 'focus' else 'recording monitor'}"
    cv.namedWindow(window, cv.WINDOW_NORMAL)

    if mode == "focus":
        visualizer = dv.visualization.EventVisualizer(reader.getEventResolution())
        slicer = dv.EventStreamSlicer()
        slicer.doEveryTimeInterval(
            timedelta(milliseconds=33),
            lambda events: cv.imshow(window, visualizer.generateImage(events)),
        )
        while reader.isRunning():
            events = reader.getNextEventBatch()
            if events is not None:
                slicer.accept(events)
            if cv.waitKey(20) == 27:
                break
    else:
        while reader.isRunning():
            frame = reader.getNextFrame()
            if frame is not None:
                cv.imshow(window, frame.image)
            if cv.waitKey(20) == 27:
                break

    cv.destroyWindow(window)


def run_viewers(mode: str) -> None:
    script = Path(__file__)
    processes = [
        subprocess.Popen(
            [sys.executable, str(script), "_one", mode, serial, str(port)]
        )
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


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "_one":
        show_one(sys.argv[3], int(sys.argv[4]), sys.argv[2])
        return 0

    parser = argparse.ArgumentParser(description="View the two DVXplorer cameras")
    parser.add_argument(
        "command",
        choices=("focus-source", "focus-view", "record-view"),
        help="Run before-recording source, focus windows, or recording monitor windows",
    )
    args = parser.parse_args()

    if args.command == "focus-source":
        return run_focus_source()
    if args.command == "focus-view":
        run_viewers("focus")
    else:
        run_viewers("record")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
