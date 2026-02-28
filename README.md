# GENESIS — Emergent Intelligence Simulation

> *"We are not building intelligence. We are building the conditions where intelligence has no choice but to emerge."*

---

## The Result First

One run. 50,600 ticks. Two agents. No hardcoded behavior.

- **Generation 30** reached before the simulation was manually stopped
- **2.83 cells apart** — the closest approach ever recorded, at tick 32,400. Both agents frozen with fear at 0.97, too fatigued to flee. Three systems conflicting simultaneously: fear said run, fatigue said can't, predator said now.
- **Social bond averaged +0.250** across the entire run. Two competing agents developed a measurably positive relationship across 30 generations of shared survival. Nobody programmed that.
- **Zero chronic stress** accumulated across 50,600 ticks. Agents in generation 30 are genuinely calmer and more stable than generation 0. That is adaptation. That is data.

---

## What GENESIS Is

GENESIS is a simulation where two agents survive on a 60×60 grid using 12 internal chemicals — hunger, fear, curiosity, satiation, aggression, fatigue, alertness, comfort, urgency, memory consolidation, social, and stress.

There are no rules like `if hungry: go to food`.

Every behavior — territory formation, starvation bravery, seasonal migration, generational learning, the social bond, the moment at 2.83 cells — emerged entirely from chemical interactions under survival pressure.

The chemicals are real. The pressure is real. The behavior is emergent.

---

## Proven Emergent Behaviors

All of the following appeared in data without being programmed:

| Behavior | First Observed | Evidence |
|---|---|---|
| Territory formation | v1.0, tick 100 | Avg separation 64 cells across 3 independent runs |
| Starvation bravery | v1.0 | Hunger²×0.9 curve suppresses fear continuously |
| Synchronized fear | v1.0 | 97% of ticks within 0.02 of each other across 13,700 ticks |
| Pathway learning plateau | v1.0, tick ~7000 | Learning ceiling at ~330 pathways, reproduced independently |
| Peace states | v1.0 | Chemical silence when all pressures simultaneously zero |
| Curiosity before death | v1.0 | 0.46 curiosity spike as hunger overrode fear in final ticks |
| Predator-forced convergence | v2.0 | Distance crashed from 64-cell average to 11.18 cells |
| Fear maxing at 1.0 | v2.0 | Winter + predator combo produced never-before-seen chemical state |
| Generational improvement | v2.0 | Generation 30 agents accumulate zero chronic stress vs early crises |
| Social bond emergence | v2.0 | +0.250 average social across 50,600 ticks between competing agents |
| Fatigue-trapped convergence | v2.0 | Tick 32,400: fear 0.97, distance 2.83, fatigue prevented escape |
| Divergent survival strategies | v2.0 | A: fewer deaths, more food per life. B: more deaths, faster evolution. |

---

## The Chemistry

No hardcoded rules. All parameters tune continuous curves.

```python
# Starvation bravery — smooth curve, not a cliff
# At hunger 0.5 → fear keeps 77%. At hunger 1.0 → fear keeps 10%.
self.chemicals["fear"] *= (1.0 - self.chemicals["hunger"] ** 2 * 0.9)

# Urgency — rises when BOTH hunger AND fear are high simultaneously
urgency_input = self.chemicals["hunger"] * self.chemicals["fear"]
self.chemicals["urgency"] = min(1.0, self.chemicals["urgency"] * 0.95 + urgency_input * 1.5)

# Social — positive when both satiated, negative when either hungry
proximity_social = 1.0 / (1.0 + other_dist ** 2 / 50.0)
hunger_compat = (1.0 - self.chemicals["hunger"]) * (1.0 - other_hunger)
social_input = proximity_social * (hunger_compat * 2.0 - 1.0)

# Fatigue scales movement cost linearly — no binary switch
fatigue_mult = 1.0 + self.chemicals["fatigue"]
```

Every interaction is a continuous function. Behavior emerges from the intersections.

---

## Install

```bash
pip install pygame numpy matplotlib
python main.py
```

## Controls

| Key | Action |
|-----|--------|
| `SPACE` | Pause / Resume |
| `+` / `-` | Speed up / Slow down |
| `R` | Restart |
| `S` | Screenshot |
| `D` | Debug overlay |
| `ESC` | Quit + generate graphs |

---

## Architecture

```
genesis/
├── main.py        # Game loop
├── world.py       # Grid, food, scent, seasons, communication markers
├── agent.py       # 12 chemicals, pathway memory, generations
├── predator.py    # Threat entity — no memory, no mercy
├── renderer.py    # Seasonal visuals, chemical sidebar, trails
├── logger.py      # CSV logging + matplotlib graphs
├── config.py      # All constants (no behavior, only gradients)
└── data/          # Logs and graphs auto-saved here
```

---

## v2.0 Systems

**Seasons** — 500-tick cycle. Food regen, scent diffusion, and energy drain change with each season. Agents sense environmental shift through existing chemicals — they are never told what season it is.

**Communication** — Agents leave chemical markers: gold food trails (fade over ~200 ticks), red alarm zones (fade over ~100 ticks). Meaning emerges from what other agents do with them.

**Predator** — Moves toward the nearest agent every N ticks. No chemicals, no memory. Pure pressure. Agents sense it through fear spikes within range.

**Generations** — Death produces offspring inheriting the top 50% of parent pathways at 70% strength. Natural selection without programming natural selection.

**12 Chemicals** — All interact. Fatigue suppresses curiosity. Comfort suppresses fear. Urgency amplifies hunger and suppresses fear simultaneously. Stress makes behavior erratic. Memory consolidation doubles pathway reinforcement during rest.

---

## What This Is Not

This is not AGI. This is not a claim about consciousness.

This is a proof that survival pressure alone — without explicit behavioral rules — produces complex, reproducible, measurable emergent behavior across multiple independent runs and 30 generations.

The question GENESIS is really asking: *at what point does the complexity of emergent behavior become indistinguishable from genuine experience?*

We don't know yet. That's why we keep building.

---

## Roadmap

- [ ] 40 chemicals (adding only when behavior gaps appear in data)
- [ ] Agent-to-agent communication (meaning emerges from what works)
- [ ] Multi-agent scaling (5, 10, 50 agents — does diversity increase?)
- [ ] Larger grid (120×120, 240×240)
- [ ] Cross-run personality analysis (are strategies heritable?)

---

## Run Data

| Run | Ticks | Generations | Closest Approach | Notable |
|-----|-------|-------------|-----------------|---------|
| v1.0 Run 1 | 13,700 | 0 | 46 cells | First peace state at tick 2,600 |
| v1.0 Run 2 | 4,500 | 0 | 53 cells | Shortest run |
| v1.0 Run 3 | 12,300 | 0 | 43 cells | 5 peace states (4% of run) |
| v2.0 Run 1 | 2,800 | 15 | 11.18 cells | First predator convergence |
| v2.0 Run 2 | 50,600+ | 30 | **2.83 cells** | Still alive when stopped |
