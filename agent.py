"""
GENESIS — Agent
Chemical-driven agent with pathway memory, generations, and 12 chemicals.
NO hardcoded behaviours.
"""

import math
import random
import config as cfg


class Agent:
    """An agent whose behaviour emerges from chemical pressure, not rules."""

    def __init__(self, agent_id: int, x: int, y: int, color_name: str):
        self.id = agent_id
        self.x = x
        self.y = y
        self.color_name = color_name       # "blue" or "red"

        # energy
        self.energy = cfg.ENERGY_START
        self.alive = True

        # 12 chemical internal states
        self.chemicals = {
            "hunger":                0.0,
            "fear":                  0.0,
            "curiosity":             0.5,
            "satiation":             0.0,
            "aggression":            0.0,
            "fatigue":               0.0,
            "alertness":             0.5,
            "comfort":               0.0,
            "urgency":               0.0,
            "memory_consolidation":  0.0,
            "social":                0.0,
            "stress":                0.0,
        }

        # pathway memory: (x, y) -> strength
        self.pathways: dict[tuple[int, int], float] = {}

        # exploration tracking
        self.visited: set[tuple[int, int]] = set()
        self.visited.add((x, y))

        # recent move history for pathway reinforcement
        self._move_history: list[tuple[int, int]] = []

        # stats
        self.food_eaten = 0
        self.total_ticks = 0

        # trail for visualisation (last N positions)
        self.trail: list[tuple[int, int]] = []
        self._trail_max = 40

        # generations (Phase 4)
        self.generation = 0
        self.parent_food_eaten = 0

        # movement tracking for fatigue
        self._stationary_ticks = 0

    # ── chemical update ──────────────────────────────────────────────────
    def update_chemicals(self, other_agent: "Agent", predator=None):
        """Recompute all 12 chemical concentrations from current state."""

        # ── hunger — inverse of energy ───────────────────────────────
        raw_hunger = 1.0 - (self.energy / 100.0)
        self.chemicals["hunger"] = max(0.0, min(1.0, raw_hunger))

        # satiation decay
        self.chemicals["satiation"] = max(
            0.0, self.chemicals["satiation"] - cfg.SATIATION_DECAY
        )
        # hunger suppression by satiation
        self.chemicals["hunger"] = max(
            0.0,
            self.chemicals["hunger"] - self.chemicals["satiation"] * 0.5,
        )

        # ── fear — proximity to other agent ──────────────────────────
        if other_agent.alive:
            dist = math.hypot(self.x - other_agent.x, self.y - other_agent.y)
            max_dist = math.hypot(cfg.GRID_SIZE, cfg.GRID_SIZE)
            self.chemicals["fear"] = max(0.0, min(
                1.0, 1.0 - (dist / max_dist)
            ))
        else:
            self.chemicals["fear"] = 0.0

        # ── predator fear boost — continuous falloff, no range cutoff ─
        if predator is not None and predator.alive:
            pred_dist = math.hypot(self.x - predator.x, self.y - predator.y)
            # smooth inverse-distance: strong nearby, fades to near-zero far away
            pred_fear = 1.0 / (1.0 + (pred_dist / cfg.PREDATOR_SENSE_RANGE) ** 2)
            self.chemicals["fear"] = min(
                1.0,
                self.chemicals["fear"] + pred_fear * cfg.PREDATOR_FEAR_BOOST
            )

        # fear suppressed by hunger — continuous gradient, no threshold
        # the hungrier the agent, the less it fears (squared for nonlinearity)
        hunger_sq = self.chemicals["hunger"] ** 2
        self.chemicals["fear"] *= (1.0 - hunger_sq * 0.9)

        # ── curiosity — rises in new cells, decays in known ──────────
        if (self.x, self.y) not in self.visited:
            self.chemicals["curiosity"] = min(
                1.0, self.chemicals["curiosity"] + 0.15
            )
            self.visited.add((self.x, self.y))
        else:
            self.chemicals["curiosity"] = max(
                0.0, self.chemicals["curiosity"] - cfg.CURIOSITY_GAIN
            )
        # fear suppresses curiosity
        self.chemicals["curiosity"] = max(
            0.0,
            self.chemicals["curiosity"] - self.chemicals["fear"] * 0.4,
        )

        # ── aggression — rises when territory invaded ────────────────
        if other_agent.alive:
            other_dist = math.hypot(
                self.x - other_agent.x, self.y - other_agent.y
            )
            # aggression — continuous inverse-square proximity, no threshold
            # closer = stronger signal, fades smoothly with distance
            proximity_pressure = 1.0 / (1.0 + other_dist ** 2 / 25.0)
            # modulated by how many pathways are nearby (territory density)
            path_density = sum(
                1.0 / (1.0 + math.hypot(other_agent.x - px, other_agent.y - py))
                for (px, py) in list(self.pathways.keys())[:20]
            ) / max(1, min(20, len(self.pathways)))
            aggression_input = proximity_pressure * path_density
            self.chemicals["aggression"] = max(0.0, min(1.0,
                self.chemicals["aggression"] * 0.95 + aggression_input * 0.1
            ))
        # fatigue suppresses aggression
        self.chemicals["aggression"] = max(
            0.0,
            self.chemicals["aggression"]
            - self.chemicals["fatigue"] * 0.3,
        )

        # ── fatigue — rises with movement, decays when stationary ────
        # updated in update() based on movement

        # fatigue suppresses curiosity
        self.chemicals["curiosity"] = max(
            0.0,
            self.chemicals["curiosity"] - self.chemicals["fatigue"] * 0.3,
        )

        # ── alertness — rises with fear and predator proximity ────────
        alert_input = self.chemicals["fear"] * 0.5
        if predator is not None and predator.alive:
            pred_dist = math.hypot(self.x - predator.x, self.y - predator.y)
            # continuous: closer predator = more alertness
            alert_input += 1.0 / (1.0 + (pred_dist / cfg.PREDATOR_SENSE_RANGE) ** 2) * 0.5
        self.chemicals["alertness"] = max(0.0, min(1.0,
            self.chemicals["alertness"] * 0.9 + alert_input * 0.3
        ))
        # alertness suppresses satiation — continuous, no threshold
        # the more alert, the more satiation is suppressed
        self.chemicals["satiation"] *= (1.0 - self.chemicals["alertness"] * 0.25)

        # ── comfort — continuous product of familiarity × satedness × safety
        familiarity = 1.0 if (self.x, self.y) in self.visited else 0.0
        satedness = 1.0 - self.chemicals["hunger"]
        safety = 1.0 - self.chemicals["fear"]
        comfort_input = familiarity * satedness * safety
        self.chemicals["comfort"] = max(0.0, min(1.0,
            self.chemicals["comfort"] * 0.97 + comfort_input * 0.03
        ))
        # comfort suppresses fear
        self.chemicals["fear"] = max(
            0.0,
            self.chemicals["fear"] - self.chemicals["comfort"] * 0.3,
        )

        # ── urgency — hunger × fear, rises when both are high ────────
        urgency_input = self.chemicals["hunger"] * self.chemicals["fear"]
        self.chemicals["urgency"] = min(
            1.0, self.chemicals["urgency"] * 0.95 + urgency_input * 1.5
        )

        # ── memory_consolidation — fatigue × satedness, continuous ────
        consolidation_input = (
            self.chemicals["fatigue"] * (1.0 - self.chemicals["hunger"])
        )
        self.chemicals["memory_consolidation"] = min(
            1.0,
            self.chemicals["memory_consolidation"] * 0.97
            + consolidation_input * 0.04,
        )

        # ── social — continuous proximity × hunger compatibility ─────
        if other_agent.alive:
            other_dist = math.hypot(
                self.x - other_agent.x, self.y - other_agent.y
            )
            proximity_social = 1.0 / (1.0 + other_dist ** 2 / 50.0)
            hunger_compat = (
                (1.0 - self.chemicals["hunger"])
                * (1.0 - other_agent.chemicals.get("hunger", 0))
            )
            # positive when both satiated, negative when either hungry
            social_input = proximity_social * (hunger_compat * 2.0 - 1.0)
            self.chemicals["social"] = max(-1.0, min(1.0,
                self.chemicals["social"] * 0.99 + social_input * 0.03
            ))

        # ── stress — continuous inverse of energy, accumulates ────────
        energy_pressure = max(0.0, 1.0 - self.energy / 50.0)
        self.chemicals["stress"] = max(0.0, min(1.0,
            self.chemicals["stress"] * 0.999 + energy_pressure * 0.01
        ))

    # ── movement decision ────────────────────────────────────────────────
    def decide_move(self, world, other_agent: "Agent",
                    predator=None) -> tuple[int, int]:
        """Score neighbouring cells via chemical weights. Return (nx, ny)."""
        best_score = -999.0
        best_cell = (self.x, self.y)

        hunger_w = self.chemicals["hunger"] * cfg.HUNGER_WEIGHT_MULTIPLIER
        fear_w = self.chemicals["fear"] * cfg.FEAR_WEIGHT_MULTIPLIER
        curiosity_w = (self.chemicals["curiosity"]
                       * cfg.CURIOSITY_WEIGHT_MULTIPLIER)

        # stress makes responses erratic
        stress_noise = self.chemicals["stress"] * 0.15

        # urgency continuously amplifies hunger, suppresses fear
        hunger_w *= (1.0 + self.chemicals["urgency"])
        fear_w *= (1.0 - self.chemicals["urgency"] * 0.7)

        # fatigue continuously suppresses curiosity
        curiosity_w *= (1.0 - self.chemicals["fatigue"] * 0.7)

        # alertness sharpens effective vision — continuous
        effective_vision = cfg.VISION_RANGE + self.chemicals["alertness"]

        neighbours = [
            (self.x + dx, self.y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if not (dx == 0 and dy == 0)
        ]

        for nx, ny in neighbours:
            if nx < 0 or ny < 0 or nx >= cfg.GRID_SIZE or ny >= cfg.GRID_SIZE:
                continue

            # food scent pull
            scent = world.get_scent(nx, ny)
            score = scent * hunger_w

            # food marker attraction
            food_mark = world.get_food_marker(nx, ny)
            score += food_mark * cfg.FOOD_MARKER_WEIGHT * self.chemicals["hunger"]

            # alarm marker repulsion
            alarm_mark = world.get_alarm_marker(nx, ny)
            score -= alarm_mark * cfg.ALARM_MARKER_WEIGHT * self.chemicals["fear"]

            # other-agent repulsion
            if other_agent.alive:
                d = math.hypot(nx - other_agent.x, ny - other_agent.y)
                proximity = 1.0 / (d + 1.0)
                score -= proximity * fear_w
                # social modulation — continuous, positive social reduces repulsion
                score += proximity * max(0.0, self.chemicals["social"]) * 0.3

            # predator repulsion
            if predator is not None and predator.alive:
                pd = math.hypot(nx - predator.x, ny - predator.y)
                if pd < cfg.PREDATOR_SENSE_RANGE:
                    pred_prox = 1.0 / (pd + 0.5)
                    score -= pred_prox * fear_w * 2.0

            # unexplored bonus
            if (nx, ny) not in self.visited:
                score += curiosity_w

            # pathway memory bonus
            pw = self.pathways.get((nx, ny), 0.0)
            score += pw * cfg.PATHWAY_WEIGHT

            # comfort bonus for known zones — continuous
            if (nx, ny) in self.visited:
                score += self.chemicals["comfort"] * 0.1

            # random noise (stress amplifies)
            noise_range = cfg.RANDOM_NOISE_RANGE + stress_noise
            score += random.uniform(-noise_range, noise_range)

            if score > best_score:
                best_score = score
                best_cell = (nx, ny)

        # if all scores negative, stay put
        if best_score < 0:
            return (self.x, self.y)
        return best_cell

    # ── tick ─────────────────────────────────────────────────────────────
    def update(self, world, other_agent: "Agent",
               predator=None) -> dict:
        """Run one tick: chemicals → decide → move → eat → pathways.
        Returns dict of events for the renderer/logger.
        """
        if not self.alive:
            return {"alive": False}

        self.total_ticks += 1
        events: dict = {"ate": False, "moved": False, "died": False}

        # 1. update chemicals
        self.update_chemicals(other_agent, predator)

        # 2. decide
        nx, ny = self.decide_move(world, other_agent, predator)
        moved = (nx, ny) != (self.x, self.y)

        # 3. energy cost (seasonal modifier)
        drain_mod = cfg.SEASON_DRAIN_MODIFIER.get(world.get_season(), 1.0)

        # fatigue scales movement cost continuously — no binary switch
        fatigue_mult = 1.0 + self.chemicals["fatigue"]

        self.energy -= cfg.ENERGY_PASSIVE_DRAIN * drain_mod
        if moved:
            self.energy -= cfg.ENERGY_MOVE_DRAIN * drain_mod * fatigue_mult
            self.x, self.y = nx, ny
            events["moved"] = True

            # fatigue rises with movement
            self.chemicals["fatigue"] = min(
                1.0, self.chemicals["fatigue"] + 0.01
            )
            self._stationary_ticks = 0

            # trail
            self.trail.append((nx, ny))
            if len(self.trail) > self._trail_max:
                self.trail.pop(0)
        else:
            # fatigue decays when stationary
            self._stationary_ticks += 1
            self.chemicals["fatigue"] = max(
                0.0, self.chemicals["fatigue"] - 0.02
            )

        # 4. eat
        gained = world.eat_food(self.x, self.y)
        if gained > 0:
            self.energy = min(cfg.ENERGY_MAX, self.energy + gained)
            self.chemicals["satiation"] = min(
                1.0, self.chemicals["satiation"] + 0.5
            )
            self.food_eaten += 1
            events["ate"] = True
            # reinforce pathway — consolidation amplifies continuously
            consolidation_mult = 1.0 + self.chemicals["memory_consolidation"]
            self._reinforce_pathways(consolidation_mult)
            # leave food marker
            world.leave_food_marker(self.x, self.y, strength=0.8)

        # leave alarm marker proportional to fear — continuous
        if self.chemicals["fear"] > 0.01:
            world.leave_alarm_marker(
                self.x, self.y,
                strength=self.chemicals["fear"] ** 2,
            )

        # 6. weaken pathway for current cell if no food gained
        if not events["ate"]:
            self._weaken_recent_path()

        # 7. record move history
        self._move_history.append((self.x, self.y))
        if len(self._move_history) > cfg.PATHWAY_LOOKBACK:
            self._move_history.pop(0)

        # 8. death check
        if self.energy <= 0:
            self.energy = 0
            self.alive = False
            events["died"] = True

        return events

    # ── pathway helpers ──────────────────────────────────────────────────
    def _reinforce_pathways(self, multiplier: float = 1.0):
        """Strengthen cells visited in the last PATHWAY_LOOKBACK ticks."""
        for pos in self._move_history:
            self.pathways[pos] = min(
                1.0,
                self.pathways.get(pos, 0.0)
                + cfg.PATHWAY_REINFORCE * multiplier,
            )

    def _weaken_recent_path(self):
        """Slightly weaken the most recent cell if no food was found."""
        if self._move_history:
            pos = self._move_history[-1]
            pw = self.pathways.get(pos, 0.0) - cfg.PATHWAY_WEAKEN
            if pw < cfg.PATHWAY_PRUNE_THRESHOLD:
                self.pathways.pop(pos, None)
            else:
                self.pathways[pos] = pw

    # ── generations (Phase 4) ────────────────────────────────────────────
    def produce_offspring(self, x: int, y: int) -> "Agent":
        """Create offspring inheriting strongest pathways."""
        child = Agent(self.id, x, y, self.color_name)
        child.generation = self.generation + 1
        child.parent_food_eaten = self.food_eaten

        # inherit top 50% of pathways by strength
        if self.pathways:
            sorted_paths = sorted(
                self.pathways.items(),
                key=lambda item: item[1],
                reverse=True,
            )
            inherit_count = max(1, len(sorted_paths) // 2)
            for pos, strength in sorted_paths[:inherit_count]:
                child.pathways[pos] = strength * cfg.INHERITANCE_STRENGTH

        return child

    # ── respawn (legacy, kept for compatibility) ─────────────────────────
    def respawn(self, x: int, y: int):
        """Reset agent for a new life, keeping pathway memory."""
        self.x = x
        self.y = y
        self.energy = cfg.ENERGY_START
        self.alive = True
        self.chemicals = {k: 0.0 for k in self.chemicals}
        self.chemicals["curiosity"] = 0.5
        self.chemicals["alertness"] = 0.5
        self.trail.clear()
        self._move_history.clear()
        self.visited.clear()
        self.visited.add((x, y))
        self._stationary_ticks = 0
