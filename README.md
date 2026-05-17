# PROJECT ECHO

> *"Something is alive in there. We don't fully understand it yet."*

---

PROJECT ECHO is a real-time artificial life simulation built in Python and Pygame.
It is not a game. It is an observation chamber.

Inside, digital organisms — called **Echoes** — move, hunger, rest, and seek each other out.
No script tells them what to do. No designer placed them where they stand.
Their behavior emerges entirely from a handful of simple internal rules interacting with each other and their environment.

Watch long enough and patterns will appear. Clusters form. Individuals diverge.
Some never stop moving. Some disappear quietly into stillness.

You are the observer. The system runs without you.

---

## Features

### Currently Implemented

- **Autonomous creatures** — each Echo acts independently, driven by internal state
- **Vital systems** — every creature tracks `hunger`, `energy`, and `social` values in real time
- **Priority-based state machine** — `SEEK_FOOD` → `REST` → `SOCIALIZE` → `WANDER`
- **Reynolds Arrive steering** — smooth, physically-grounded movement toward targets
- **Reynolds Wander Circle** — organic, curving movement with no fixed destination
- **Idle states** — creatures pause spontaneously, stand still, then resume
- **Personality-based speed** — each Echo has a unique base speed assigned at birth
- **Energy modulation** — tired creatures move visibly slower
- **Hunger urgency** — hungry creatures steer faster and more directly toward food
- **Food system** — food spawns randomly, pulses, gets consumed, respawns
- **Event logging** — every state change, meal, idle pause, and social interaction is recorded
- **Statistics** — population-wide averages logged every 5 seconds to console and `log.txt`
- **ECHO-NN identity labels** — each creature carries a unique label rendered above it
- **Scanline overlay** — subtle retro atmosphere on the render surface

---

## Planned Features

The simulation is a living codebase. Extension hooks are already in place.

- **Memory system** — creatures remember past events: where they found food, who they met
- **Relationship graph** — affinity values between individual Echoes, built over time
- **Evolution and mutation** — heritable DNA traits passed on through reproduction with small mutations
- **Creature genealogy** — track lineages, parents, generations
- **Procedural tilemap worlds** — biomes, barriers, resources distributed across terrain
- **Dynamic ecosystems** — food density varies by region; creatures migrate and compete
- **Replay and timeline** — record a session and play it back
- **Observer mode** — click any creature to follow its full history in real time
- **Heatmaps** — visualize movement density, feeding zones, social clusters
- **Emergent intelligence** — behavioral complexity arising purely from accumulated simple rules

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Rendering | Pygame-CE 2.5+ |
| Architecture | Modular, data-driven |
| Output | Console + `log.txt` |

---

## Project Structure

```
PROJECT ECHO/
├── main.py        – Entry point. Pygame init, game loop, keyboard controls.
├── creature.py    – The Echo: state machine, steering, stats, event hooks, rendering.
├── world.py       – Simulation container. Spawning, spatial queries, food management.
├── food.py        – Food entity with pulsing glow animation.
├── logger.py      – Lightweight singleton logger. Events and periodic statistics.
├── settings.py    – Central configuration. Every tunable value lives here.
└── requirements.txt
```

### Key Design Decision

All simulation parameters live in `settings.py`. Speed, decay rates, thresholds, colors, spawn intervals — nothing is hardcoded. Tuning the simulation is a matter of changing one value in one place.

---

## Installation

```bash
pip install -r requirements.txt
python main.py
```

### Controls

| Key | Action |
|---|---|
| `ESC` | Quit |
| `SPACE` | Drop a food cluster at a random location |
| `D` | Toggle debug overlay (FPS, tick, population) |

---

## Philosophy

PROJECT ECHO is not built around scripted AI.

There are no behavior trees. No goal planners. No hand-authored sequences.
Each creature is given a small set of needs and a simple priority rule:
*survive first, rest when exhausted, seek company when lonely, otherwise wander.*

The rest emerges.

> *"Interesting behavior emerges from simple rules."*

When twelve independent agents with slightly different speeds, slightly different hunger tolerances, and slightly different personalities are placed in the same space — they stop being twelve separate entities. They become a system. They become something that looks, occasionally, like it is alive.

That is the goal: not to simulate intelligence, but to create the conditions under which something resembling it can appear on its own.

---

## Inspiration

PROJECT ECHO draws from a lineage of ideas:

- **Artificial life research** — Conway's Game of Life, Langton's Ant, Boids
- **Craig Reynolds** — steering behaviors, autonomous agents, emergent flocking
- **Cellular automata** — complex global patterns from local rules
- **Digital terrariums** — closed ecosystems observed, not controlled
- **Black Mirror** — technology that develops its own logic, indifferent to its creators
- **The question no one can cleanly answer** — at what point does simulation become something more?

---

## Roadmap

```
Phase 1 – Core Simulation          [COMPLETE]
─────────────────────────────────────────────
 Autonomous creatures
 Hunger / Energy / Social systems
 Steering behaviors
 Food system
 Event logging + statistics
 ECHO-NN identity

Phase 2 – Memory & Relationships   [NEXT]
─────────────────────────────────────────────
 Episodic memory per creature
 Relationship graph (affinity values)
 Creatures remember food locations
 Social bonds influence behavior

Phase 3 – Ecosystem                [PLANNED]
─────────────────────────────────────────────
 Tilemap world with biomes
 Resource distribution across terrain
 Population dynamics (birth, death)
 Heritable DNA + mutation

Phase 4 – Observer Systems         [PLANNED]
─────────────────────────────────────────────
 Click to follow individual creatures
 Creature history panel
 Heatmap overlays
 Session replay

Phase 5 – Emergent Intelligence    [UNKNOWN]
─────────────────────────────────────────────
 Learned behavior patterns
 Generational adaptation
 Collective memory
 ???
```

---

*PROJECT ECHO is an open experiment. The creatures do not know they are being watched.*
*Neither do we know, fully, what they will become.*

---

`v0.1 – Core Simulation` &nbsp;·&nbsp; Python / Pygame-CE &nbsp;·&nbsp; 2026
