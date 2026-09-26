#!/usr/bin/env python3
"""Check the hardware and timestamp synchronization of both DVXplorer cameras."""

import sys

import dv_processing as dv


CAMERAS = ("DXAS0102", "DXAS0050")


def print_status(cameras) -> None:
    for serial in CAMERAS:
        camera = cameras[serial]
        role = "master" if camera.isMaster() else "slave"
        synchronized = "yes" if camera.isSynchronized() else "no"
        print(f"{serial}: role={role}, synchronized={synchronized}")


def main() -> int:
    detected = {device.serialNumber for device in dv.io.camera.discover()}
    missing = [serial for serial in CAMERAS if serial not in detected]
    if missing:
        print("Cannot check synchronization. Missing camera(s): " + ", ".join(missing))
        return 1

    cameras = {serial: dv.io.camera.openSync(serial) for serial in CAMERAS}

    print("Status reported by the connected cameras:")
    print_status(cameras)

    masters = [serial for serial, camera in cameras.items() if camera.isMaster()]
    if len(masters) != 1:
        print(f"Synchronization cable check failed: expected one master, found {len(masters)}.")
        return 1

    print(f"Hardware roles are correct. Master camera: {masters[0]}")
    print("Synchronizing the two camera timestamps...")
    dv.io.camera.synchronizeAnyTwo(cameras[CAMERAS[0]], cameras[CAMERAS[1]])

    print("Status after timestamp synchronization:")
    print_status(cameras)
    if not all(camera.isSynchronized() for camera in cameras.values()):
        print("Timestamp synchronization failed.")
        return 1

    print("Both cameras synchronized in this check session.")
    print("Start a new recording only after checking its own clock status; this")
    print("one-off check does not synchronize the separate recording processes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
