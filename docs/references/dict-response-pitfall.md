# Dict Response Pitfall: "Got N commands from Hermes" with Dict Keys

## Symptom

The HermesBridge.log shows:
```
*** Hermes Bridge: Got 5 commands from Hermes ***
Hermes Bridge Command Exec Error: global name 'any' is not defined for: strategy_summary
Hermes Bridge Command Exec Error: global name 'any' is not defined for: commands
Hermes Bridge Command Exec Error: global name 'any' is not defined for: whip_actions
Hermes Bridge Command Exec Error: global name 'any' is not defined for: reasoning
Hermes Bridge Command Exec Error: global name 'any' is not defined for: questions_for_human
```

The "commands" being executed are clearly dict keys (strategy_summary, commands, whip_actions, reasoning, questions_for_human), not Python command strings.

## Cause

The Windows-side `hermes_bridge.py` does:

```python
commands = json.loads(response)
for cmd in commands:
    exec cmd in globals()
```

When `response` is a JSON **dict** (e.g., `{"strategy_summary": "...", "commands": [...]}`), `json.loads()` returns a dict. `for cmd in commands` iterates over the **dict keys**, not the actual command list. Each key name then gets `exec`'d as a bare Python identifier, which fails with `NameError: global name 'X' is not defined`.

## Root Causes

### 1. Old bridge process still listening

An old bridge process (with outdated code, possibly from a previous iteration of the project) is still running on port 3334. It responds with a dict instead of a list.

**Fix:** Kill ALL bridge processes before starting a new one:
```bash
fuser -k 3334/tcp   # SIGTERM
sleep 1
ss -tlnp | grep 3334 && echo "STILL RUNNING" || echo "port free"
# If SIGTERM doesn't work (process blocked in socket accept):
kill -9 <PID>
```

### 2. Bridge returning a dict instead of a list

If the bridge code does `json.dumps({"commands": [...]})` instead of `json.dumps([...])`, the response becomes a dict.

**Fix:** The bridge response MUST be:
```python
response = json.dumps(commands)  # where commands is a LIST of strings
# NOT:
response = json.dumps({"commands": commands, "reasoning": "..."})
```

### 3. Stale command file from previous session

If a previous bridge left a commands file containing a dict (e.g., from an earlier iteration), and the new bridge reads it without validating format, it sends a dict to Civ4.

**Fix:** The bridge clears the commands file before each poll cycle:
```python
if os.path.exists(CMD_FILE):
    os.remove(CMD_FILE)
```

## Verification

To test what the bridge is actually returning:
```bash
# From WSL — test with instant-response bridge:
python3 -c "
import socket, json
s = socket.socket(); s.settimeout(10)
s.connect(('127.0.0.1', 3334))
state = {'turn':0,'player_id':1,'units':[],'cities':[],'gold':0}
s.sendall((json.dumps(state) + '\n').encode())
resp = s.recv(4096).decode()
print('Response:', resp)  # Should be a JSON array of command strings
s.close()
"
```

### Test with pre-written commands override:
```python
import socket, json
s = socket.socket(); s.settimeout(10)
s.connect(('127.0.0.1', 3334))
# Write pre-written commands BEFORE sending state
cmds = ['# HERMES test', 'print("test")']
with open('/home/gainq/.hermes/civ4_commands.json', 'w') as f:
    json.dump(cmds, f)
# Now send state — bridge should use pre-writes
state = {'turn':0,'player_id':1,'units':[],'cities':[],'gold':0}
s.sendall((json.dumps(state) + '\n').encode())
resp = s.recv(4096).decode()
print("Response:", resp)  # Should show the pre-written commands
s.close()
```

## Prevention

- Always kill old processes before starting a new bridge
- Always return a JSON **array** (list), never a JSON object (dict)
- The bridge checks for a commands file on each connection — ensure the file is a JSON array
- The bridge falls back to simple defaults (move +1x, build warrior) when no pre-writes exist — these are safe stubs
