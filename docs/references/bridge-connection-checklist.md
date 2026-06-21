# Bridge Connection Checklist

When setting up the Civ4-Hermes bridge between Windows (Civ4) and WSL (Hermes), avoid the common pitfalls below.

## The Right Tool: TCP Bridge, NOT HTTP Proxy

**Critical:** The Civ4 mod uses a **raw TCP socket bridge** on port **3334**, NOT the `hermes proxy` HTTP server (port 8645).

| Component | Port | Protocol | Where to run |
|---|---|---|---|
| Civ4 Bridge Server | **3334** | Raw TCP (JSON list of commands over socket) | **WSL** (Hermes side) |
| Hermes HTTP Proxy | 8645 | HTTP/OpenAI API | Hermes proxy (WRONG — for API forwarding, not game bridge) |

## `hermes_config.py` Required Values

```python
HERMES_HOST = "172.29.235.138"    # WSL virtual IP — get from `hostname -I` in WSL
HERMES_PORT = 3334                 # TCP bridge, NOT 8645
HERMES_PLAYER_ID = 1               # Which Civ4 player slot
```

**Pitfall:** The `import hermes_config` statement in `hermes_bridge.py` can fail sporadically in Civ4's Python 2.4 due to module path loading order. When it fails, the fallback sets `HERMES_HOST = '127.0.0.1'` which is unreachable from Civ4 on Windows. **Fix:** Hardcode the values directly in `hermes_bridge.py`.

## Getting the WSL IP

From WSL terminal:
```bash
hostname -I | awk '{print $1}'
```

The IP typically looks like `172.29.x.x` or `172.18.x.x` — this is the WSL virtual network adapter visible to Windows. **This IP can change on WSL restart.** If the game was working and suddenly isn't, check if the WSL IP changed.

## Bridge Data Flow

1. **Civ4 mod** (Windows) → calls `send_state_to_hermes(state)` on Hermes' player turn
2. Sends JSON game state over TCP to WSL IP:3334
3. **Bridge server** (WSL) → receives state, writes to file, checks for pre-written commands file, **responds INSTANTLY (0.00s)**
4. If pre-written commands exist (from you analyzing the previous turn), bridge uses those
5. If no pre-written commands, bridge returns **empty list `[]`** — does NOTHING that turn (no auto-research, no forced moves, no auto-build)
6. **YOU (Hermes LLM)** → read the state file AFTER the turn was processed, analyze position, write commands for the **next** turn
7. **Next Civ4 connection** → bridge picks up your pre-written commands

**CRITICAL: No AI logic in bridge.** Nick explicitly rejected preprogrammed research/build/move. The bridge is a pure relay. Every decision comes from the LLM, every turn.

## Response Format (CRITICAL)

```python
# ✅ CORRECT — list of Python 2.4 command strings to exec in Civ4 context
["pPlayer.setGold(pPlayer.getGold() + 50)", "print('executed')"]

# ❌ WRONG — dict will crash. The mod iterates the response as a list of commands.
{"reasoning": "...", "commands": [...]}
```

## ⚠️ Bridge returns empty list (no defaults)

The bridge does NOT poll for commands. It has a `get_commands()` function that:
1. Checks for a pre-written commands file (`~/.hermes/civ4_commands.json`)
2. If found, reads it, deletes it, returns those commands
3. If not found, returns **empty list `[]`** — does nothing that turn (pure relay, no AI logic)
4. Sends response and closes connection immediately

Previously the bridge had "smart defaults" (research Mining, move units east, build Settlers) — these were removed per Nick's instruction. The bridge is now a pure relay with zero decision-making logic.

## Server Binding

- Must bind to `0.0.0.0` (all interfaces), NOT `127.0.0.1`
- `127.0.0.1` in WSL is WSL-local — Windows cannot reach it
- `0.0.0.0` exposes it on the WSL virtual NIC at the IP Windows sees (e.g. 172.29.x.x)

## Python 2.4 Pitfalls in Mod Code

Civ4 BTS ships with **Python 2.4**. Common incompatibilities:
- ❌ `any(...)` — not available, use `for` loop with `_safe` flag
- ❌ `all(...)` — not available
- ❌ `next(iterator)` — not available, use manual loop
- ❌ `with` statement — does not exist, use explicit open/close
- ❌ `exec` in nested function — causes free-variable error
- ❌ Generator expressions passed to functions — use list comps instead
- ❌ `except Exception, e:` — valid in Py2.4 but flagged as syntax error by Py3 linters. Ignore the lint warning.
- ✅ `socket`, `json` (via bundled `simplejson`), `os`, `CvUtil` — all available
## Common Mistakes

- ❌ Using `hermes proxy` (port 8645, HTTP, needs Nous Portal auth) instead of TCP bridge (port 3334)
- ❌ Binding bridge to `127.0.0.1` instead of `0.0.0.0` (not reachable from Windows)
- ❌ Forgetting to start the bridge before launching the game
- ❌ Returning a dict from the bridge instead of a list of command strings
- ❌ Using Python 3 syntax in mod files that run under Civ4's Python 2.4
- ❌ Building AI/decision logic into the bridge script — the bridge is a pure relay; it returns `[]` when no commands file exists, not "smart defaults"
- ❌ Not killing old bridge processes before restarting (causes stale-process response corruption)
- ❌ Using polling in the bridge — Civ4 expects an instant response (0.00s), not a 30s delay
- ❌ Saying "I'll make the move now" — you're always one turn behind; the bridge already responded
