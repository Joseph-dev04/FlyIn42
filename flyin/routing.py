import heapq
import math
from typing import Dict, List, Optional, Set, Tuple

from domain import NetworkGraph, Zone, ZoneType


class Path:

    def __init__(self, zones: List[Zone], total_cost: int) -> None:
        self.zones: List[Zone] = zones
        self.total_cost: int = total_cost
        self.assigned_drones_count: int = 0

    def get_estimated_finish_turn(self) -> int:
        return self.total_cost + self.assigned_drones_count


class Router:

    def __init__(self, graph: NetworkGraph) -> None:
        self.graph = graph

    def _euclidean_distance(self, z1: Zone, z2: Zone) -> float:
        return math.hypot(z1.x - z2.x, z1.y - z2.y)

    def find_single_path_astar(
        self,
        start: Zone,
        goal: Zone,
        ignored_zones: Optional[Set[str]] = None,
        ignored_edges: Optional[Set[Tuple[str, str]]] = None
    ) -> Optional[Path]:
        if ignored_zones is None:
            ignored_zones = set()
        if ignored_edges is None:
            ignored_edges = set()

        counter = 0
        pq: List[Tuple[float, int, str, List[Zone], int]] = []

        start_h = self._euclidean_distance(start, goal)
        heapq.heappush(pq, (start_h, counter, start.name, [start], 0))

        visited: Dict[str, int] = {}

        while pq:
            _, _, current_name, path, g_cost = heapq.heappop(pq)

            if current_name == goal.name:
                return Path(path, g_cost)

            if current_name in visited and visited[current_name] <= g_cost:
                continue
            visited[current_name] = g_cost

            for neighbor, conn in self.graph.adjacency_list[current_name]:
                if (
                    neighbor.zone_type == ZoneType.BLOCKED
                    or neighbor.name in ignored_zones
                ):
                    if neighbor.name != goal.name:
                        continue

                edge_key = tuple(sorted([current_name, neighbor.name]))
                if edge_key in ignored_edges:
                    continue

                move_cost = neighbor.get_movement_cost()
                tie_breaker_bonus = (
                    -0.1 if neighbor.zone_type == ZoneType.PRIORITY else 0.0
                    )

                new_g = g_cost + move_cost
                f_score = (
                    new_g +
                    self._euclidean_distance(neighbor, goal) +
                    tie_breaker_bonus
                )

                counter += 1
                heapq.heappush(
                    pq,
                    (
                        f_score,
                        counter, neighbor.name, path + [neighbor], new_g))

        return None

    def find_disjoint_paths(self) -> List[Path]:
        paths: List[Path] = []
        seen_path_signatures: Set[Tuple[str, ...]] = set()
        ignored_zones: Set[str] = set()
        ignored_edges: Set[Tuple[str, str]] = set()

        assert self.graph.start_hub is not None
        assert self.graph.end_hub is not None

        while True:
            path = self.find_single_path_astar(
                self.graph.start_hub,
                self.graph.end_hub,
                ignored_zones,
                ignored_edges
            )
            if not path:
                break

            path_signature = tuple(z.name for z in path.zones)
            if path_signature in seen_path_signatures:
                break

            seen_path_signatures.add(path_signature)
            paths.append(path)

            for zone in path.zones:
                if zone != self.graph.start_hub and zone != self.graph.end_hub:
                    if zone.max_drones == 1:
                        ignored_zones.add(zone.name)

        if not paths:
            fallback = (
                self.find_single_path_astar(
                    self.graph.start_hub, self.graph.end_hub)
                )
            if fallback:
                paths.append(fallback)

        return paths

    def assign_paths_to_drones(self, num_drones: int) -> Dict[int, Path]:
        paths = self.find_disjoint_paths()
        if not paths:
            raise ValueError("No valid path was found towards the 'end_hub'")

        assignments: Dict[int, Path] = {}

        for drone_id in range(1, num_drones + 1):
            best_path = min(paths, key=lambda p: p.get_estimated_finish_turn())
            assignments[drone_id] = best_path
            best_path.assigned_drones_count += 1

        return assignments
