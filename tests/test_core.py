import tempfile
import unittest
from pathlib import Path

from game.core import Combat, Game, Mood, NPC, Character


class TestNPC(unittest.TestCase):
    def test_npc_memory_is_bounded(self):
        npc = NPC("A", "Ironveil Compact", "worker", "s", "w", "f", {"loyal": 5})
        for i in range(60):
            npc.remember(f"event-{i}")
        self.assertEqual(len(npc.memory), 50)
        self.assertEqual(npc.memory[0], "event-10")

    def test_helpful_dialogue_improves_mood(self):
        npc = NPC("A", "Ironveil Compact", "worker", "s", "w", "f", {"loyal": 5})
        text = npc.react_to_player("I will help you")
        self.assertIn("trusts you more", text)
        self.assertEqual(npc.mood, Mood.FRIENDLY)


class TestWorldAndSystems(unittest.TestCase):
    def test_rest_advances_time(self):
        game = Game(seed=1)
        before = (game.world.day, game.world.hour)
        game.rest()
        after = (game.world.day, game.world.hour)
        self.assertNotEqual(before, after)

    def test_trade_moves_market(self):
        game = Game(seed=1)
        old_price = game.world.economy.grain_price
        game.trade("grain", 10)
        self.assertGreaterEqual(game.world.economy.grain_price, old_price)

    def test_crime_creates_bounty_and_record(self):
        game = Game(seed=1)
        msg = game.commit_crime("robbed caravan")
        self.assertIn("Bounty", msg)
        self.assertGreater(game.world.law.bounty, 0)
        self.assertEqual(len(game.world.law.criminal_record), 1)

    def test_taming_progression(self):
        game = Game(seed=1)
        game.tame_beast("observe")
        game.tame_beast("approach")
        final = game.tame_beast("trust")
        self.assertIn("Bond formed", final)
        self.assertIsNotNone(game.beast)
        self.assertEqual(game.beast.taming_stage, 3)

    def test_boss_negotiation_requires_standing(self):
        game = Game(seed=1)
        fail = game.boss_encounter("negotiate")
        self.assertIn("fails", fail)
        game.world.factions["Thornroot Covenant"].standing = 2
        success = game.boss_encounter("negotiate")
        self.assertIn("broker a pact", success)

    def test_save_and_load_roundtrip(self):
        game = Game(seed=1)
        game.commit_crime("poaching")
        game.tame_beast("observe")
        game.tame_beast("approach")
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "save.json"
            game.save(p)
            loaded = Game.load(p)
        self.assertEqual(loaded.world.law.bounty, game.world.law.bounty)
        self.assertIsNotNone(loaded.beast)
        self.assertEqual(loaded.beast.taming_stage, 2)


class TestCombat(unittest.TestCase):
    def test_combat_finishes_with_result(self):
        party = [Character("P", 20, 12, 4, (2, 5))]
        enemies = [Character("E", 8, 10, 2, (1, 3))]
        combat = Combat(party, enemies, seed=2)
        result = combat.run()
        self.assertIn(result, {"party_victory", "party_defeat"})
        self.assertTrue(combat.log)


if __name__ == "__main__":
    unittest.main()
