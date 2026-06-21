#!/usr/bin/env python3
"""
Civ4-Hermes Bridge Server – Reference Implementation (Instant Response)

Threaded TCP server that relays game state to Hermes (the LLM) and
responds INSTANTLY with pre-written or default commands.

CRITICAL:
  - Responds INSTANTLY — no polling. Civ4 expects an immediate reply.
  - Checks for pre-written commands file (~/.hermes/civ4_commands.json) first.
  - Falls back to default commands (move +1x, build warrior) if no pre-writes.
  - YOU (Hermes LLM) read the saved state afterwards and pre-write for next turn.
  - Response MUST be a JSON list of Python 2.4 command strings, NOT a dict.
  - ZERO AI/decision logic — defaults are simple movement + production stubs.
"""

import socket
import json
import signal
import sys
import os
import time
import threading

HOST = "0.0.0.0"
PORT = 3334
STATE_FILE = os.path.expanduser("~/.hermes/civ4_state.json")
CMDS_FILE = os.path.expanduser("~/.hermes/civ4_commands.json")

running = True


def signal_handler(sig, frame):
    global running
    print("\nShutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def get_commands(state):
    """Return commands for this turn. Uses pre-written file if available, else defaults.
    ZERO AI — defaults are simple stubs that let the game advance."""
    turn = state.get("turn", 0)
    pid = state.get("player_id", 1)
    units = state.get("units", [])
    cities = state.get("cities", [])

    # Check for pre-written commands from Hermes (from analyzing previous turn)
    if os.path.exists(CMDS_FILE):
        try:
            with open(CMDS_FILE, "r") as f:
                cmds = json.load(f)
            os.remove(CMDS_FILE)
            if cmds:
                print(f"[Bridge] Using {len(cmds)} pre-written commands (turn {turn})")
                return cmds
        except (json.JSONDecodeError, IOError) as e:
            print(f"[Bridge] Bad cmds file: {e}")

    # Default commands: explore with first unit, build warrior
    cmds = [f"# Hermes: turn {turn} defaults"]
    cmds.append(f"p = gc.getPlayer({pid})")

    for u in units[:1]:
        uid = u.get("id", 0)
        ux, uy = u.get("x", 0), u.get("y", 0)
        cmds.append(f"pUnit = p.getUnit({uid})")
        cmds.append(f"if pUnit and not pUnit.isDead() and pUnit.getMoves() > 0:")
        cmds.append(f"  group = pUnit.getGroup()")
        cmds.append(f"  CyInterface().pushMission(group, MissionTypes.MISSION_MOVE_TO, {ux+1}, {uy}, 0, False, False, MissionAITypes.MISSIONAI_EXPLORE, pUnit)")

    for c in cities[:1]:
        cid = c.get("id", 0)
        cmds.append(f"pCity = p.getCity({cid})")
        cmds.append(f"if pCity:")
        cmds.append(f"  pCity.pushOrder(OrderTypes.ORDER_TRAIN, UnitTypes.UNIT_WARRIOR, -1, 0, False, False, False)")

    cmds.append(f"print('Hermes: turn {turn} done')")
    print(f"[Bridge] Sending {len(cmds)} default commands (turn {turn})")
    return cmds


def handle_client(conn, addr, cid):
    try:
        conn.settimeout(10.0)
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in data:
                break
        if not data:
            conn.close()
            return

        raw = data.decode("utf-8", errors="replace").strip()
        state = json.loads(raw)
        state["_received_at"] = time.time()

        # Save state for Hermes to analyze after the turn
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

        turn = state.get("turn", "?")
        nc = state.get("numCities", 0)
        nu = state.get("numUnits", 0)
        print(f"[{cid}] Turn {turn}: {nc}c {nu}u — generating instant response")

        # Get commands instantly — no polling
        cmds = get_commands(state)

        conn.sendall((json.dumps(cmds) + "\n").encode("utf-8"))
        print(f"[{cid}] Sent {len(cmds)} commands in 0.00s")

    except Exception as e:
        print(f"[{cid}] Error: {e}")
    finally:
        conn.close()


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    server.settimeout(2.0)

    print("Civ4-Hermes Bridge (instant response)")
    print(f"Listening on {HOST}:{PORT}")
    print("Write commands to civ4_commands.json to override defaults")
    print("=" * 60)

    cid = 0
    while running:
        try:
            conn, addr = server.accept()
            cid += 1
            t = threading.Thread(target=handle_client, args=(conn, addr, cid), daemon=True)
            t.start()
        except socket.timeout:
            continue
        except OSError:
            break

    server.close()
    print("Stopped.")


if __name__ == "__main__":
    main()
