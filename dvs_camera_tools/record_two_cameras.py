#!/usr/bin/env python3
"""Record two DVXplorer cameras into separate AEDAT4 files."""

import argparse
import multiprocessing
import re
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2 as cv
import dv_processing as dv


CAMERAS = ("DXAS0102", "DXAS0050")
MONITOR_PORTS = {"DXAS0102": 56102, "DXAS0050": 56050}
DEFAULT_OUTPUT_ROOT = Path("/var/dvs_data")


def record_camera(serial: str, output_path: Path, monitor_interval: float, stop_event) -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    camera = dv.io.camera.openSync(serial)
    writer = dv.io.MonoCameraWriter(str(output_path), camera)
    visualizer = dv.visualization.EventVisualizer(camera.getEventResolution())
    monitor_stream = dv.io.Stream.FrameStream(
        0, "frames", camera.getCameraName(), camera.getEventResolution()
    )
    monitor = dv.io.NetworkWriter("127.0.0.1", MONITOR_PORTS[serial], monitor_stream)
    snapshot_path = output_path.with_suffix(".monitor.png")
    next_status = time.monotonic() + monitor_interval
    interval_events = 0
    interval_triggers = 0
    total_triggers = 0
    recent_events = dv.EventStore()

    role = "master" if camera.isMaster() else "slave"
    print(f"[{serial}] Recording to {output_path} (clock role: {role})", flush=True)
    print(f"[{serial}] Monitor image: {snapshot_path}", flush=True)
    while camera.isRunning() and not stop_event.is_set():
        events = camera.getNextEventBatch()
        if events is not None:
            writer.writeEvents(events, streamName="events")
            interval_events += len(events)
            recent_events.add(events)
            recent_events.retainDuration(timedelta(milliseconds=150))

        imus = camera.getNextImuBatch()
        if imus is not None:
            writer.writeImuPacket(imus, streamName="imu")

        triggers = camera.getNextTriggerBatch()
        if triggers is not None:
            writer.writeTriggerPacket(triggers, streamName="triggers")
            interval_triggers += len(triggers)
            total_triggers += len(triggers)

        if time.monotonic() >= next_status and len(recent_events) > 0:
            image = visualizer.generateImage(recent_events)
            cv.putText(
                image,
                f"{serial}  TTL: {total_triggers}",
                (12, 28),
                cv.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 0),
                2,
            )
            cv.imwrite(str(snapshot_path), image)
            if monitor.getClientCount() > 0:
                monitor.writeFrame(dv.Frame(recent_events.getHighestTime(), image))
            print(
                f"[{serial}] Last {monitor_interval:g}s: {interval_events} events, "
                f"{interval_triggers} new TTL pulses, {total_triggers} TTL pulses total. "
                f"Monitor image: {snapshot_path}",
                flush=True,
            )
            interval_events = 0
            interval_triggers = 0
            next_status = time.monotonic() + monitor_interval

    camera_stopped_unexpectedly = not stop_event.is_set()
    del writer
    if camera_stopped_unexpectedly:
        print(f"[{serial}] ERROR: The camera stopped unexpectedly.", file=sys.stderr, flush=True)
        raise RuntimeError(f"Camera {serial} stopped unexpectedly")
    print(f"[{serial}] Recording stopped", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record DXAS0102 and DXAS0050 at the same time."
    )
    parser.add_argument(
        "--session",
        default="experiment",
        help="Name used for both output files",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Root folder for the two camera recordings",
    )
    parser.add_argument(
        "--monitor-interval",
        type=float,
        default=5,
        help="Seconds between recording status lines and event preview frames (default: 5)",
    )
    args = parser.parse_args()
    if re.fullmatch(r"[A-Za-z0-9_-]+", args.session) is None:
        parser.error("--session may contain only letters, numbers, hyphens, and underscores")
    if args.monitor_interval <= 0:
        parser.error("--monitor-interval must be greater than zero")
    return args


def main() -> int:
    args = parse_args()
    recording_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print("Checking the connected cameras...", flush=True)
    discovered = {device.serialNumber for device in dv.io.camera.discover()}
    missing = [serial for serial in CAMERAS if serial not in discovered]
    if missing:
        print("Cannot start. Missing camera(s): " + ", ".join(missing), file=sys.stderr)
        return 1

    output_paths = {
        serial: (
            args.output_root
            / serial
            / f"{args.session}_{serial}_{recording_timestamp}.aedat4"
        )
        for serial in CAMERAS
    }
    for output_path in output_paths.values():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Session: {args.session}", flush=True)
    print(f"Recording timestamp: {recording_timestamp}", flush=True)
    print("Both required cameras were found:", flush=True)
    for serial in CAMERAS:
        print(f"  {serial}", flush=True)
    print("Output files:", flush=True)
    for serial in CAMERAS:
        print(f"  {output_paths[serial]}", flush=True)
    print(
        f"Recording monitor: one status line and event image every "
        f"{args.monitor_interval:g} seconds per camera.",
        flush=True,
    )

    context = multiprocessing.get_context("spawn")
    stop_event = context.Event()
    processes = [
        context.Process(
            target=record_camera,
            args=(serial, output_paths[serial], args.monitor_interval, stop_event),
            name=f"record-{serial}",
        )
        for serial in CAMERAS
    ]

    def stop_recording(_signum, _frame) -> None:
        print("\nStop requested. Finishing both recording files...", flush=True)
        stop_event.set()

    signal.signal(signal.SIGINT, stop_recording)
    signal.signal(signal.SIGTERM, stop_recording)

    print("Starting one recording process for each camera...", flush=True)
    print("Press Ctrl+C once to stop both recordings safely.", flush=True)
    for process in processes:
        process.start()

    try:
        while all(process.is_alive() for process in processes):
            time.sleep(0.2)
    finally:
        stop_event.set()
        for process in processes:
            process.join()

    failed = [process.name for process in processes if process.exitcode != 0]
    if failed:
        print("Recording process failed: " + ", ".join(failed), file=sys.stderr)
        return 1

    print("Recording finished successfully. Saved files:")
    for serial in CAMERAS:
        print(f"  {output_paths[serial]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
