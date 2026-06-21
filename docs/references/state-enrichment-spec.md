# State Enrichment Spec — Gridlock's Option A

**Source:** Session May 31, 2026 — Grok produced this spec for enriching the Hermes Civ4 state with diplomatic, military, and production data.

**Integration:** Three helper functions slot into the Windows-side hermes_bridge.py state builder. WSL relay needs zero changes.

## Target JSON Structure (Additions)

```json
{
  "diplo": {
    "metCivs": [0, 2, 3, 5],
    "attitudes": [
      {"playerId": 0, "level": 4, "levelName": "Pleased"}
    ],
    "warStatus": [
      {"playerId": 0, "atWar": false},
      {"playerId": 3, "atWar": true}
    ],
    "activeDeals": [
      {
        "partner": 0,
        "type": "openBorders",
        "ourItems": ["Gold 5/turn", "Cow"],
        "theirItems": ["Spices", "Map"]
      }
    ]
  },
  "visibleEnemies": {
    "byOwner": {
      "0": {
        "units": [
          {"id": 12345, "owner": 0, "unitType": 12, "x": 45, "y": 67, "damage": 0, "movesLeft": 2}
        ],
        "summary": "3 units near Bombay area"
      }
    },
    "totalVisible": 7
  },
  "cities": [
    {
      "id": 7, "x": 58, "y": 31, "name": "Delhi", "population": 7,
      "production": {
        "name": "Axeman",
        "turnsLeft": 1,
        "isBuildingUnit": true
      },
      "growth": {
        "foodPerTurn": 4,
        "foodStored": 12,
        "foodNeeded": 22,
        "turnsToGrow": 3,
        "isStarving": false
      }
    }
  ]
}
```

## Helper 1: get_diplo_snapshot(ourPlayerID)

```python
def get_diplo_snapshot(ourPlayerID):
    result = {"metCivs": [], "attitudes": [], "warStatus": [], "activeDeals": []}
    try:
        pOurPlayer = gc.getPlayer(ourPlayerID)
        ourTeam = pOurPlayer.getTeam()
        pOurTeam = gc.getTeam(ourTeam)

        for i in range(gc.getMAX_CIV_PLAYERS()):
            if i == ourPlayerID:
                continue
            pLoop = gc.getPlayer(i)
            if not pLoop.isAlive() or pLoop.isBarbarian():
                continue

            loopTeam = pLoop.getTeam()
            if pOurTeam.isHasMet(loopTeam):
                result["metCivs"].append(i)

                # Attitude (0=Furious, 1=Annoyed, 2=Cautious, 3=Pleased, 4=Friendly)
                try:
                    att = pOurPlayer.AI_getAttitude(i)
                    level = int(att) if att is not None else -1
                    levelName = ""
                    try:
                        info = gc.getAttitudeInfo(att)
                        if info:
                            levelName = info.getDescription()
                    except:
                        pass
                    result["attitudes"].append({
                        "playerId": i,
                        "level": level,
                        "levelName": levelName
                    })
                except:
                    pass

                # War status
                try:
                    result["warStatus"].append({
                        "playerId": i,
                        "atWar": bool(pOurTeam.isAtWar(loopTeam))
                    })
                except:
                    pass

        # Active deals
        try:
            for i in range(gc.getGame().getIndexAfterLastDeal()):
                deal = gc.getGame().getDeal(i)
                if deal.isNone():
                    continue

                first = deal.getFirstPlayer()
                second = deal.getSecondPlayer()

                if first == ourPlayerID or second == ourPlayerID:
                    partner = second if first == ourPlayerID else first
                    ourItems = []
                    theirItems = []

                    for j in range(deal.getLengthFirstTrades()):
                        try:
                            item = deal.getFirstTrade(j)
                            # itemStr = _format_trade_item(item) -- implement as needed
                            if first == ourPlayerID:
                                ourItems.append(str(item))
                            else:
                                theirItems.append(str(item))
                        except:
                            pass

                    for j in range(deal.getLengthSecondTrades()):
                        try:
                            item = deal.getSecondTrade(j)
                            if second == ourPlayerID:
                                ourItems.append(str(item))
                            else:
                                theirItems.append(str(item))
                        except:
                            pass

                    result["activeDeals"].append({
                        "partner": partner,
                        "type": "trade",  # refine: openBorders if both sides empty, peace if no items
                        "ourItems": ourItems,
                        "theirItems": theirItems
                    })
        except Exception, e:
            print("HERMES: Deal iteration error: " + str(e))

    except Exception, e:
        print("HERMES: get_diplo_snapshot fatal: " + str(e))

    return result
```

