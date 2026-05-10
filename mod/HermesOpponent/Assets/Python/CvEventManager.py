# CvEventManager.py - Custom event hooks for HermesOpponent mod
# Phase 2: Listen only for Hermes player ID

from CvPythonExtensions import *
import CvEventManager

import hermes_bridge

class HermesEventManager(CvEventManager.CvEventManager):
    def __init__(self):
        CvEventManager.CvEventManager.__init__(self)

    def onBeginPlayerTurn(self, argsList):
        iPlayer, iTurn = argsList
        pPlayer = gc.getPlayer(iPlayer)
        if iPlayer != hermes_bridge.HERMES_PLAYER_ID:
            return
        CvUtil.pyPrint('Hermes Turn Start - Bridging to AI')
        state = hermes_bridge.get_minimal_state(pPlayer)
        commands = hermes_bridge.send_state_to_hermes(state)
        hermes_bridge.execute_commands(commands)

    # Add more hooks as needed: unitCanMove, etc.
    def onUnitCanMove(self, argsList):
        pUnit, iPlayer = argsList  # adjust per actual API
        if iPlayer != hermes_bridge.HERMES_PLAYER_ID:
            return
        # Stub for unit updates
        pass

# Hook into game
modEventManager = HermesEventManager()