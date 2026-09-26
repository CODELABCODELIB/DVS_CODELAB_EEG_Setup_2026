#!/usr/bin/env python3
"""Show live DVXplorer events received from a dv-processing network stream."""

import argparse
from datetime import timedelta

import cv2 as cv
import dv_processing as dv


def main() -> None:
    parser = argparse.ArgumentParser(description="Display one live DVS camera stream")
    parser.add_argument("serial", choices=("DXAS0102", "DXAS0050"))
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    reader = dv.io.NetworkReader("127.0.0.1", args.port)
    visualizer = dv.visualization.EventVisualizer(reader.getEventResolution())
    slicer = dv.EventStreamSlicer()
    window = f"DVXplorer {args.serial}"
    cv.namedWindow(window, cv.WINDOW_NORMAL)

    def show_events(events: dv.EventStore) -> None:
        cv.imshow(window, visualizer.generateImage(events))
        if cv.waitKey(2) == 27:
            raise SystemExit(0)

    slicer.doEveryTimeInterval(timedelta(milliseconds=33), show_events)
    while reader.isRunning():
        events = reader.getNextEventBatch()
        if events is not None:
            slicer.accept(events)


if __name__ == "__main__":
    main()
