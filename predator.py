"""
GENESIS — Predator
A threat entity with no chemicals, no memory, no mercy.
Moves toward nearest agent. Agents must sense and respond.
"""

import math
import config as cfg


class Predator:
    """Simple predator that moves toward the nearest living agent."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.alive = True
        self.speed_interval = cfg.PREDATOR_SPEED  # moves every N ticks
        self.trail: list[tuple[int, int]] = []
        self._trail_max = 25

    def update(self, agents, tick):
        """Move toward nearest living agent; attack if adjacent."""
        if tick % self.speed_interval != 0:
            return

        # find nearest living agent
        nearest = None
        nearest_dist = float("inf")
        for agent in agents:
            if agent.alive:
                d = math.hypot(self.x - agent.x, self.y - agent.y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = agent

        if nearest is None:
            return

        # move one step toward nearest agent
        dx = nearest.x - self.x
        dy = nearest.y - self.y
        if abs(dx) > abs(dy):
            self.x += 1 if dx > 0 else -1
        elif abs(dy) > 0:
            self.y += 1 if dy > 0 else -1

        # clamp to grid
        self.x = max(0, min(cfg.GRID_SIZE - 1, self.x))
        self.y = max(0, min(cfg.GRID_SIZE - 1, self.y))

        # trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > self._trail_max:
            self.trail.pop(0)

        # attack if adjacent to any agent
        for agent in agents:
            if agent.alive:
                d = math.hypot(self.x - agent.x, self.y - agent.y)
                if d < 2.0:
                    agent.energy -= cfg.PREDATOR_DAMAGE
