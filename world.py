"""
GENESIS — World
Grid environment: food, scent diffusion, seasons, chemical markers.
"""

import numpy as np
import config as cfg


class World:
    """60×60 grid world with food, scent diffusion, seasons, and markers."""

    def __init__(self):
        self.size = cfg.GRID_SIZE
        self.food = np.zeros((self.size, self.size), dtype=np.float64)
        self.scent = np.zeros((self.size, self.size), dtype=np.float64)

        # communication markers (Phase 2)
        self.food_markers = np.zeros((self.size, self.size), dtype=np.float64)
        self.alarm_markers = np.zeros((self.size, self.size), dtype=np.float64)

        # seasons (Phase 1)
        self.tick_count = 0
        self.current_season = "Spring"
        self.season_index = 0

        self._spawn_food()

    # ── initialisation ───────────────────────────────────────────────────
    def _spawn_food(self):
        """Randomly place food on ~15 % of cells."""
        mask = np.random.random((self.size, self.size)) < cfg.FOOD_SPAWN_RATE
        self.food[mask] = np.random.uniform(0.5, 1.0, size=mask.sum())

    # ── season helpers ───────────────────────────────────────────────────
    def get_season(self) -> str:
        return self.current_season

    def get_season_progress(self) -> float:
        """Returns 0.0–1.0 progress through current season."""
        return (self.tick_count % cfg.SEASON_LENGTH) / cfg.SEASON_LENGTH

    def get_season_tick(self) -> int:
        """Tick within the current season (0 to SEASON_LENGTH-1)."""
        return self.tick_count % cfg.SEASON_LENGTH

    def get_total_food(self) -> float:
        """Sum of all food on the grid."""
        return float(np.sum(self.food))

    # ── per-tick update ──────────────────────────────────────────────────
    def update(self):
        """Regenerate food, diffuse scent, advance season, decay markers."""
        self.tick_count += 1

        # advance season
        new_index = (self.tick_count // cfg.SEASON_LENGTH) % 4
        if new_index != self.season_index:
            self.season_index = new_index
            self.current_season = cfg.SEASONS[self.season_index]

        # seasonal food decay (autumn/winter)
        decay_rate = cfg.SEASON_FOOD_DECAY[self.current_season]
        if decay_rate > 0:
            decay_mask = np.random.random((self.size, self.size)) < decay_rate
            self.food[decay_mask] *= 0.9

        # seasonal food regeneration
        regen_rate = cfg.SEASON_FOOD_REGEN[self.current_season]
        regen = np.random.random((self.size, self.size)) < regen_rate
        self.food[regen] = np.minimum(self.food[regen] + 0.1, 1.0)

        # scent diffusion (seasonal)
        self._diffuse_scent()

        # decay communication markers
        self.food_markers *= (1.0 - cfg.FOOD_MARKER_DECAY)
        self.alarm_markers *= (1.0 - cfg.ALARM_MARKER_DECAY)
        np.clip(self.food_markers, 0, 1, out=self.food_markers)
        np.clip(self.alarm_markers, 0, 1, out=self.alarm_markers)

    def _diffuse_scent(self):
        """Scent = blurred food map with seasonal diffusion factor."""
        self.scent = self.food.copy()
        diffusion = cfg.SEASON_SCENT_DIFFUSION.get(
            self.current_season, cfg.SCENT_DIFFUSION
        )

        padded = np.pad(self.scent, 1, mode="constant", constant_values=0)
        for _ in range(3):
            new = padded.copy()
            new[1:-1, 1:-1] = (
                padded[1:-1, 1:-1] * (1.0 - diffusion)
                + (padded[:-2, 1:-1] + padded[2:, 1:-1]
                   + padded[1:-1, :-2] + padded[1:-1, 2:])
                * (diffusion / 4.0)
            )
            padded = new
        self.scent = padded[1:-1, 1:-1]

        self.scent *= (1.0 - cfg.SCENT_DECAY)
        self.scent = np.clip(self.scent, 0.0, 1.0)

    # ── agent interactions ───────────────────────────────────────────────
    def eat_food(self, x: int, y: int) -> float:
        """Agent eats food at (x, y). Returns energy gained."""
        if self.food[y, x] > 0.05:
            gained = min(self.food[y, x], 1.0) * cfg.ENERGY_FOOD_GAIN
            self.food[y, x] = 0.0
            return gained
        return 0.0

    def get_scent(self, x: int, y: int) -> float:
        if 0 <= x < self.size and 0 <= y < self.size:
            return float(self.scent[y, x])
        return 0.0

    def get_food(self, x: int, y: int) -> float:
        if 0 <= x < self.size and 0 <= y < self.size:
            return float(self.food[y, x])
        return 0.0

    def has_food(self, x: int, y: int) -> bool:
        return self.get_food(x, y) > 0.05

    def get_visible_scent(self, cx: int, cy: int, r: int):
        """Return dict {(dx,dy): scent} for cells within vision range."""
        visible = {}
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    visible[(dx, dy)] = float(self.scent[ny, nx])
        return visible

    # ── communication markers ────────────────────────────────────────────
    def leave_food_marker(self, x: int, y: int, strength: float = 1.0):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.food_markers[y, x] = min(1.0, self.food_markers[y, x] + strength)

    def leave_alarm_marker(self, x: int, y: int, strength: float = 1.0):
        if 0 <= x < self.size and 0 <= y < self.size:
            self.alarm_markers[y, x] = min(1.0, self.alarm_markers[y, x] + strength)

    def get_food_marker(self, x: int, y: int) -> float:
        if 0 <= x < self.size and 0 <= y < self.size:
            return float(self.food_markers[y, x])
        return 0.0

    def get_alarm_marker(self, x: int, y: int) -> float:
        if 0 <= x < self.size and 0 <= y < self.size:
            return float(self.alarm_markers[y, x])
        return 0.0
