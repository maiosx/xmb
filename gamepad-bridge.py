#!/usr/bin/env python3
"""Gamepad bridge for the XMB menu.

Watches connected gamepads and prints simple navigation tokens to stdout,
one per line, mirroring the menu's own keyboard actions:

    up down left right confirm back cancel delete pageup pagedown

Menu.qml runs this as a Process and feeds each line into root.dispatchAction(),
the same dispatcher used for keyboard input, so no button/axis codes need to
live in QML.

Xbox controllers (kernel xpad driver) and PS5 DualSense/DualShock controllers
(hid-sony / hid-playstation) are both handled by the same mapping below,
because the kernel's gamepad event codes (BTN_SOUTH, BTN_EAST, BTN_NORTH,
BTN_WEST, ...) are defined by physical button position rather than brand:
BTN_SOUTH is Xbox A / PS Cross, BTN_EAST is Xbox B / PS Circle, and so on.
Any other controller whose driver follows that same convention works too.

Requires python-evdev (e.g. `sudo pacman -S python-evdev`). If it isn't
installed, this exits quietly and the menu simply has no gamepad input --
keyboard, mouse, and touchpad navigation are unaffected.
"""
import glob
import select
import sys
import time

try:
    import evdev
    from evdev import ecodes
except ImportError:
    sys.stderr.write(
        "xmb-menu: python-evdev not installed; gamepad support disabled "
        "(install with 'sudo pacman -S python-evdev')\n"
    )
    sys.exit(0)

RESCAN_INTERVAL = 3.0   # seconds between checks for newly connected pads
REPEAT_DELAY = 0.38     # seconds a direction must be held before it repeats
REPEAT_RATE = 0.12      # seconds between repeats while a direction is held
DEADZONE = 0.45         # fraction of full stick travel before it counts

# Buttons that fire once per press. Both Xbox and PS5/DualSense pads report
# these same symbolic codes for the equivalent physical button.
BUTTON_ACTIONS = {
    ecodes.BTN_SOUTH: "confirm",   # Xbox A / PS Cross
    ecodes.BTN_EAST: "back",       # Xbox B / PS Circle
    ecodes.BTN_NORTH: "delete",    # Xbox Y / PS Triangle
    ecodes.BTN_START: "cancel",    # Xbox Menu / PS Options
    ecodes.BTN_SELECT: "cancel",   # Xbox View / PS Share-Create
    ecodes.BTN_TL: "pageup",       # LB / L1
    ecodes.BTN_TR: "pagedown",     # RB / R1
    ecodes.BTN_MODE: "summon",     # Xbox Guide button / PS button (center)
}

# A handful of pads report the D-pad as four discrete buttons instead of an
# ABS_HAT0X/Y hat axis.
DPAD_BUTTONS = {
    ecodes.BTN_DPAD_UP: "up",
    ecodes.BTN_DPAD_DOWN: "down",
    ecodes.BTN_DPAD_LEFT: "left",
    ecodes.BTN_DPAD_RIGHT: "right",
}


def emit(token):
    print(token, flush=True)


def open_if_gamepad(path):
    """Return an opened InputDevice if `path` looks like a gamepad, else None."""
    try:
        dev = evdev.InputDevice(path)
    except (OSError, PermissionError):
        return None
    caps = dev.capabilities()
    has_face_button = ecodes.BTN_SOUTH in caps.get(ecodes.EV_KEY, [])
    has_axes = ecodes.EV_ABS in caps
    if has_face_button and has_axes:
        return dev
    dev.close()
    return None


def scan_for_new_gamepads(known_paths):
    found = {}
    for path in glob.glob("/dev/input/event*"):
        if path in known_paths:
            continue
        dev = open_if_gamepad(path)
        if dev is not None:
            found[path] = dev
    return found


def set_direction(state, direction):
    """Emit `direction` on a rising edge and arm/disarm the repeat timer."""
    if direction == state["dir"]:
        return
    state["dir"] = direction
    if direction:
        emit(direction)
        state["next_fire"] = time.time() + REPEAT_DELAY
    else:
        state["next_fire"] = 0


def update_dpad(state):
    x, y = state.get("hat_x", 0), state.get("hat_y", 0)
    if y < 0:
        set_direction(state, "up")
    elif y > 0:
        set_direction(state, "down")
    elif x < 0:
        set_direction(state, "left")
    elif x > 0:
        set_direction(state, "right")
    else:
        set_direction(state, None)


def update_stick(dev, event, state):
    lo, hi = dev.absinfo(event.code).min, dev.absinfo(event.code).max
    span = (hi - lo) or 1
    normalized = ((event.value - lo) / span) * 2 - 1  # -1..1

    if event.code == ecodes.ABS_X:
        state["stick_x"] = normalized
    else:
        state["stick_y"] = normalized

    # The D-pad wins when it's active, so the two inputs don't fight.
    if state.get("hat_x", 0) or state.get("hat_y", 0):
        return

    sx, sy = state.get("stick_x", 0), state.get("stick_y", 0)
    if abs(sy) > DEADZONE and abs(sy) >= abs(sx):
        set_direction(state, "up" if sy < 0 else "down")
    elif abs(sx) > DEADZONE:
        set_direction(state, "left" if sx < 0 else "right")
    else:
        set_direction(state, None)


def handle_event(dev, event, state):
    if event.type == ecodes.EV_KEY and event.value == 1:  # press only, no release/repeat
        if event.code in DPAD_BUTTONS:
            emit(DPAD_BUTTONS[event.code])
        elif event.code in BUTTON_ACTIONS:
            emit(BUTTON_ACTIONS[event.code])
        return

    if event.type != ecodes.EV_ABS:
        return

    if event.code == ecodes.ABS_HAT0X:
        state["hat_x"] = event.value
        update_dpad(state)
    elif event.code == ecodes.ABS_HAT0Y:
        state["hat_y"] = event.value
        update_dpad(state)
    elif event.code in (ecodes.ABS_X, ecodes.ABS_Y):
        update_stick(dev, event, state)


def main():
    devices = {}
    held = {}
    last_scan = 0.0

    while True:
        now = time.time()
        if now - last_scan > RESCAN_INTERVAL:
            for path, dev in scan_for_new_gamepads(devices).items():
                devices[path] = dev
                held[path] = {"dir": None, "next_fire": 0}
                sys.stderr.write("xmb-menu: gamepad connected (%s)\n" % dev.name)
            last_scan = now

        if not devices:
            time.sleep(1)
            continue

        try:
            ready, _, _ = select.select(list(devices.values()), [], [], 0.05)
        except (OSError, ValueError):
            ready = []

        for path in list(devices.keys()):
            dev = devices[path]
            if dev not in ready:
                continue
            try:
                for event in dev.read():
                    handle_event(dev, event, held[path])
            except OSError:
                del devices[path]
                del held[path]
                sys.stderr.write("xmb-menu: gamepad disconnected\n")

        now = time.time()
        for state in held.values():
            if state["dir"] and now >= state["next_fire"]:
                emit(state["dir"])
                state["next_fire"] = now + REPEAT_RATE


if __name__ == "__main__":
    main()
