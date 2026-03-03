from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import random
from pathlib import Path
from typing import Dict, List


class Mood(str, Enum):
    CALM = "calm"
    WARY = "wary"
    FRIENDLY = "friendly"
    HOSTILE = "hostile"


@dataclass
class Identity:
    name: str
    race: str
    role_class: str
    faith: str
    faction: str


@dataclass
class NPC:
    name: str
    faction: str
    social_class: str
    secret: str
    want: str
    fear: str
    traits: Dict[str, int]
    mood: Mood = Mood.CALM
    memory: List[str] = field(default_factory=list)
    reputation_with_player: int = 0

    def remember(self, event: str) -> None:
        self.memory.append(event)
        self.memory = self.memory[-50:]

    def react_to_player(self, player_line: str) -> str:
        self.remember(f"Player: {player_line}")
        lower = player_line.lower()
        if any(k in lower for k in ["help", "protect", "support", "aid"]):
            self.reputation_with_player += 5
            self.mood = Mood.FRIENDLY
            return f"{self.name} trusts you more and leaks a rumor: {self.secret}."
        if any(k in lower for k in ["threat", "pay", "extort", "bribe"]):
            self.reputation_with_player -= 7
            self.mood = Mood.WARY if self.reputation_with_player > -15 else Mood.HOSTILE
            return f"{self.name} pulls back. You feel social consequences building."
        return f"{self.name} considers your words, offering little for now."


@dataclass
class Companion:
    name: str
    approval: int = 0
    trust: int = 0
    bond: int = 0


@dataclass
class Beast:
    species: str
    temper: str
    taming_stage: int = 0  # 0 observe -> 1 approach -> 2 trust -> 3 bonded


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
    wing_scores: Dict[str, int] = field(default_factory=dict)


@dataclass
class EconomyState:
    grain_price: int = 10
    fish_price: int = 7
    iron_price: int = 12
    food_supply: int = 100


@dataclass
class EcologyState:
    predators: int = 40
    herbivores: int = 70
    vegetation: int = 100
    blight: int = 0


@dataclass
class DiseaseState:
    pressure: int = 0
    outbreak: bool = False


@dataclass
class LawState:
    bounty: int = 0
    criminal_record: List[str] = field(default_factory=list)


@dataclass
class MythState:
    legend: int = 0
    titles: List[str] = field(default_factory=list)


