"""
GENESIS — Renderer
Pygame visualisation: seasonal grid, agents, markers, predator, sidebar.
"""

import math
import pygame
import config as cfg


# ── colour palette ───────────────────────────────────────────────────────
GRID_LINE = (25, 25, 30)
FOOD_GREEN = (30, 200, 60)
SCENT_TINT = (15, 60, 20)
AGENT_BLUE = (50, 140, 255)
AGENT_RED = (255, 70, 70)
TRAIL_BLUE = (30, 70, 140, 90)
TRAIL_RED = (140, 30, 30, 90)
PREDATOR_COLOR = (140, 40, 180)
PREDATOR_TRAIL = (80, 20, 100, 70)
FOOD_MARKER_COLOR = (200, 180, 50)
ALARM_MARKER_COLOR = (200, 40, 40)
SIDEBAR_BG = (18, 18, 24)
TEXT_COLOR = (210, 210, 215)
TEXT_DIM = (120, 120, 130)
TEXT_ACCENT_BLUE = (100, 180, 255)
TEXT_ACCENT_RED = (255, 120, 120)
FLASH_COLOR = (255, 255, 180)
HEADER_BG = (14, 14, 20)
DIVIDER = (40, 40, 50)

SEASON_LABEL_COLOR = {
    "Spring": (100, 220, 120),
    "Summer": (240, 200, 60),
    "Autumn": (220, 140, 50),
    "Winter": (140, 160, 220),
}


