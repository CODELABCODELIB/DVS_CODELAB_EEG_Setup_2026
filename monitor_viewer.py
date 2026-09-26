#!/usr/bin/env python3
"""Display low-rate event snapshots from one camera during recording."""

import argparse

import cv2 as cv
import dv_processing as dv


def main() -> None:
    parser = argparse.ArgumentParser(description="Display one recording monitor stream")
    parser.add_argument("serial", choices=("DXAS0102", "DXAS0050"))
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    reader = dv.io.NetworkReader("127.0.0.1", args.port)
    window = f"Recording monitor {args.serial}"
    cv.namedWindow(window, cv.WINDOW_NORMAL)
    while reader.isRunning():
        frame = reader.getNextFrame()
        if frame is not None:
            cv.imshow(window, frame.image)
        if cv.waitKey(20) == 27:
            break
    cv.destroyWindow(window)


if __name__ == "__main__":
    main()
