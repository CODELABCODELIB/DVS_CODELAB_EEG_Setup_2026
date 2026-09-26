#!/usr/bin/env python3
"""Count events and triggers in an AEDAT4 recording."""

import argparse

import dv_processing as dv


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect one AEDAT4 recording")
    parser.add_argument("file")
    args = parser.parse_args()

    recording = dv.io.MonoCameraRecording(args.file)
    events_count = 0
    trigger_count = 0
    trigger_types = {}

    while True:
        events = recording.getNextEventBatch()
        if events is None:
            break
        events_count += len(events)

    while True:
        triggers = recording.getNextTriggerBatch()
        if triggers is None:
            break
        for trigger in triggers:
            trigger_count += 1
            name = str(trigger.type)
            trigger_types[name] = trigger_types.get(name, 0) + 1

    print(f"File: {args.file}")
    print(f"Events: {events_count}")
    print(f"Triggers: {trigger_count}")
    for name, count in trigger_types.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
