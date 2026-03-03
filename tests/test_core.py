import unittest

from game.core import Game, NPC, Mood, Character, Combat


class TestNPC(unittest.TestCase):
    def test_npc_memory_is_bounded(self):
        npc = NPC("A", "s", "w", "f", {"loyal": 5}, "Ironveil")
        for i in range(60):
            npc.remember(f"event-{i}")
        self.assertEqual(len(npc.memory), 50)
        self.assertEqual(npc.memory[0], "event-10")

    def test_helpful_dialogue_improves_mood(self):
        npc = NPC("A", "s", "w", "f", {"loyal": 5}, "Ironveil")
        text = npc.react_to_player("I will help you")
        self.assertIn("shares a rumor", text)
        self.assertEqual(npc.mood, Mood.FRIENDLY)


class TestWorldAndCombat(unittest.TestCase):
    def test_rest_advances_time(self):
        game = Game(seed=1)
        before = (game.world.day, game.world.hour)
        game.rest()
        after = (game.world.day, game.world.hour)
        self.assertNotEqual(before, after)

    def test_combat_finishes_with_result(self):
        party = [Character("P", 20, 12, 4, (2, 5))]
        enemies = [Character("E", 8, 10, 2, (1, 3))]
        combat = Combat(party, enemies, rng_seed=2)
        result = combat.run()
        self.assertIn(result, {"party_victory", "party_defeat"})
        self.assertTrue(combat.log)


if __name__ == "__main__":
    unittest.main()
