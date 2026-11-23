from typing import Dict, List, Set

from domain import Connection, Drone, NetworkGraph, Zone, ZoneType
from routing import Path


class TurnLog:

    def __init__(self, turn_number: int) -> None:
        self.turn_number: int = turn_number
        self.movements: List[str] = []

    def add_movement(self, drone_id: int, target: str) -> None:
        self.movements.append(f"D{drone_id}-{target}")

    def to_string(self) -> str:
        return " ".join(self.movements)


class SimulationEngine:

    def __init__(
            self,
            graph: NetworkGraph, drone_paths: Dict[int, Path]) -> None:
        self.graph = graph
        self.drone_paths = drone_paths
        assert self.graph.start_hub is not None
        assert self.graph.end_hub is not None
        self.start_hub = self.graph.start_hub
        self.end_hub = self.graph.end_hub
        self.drones: Dict[int, Drone] = {}
        self.drone_path_indices: Dict[int, int] = {}

        for drone_id in sorted(drone_paths.keys()):
            drone = Drone(drone_id, self.start_hub)
            self.drones[drone_id] = drone
            self.drone_path_indices[drone_id] = 0
            self.start_hub.current_drones.append(drone)

        self.delivered_drones: Set[int] = set()
        self.turn_logs: List[TurnLog] = []

    def is_finished(self) -> bool:
        return len(self.delivered_drones) == len(self.drones)

    def step_turn(self) -> TurnLog:

        current_turn = len(self.turn_logs) + 1
        log = TurnLog(current_turn)

        active_drone_ids = [
            d_id for d_id, d in self.drones.items()
            if d_id not in self.delivered_drones
        ]
        for drone_id in active_drone_ids:
            drone = self.drones[drone_id]
            if drone.in_transit_connection is not None:
                drone.turns_remaining_in_transit -= 1
                if drone.turns_remaining_in_transit == 0:
                    target_zone = drone.target_zone
                    assert target_zone is not None
                    conn = drone.in_transit_connection
                    if drone in conn.active_transits:
                        del conn.active_transits[drone]
                    drone.current_zone = target_zone
                    target_zone.current_drones.append(drone)
                    drone.in_transit_connection = None
                    drone.target_zone = None
                    log.add_movement(drone.id, target_zone.name)

                    if target_zone == self.end_hub:
                        self.delivered_drones.add(drone.id)
        for drone_id in active_drone_ids:
            drone = self.drones[drone_id]
            if (
                drone.in_transit_connection is not None
                or drone_id in self.delivered_drones
            ):
                continue

            current_idx = self.drone_path_indices[drone_id]
            path = self.drone_paths[drone_id]

            if current_idx >= len(path.zones) - 1:
                continue

            next_zone = path.zones[current_idx + 1]
            current_zone = drone.current_zone

            conn = self._get_connection_between(current_zone, next_zone)

            if not conn.has_link_capacity():
                continue

            if next_zone.zone_type == ZoneType.RESTRICTED:
                if next_zone != self.end_hub and not next_zone.has_capacity():
                    continue

                current_zone.current_drones.remove(drone)
                drone.in_transit_connection = conn
                drone.target_zone = next_zone
                drone.turns_remaining_in_transit = 1
                conn.active_transits[drone] = 1

                self.drone_path_indices[drone_id] += 1
                conn_name = f"{current_zone.name}-{next_zone.name}"
                log.add_movement(drone.id, conn_name)

            else:
                can_enter = (
                    (next_zone == self.end_hub) or next_zone.has_capacity()
                    )
                if can_enter:
                    current_zone.current_drones.remove(drone)
                    drone.current_zone = next_zone
                    next_zone.current_drones.append(drone)

                    self.drone_path_indices[drone_id] += 1
                    log.add_movement(drone.id, next_zone.name)

                    if next_zone == self.end_hub:
                        self.delivered_drones.add(drone.id)

        self.turn_logs.append(log)
        return log

    def run_full_simulation(self) -> List[TurnLog]:
        while not self.is_finished():
            self.step_turn()
        return self.turn_logs

    def _get_connection_between(self, z1: Zone, z2: Zone) -> Connection:
        for neighbor, conn in self.graph.adjacency_list[z1.name]:
            if neighbor.name == z2.name:
                return conn
        raise ValueError(f"There is no direct connection between"
                         f"'{z1.name}' y '{z2.name}'")
