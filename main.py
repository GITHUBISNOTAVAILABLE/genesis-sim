"""
GENESIS v2 — Main entry point
Game loop: events → world → predator → agents → render → log.
"""

import sys
import pygame
import config as cfg
from world import World
from agent import Agent
from predator import Predator
from renderer import Renderer
from logger import Logger


def create_agents() -> list[Agent]:
    """Spawn two agents at opposite corners."""
    a = Agent(0, 2, 2, "blue")
    b = Agent(1, cfg.GRID_SIZE - 3, cfg.GRID_SIZE - 3, "red")
    return [a, b]


def main():
    world = World()
    agents = create_agents()
    pred = Predator(cfg.PREDATOR_START_X, cfg.PREDATOR_START_Y)
    renderer = Renderer()
    logger = Logger(output_dir="data")

    tick = 0
    paused = False
    speed_mult = 1.0
    running = True
    last_season = world.get_season()

    renderer.add_event("GENESIS v2 started")

    while running:
        # ── events ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    renderer.add_event("Paused" if paused else "Resumed")

                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS,
                                   pygame.K_KP_PLUS):
                    speed_mult = min(10.0, speed_mult + 0.5)
                    renderer.add_event(f"Speed → {speed_mult:.1f}x")

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_mult = max(0.5, speed_mult - 0.5)
                    renderer.add_event(f"Speed → {speed_mult:.1f}x")

                elif event.key == pygame.K_r:
                    world = World()
                    agents = create_agents()
                    pred = Predator(cfg.PREDATOR_START_X,
                                    cfg.PREDATOR_START_Y)
                    tick = 0
                    last_season = "Spring"
                    renderer.add_event("*** RESTARTED ***")

                elif event.key == pygame.K_s:
                    fname = f"genesis_screenshot_{tick}.png"
                    renderer.screenshot(fname)
                    renderer.add_event(f"Screenshot: {fname}")

                elif event.key == pygame.K_d:
                    renderer.toggle_debug()
                    renderer.add_event(
                        "Debug ON" if renderer.debug else "Debug OFF"
                    )

        if paused:
            renderer.draw(world, agents, tick, paused, speed_mult, pred)
            renderer.tick(int(cfg.TARGET_FPS * speed_mult))
            continue

        # ── simulation tick ──────────────────────────────────────────
        tick += 1

        # world step
        world.update()

        # season change event
        current_season = world.get_season()
        if current_season != last_season:
            renderer.add_event(f"T{tick}: ═══ {current_season.upper()} ═══")
            last_season = current_season

        # predator step
        pred.update(agents, tick)

        # agent steps
        for i, agent in enumerate(agents):
            other = agents[1 - i]
            events = agent.update(world, other, pred)

            if events.get("ate"):
                renderer.flash(agent.x, agent.y)
                label = "A" if agent.id == 0 else "B"
                renderer.add_event(
                    f"T{tick}: {label} ate (E={agent.energy:.0f})"
                )
            if events.get("died"):
                label = "A" if agent.id == 0 else "B"
                renderer.add_event(
                    f"T{tick}: {label} DIED (Gen {agent.generation})"
                )
                # produce offspring instead of simple respawn
                sx = 2 if agent.id == 0 else cfg.GRID_SIZE - 3
                sy = 2 if agent.id == 0 else cfg.GRID_SIZE - 3
                offspring = agent.produce_offspring(sx, sy)
                agents[i] = offspring
                renderer.add_event(
                    f"T{tick}: Gen {offspring.generation} born "
                    f"({len(offspring.pathways)} paths)"
                )

        # log
        logger.maybe_log(tick, agents, world)

        # ── render ───────────────────────────────────────────────────
        renderer.draw(world, agents, tick, paused, speed_mult, pred)
        renderer.tick(int(cfg.TARGET_FPS * speed_mult))

    # ── shutdown ─────────────────────────────────────────────────────
    pygame.quit()
    logger.generate_graphs()
    print("[GENESIS] Simulation ended. Graphs saved to data/.")
    sys.exit(0)


if __name__ == "__main__":
    main()
