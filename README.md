# Eternum Prototype

This repository now contains a **playable CLI prototype** for the design direction captured in `docs/GDD_v3.md`.

## What is implemented

- NPC memory + mood/reputation shifts in dialogue
- A lightweight living world tick (time, weather, economy pressure, disease pressure)
- Faction standing impacts from conversation outcomes
- Turn-based D20-style combat loop (attack roll vs AC + damage)
- A tiny vertical slice entrypoint (`python -m game.main`)

## Run

```bash
python -m game.main
```

## Test

```bash
python -m unittest discover -s tests -v
```
