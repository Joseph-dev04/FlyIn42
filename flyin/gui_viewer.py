import sys
from typing import Dict, List, Tuple
import pygame

from domain import NetworkGraph, ZoneType
from simulation import TurnLog, SimulationEngine
from routing import Path


# RGB COLOR
COLOR_MAP = {
    "green": (46, 204, 113),
    "yellow": (241, 196, 15),
    "red": (231, 76, 60),
    "blue": (52, 152, 219),
    "gray": (149, 165, 166),
    "purple": (155, 89, 182),
    "white": (236, 240, 241),
    "dark_bg": (30, 30, 36),
    "line": (127, 140, 141),
}


class PygameViewer:
    """Visualizador gráfico interactivo basado en Pygame."""

    def __init__(
            self,
            graph: NetworkGraph,
            drone_paths: Dict[int, Path],
            width: int = 1000, height: int = 800) -> None:
        pygame.init()
        pygame.font.init()

        self.graph = graph
        self.drone_paths = drone_paths
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Fly-in: Drone Routing Simulation")

        self.font = pygame.font.SysFont("Consolas", 14, bold=True)
        self.clock = pygame.time.Clock()

        self.engine = SimulationEngine(self.graph, self.drone_paths)
        self.turn_logs: List[TurnLog] = []
        self.current_turn_idx: int = 0
        self.auto_play: bool = False

        self.node_positions: Dict[str, Tuple[int, int]] = (
            self._calculate_screen_positions())

    def _calculate_screen_positions(self) -> Dict[str, Tuple[int, int]]:
        if not self.graph.zones:
            return {}

        x_coords = [z.x for z in self.graph.zones.values()]
        y_coords = [z.y for z in self.graph.zones.values()]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        padding = 100
        drawable_w = self.width - (2 * padding)
        drawable_h = self.height - (2 * padding)

        range_x = (max_x - min_x) if max_x != min_x else 1
        range_y = (max_y - min_y) if max_y != min_y else 1

        positions: Dict[str, Tuple[int, int]] = {}
        for zone_name, zone in self.graph.zones.items():
            screen_x = int(padding + ((zone.x - min_x) / range_x) * drawable_w)
            screen_y = int(padding + ((zone.y - min_y) / range_y) * drawable_h)
            positions[zone_name] = (screen_x, screen_y)

        return positions

    def run(self) -> None:
        running = True

        self.turn_logs = self.engine.run_full_simulation()

        while running:
            self.screen.fill(COLOR_MAP["dark_bg"])
            self._handle_events()

            if self.auto_play and self.current_turn_idx < len(self.turn_logs):
                self.current_turn_idx += 1
                pygame.time.delay(500)

            self._draw_connections()
            self._draw_zones()
            self._draw_drones_and_info()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if self.current_turn_idx < len(self.turn_logs):
                        self.current_turn_idx += 1
                elif event.key == pygame.K_LEFT:
                    if self.current_turn_idx > 0:
                        self.current_turn_idx -= 1
                elif event.key == pygame.K_SPACE:
                    self.auto_play = not self.auto_play

    def _draw_connections(self) -> None:

        for conn in self.graph.connections:
            p1 = self.node_positions[conn.zone1.name]
            p2 = self.node_positions[conn.zone2.name]
            pygame.draw.line(self.screen, COLOR_MAP["line"], p1, p2, 2)

    def _draw_zones(self) -> None:

        for name, zone in self.graph.zones.items():
            pos = self.node_positions[name]

            color = (
                COLOR_MAP.get(zone.color, COLOR_MAP["blue"])
                if zone.color
                else COLOR_MAP["blue"]
                )
            if zone == self.graph.start_hub:
                color = COLOR_MAP["green"]
            elif zone == self.graph.end_hub:
                color = COLOR_MAP["yellow"]
            elif zone.zone_type == ZoneType.RESTRICTED:
                color = COLOR_MAP["red"]
            elif zone.zone_type == ZoneType.BLOCKED:
                color = COLOR_MAP["gray"]

            pygame.draw.circle(self.screen, color, pos, 22)
            pygame.draw.circle(self.screen, (255, 255, 255), pos, 22, 2)

            label = self.font.render(zone.name, True, COLOR_MAP["white"])
            self.screen.blit(label, (pos[0] - 15, pos[1] - 35))

    def _draw_drones_and_info(self) -> None:
        turn_text = f"Turno: {self.current_turn_idx} / {len(self.turn_logs)}"
        control_text = "FLECHAS: manual | ESPACIO: Auto Play"

        lbl_turn = self.font.render(turn_text, True, COLOR_MAP["white"])
        lbl_ctrl = self.font.render(control_text, True, COLOR_MAP["gray"])

        self.screen.blit(lbl_turn, (20, 20))
        self.screen.blit(lbl_ctrl, (20, 45))

        if 0 < self.current_turn_idx <= len(self.turn_logs):
            current_log = self.turn_logs[self.current_turn_idx - 1]
            log_str = f"Movimientos: {current_log.to_string()}"
            lbl_log = self.font.render(log_str, True, COLOR_MAP["yellow"])
            self.screen.blit(lbl_log, (20, 70))
