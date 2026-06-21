#!/usr/bin/env python3
"""Civ4-Hermes Bridge — pure relay. No AI logic.
Listens for game state from the Civ4 Python SDK client and returns pending commands.
"""
import socket, json, os, threading, shutil, time
HOST, PORT = "0.0.0.0", 3334
STATE = os.path.expanduser("~/.hermes/civ4_state.json")
GATE = os.path.expanduser("~/.hermes/turn_gate.json")
CMDS = os.path.expanduser("~/.hermes/civ4_commands.json")
WIN = os.path.expanduser("/mnt/c/Users/gainq/.hermes/civ4_commands.json")
running = True


def _reply(conn, cmds):
    conn.sendall((json.dumps(cmds) + "\n").encode())


def _load_cmds():
    if not os.path.exists(CMDS):
        return []
    with open(CMDS) as f:
        return json.load(f)


def handle(conn):
    try:
        conn.settimeout(10)
        d = b""
        while True:
            c = conn.recv(4096)
            if not c:
                break
            d += c
            if b"\n" in d:
                break
        if not d:
            return
        payload = json.loads(d.decode().strip())
        payload["_received_at"] = time.time()

        # Hotseat handoff signal — not a full game state; do not overwrite civ4_state.json
        if payload.get("event") == "handoff_pending":
            with open(GATE, "w") as f:
                json.dump(payload, f, indent=2)
            print(
                "HANDOFF pending: P{} turn {}".format(
                    payload.get("player_id", "?"), payload.get("turn", "?")
                )
            )
            _reply(conn, [])
            return

        with open(STATE, "w") as f:
            json.dump(payload, f, indent=2)
        print(
            "T{}: {}c {}u".format(
                payload.get("turn", "?"),
                payload.get("numCities", 0),
                payload.get("numUnits", 0),
            )
        )
        cmds = _load_cmds()
        if os.path.exists(CMDS):
            try:
                shutil.copy2(CMDS, WIN)
            except Exception:
                pass
        _reply(conn, cmds)
    except Exception as e:
        print(f"ERR: {e}")
    finally:
        conn.close()


def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    s.settimeout(1)
    print(f"Bridge relay on {PORT}")
    while running:
        try:
            c, _ = s.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()
        except socket.timeout:
            continue
        except Exception:
            break
    s.close()


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, lambda *a: exit())
    signal.signal(signal.SIGTERM, lambda *a: exit())
    main()
