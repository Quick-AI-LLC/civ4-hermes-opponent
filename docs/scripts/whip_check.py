#!/usr/bin/env python3
"""
whip_check.py – Helper script to evaluate whipping opportunities.

Given a city's current build item, food surplus, and population, this
script calculates whether whipping the current build completes it early,
and reports the expected hammers gained.

Typical usage from a skill implementation:
    output = subprocess.run(
        ["python3", "scripts/whip_check.py", str(city_id), str(current_build_cost_hammers)],
        capture_output=True, text=True
    )
    # Parse JSON output for whip_actions list
"""

import sys
import json
from typing import Dict, List


def calculate_whip(city_id: int, build_hammers: int) -> List[str]:
    """
    Return a list of 'cityID:hammers_gained' strings for logging.

    This simplified model assumes:
      - Food surplus = 5 (arbitrary threshold for demo)
      - Population loss on whip = 1
    In a real implementation you would query the city's actual food,
    population, and production cost.
    """
    if city_id is None or build_hammers is None:
        return []

    # Demo logic – replace with real game state checks
    food_surplus = 5  # placeholder; actual check would examine city food
    population_loss = 1  # placeholder

    # Deterministic output for testing
    hammers_gained = min(build_hammers * 2, 120)  # cap at 120 for demo
    return [f"{city_id}:{hammers_gained}"]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(json.dumps({"error": "usage: whip_check.py <city_id> <build_hammers>"}))
        sys.exit(1)

    city_id = int(sys.argv[1])
    build_hammers = int(sys.argv[2])
    result = calculate_whip(city_id, build_hammers)
    print(json.dumps(result))