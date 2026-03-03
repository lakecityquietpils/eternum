from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import random
from typing import Dict, List


class Mood(str, Enum):
    CALM = "calm"
    WARY = "wary"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"


@dataclass
class NPC:
    name: str
    secret: str
    want: str
    fear: str
    traits: Dict[str, int]
    faction: str
    mood: Mood = Mood.CALM
    memory: List[str] = field(default_factory=list)
    reputation_with_player: int = 0

    def remember(self, event: str) -> None:
        self.memory.append(event)
        # keep a bounded memory like the GDD target architecture
        self.memory = self.memory[-50:]

    def react_to_player(self, player_choice: str) -> str:
        self.remember(f"Player said: {player_choice}")
        if "help" in player_choice.lower() or "protect" in player_choice.lower():
            self.reputation_with_player += 5
            self.mood = Mood.FRIENDLY
            return f"{self.name} softens and shares a rumor about {self.secret}."
        if "threat" in player_choice.lower() or "pay" in player_choice.lower():
            self.reputation_with_player -= 7
            self.mood = Mood.WARY if self.reputation_with_player > -15 else Mood.HOSTILE
            return f"{self.name} recoils and refuses to trust you."
        return f"{self.name} listens, uncertain how to respond."


@dataclass
class Character:
    name: str
    hp: int
    ac: int
    attack_bonus: int
    damage_range: tuple[int, int]

    @property
    def alive(self) -> bool:
        return self.hp > 0


@dataclass
class FactionState:
    name: str
    standing: int = 0


@dataclass
class WorldState:
    day: int = 1
    hour: int = 8
    weather: str = "clear"
    grain_price: int = 10
    fish_price: int = 7
    disease_pressure: int = 0
    factions: Dict[str, FactionState] = field(default_factory=dict)

    def tick(self, hours: int = 8) -> None:
        self.hour += hours
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
            self._simulate_daily_changes()

    def _simulate_daily_changes(self) -> None:
        # minimal economy + weather + disease simulation
        self.weather = random.choice(["clear", "rain", "fog", "storm"])
        self.grain_price = max(4, self.grain_price + random.randint(-1, 2))
        self.fish_price = max(3, self.fish_price + random.randint(-2, 1))
        self.disease_pressure = max(0, self.disease_pressure + random.randint(-1, 2))


class Combat:
    def __init__(self, party: List[Character], enemies: List[Character], rng_seed: int | None = None):
        self.party = party
        self.enemies = enemies
        self.rng = random.Random(rng_seed)
        self.log: List[str] = []

    def _attack(self, attacker: Character, target: Character) -> None:
        roll = self.rng.randint(1, 20)
        total = roll + attacker.attack_bonus
        if total >= target.ac:
            dmg = self.rng.randint(*attacker.damage_range)
            target.hp = max(0, target.hp - dmg)
            self.log.append(f"{attacker.name} hits {target.name} for {dmg}.")
        else:
            self.log.append(f"{attacker.name} misses {target.name}.")

    def run(self) -> str:
        round_num = 1
        while any(c.alive for c in self.party) and any(e.alive for e in self.enemies):
            self.log.append(f"-- Round {round_num} --")
            for hero in [c for c in self.party if c.alive]:
                targets = [e for e in self.enemies if e.alive]
                if not targets:
                    break
                self._attack(hero, targets[0])
            for enemy in [e for e in self.enemies if e.alive]:
                targets = [c for c in self.party if c.alive]
                if not targets:
                    break
                self._attack(enemy, targets[0])
            round_num += 1
            if round_num > 20:  # safety stop
                break

        if any(c.alive for c in self.party):
            result = "party_victory"
        else:
            result = "party_defeat"
        self.log.append(result)
        return result


class Game:
    def __init__(self, seed: int | None = 42):
        random.seed(seed)
        self.world = WorldState(
            factions={
                "Ironveil Compact": FactionState("Ironveil Compact", 0),
                "Thornroot Covenant": FactionState("Thornroot Covenant", 0),
            }
        )
        self.npcs = {
            "Mira": NPC(
                name="Mira",
                secret="she hides refugees beneath the granary",
                want="food stability for the district",
                fear="an Ironveil crackdown",
                traits={"brave": 7, "greedy": 2, "loyal": 8},
                faction="Thornroot Covenant",
            )
        }

    def talk(self, npc_name: str, choice: str) -> str:
        npc = self.npcs[npc_name]
        response = npc.react_to_player(choice)
        if npc.reputation_with_player >= 10:
            self.world.factions[npc.faction].standing += 2
        elif npc.reputation_with_player <= -10:
            self.world.factions[npc.faction].standing -= 2
        return response

    def rest(self) -> None:
        self.world.tick(hours=8)

    def sample_combat(self) -> tuple[str, List[str]]:
        party = [
            Character("Player", hp=26, ac=14, attack_bonus=5, damage_range=(3, 8)),
            Character("Scout", hp=18, ac=13, attack_bonus=4, damage_range=(2, 6)),
        ]
        enemies = [
            Character("Bandit", hp=14, ac=12, attack_bonus=3, damage_range=(2, 5)),
            Character("Raider", hp=16, ac=12, attack_bonus=3, damage_range=(2, 5)),
        ]
        combat = Combat(party, enemies, rng_seed=7)
        return combat.run(), combat.log
