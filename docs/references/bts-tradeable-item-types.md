# BTS Tradeable Item Types (CvEnums.h)

These are the enum values for `TradeableItems` used in deal iteration. Needed for `_format_trade_item()` and deal type classification in state enrichment.

## Enum Values

| ID | Name | Description |
|----|------|-------------|
| 0 | TRADE_TECHNOLOGIES | Offering a specific tech (data=techID) |
| 1 | TRADE_RESOURCES | Offering a resource/bonus (data=bonusID) |
| 2 | TRADE_GOLD | Lump sum gold (data=amount) |
| 3 | TRADE_GOLD_PER_TURN | Gold per turn (data=amount) |
| 4 | TRADE_MAPS | World map exchange (data=0) |
| 5 | TRADE_VASSAL | Offer to become vassal state |
| 6 | TRADE_SURRENDER | Unconditional surrender |
| 7 | TRADE_OPEN_BORDERS | Open borders treaty (data=0) |
| 8 | TRADE_DEFENSIVE_PACT | Defensive pact agreement |
| 9 | TRADE_PERMANENT_ALLIANCE | Permanent alliance offer |
| 10 | TRADE_PEACE | Peace treaty / force peace with third party (data=playerID) |
| 11 | TRADE_WORKER | Worker/slave labor (not commonly used) |
| 12 | TRADE_MILITARY_UNIT | Military unit gift (not commonly used) |
| 13 | TRADE_CITY | City in trade (data=cityID) |
| 14 | TRADE_EMBASSY | Establish embassy |
| 15 | TRADE_CONTACT | Contact with a third civ (data=playerID) |
| 16 | TRADE_CORPORATION | Corporation access (data=corpID) |
| 17 | TRADE_CIVIC | Civic change demand (data=civicID) |
| 18 | TRADE_RELIGION | Religion conversion (data=religionID) |

## Deal Type Classification Logic

```python
dt = "trade"  # default
for each item in trade:
    it = int(item.getItemType())
    if it == 7: dt = "openBorders"
    elif it == 10: dt = "peace"
    elif it == 5 or it == 6: dt = "vassal"
    # else stays "trade"
```

## _format_trade_item Implementation (Python 2.4)

```python
def _format_trade_item(item):
    try:
        t = int(item.getItemType()); d = item.getData()
        if t == 0: return "Tech_%d" % d
        if t == 1: return "Resource_%d" % d
        if t == 2: return "Gold_%d" % d
        if t == 3: return "GoldPerTurn_%d" % d
        if t == 4: return "Map"
        if t == 7: return "OpenBorders"
        if t == 10: return "Peace"
        if t == 13: return "City_%d" % d
        if t == 5: return "Vassal"
        if t == 6: return "Surrender"
        if t == 14: return "Embassy"
        if t == 15: return "Contact_%d" % d
        if t == 16: return "Corporation_%d" % d
        return "TradeItem_%d" % t
    except:
        return "Unknown"
```

## Deal Iteration Pattern (Safe)

```python
g = gc.getGame()
for di in range(g.getIndexAfterLastDeal()):
    deal = g.getDeal(di)
    if deal.isNone(): continue  # CRITICAL — invalid deals exist in the slot range
    fst = deal.getFirstPlayer()
    snd = deal.getSecondPlayer()
    # ... process items with try/except around each access
```

## Key Methods on CvDeal

- `deal.isNone()` — check before ANY access
- `deal.getFirstPlayer()` / `deal.getSecondPlayer()` — participant IDs
- `deal.getLengthFirstTrades()` — count of items first player is giving
- `deal.getLengthSecondTrades()` — count of items second player is giving
- `deal.getFirstTrade(j)` — CvTradeableItem from first player at index j
- `deal.getSecondTrade(j)` — CvTradeableItem from second player at index j

## Key Methods on CvTradeableItem

- `item.getItemType()` — returns TradeableItems enum value (int)
- `item.getData()` — secondary data (tech ID, gold amount, bonus ID, etc.)
