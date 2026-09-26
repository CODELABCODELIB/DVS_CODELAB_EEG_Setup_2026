#!/usr/bin/env python3
"""Read both DVXplorer cameras and publish their live event streams locally."""

import multiprocessing
import signal
import sys
import time

import dv_processing as dv


PORTS = {"DXAS0102": 56102, "DXAS0050": 56050}


def publish_camera(serial: str, port: int, stop_event) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    camera = dv.io.camera.openSync(serial)
    stream = dv.io.Stream.EventStream(
        0, "events", camera.getCameraName(), camera.getEventResolution()
    )
    server = dv.io.NetworkWriter("127.0.0.1", port, stream)
    print(f"[{serial}] Preview stream ready on local port {port}.", flush=True)
    while camera.isRunning() and not stop_event.is_set():
        events = camera.getNextEventBatch()
        if events is not None and server.getClientCount() > 0:
            server.writeEvents(events)


def main() -> int:
    detected = {device.serialNumber for device in dv.io.camera.discover()}
    missing = [serial for serial in PORTS if serial not in detected]
    if missing:
        print("Missing camera(s): " + ", ".join(missing), file=sys.stderr)
        return 1

    context = multiprocessing.get_context("spawn")
    stop_event = context.Event()
    processes = [
        context.Process(
            target=publish_camera, args=(serial, port, stop_event), name=serial
        )
        for serial, port in PORTS.items()
    ]
    for process in processes:
        process.start()

    print("Press Ctrl+C to stop both preview streams.", flush=True)
    try:
        while all(process.is_alive() for process in processes):
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("Stopping preview streams...", flush=True)
    finally:
        stop_event.set()
        for process in processes:
            process.join()

    failed = [process.name for process in processes if process.exitcode != 0]
    if failed:
        print("Preview source failed for: " + ", ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
