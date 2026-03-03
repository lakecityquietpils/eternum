# Eternum Prototype

This repository contains a **playable interactive CLI RPG prototype** inspired by the full vision in `docs/GDD_v3.md`.

> Note: the GDD describes a massive production-scale game. This prototype implements a broad vertical slice of interconnected systems in a single-player terminal experience.

## Implemented systems (prototype)

- Identity seed (race/class/faith/faction)
- NPC memory, mood, and relationship shifts
- Faction standings + internal wing power drift
- World calendar and temporal simulation
- Economy simulation (supply/demand + market reactions)
- Ecology simulation (predator/prey/vegetation/blight)
- Disease pressure + outbreak flags
- Law and criminal record with bounties
- Myth/legend progression and title unlocks
- Companion trust/approval and trauma processing
- Multi-stage beast taming
- Boss resolution via combat or negotiation
- Save/load game state to JSON

## Run

```bash
python -m game.main
```

## Core commands in game

- `status`
- `talk <NPC> <line>`
- `rest`
- `trade <grain|fish|iron> <amount>`
- `crime <description>`
- `trauma`
- `tame <observe|approach|trust>`
- `boss <fight|negotiate>`
- `save [path]`
- `load [path]`
- `help`
- `quit`

## Test

```bash
python -m unittest discover -s tests -v
```
