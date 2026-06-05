#!/usr/bin/env python3
"""Civ4-Hermes Bridge — pure relay. No AI logic.
Listens for game state from the Civ4 Python SDK client and returns pending commands.
"""
import socket, json, os, threading, shutil, time
HOST, PORT = "0.0.0.0", 3334
STATE = os.path.expanduser("~/.hermes/civ4_state.json")
CMDS = os.path.expanduser("~/.hermes/civ4_commands.json")
WIN = os.path.expanduser("/mnt/c/Users/gainq/.hermes/civ4_commands.json")
running = True


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
        st = json.loads(d.decode().strip())
        st["_received_at"] = time.time()
        with open(STATE, "w") as f:
            json.dump(st, f, indent=2)
        print(f"T{st.get('turn','?')}: {st.get('numCities',0)}c {st.get('numUnits',0)}u")
        cmds = []
        if os.path.exists(CMDS):
            with open(CMDS) as f:
                cmds = json.load(f)
            try:
                shutil.copy2(CMDS, WIN)
            except Exception:
                pass
        conn.sendall((json.dumps(cmds) + "\n").encode())
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
