from __future__ import annotations

from pathlib import Path

from game.core import Game


def print_help() -> None:
    print(
        """
Commands:
  status                              Show world/system status
  talk <NPC> <line>                   Talk to an NPC (Mira, Marshal Venn)
  rest                                Long rest (+8h) and advance world systems
  trade <grain|fish|iron> <amount>    Move market supply/demand
  crime <description>                 Commit crime and trigger law/myth effects
  trauma                              Process trauma through camp conversation
  tame <observe|approach|trust>       Progress beast taming stages
  boss <fight|negotiate>              Resolve boss thread by combat or diplomacy
  save [path]                         Save game JSON (default: savegame.json)
  load [path]                         Load game JSON (default: savegame.json)
  help                                Show this help
  quit                                Exit game
""".strip()
    )


def main() -> None:
    game = Game(seed=42)
    print("=== Eternum: Living World CLI ===")
    print("A deeper systems prototype inspired by the GDD.")
    print_help()

    while True:
        raw = input("\n> ").strip()
        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "quit":
            print("Farewell, traveler.")
            break

        if cmd == "help":
            print_help()
            continue

        if cmd == "status":
            for line in game.status_lines():
                print(line)
            continue

        if cmd == "talk":
            if len(parts) < 3:
                print("Usage: talk <NPC> <line>")
                continue
            npc = parts[1]
            if npc not in game.npcs:
                print(f"Unknown NPC '{npc}'. Try: {', '.join(game.npcs.keys())}")
                continue
            line = raw.split(maxsplit=2)[2]
            print(game.talk(npc, line))
            continue

        if cmd == "rest":
            logs = game.rest()
            print("You rest. Time passes and the world changes.")
            for event in logs:
                print(f" - {event}")
            continue

        if cmd == "trade":
            if len(parts) != 3 or not parts[2].isdigit():
                print("Usage: trade <grain|fish|iron> <amount>")
                continue
            print(game.trade(parts[1], int(parts[2])))
            continue

        if cmd == "crime":
            if len(parts) < 2:
                print("Usage: crime <description>")
                continue
            print(game.commit_crime(raw.split(maxsplit=1)[1]))
            continue

        if cmd == "trauma":
            print(game.process_trauma(with_companion=True))
            continue

        if cmd == "tame":
            if len(parts) != 2:
                print("Usage: tame <observe|approach|trust>")
                continue
            print(game.tame_beast(parts[1]))
            continue

        if cmd == "boss":
            if len(parts) != 2 or parts[1] not in {"fight", "negotiate"}:
                print("Usage: boss <fight|negotiate>")
                continue
            stance = "negotiate" if parts[1] == "negotiate" else "fight"
            print(game.boss_encounter(stance))
            continue

        if cmd == "save":
            path = Path(parts[1]) if len(parts) > 1 else Path("savegame.json")
            game.save(path)
            print(f"Saved to {path}")
            continue

        if cmd == "load":
            path = Path(parts[1]) if len(parts) > 1 else Path("savegame.json")
            if not path.exists():
                print(f"No save found at {path}")
                continue
            game = Game.load(path)
            print(f"Loaded from {path}")
            continue

        print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