@dataclass
class WorldState:
    day: int = 1
    hour: int = 8
    season: str = "Spring"
    weather: str = "clear"
    economy: EconomyState = field(default_factory=EconomyState)
    ecology: EcologyState = field(default_factory=EcologyState)
    disease: DiseaseState = field(default_factory=DiseaseState)
    law: LawState = field(default_factory=LawState)
    myth: MythState = field(default_factory=MythState)
    factions: Dict[str, FactionState] = field(default_factory=dict)

    def tick(self, rng: random.Random, hours: int = 8) -> List[str]:
        logs: List[str] = []
        self.hour += hours
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
            logs.extend(self._daily_update(rng))
        return logs

    def _daily_update(self, rng: random.Random) -> List[str]:
        logs: List[str] = []
        self.season = ["Spring", "Summer", "Autumn", "Winter"][(self.day // 30) % 4]
        self.weather = rng.choice(["clear", "rain", "fog", "storm", "snow"])

        # Economy reacts to ecology + weather + disease
        eco = self.ecology
        econ = self.economy
        dis = self.disease
        econ.food_supply = max(0, econ.food_supply + (eco.vegetation // 25) - dis.pressure)
        econ.grain_price = max(2, econ.grain_price + (5 if self.weather in {"storm", "snow"} else 0) - econ.food_supply // 80)
        econ.fish_price = max(2, econ.fish_price + rng.randint(-1, 2) + (1 if self.weather == "storm" else 0))
        econ.iron_price = max(4, econ.iron_price + rng.randint(-1, 1))

        # Ecology loop
        eco.herbivores = max(0, eco.herbivores + (eco.vegetation // 40) - (eco.predators // 25) - eco.blight)
        eco.predators = max(0, eco.predators + (eco.herbivores // 50) - 1)
        eco.vegetation = max(0, eco.vegetation + 4 - (eco.herbivores // 20) - eco.blight)
        if self.weather == "storm" and rng.random() < 0.2:
            eco.blight += 1
            logs.append("Blight worsened after storms.")

        # Disease
        dis.pressure = max(0, dis.pressure + rng.randint(-1, 2) + (1 if econ.food_supply < 60 else 0))
        dis.outbreak = dis.pressure >= 8
        if dis.outbreak:
            logs.append("Outbreak warning: healers request aid.")

        # Temporal faction and myth drift
        for faction in self.factions.values():
            for wing in faction.wing_scores:
                faction.wing_scores[wing] += rng.randint(-1, 1)
        if self.day % 14 == 0 and self.myth.legend >= 10 and "River-Name" not in self.myth.titles:
            self.myth.titles.append("River-Name")
            logs.append("Bards spread your title: River-Name.")

        return logs


class Combat:
    def __init__(self, party: List[Character], enemies: List[Character], seed: int | None = None):
        self.party = party
        self.enemies = enemies
        self.rng = random.Random(seed)
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

    def run(self, max_rounds: int = 20) -> str:
        for round_num in range(1, max_rounds + 1):
            if not any(c.alive for c in self.party) or not any(e.alive for e in self.enemies):
                break
            self.log.append(f"-- Round {round_num} --")
            for hero in [c for c in self.party if c.alive]:
                targets = [e for e in self.enemies if e.alive]
                if targets:
                    self._attack(hero, targets[0])
            for foe in [e for e in self.enemies if e.alive]:
                targets = [c for c in self.party if c.alive]
                if targets:
                    self._attack(foe, targets[0])

        result = "party_victory" if any(c.alive for c in self.party) else "party_defeat"
        self.log.append(result)
        return result


class Game:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.identity = Identity("Arin", "Human", "Ranger", "Soleth", "Free Cities League")
        self.world = WorldState(
            factions={
                "Ironveil Compact": FactionState("Ironveil Compact", 0, {"Hardliners": 3, "Pragmatists": 2}),
                "Thornroot Covenant": FactionState("Thornroot Covenant", 0, {"Wardens": 2, "Mystics": 2}),
                "Free Cities League": FactionState("Free Cities League", 0, {"Merchants": 2, "Reformers": 1}),
            }
        )
        self.npcs: Dict[str, NPC] = {
            "Mira": NPC(
                name="Mira",
                faction="Thornroot Covenant",
                social_class="artisan",
                secret="she shelters refugees beneath the granary",
                want="food stability",
                fear="an Ironveil purge",
                traits={"brave": 7, "greedy": 2, "loyal": 8},
            ),
            "Marshal Venn": NPC(
                name="Marshal Venn",
                faction="Ironveil Compact",
                social_class="noble",
                secret="he skims taxes to fund a private militia",
                want="order",
                fear="civil unrest",
                traits={"brave": 6, "greedy": 6, "loyal": 4},
            ),
        }
        self.companions: List[Companion] = [Companion("Tamsin", approval=5, trust=3)]
        self.beast: Beast | None = None
        self.trauma: Dict[str, int] = {"grief": 0, "guilt": 0, "paranoia": 0, "dissociation": 0}
        self.active_boss_alive: bool = True

    # ===== Player actions =====
    def talk(self, npc_name: str, line: str) -> str:
        npc = self.npcs[npc_name]
        response = npc.react_to_player(line)
        standing_delta = 0
        if npc.reputation_with_player >= 10:
            standing_delta = 2
        elif npc.reputation_with_player <= -10:
            standing_delta = -2
        self.world.factions[npc.faction].standing += standing_delta

        if standing_delta > 0:
            self.world.myth.legend += 1
        if standing_delta < 0:
            self.world.law.bounty += 5

        return response

    def rest(self) -> List[str]:
        logs = self.world.tick(self.rng, hours=8)
        if self.world.disease.outbreak:
            self.trauma["paranoia"] += 1
        return logs

    def trade(self, buy: str, amount: int) -> str:
        prices = {
            "grain": self.world.economy.grain_price,
            "fish": self.world.economy.fish_price,
            "iron": self.world.economy.iron_price,
        }
        if buy not in prices:
            return "Unknown good."
        market_swing = amount // 5
        if buy == "grain":
            self.world.economy.grain_price += market_swing
        elif buy == "fish":
            self.world.economy.fish_price += market_swing
        else:
            self.world.economy.iron_price += market_swing
        self.world.myth.legend += 1 if amount >= 10 else 0
        return f"You move {amount} units of {buy}; market reacts immediately."

    def commit_crime(self, action: str) -> str:
        self.world.law.bounty += 10
        self.world.law.criminal_record.append(action)
        self.world.myth.legend += 1
        self.trauma["guilt"] += 1
        return f"Crime recorded: {action}. Bounty is now {self.world.law.bounty}."

    def process_trauma(self, with_companion: bool = True) -> str:
        if with_companion and self.companions:
            comp = self.companions[0]
            comp.trust += 1
            comp.approval += 1
            for key in self.trauma:
                self.trauma[key] = max(0, self.trauma[key] - 1)
            return f"You open up to {comp.name}. Burdens lighten; trust deepens."
        return "No one is available to talk."

    def tame_beast(self, method: str) -> str:
        if self.beast is None:
            self.beast = Beast(species="Dusk Wolf", temper="wary", taming_stage=0)
        if method == "observe" and self.beast.taming_stage == 0:
            self.beast.taming_stage = 1
            return "You observe tracks and body language. Stage: Approach unlocked."
        if method == "approach" and self.beast.taming_stage == 1:
            self.beast.taming_stage = 2
            return "You approach with care. Stage: Trust-building unlocked."
        if method == "trust" and self.beast.taming_stage == 2:
            self.beast.taming_stage = 3
            self.world.myth.legend += 2
            return "Bond formed. The Dusk Wolf joins your camp."
        return "That method has no effect right now."

    def boss_encounter(self, stance: str) -> str:
        if not self.active_boss_alive:
            return "The frontier boss thread is resolved."

        if stance == "negotiate":
            standing = self.world.factions["Thornroot Covenant"].standing
            if standing >= 2:
                self.active_boss_alive = False
                self.world.myth.legend += 3
                return "You broker a pact with the Root-Titan. It withdraws from trade roads."
            return "Negotiation fails; you lack leverage with Thornroot mediators."

        party = [Character("Player", 28, 14, 5, (3, 8)), Character("Tamsin", 18, 13, 4, (2, 6))]
        enemies = [Character("Root-Titan", 30, 13, 5, (3, 9))]
        if self.beast and self.beast.taming_stage == 3:
            party.append(Character("Dusk Wolf", 16, 13, 4, (2, 5)))

        combat = Combat(party, enemies, seed=self.seed + self.world.day)
        result = combat.run()
        if result == "party_victory":
            self.active_boss_alive = False
            self.world.factions["Thornroot Covenant"].standing += 3
            self.world.myth.legend += 4
            return "Boss defeated. Frontier stabilizes."

        self.trauma["grief"] += 1
        self.world.law.bounty = max(0, self.world.law.bounty - 2)
        return "You were forced to retreat. The boss remembers you."

    # ===== Persistence =====
    def save(self, path: str | Path) -> None:
        payload = {
            "seed": self.seed,
            "identity": asdict(self.identity),
            "world": self._world_to_dict(),
            "npcs": {name: self._npc_to_dict(npc) for name, npc in self.npcs.items()},
            "companions": [asdict(c) for c in self.companions],
            "beast": asdict(self.beast) if self.beast else None,
            "trauma": self.trauma,
            "active_boss_alive": self.active_boss_alive,
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Game":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        game = cls(seed=raw["seed"])
        game.identity = Identity(**raw["identity"])
        game.world = cls._world_from_dict(raw["world"])
        game.npcs = {name: cls._npc_from_dict(data) for name, data in raw["npcs"].items()}
        game.companions = [Companion(**c) for c in raw["companions"]]
        game.beast = Beast(**raw["beast"]) if raw["beast"] else None
        game.trauma = {k: int(v) for k, v in raw["trauma"].items()}
        game.active_boss_alive = bool(raw["active_boss_alive"])
        return game

    @staticmethod
    def _npc_to_dict(npc: NPC) -> dict:
        data = asdict(npc)
        data["mood"] = npc.mood.value
        return data

    @staticmethod
    def _npc_from_dict(data: dict) -> NPC:
        data = dict(data)
        data["mood"] = Mood(data["mood"])
        return NPC(**data)

    def _world_to_dict(self) -> dict:
        return {
            "day": self.world.day,
            "hour": self.world.hour,
            "season": self.world.season,
            "weather": self.world.weather,
            "economy": asdict(self.world.economy),
            "ecology": asdict(self.world.ecology),
            "disease": asdict(self.world.disease),
            "law": asdict(self.world.law),
            "myth": asdict(self.world.myth),
            "factions": {k: asdict(v) for k, v in self.world.factions.items()},
        }

    @staticmethod
    def _world_from_dict(data: dict) -> WorldState:
        return WorldState(
            day=data["day"],
            hour=data["hour"],
            season=data["season"],
            weather=data["weather"],
            economy=EconomyState(**data["economy"]),
            ecology=EcologyState(**data["ecology"]),
            disease=DiseaseState(**data["disease"]),
            law=LawState(**data["law"]),
            myth=MythState(**data["myth"]),
            factions={k: FactionState(**v) for k, v in data["factions"].items()},
        )

    # ===== UI helpers =====
    def status_lines(self) -> List[str]:
        econ = self.world.economy
        eco = self.world.ecology
        return [
            f"Day {self.world.day} {self.world.hour:02d}:00 | {self.world.season} | weather={self.world.weather}",
            f"Economy: grain={econ.grain_price}, fish={econ.fish_price}, iron={econ.iron_price}, supply={econ.food_supply}",
            f"Ecology: predators={eco.predators}, herbivores={eco.herbivores}, vegetation={eco.vegetation}, blight={eco.blight}",
            f"Disease pressure={self.world.disease.pressure} outbreak={self.world.disease.outbreak}",
            f"Law bounty={self.world.law.bounty} crimes={len(self.world.law.criminal_record)}",
            f"Myth legend={self.world.myth.legend} titles={self.world.myth.titles or ['none']}",
            f"Trauma={self.trauma}",
            f"Boss alive={self.active_boss_alive}",
        ]
