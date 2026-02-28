"""
GENESIS — Logger
CSV data capture and Matplotlib graph generation.
Expanded for v2.0: seasons, generations, additional chemicals.
"""

import csv
import math
import os
from datetime import datetime

import numpy as np
import config as cfg


class Logger:
    """Logs simulation data every TICKS_PER_LOG ticks and produces graphs."""

    def __init__(self, output_dir: str = "."):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = os.path.join(output_dir, f"genesis_log_{timestamp}.csv")
        self._rows: list[dict] = []
        self._header_written = False

    # ── per-tick check ───────────────────────────────────────────────────
    def maybe_log(self, tick: int, agents, world):
        if tick % cfg.TICKS_PER_LOG != 0:
            return
        a, b = agents
        dist = math.hypot(a.x - b.x, a.y - b.y)
        row = {
            "tick":               tick,
            "season":             world.get_season(),
            "season_tick":        world.get_season_tick(),
            "total_food":         round(float(np.sum(world.food)), 1),
            "agent_a_energy":     round(a.energy, 2),
            "agent_b_energy":     round(b.energy, 2),
            "agent_a_hunger":     round(a.chemicals["hunger"], 3),
            "agent_b_hunger":     round(b.chemicals["hunger"], 3),
            "agent_a_fear":       round(a.chemicals["fear"], 3),
            "agent_b_fear":       round(b.chemicals["fear"], 3),
            "agent_a_curiosity":  round(a.chemicals["curiosity"], 3),
            "agent_b_curiosity":  round(b.chemicals["curiosity"], 3),
            "agent_a_stress":     round(a.chemicals["stress"], 3),
            "agent_b_stress":     round(b.chemicals["stress"], 3),
            "agent_a_fatigue":    round(a.chemicals["fatigue"], 3),
            "agent_b_fatigue":    round(b.chemicals["fatigue"], 3),
            "agent_a_social":     round(a.chemicals["social"], 3),
            "agent_b_social":     round(b.chemicals["social"], 3),
            "agent_a_food_eaten": a.food_eaten,
            "agent_b_food_eaten": b.food_eaten,
            "agent_a_pathways":   len(a.pathways),
            "agent_b_pathways":   len(b.pathways),
            "agent_a_generation": a.generation,
            "agent_b_generation": b.generation,
            "distance":           round(dist, 2),
        }
        self._rows.append(row)
        self._write_row(row)

    def _write_row(self, row: dict):
        mode = "a" if self._header_written else "w"
        with open(self.csv_path, mode, newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            if not self._header_written:
                writer.writeheader()
                self._header_written = True
            writer.writerow(row)

    # ── graph generation ─────────────────────────────────────────────────
    def generate_graphs(self):
        if not self._rows:
            return
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        ticks = [r["tick"] for r in self._rows]

        graphs = [
            {
                "title": "Energy Over Time",
                "filename": "graph_energy.png",
                "series": [
                    ("Agent A", [r["agent_a_energy"] for r in self._rows], "#3A8CFF"),
                    ("Agent B", [r["agent_b_energy"] for r in self._rows], "#FF4646"),
                ],
                "ylabel": "Energy",
            },
            {
                "title": "Hunger Over Time",
                "filename": "graph_hunger.png",
                "series": [
                    ("Agent A", [r["agent_a_hunger"] for r in self._rows], "#3A8CFF"),
                    ("Agent B", [r["agent_b_hunger"] for r in self._rows], "#FF4646"),
                ],
                "ylabel": "Hunger",
            },
            {
                "title": "Cumulative Food Eaten",
                "filename": "graph_food_eaten.png",
                "series": [
                    ("Agent A", [r["agent_a_food_eaten"] for r in self._rows], "#3A8CFF"),
                    ("Agent B", [r["agent_b_food_eaten"] for r in self._rows], "#FF4646"),
                ],
                "ylabel": "Food Eaten",
            },
            {
                "title": "Distance Between Agents",
                "filename": "graph_distance.png",
                "series": [
                    ("Distance", [r["distance"] for r in self._rows], "#A070FF"),
                ],
                "ylabel": "Distance (cells)",
            },
            {
                "title": "Total Food on Grid (Seasonality)",
                "filename": "graph_food_supply.png",
                "series": [
                    ("Food Supply", [r["total_food"] for r in self._rows], "#40C060"),
                ],
                "ylabel": "Total Food",
            },
            {
                "title": "Stress Over Time",
                "filename": "graph_stress.png",
                "series": [
                    ("Agent A", [r["agent_a_stress"] for r in self._rows], "#3A8CFF"),
                    ("Agent B", [r["agent_b_stress"] for r in self._rows], "#FF4646"),
                ],
                "ylabel": "Stress",
            },
        ]

        for g in graphs:
            fig, ax = plt.subplots(figsize=(10, 4))
            fig.patch.set_facecolor("#0E0E14")
            ax.set_facecolor("#14141C")
            for label, data, color in g["series"]:
                ax.plot(ticks, data, label=label, color=color, linewidth=1.4)
            ax.set_title(g["title"], color="white", fontsize=14)
            ax.set_xlabel("Tick", color="gray")
            ax.set_ylabel(g["ylabel"], color="gray")
            ax.tick_params(colors="gray")
            ax.legend(facecolor="#1A1A24", edgecolor="#333", labelcolor="white")
            ax.grid(True, alpha=0.15)
            for spine in ax.spines.values():
                spine.set_color("#333")

            # mark season boundaries
            for i, row in enumerate(self._rows):
                if i > 0 and row["season"] != self._rows[i - 1]["season"]:
                    ax.axvline(row["tick"], color="#555", linestyle="--",
                               linewidth=0.7, alpha=0.5)

            path = os.path.join(self.output_dir, g["filename"])
            fig.savefig(
                path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(),
            )
            plt.close(fig)
            print(f"[GENESIS] Graph saved: {path}")
