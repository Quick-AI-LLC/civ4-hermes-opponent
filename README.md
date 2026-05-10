# Hermes as Civ 4 Opponent (Python-Bridge Route)

**Quick AI LLC** North Idaho AI integration experiment – Agentic Organizations + ASO pipeline  
[quickai.build](https://quickai.build) | [github.com/Quick-AI-LLC](https://github.com/Quick-AI-LLC) | [linktr.ee/CDAQAI](https://linktr.ee/CDAQAI)

This repo implements the exact development outline from `modoutline.docx` for turning Hermes (Quick AI agent) into a full AI opponent in Civilization IV: Beyond the Sword using a lightweight Python TCP bridge.

## Phase Status
✅ **Phase 1 & 2 Complete** – Prerequisites, mod setup, event hooks, and TCP bridge skeleton.

## Quick Start (Phase 1)
1. Install Civ 4 Beyond the Sword patched to 1.74.  
2. Download the official pyconsole mod: https://github.com/civ4-mp/pyconsole  
3. Copy the `mod/HermesOpponent` folder into your `Civilization IV/Beyond the Sword/Mods/` directory.  
4. In-game: Select the "HermesOpponent" mod when starting a new game.  
5. Run Hermes locally (or in Paperclip org) with the new "Civ 4 Player" skill enabled. It listens on `127.0.0.1:3334` by default.

## Files in this Repo
- `mod/HermesOpponent/` – Ready-to-drop Civ 4 mod folder with custom bridge.  
- `hermes-skill/` – Prompt + schema for Hermes "Civ 4 Player" skill (Phase 3).  

## Development Approach (per outline)
- Event hooks only fire for Hermes player ID.  
- Minimal JSON state serialization → TCP to Hermes → Python command list → execute via pyconsole/CvUtil.  
- Start with unit movement; expand to cities/tech/diplomacy.

## Next Steps
- Phase 3: Build Hermes skill (prompt + memory across games).  
- Phase 4: Test on 7-player map + iterate.  
- Phase 5: README + setup script polish.

**Ombudsmen Record Note**: Autonomous push by Grok + team (Finn, Brian, Jimbo) following OMBUDSMEN-OPERATIONS-GUIDE.md. Token tracking & handoff protocol observed. See full history in repo.

Live at: https://github.com/Quick-AI-LLC/civ4-hermes-opponent

Built for Quick AI LLC clients and internal agentic experiments.