from game.core import Game


def main() -> None:
    game = Game(seed=42)

    print("=== Infinitum Prototype Slice ===")
    print(f"Day {game.world.day}, {game.world.hour}:00, weather: {game.world.weather}")

    print("\nYou meet Mira in the market district.")
    player_line = "I will help protect your people."
    print(f"> {player_line}")
    print(game.talk("Mira", player_line))

    game.rest()
    print(
        f"\nAfter resting: Day {game.world.day}, {game.world.hour}:00, "
        f"weather={game.world.weather}, grain={game.world.grain_price}, disease={game.world.disease_pressure}"
    )

    result, log = game.sample_combat()
    print("\nCombat preview:")
    for entry in log[:8]:
        print(f" - {entry}")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
