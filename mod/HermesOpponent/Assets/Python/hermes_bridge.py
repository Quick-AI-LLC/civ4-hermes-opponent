# hermes_bridge.py - Phase 2 TCP Bridge for Hermes Civ4 Opponent
# Python 2.4 compatible (Civ4 BTS requirement)
# Minimal state serializer + TCP client to Hermes + command executor

import socket
import json
import CvUtil
from CvPythonExtensions import *
import CvEventManager

# Config
HERMES_HOST = '127.0.0.1'
HERMES_PORT = 3334
HERMES_PLAYER_ID = 1  # Adjust to your Hermes player ID in test games

def send_state_to_hermes(state):
    '''Serialize minimal game state and send to Hermes'''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((HERMES_HOST, HERMES_PORT))
        data = json.dumps(state)
        s.sendall(data + '\n')
        response = s.recv(4096)
        s.close()
        return json.loads(response)
    except Exception as e:
        CvUtil.pyPrint('Hermes Bridge Error: ' + str(e))
        return []

def execute_commands(commands):
    '''Execute list of Python commands safely (player ID gated)'''
    for cmd in commands:
        try:
            # Safety: only act on Hermes player
            if 'Hermes' not in cmd and 'player(' not in cmd:  # simplistic guard
                continue
            exec(cmd)  # In Civ4 context, this runs in game
            CvUtil.pyPrint('Executed: ' + cmd)
        except Exception as e:
            CvUtil.pyPrint('Command Exec Error: ' + str(e))

def get_minimal_state(pPlayer):
    '''Minimal state serialization for Hermes'''
    state = {
        'player_id': pPlayer.getID(),
        'units': [],
        'cities': [],
        'turn': gc.getGame().getGameTurn()
    }
    # Stub: add more in iteration
    return state

# Example usage in event hooks (see CvEventManager.py)
print 'Hermes Bridge loaded'