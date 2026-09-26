# Two DVXplorer cameras: operator guide

This folder contains the code used on the CODELABPSI laboratory computer for
camera `DXAS0102` and camera `DXAS0050`. It records each camera to a separate
AEDAT4 file. These files contain visual events, motion sensor (IMU) readings,
and any electrical trigger pulses (TTL) received by that camera. Event cameras
record changes in brightness, not ordinary RGB video.

## Before the first session

Connect both cameras to the computer with their USB cables and switch them on.
In a terminal on the laboratory computer, open the installed code folder:

```bash
cd /home/zhen/dvs_tools
./install.sh
```

`install.sh` checks the existing Python environment first. If the required
packages are already present, it keeps them. Its final message says when
`start_recording.sh` is ready.

The GitHub repository can be cloned into another folder. In that case, run
`./install.sh` inside the cloned folder and use that folder for the commands
below. Never put AEDAT4 data or environment files into Git.

## Check focus before recording

The camera preview and recorder both open the cameras. Run the preview first,
then stop it before starting a recording.

On the laboratory computer's graphical desktop, open two terminals in the code
folder. In terminal 1 run:

```bash
./.venv/bin/python preview_source.py
```

In terminal 2 run:

```bash
./.venv/bin/python preview_two_cameras.py
```

Two windows show the event views. Ask somebody to move a hand at the intended
recording position while turning the physical focus ring on each lens. Moving
edges should look clearest at the correct focus. Press Esc in a window to close
the viewers, then press Ctrl+C in terminal 1 to release both cameras.

This custom Python preview uses the packages installed on Ubuntu 26.04. The
windows require a logged-in graphical desktop. It is separate from the
manufacturer's DV GUI.

## Start recording

Stop the focus preview and any other software using the cameras. Then run:

```bash
./start_recording.sh --session participant_01 --monitor-interval 5
```

Use a unique session name containing only letters, numbers, underscores, and
hyphens. The program checks that both cameras are connected, prints the
camera serial numbers and full output paths, then starts recording. The default
data root on CODELABPSI is `/home/zhen/dvs_cam`:

```text
/home/zhen/dvs_cam/DXAS0102/participant_01_DXAS0102.aedat4
/home/zhen/dvs_cam/DXAS0050/participant_01_DXAS0050.aedat4
```

To use a different data location, add `--output-root /path/to/data`.

## Watch the recording

Every 5 seconds, each camera prints how many visual events it recorded in that
period, how many new TTL pulses it received, and its total TTL count. It also
updates an event image next to its AEDAT4 file:

```text
/home/zhen/dvs_cam/DXAS0102/participant_01_DXAS0102.monitor.png
/home/zhen/dvs_cam/DXAS0050/participant_01_DXAS0050.monitor.png
```

The images show recent brightness changes. They are status snapshots, not RGB
photographs. You can open them from the laboratory computer or VS Code while
recording. To see them update automatically in two windows, open a separate
terminal on the laboratory computer's graphical desktop and run:

```bash
./.venv/bin/python monitor_two_cameras.py
```

This monitor connects to the running recorder. It does not open the cameras
again. Leave the recorder running in its original terminal. Press Esc in a
monitor window to close the windows; recording continues.

For a remote display on Zhen's computer, keep this SSH tunnel open locally:

```bash
ssh -N -L 56102:127.0.0.1:56102 -L 56050:127.0.0.1:56050 dvs_lab
```

In another local terminal, run `python3 monitor_two_cameras.py` from a local
copy of this folder with `dv-processing` and OpenCV installed. The camera
streams listen only on the lab computer itself; the tunnel carries them to the
local viewer. The same tunnel and `preview_two_cameras.py` can be used for the
pre-recording focus preview.

If you prefer less frequent updates, start the recorder with
`--monitor-interval 30` for one update every 30 seconds per camera.

## Stop and inspect

Press Ctrl+C **once** in the recording terminal. Wait for
`Recording finished successfully. Saved files:` before disconnecting cameras
or closing the terminal. Then inspect each file, for example:

```bash
./.venv/bin/python inspect_recording.py \
  /home/zhen/dvs_cam/DXAS0050/participant_01_DXAS0050.aedat4
```

The `Triggers:` count shows how many TTL pulses that camera recorded. During
the September test, `DXAS0050` received one external pulse about every minute
and `DXAS0102` received none. The actual count for each new session must be
checked in that session's files.

## Camera-to-camera timing

You can run `./.venv/bin/python check_camera_sync.py` while the recorder and
preview are stopped. It reports which camera sees itself as master or slave
and tests timestamp synchronization in that check session. On 26 September,
both connected cameras still reported `master`; the synchronization cable was
therefore not confirmed to be working. The recording script opens the cameras
in separate processes and does not call a two-camera synchronization function.
Do not treat its two AEDAT4 timestamps as one hardware-synchronized clock.

For later analysis, match activity visible to both cameras at several points
throughout the recording, including near its beginning and end. This allows
the relative clock drift to be estimated. Match the TTL timestamps from
`DXAS0050` with the corresponding TTL timestamps in the other device to put
that camera on the other device's timeline.

## Storage and sharing

The September 12-minute-40-second test produced about 1.97 GB from both
cameras. At similar scene activity, two hours would use about 19 GB. Movement
and lighting changes affect the actual size. Keep AEDAT4 files on the lab data
disk. This GitHub repository contains only code and instructions.
