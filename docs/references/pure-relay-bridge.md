# Pure Relay Bridge (Current Working Architecture)

## What it is

A minimal Python TCP server that:
1. Listens on port 3334 for Civ4 game state
2. Saves state to `~/.hermes/civ4_state.json` with timestamp
3. Reads commands from `~/.hermes/civ4_commands.json` (persistent — NOT deleted)
4. Syncs commands to Windows path (`/mnt/c/Users/gainq/.hermes/`)
5. Sends commands back to Civ4
6. **Contains ZERO decision logic** — decisions come from the LLM writing commands

## The Script

Location: `~/.hermes/scripts/civ4_bridge.py`

Key features:
- **Threaded** — handles one connection at a time (Civ4 sends one state per turn)
- **Socket timeout 1s** on accept — responsive shutdown
- **Saves state** with `_received_at` timestamp for staleness detection
- **Reads commands file every connection** — persistent commands run every turn
- **Syncs to Windows** — so callbacks (`get_desired_research()`, `handle_ai_production()`) running inside Civ4 (Windows Python) can find the file
- **No defaults** — returns `[]` when no commands file exists (pure relay)

## What NOT to put in the bridge

Nick explicitly rejected embedded decision logic. Do NOT add:
- `decide()` or `make_decisions()` functions
- Tech path priorities or `pick_next_tech()`
- Unit type counting or settler deployment logic
- City production priority logic
- ANY function that reads state and returns commands

The bridge reads commands from the file and sends them. That's it.

## Verifying It's Running

```bash
ps aux | grep civ4_bridge | grep -v grep
# Should show: python3 /home/gainq/.hermes/scripts/civ4_bridge.py
```

## Restart Sequence

```bash
kill $(ps aux | grep civ4_bridge | grep python3 | awk '{print $2}') 2>/dev/null
sleep 1
python3 /home/gainq/.hermes/scripts/civ4_bridge.py &
```