class Renderer:
    """Draws the GENESIS world each frame."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("GENESIS v2 — Emergent Intelligence")
        self.clock = pygame.time.Clock()

        # fonts
        self.font_sm = pygame.font.SysFont("consolas", 12)
        self.font_md = pygame.font.SysFont("consolas", 14)
        self.font_lg = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 20, bold=True)

        # flash animation bookkeeping
        self._flashes: dict[tuple[int, int], int] = {}

        # event log
        self._event_log: list[str] = []
        self._log_max = 6

        # debug mode
        self.debug = False

        # trail surface
        self._trail_surf = pygame.Surface(
            (cfg.GRID_PIXEL_SIZE, cfg.GRID_PIXEL_SIZE), pygame.SRCALPHA
        )

    # ── helpers ──────────────────────────────────────────────────────────
    def add_event(self, text: str):
        self._event_log.insert(0, text)
        if len(self._event_log) > self._log_max:
            self._event_log.pop()

    def flash(self, x: int, y: int):
        self._flashes[(x, y)] = 6

    def toggle_debug(self):
        self.debug = not self.debug

    # ── main draw ────────────────────────────────────────────────────────
    def draw(self, world, agents, tick, paused, speed_mult,
             predator=None):
        # seasonal background
        bg = cfg.SEASON_SKY_COLOR.get(world.get_season(), (10, 10, 15))
        self.screen.fill(bg)

        self._draw_grid(world)
        self._draw_markers(world)
        self._draw_trails(agents, predator)
        self._draw_agents(agents)
        if predator is not None:
            self._draw_predator(predator, tick)
        self._draw_flashes()
        if self.debug:
            self._draw_debug(world, agents)
        self._draw_sidebar(world, agents, tick, paused, speed_mult,
                           predator)
        pygame.display.flip()

    # ── grid ─────────────────────────────────────────────────────────────
    def _draw_grid(self, world):
        cs = cfg.CELL_SIZE
        for y in range(cfg.GRID_SIZE):
            for x in range(cfg.GRID_SIZE):
                px, py = x * cs, y * cs

                # scent tint
                s = world.scent[y, x]
                if s > 0.01:
                    tint = (
                        int(SCENT_TINT[0] * s),
                        int(SCENT_TINT[1] * s),
                        int(SCENT_TINT[2] * s),
                    )
                    pygame.draw.rect(self.screen, tint, (px, py, cs, cs))

                # food dot
                f = world.food[y, x]
                if f > 0.05:
                    # autumn/winter: food tints orange
                    season = world.get_season()
                    if season == "Autumn":
                        brightness = int(80 + 175 * f)
                        color = (brightness, int(brightness * 0.6), 20)
                    elif season == "Winter":
                        brightness = int(60 + 140 * f)
                        color = (40, brightness, int(brightness * 0.8))
                    else:
                        brightness = int(80 + 175 * f)
                        color = (30, brightness, 40)
                    radius = max(2, int(cs * 0.3 * f) + 1)
                    pygame.draw.circle(
                        self.screen, color,
                        (px + cs // 2, py + cs // 2), radius,
                    )

    # ── markers ──────────────────────────────────────────────────────────
    def _draw_markers(self, world):
        cs = cfg.CELL_SIZE
        for y in range(cfg.GRID_SIZE):
            for x in range(cfg.GRID_SIZE):
                # food markers (gold)
                fm = world.food_markers[y, x]
                if fm > 0.02:
                    alpha = int(min(120, fm * 150))
                    surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    surf.fill((200, 180, 50, alpha))
                    self.screen.blit(surf, (x * cs, y * cs))

                # alarm markers (red)
                am = world.alarm_markers[y, x]
                if am > 0.02:
                    alpha = int(min(100, am * 130))
                    surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    surf.fill((200, 40, 40, alpha))
                    self.screen.blit(surf, (x * cs, y * cs))

    # ── trails ───────────────────────────────────────────────────────────
    def _draw_trails(self, agents, predator=None):
        self._trail_surf.fill((0, 0, 0, 0))
        cs = cfg.CELL_SIZE
        for agent in agents:
            if not agent.trail:
                continue
            color = TRAIL_BLUE if agent.color_name == "blue" else TRAIL_RED
            for i, (tx, ty) in enumerate(agent.trail):
                alpha = int(40 + 50 * (i / max(len(agent.trail), 1)))
                c = (color[0], color[1], color[2], alpha)
                rect = pygame.Rect(tx * cs + 2, ty * cs + 2, cs - 4, cs - 4)
                pygame.draw.rect(self._trail_surf, c, rect, border_radius=2)
        # predator trail
        if predator is not None:
            for i, (tx, ty) in enumerate(predator.trail):
                alpha = int(30 + 40 * (i / max(len(predator.trail), 1)))
                c = (PREDATOR_TRAIL[0], PREDATOR_TRAIL[1],
                     PREDATOR_TRAIL[2], alpha)
                rect = pygame.Rect(tx * cs + 1, ty * cs + 1, cs - 2, cs - 2)
                pygame.draw.rect(self._trail_surf, c, rect, border_radius=2)
        self.screen.blit(self._trail_surf, (0, 0))

    # ── agents ───────────────────────────────────────────────────────────
    def _draw_agents(self, agents):
        cs = cfg.CELL_SIZE
        for agent in agents:
            if not agent.alive:
                continue
            color = AGENT_BLUE if agent.color_name == "blue" else AGENT_RED
            cx = agent.x * cs + cs // 2
            cy = agent.y * cs + cs // 2
            # glow
            glow_surf = pygame.Surface((cs * 3, cs * 3), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surf, (*color[:3], 35),
                (cs * 3 // 2, cs * 3 // 2), cs,
            )
            self.screen.blit(glow_surf, (cx - cs * 3 // 2, cy - cs * 3 // 2))
            # body
            pygame.draw.circle(self.screen, color, (cx, cy), cs // 2 + 1)
            # energy ring
            energy_frac = max(0.0, agent.energy / cfg.ENERGY_MAX)
            pygame.draw.arc(
                self.screen, (255, 255, 255),
                (cx - cs // 2 - 2, cy - cs // 2 - 2, cs + 4, cs + 4),
                0, 6.283 * energy_frac, 2,
            )

    # ── predator ─────────────────────────────────────────────────────────
    def _draw_predator(self, predator, tick):
        cs = cfg.CELL_SIZE
        cx = predator.x * cs + cs // 2
        cy = predator.y * cs + cs // 2
        # pulsing glow
        pulse = abs(math.sin(tick * 0.1)) * 0.5 + 0.5
        glow_r = int(cs * 1.5 * pulse)
        glow_surf = pygame.Surface(
            (glow_r * 2, glow_r * 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            glow_surf, (140, 40, 180, int(40 * pulse)),
            (glow_r, glow_r), glow_r,
        )
        self.screen.blit(glow_surf, (cx - glow_r, cy - glow_r))
        # body — larger than agents
        pygame.draw.circle(
            self.screen, PREDATOR_COLOR, (cx, cy), cs // 2 + 3
        )
        pygame.draw.circle(
            self.screen, (60, 10, 80), (cx, cy), cs // 2 + 1
        )

    # ── flashes ──────────────────────────────────────────────────────────
    def _draw_flashes(self):
        cs = cfg.CELL_SIZE
        done = []
        for (x, y), frames in self._flashes.items():
            alpha = int(200 * (frames / 6))
            surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
            surf.fill((*FLASH_COLOR, alpha))
            self.screen.blit(surf, (x * cs, y * cs))
            self._flashes[(x, y)] = frames - 1
            if frames - 1 <= 0:
                done.append((x, y))
        for k in done:
            del self._flashes[k]

    # ── debug overlay ────────────────────────────────────────────────────
    def _draw_debug(self, world, agents):
        cs = cfg.CELL_SIZE
        for agent in agents:
            color = (TEXT_ACCENT_BLUE if agent.color_name == "blue"
                     else TEXT_ACCENT_RED)
            for (px, py), strength in agent.pathways.items():
                if strength > 0.02:
                    alpha = int(min(255, strength * 255))
                    surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
                    surf.fill((*color[:3], alpha // 2))
                    self.screen.blit(surf, (px * cs, py * cs))

    # ── sidebar ──────────────────────────────────────────────────────────
    def _draw_sidebar(self, world, agents, tick, paused, speed_mult,
                      predator=None):
        sx = cfg.GRID_PIXEL_SIZE
        sw = cfg.SCREEN_WIDTH - sx
        sh = cfg.SCREEN_HEIGHT

        # background
        pygame.draw.rect(self.screen, SIDEBAR_BG, (sx, 0, sw, sh))
        pygame.draw.line(self.screen, DIVIDER, (sx, 0), (sx, sh), 2)

        # header
        pygame.draw.rect(self.screen, HEADER_BG, (sx, 0, sw, 44))
        title = self.font_title.render("GENESIS v2", True, TEXT_COLOR)
        self.screen.blit(title, (sx + sw // 2 - title.get_width() // 2, 10))

        y_pos = 50
        pad = sx + 10

        # ── season info ──────────────────────────────────────────────
        season = world.get_season()
        season_color = SEASON_LABEL_COLOR.get(season, TEXT_COLOR)
        season_surf = self.font_lg.render(season.upper(), True, season_color)
        self.screen.blit(season_surf, (pad, y_pos))
        y_pos += 22

        # season progress bar
        bar_w = sw - 20
        bar_h = 6
        progress = world.get_season_progress()
        pygame.draw.rect(
            self.screen, (30, 30, 35),
            (pad, y_pos, bar_w, bar_h), border_radius=3,
        )
        pygame.draw.rect(
            self.screen, season_color,
            (pad, y_pos, int(bar_w * progress), bar_h), border_radius=3,
        )
        y_pos += 12

        s_tick = self.font_sm.render(
            f"Season tick: {world.get_season_tick()}/{cfg.SEASON_LENGTH}",
            True, TEXT_DIM,
        )
        self.screen.blit(s_tick, (pad, y_pos))
        y_pos += 16

        pygame.draw.line(
            self.screen, DIVIDER, (pad, y_pos), (sx + sw - 10, y_pos)
        )
        y_pos += 6

        # ── agent stats ──────────────────────────────────────────────
        for agent in agents:
            color = (TEXT_ACCENT_BLUE if agent.color_name == "blue"
                     else TEXT_ACCENT_RED)
            label = f"AGENT {'A' if agent.id == 0 else 'B'}  Gen {agent.generation}"
            if not agent.alive:
                label += " [DEAD]"
            hdr = self.font_md.render(label, True, color)
            self.screen.blit(hdr, (pad, y_pos))
            y_pos += 18

            # energy bar
            bar_w = sw - 20
            bar_h = 8
            frac = max(0.0, agent.energy / cfg.ENERGY_MAX)
            pygame.draw.rect(
                self.screen, (35, 35, 40),
                (pad, y_pos, bar_w, bar_h), border_radius=3,
            )
            bar_color = (int(255 * (1 - frac)), int(200 * frac), 50)
            pygame.draw.rect(
                self.screen, bar_color,
                (pad, y_pos, int(bar_w * frac), bar_h), border_radius=3,
            )
            y_pos += 12

            # chemical stats — compact 2-column layout
            chems = agent.chemicals
            chem_pairs = [
                (f"E:{agent.energy:5.0f}", f"Hgr:{chems['hunger']:.2f}"),
                (f"Fear:{chems['fear']:.2f}", f"Cur:{chems['curiosity']:.2f}"),
                (f"Sat:{chems['satiation']:.2f}", f"Agr:{chems['aggression']:.2f}"),
                (f"Ftg:{chems['fatigue']:.2f}", f"Alt:{chems['alertness']:.2f}"),
                (f"Cmf:{chems['comfort']:.2f}", f"Urg:{chems['urgency']:.2f}"),
                (f"Mem:{chems['memory_consolidation']:.2f}", f"Soc:{chems['social']:+.2f}"),
                (f"Str:{chems['stress']:.2f}", f"Pw:{len(agent.pathways)}"),
            ]
            col_w = (sw - 20) // 2
            for left, right in chem_pairs:
                left_s = self.font_sm.render(left, True, TEXT_COLOR)
                right_s = self.font_sm.render(right, True, TEXT_COLOR)
                self.screen.blit(left_s, (pad, y_pos))
                self.screen.blit(right_s, (pad + col_w, y_pos))
                y_pos += 14

            eaten = self.font_sm.render(
                f"Food: {agent.food_eaten}", True, TEXT_DIM
            )
            self.screen.blit(eaten, (pad, y_pos))
            y_pos += 14

            pygame.draw.line(
                self.screen, DIVIDER, (pad, y_pos), (sx + sw - 10, y_pos)
            )
            y_pos += 5

        # ── sim info ─────────────────────────────────────────────────
        state = "PAUSED" if paused else "RUNNING"
        info_lines = [
            f"Tick: {tick}   {state}",
            f"Speed: {speed_mult:.1f}x  FPS: {self.clock.get_fps():.0f}",
            f"Food on grid: {world.get_total_food():.0f}",
        ]
        if predator is not None:
            info_lines.append(
                f"Predator: ({predator.x},{predator.y})"
            )
        for line in info_lines:
            surf = self.font_sm.render(line, True, TEXT_DIM)
            self.screen.blit(surf, (pad, y_pos))
            y_pos += 15
        y_pos += 4

        # ── event log ────────────────────────────────────────────────
        pygame.draw.line(
            self.screen, DIVIDER, (pad, y_pos), (sx + sw - 10, y_pos)
        )
        y_pos += 5
        ev_hdr = self.font_sm.render("EVENT LOG", True, TEXT_DIM)
        self.screen.blit(ev_hdr, (pad, y_pos))
        y_pos += 15
        for line in self._event_log:
            surf = self.font_sm.render(line[:38], True, TEXT_DIM)
            self.screen.blit(surf, (pad, y_pos))
            y_pos += 13

    # ── screenshot ───────────────────────────────────────────────────────
    def screenshot(self, filename: str = "genesis_screenshot.png"):
        pygame.image.save(self.screen, filename)

    # ── tick ─────────────────────────────────────────────────────────────
    def tick(self, fps: int):
        self.clock.tick(fps)