## Helper 2: get_visible_enemy_units(ourPlayerID)

```python
def get_visible_enemy_units(ourPlayerID):
    result = {"byOwner": {}, "totalVisible": 0}
    try:
        pOurPlayer = gc.getPlayer(ourPlayerID)
        ourTeam = pOurPlayer.getTeam()

        for i in range(gc.getMAX_CIV_PLAYERS()):
            if i == ourPlayerID:
                continue
            pLoop = gc.getPlayer(i)
            if not pLoop.isAlive():
                continue

            visible_units = []
            (pUnit, iter) = pLoop.firstUnit(False)
            while pUnit:
                try:
                    if not pUnit.isDead() and pUnit.isVisible(ourTeam, False):
                        visible_units.append({
                            "id": pUnit.getID(),
                            "owner": i,
                            "unitType": pUnit.getUnitType(),
                            "x": pUnit.getX(),
                            "y": pUnit.getY(),
                            "damage": pUnit.getDamage(),
                            "movesLeft": pUnit.getMoves(),
                        })
                        result["totalVisible"] += 1
                except:
                    pass
                (pUnit, iter) = pLoop.nextUnit(iter, False)

            if visible_units:
                result["byOwner"][str(i)] = {
                    "units": visible_units,
                    "summary": "%d visible units" % len(visible_units)
                }
    except Exception, e:
        print("HERMES: get_visible_enemy_units error: " + str(e))
    return result
```

## Helper 3: enhance_city_with_production(cityDict, pCity)

```python
def enhance_city_with_production(cityDict, pCity):
    """Mutates cityDict with production and growth info."""
    try:
        # Production
        prodName = ""
        turnsLeft = -1
        try:
            prodName = pCity.getProductionName()
            turnsLeft = pCity.getGeneralProductionTurnsLeft()
        except:
            pass

        cityDict["production"] = {
            "name": prodName,
            "turnsLeft": turnsLeft,
            "isBuildingUnit": prodName.lower().find("unit") != -1 or False
        }

        # Growth / Food
        try:
            foodPerTurn = pCity.getYieldRate(YieldTypes.YIELD_FOOD)
            foodStored = pCity.getFood()
            foodNeeded = pCity.growthThreshold()
            turnsToGrow = -1
            try:
                turnsToGrow = pCity.getFoodTurnsLeft()
            except:
                pass

            cityDict["growth"] = {
                "foodPerTurn": foodPerTurn,
                "foodStored": foodStored,
                "foodNeeded": foodNeeded,
                "turnsToGrow": turnsToGrow,
                "isStarving": foodPerTurn < 0
            }
        except:
            cityDict["growth"] = {}
    except:
        pass
    return cityDict
```

## Integration

In the main state builder:
```python
state = get_minimal_state(iPlayer)
state["diplo"] = get_diplo_snapshot(iPlayer)
state["visibleEnemies"] = get_visible_enemy_units(iPlayer)

# Enhance each city in the loop
for cityData in state.get("cities", []):
    # pCity available from your city iterator
    enhance_city_with_production(cityData, pCity)
```

Include new sections in both TCP path AND any file-callback state dumps.

## Py2.4 Footguns

- Wrap EVERY API call in try/except — C++ objects throw on missing methods
- isNone() guard on each deal before accessing it
- Never pass unicode to getInfoTypeForString — wrap in str()
- Never hasattr() on C++ objects — always try/except
- int() cast attitude with fallback
- Use _hermes_log / print for debugging since PythonDbg.log captures stdout