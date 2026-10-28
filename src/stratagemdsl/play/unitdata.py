"""Approximate combat numbers for the units StratagemDSL maps use (LotV, no upgrades).

Only `play.plansim` reads this table. It is a stand-in so that a simulated
fight has a plausible winner; it is not a balance reference. Damage is a
flat DPS per target class (no armour, bonuses only as a coarse "vs armored /
vs light" figure averaged in), splash and spells are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitStats:
    hp: float
    shield: float = 0.0
    dps_ground: float = 0.0
    dps_air: float = 0.0
    range_ground: float = 0.0
    range_air: float = 0.0
    speed: float = 3.15          # cells per second (faster game speed)
    radius: float = 0.5
    air: bool = False
    structure: bool = False
    sight: float = 9.0
    energy: float = 0.0


def _u(hp, shield=0.0, dg=0.0, da=0.0, rg=0.0, ra=0.0, speed=3.15, radius=0.5, sight=9.0, energy=0.0):
    return UnitStats(hp, shield, dg, da, rg, ra, speed, radius, False, False, sight, energy)


def _air(hp, shield=0.0, dg=0.0, da=0.0, rg=0.0, ra=0.0, speed=3.85, radius=0.75, sight=10.0, energy=0.0):
    return UnitStats(hp, shield, dg, da, rg, ra, speed, radius, True, False, sight, energy)


def _s(hp, shield=0.0, dg=0.0, da=0.0, rg=0.0, ra=0.0, radius=1.5, sight=9.0):
    return UnitStats(hp, shield, dg, da, rg, ra, 0.0, radius, False, True, sight, 0.0)


MELEE = 0.6

STATS: dict[str, UnitStats] = {
    # ------------------------------------------------------------------ Protoss
    "Probe": _u(20, 20, 4.7, 0, MELEE, 0, 3.94, 0.375, 8),
    "Zealot": _u(100, 50, 18.6, 0, MELEE, 0, 3.15, 0.5),
    "Stalker": _u(80, 80, 11.0, 11.0, 6, 6, 4.13, 0.625, 10),
    "Adept": _u(70, 70, 9.0, 0, 4, 0, 3.5, 0.5),
    "Sentry": _u(40, 40, 8.4, 8.4, 5, 5, 3.15, 0.5, 10, 50),
    "HighTemplar": _u(40, 40, 3.2, 0, 6, 0, 2.62, 0.375, 10, 50),
    "DarkTemplar": _u(40, 80, 37.2, 0, MELEE, 0, 3.94, 0.375, 8),
    "Archon": _u(10, 350, 20.0, 20.0, 3, 3, 3.94, 1.0),
    "Immortal": _u(200, 100, 30.0, 0, 6, 0, 3.15, 0.75),
    "Colossus": _u(200, 150, 18.7, 0, 7, 0, 3.15, 1.0, 10),
    "Disruptor": _u(100, 100, 0, 0, 0, 0, 3.15, 0.5),
    "Observer": _air(40, 30, speed=2.63, radius=0.5, sight=11),
    "WarpPrism": _air(80, 100, speed=4.13, radius=0.875),
    "Phoenix": _air(120, 60, 0, 12.7, 0, 5, 5.95),
    "VoidRay": _air(150, 100, 16.8, 16.8, 6, 6, 3.85, 1.0),
    "Oracle": _air(100, 60, 24.4, 0, 4, 0, 5.6, 0.75, energy=50),
    "Tempest": _air(200, 150, 12.0, 12.0, 10, 14, 3.15, 1.25),
    "Carrier": _air(300, 150, 37.4, 37.4, 8, 8, 2.62, 1.25, 12),
    "Mothership": _air(350, 350, 22.8, 22.8, 7, 7, 2.62, 1.375, 14, 50),
    "Nexus": _s(1000, 1000, radius=2.75, sight=11),
    "Pylon": _s(200, 200, radius=1.0),
    "Gateway": _s(500, 500, radius=1.75),
    "WarpGate": _s(500, 500, radius=1.75),
    "Forge": _s(400, 400, radius=1.75),
    "CyberneticsCore": _s(550, 550, radius=1.75),
    "Assimilator": _s(450, 450, radius=1.75),
    "PhotonCannon": _s(150, 150, 22.4, 22.4, 7, 7, radius=1.0, sight=11),
    "ShieldBattery": _s(150, 150, radius=1.0),
    # ------------------------------------------------------------------ Terran
    "SCV": _u(45, 0, 4.7, 0, MELEE, 0, 3.94, 0.375, 8),
    "MULE": _u(60, 0, 0, 0, 0, 0, 3.94, 0.375, 8),
    "Marine": _u(45, 0, 9.8, 9.8, 5, 5, 3.15, 0.375),
    "Marauder": _u(125, 0, 14.0, 0, 6, 0, 3.15, 0.5625, 10),
    "Reaper": _u(60, 0, 10.1, 0, 5, 0, 5.25, 0.375),
    "Ghost": _u(100, 0, 9.3, 9.3, 6, 6, 3.94, 0.375, 11, 75),
    "Hellion": _u(90, 0, 8.0, 0, 5, 0, 5.95, 0.625, 10),
    "HellionTank": _u(135, 0, 18.0, 0, 2, 0, 3.15, 0.625, 10),
    "SiegeTank": _u(175, 0, 20.3, 0, 7, 0, 3.15, 0.875, 11),
    "SiegeTankSieged": UnitStats(175, 0, 30.0, 0, 13, 0, 0.0, 0.875, False, False, 11),
    "Cyclone": _u(120, 0, 22.0, 22.0, 5, 5, 4.13, 0.75, 11),
    "WidowMine": _u(90, 0, 0, 0, 0, 0, 3.94, 0.5, 7),
    "WidowMineBurrowed": UnitStats(90, 0, 40.0, 40.0, 5, 5, 0.0, 0.5, False, False, 7),
    "Thor": _u(400, 0, 65.9, 11.2, 7, 10, 2.62, 1.25, 11),
    "VikingFighter": _air(135, 0, 0, 14.0, 0, 9, 3.85),
    "VikingAssault": _u(135, 0, 16.8, 0, 6, 0, 3.15, 0.75, 10),
    "Medivac": _air(150, 0, speed=3.5, energy=50),
    "Liberator": _air(180, 0, 0, 7.8, 0, 5, 4.72),
    "Raven": _air(140, 0, speed=3.85, sight=11, energy=50),
    "Banshee": _air(140, 0, 27.0, 0, 6, 0, 3.85, energy=50),
    "Battlecruiser": _air(550, 0, 50.0, 31.0, 6, 6, 2.62, 1.25, 12),
    "CommandCenter": _s(1500, radius=2.75, sight=11),
    "OrbitalCommand": _s(1500, radius=2.75, sight=11),
    "PlanetaryFortress": _s(1500, 0, 28.0, 0, 6, 0, radius=2.75, sight=11),
    "SupplyDepot": _s(400, radius=1.0),
    "SupplyDepotLowered": _s(400, radius=1.0),
    "Barracks": _s(1000, radius=1.75),
    "Factory": _s(1250, radius=1.75),
    "Starport": _s(1300, radius=1.75),
    "Bunker": _s(400, 0, 39.2, 39.2, 6, 6, radius=1.5, sight=10),
    "MissileTurret": _s(250, 0, 0, 39.4, 0, 7, radius=1.0, sight=11),
    "Refinery": _s(500, radius=1.75),
    "EngineeringBay": _s(850, radius=1.75),
    # ------------------------------------------------------------------ Zerg
    "Drone": _u(40, 0, 4.7, 0, MELEE, 0, 3.94, 0.375, 8),
    "Larva": UnitStats(25, 0, 0, 0, 0, 0, 0.0, 0.25, False, False, 5),
    "Zergling": _u(35, 0, 10.0, 0, MELEE, 0, 4.13, 0.375, 8),
    "Baneling": _u(30, 0, 25.0, 0, MELEE, 0, 3.5, 0.375, 8),
    "Roach": _u(145, 0, 11.2, 0, 4, 0, 3.15, 0.625),
    "RoachBurrowed": UnitStats(145, 0, 0, 0, 0, 0, 0.0, 0.625, False, False, 4),
    "Ravager": _u(120, 0, 14.0, 0, 6, 0, 3.85, 0.75),
    "Hydralisk": _u(90, 0, 22.4, 22.4, 5, 5, 3.15, 0.625),
    "Lurker": _u(200, 0, 0, 0, 0, 0, 4.13, 0.9375, 10),
    "LurkerBurrowed": UnitStats(200, 0, 20.0, 0, 8, 0, 0.0, 0.9375, False, False, 10),
    "Infestor": _u(90, 0, 0, 0, 0, 0, 3.15, 0.75, 10, 50),
    "SwarmHostMP": _u(160, 0, 0, 0, 0, 0, 3.15, 0.8125, 10),
    "Ultralisk": _u(500, 0, 57.4, 0, MELEE + 0.4, 0, 4.13, 1.0),
    "Queen": _u(175, 0, 11.2, 12.6, 5, 7, 1.31, 0.875, 9, 25),
    "Mutalisk": _air(120, 0, 8.6, 8.6, 3, 3, 5.6, 0.5, 11),
    "Corruptor": _air(200, 0, 0, 10.3, 0, 6, 4.73),
    "BroodLord": _air(225, 0, 11.2, 0, 10, 0, 1.97, 1.0, 12),
    "Viper": _air(150, 0, speed=4.13, sight=11, energy=50),
    "Overlord": _air(200, 0, speed=0.9, radius=1.0, sight=11),
    "Overseer": _air(200, 0, speed=2.62, radius=1.0, sight=11, energy=50),
    "Hatchery": _s(1500, radius=2.75, sight=12),
    "Lair": _s(2000, radius=2.75, sight=12),
    "Hive": _s(2500, radius=2.75, sight=12),
    "SpawningPool": _s(1000, radius=1.75),
    "EvolutionChamber": _s(750, radius=1.75),
    "Extractor": _s(500, radius=1.75),
    "SpineCrawler": _s(300, 0, 18.9, 0, 7, 0, radius=1.0, sight=11),
    "SporeCrawler": _s(400, 0, 0, 24.4, 0, 7, radius=1.0, sight=11),
    "NydusNetwork": _s(850, radius=1.75),
    "NydusCanal": _s(300, radius=1.0),
    "CreepTumor": _s(50, radius=0.5, sight=10),
}

DEFAULT_UNIT = _u(100, 0, 8.0, 0, 4, 0)
DEFAULT_STRUCTURE = _s(500)

# morphs the simulator models: (from, ability keyword) -> to
MORPHS = {
    ("SiegeTank", "siegemode"): "SiegeTankSieged",
    ("SiegeTankSieged", "unsiege"): "SiegeTank",
    ("Hellion", "hellbat"): "HellionTank",
    ("HellionTank", "hellion"): "Hellion",
    ("VikingFighter", "assaultmode"): "VikingAssault",
    ("VikingAssault", "fightermode"): "VikingFighter",
    ("SupplyDepot", "lower"): "SupplyDepotLowered",
    ("SupplyDepotLowered", "raise"): "SupplyDepot",
    ("WidowMine", "burrowdown"): "WidowMineBurrowed",
    ("WidowMineBurrowed", "burrowup"): "WidowMine",
    ("Roach", "burrowdown"): "RoachBurrowed",
    ("RoachBurrowed", "burrowup"): "Roach",
    ("Lurker", "burrowdown"): "LurkerBurrowed",
    ("LurkerBurrowed", "burrowup"): "Lurker",
}


# armour (hit points only; shields take full damage) and damage per attack, for the units that have it
ARMOR = {"Zealot": 1, "Stalker": 1, "Immortal": 1, "Colossus": 1, "Archon": 0, "Roach": 1, "Ravager": 1,
         "Queen": 1, "Lurker": 1, "Ultralisk": 2, "Marauder": 1, "SiegeTank": 1, "SiegeTankSieged": 1, "Thor": 1,
         "Battlecruiser": 3, "Carrier": 2, "Tempest": 2, "Cyclone": 1, "BroodLord": 1, "Corruptor": 2, "Viper": 1,
         "Mutalisk": 1, "Overlord": 0}
HIT = {"Zergling": 5, "Marine": 6, "Zealot": 8, "Stalker": 13, "Adept": 10, "Roach": 16, "Hydralisk": 12,
       "Baneling": 16, "Hellion": 8, "HellionTank": 18, "Immortal": 20, "Colossus": 10, "Marauder": 10,
       "Queen": 4, "Mutalisk": 9, "SpineCrawler": 25, "PhotonCannon": 20, "Probe": 5, "SCV": 5, "Drone": 5,
       "DarkTemplar": 45, "Ultralisk": 35, "Archon": 25, "SiegeTank": 15, "SiegeTankSieged": 40, "Ravager": 16,
       "Reaper": 4, "Ghost": 10, "Thor": 30, "VoidRay": 6, "Phoenix": 5, "Oracle": 15, "Banshee": 12,
       "Battlecruiser": 8, "Carrier": 5, "Bunker": 6, "PlanetaryFortress": 40, "Sentry": 6}
STRUCTURE_ARMOR = 1


def armor_of(unit_type: str, structure: bool) -> float:
    return float(ARMOR.get(unit_type, STRUCTURE_ARMOR if structure else 0))


def hit_of(unit_type: str) -> float:
    return float(HIT.get(unit_type, 10))


# burrowing keeps a unit's numbers but the game reports another unit type
BURROWED_NAME = {"Zergling": "ZerglingBurrowed", "Baneling": "BanelingBurrowed", "Hydralisk": "HydraliskBurrowed",
                 "Drone": "DroneBurrowed", "Infestor": "InfestorBurrowed", "Ultralisk": "UltraliskBurrowed",
                 "Queen": "QueenBurrowed", "Ravager": "RavagerBurrowed", "SwarmHostMP": "SwarmHostBurrowedMP"}
UNBURROWED_NAME = {v: k for k, v in BURROWED_NAME.items()}


def stats_of(unit_type: str, structure_hint: bool = False) -> UnitStats:
    if unit_type in STATS:
        return STATS[unit_type]
    return DEFAULT_STRUCTURE if structure_hint else DEFAULT_UNIT
