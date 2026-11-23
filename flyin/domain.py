from enum import Enum
from typing import Dict, List, Optional, Tuple


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone_type: ZoneType = ZoneType.NORMAL,
        max_drones: int = 1,
        color: Optional[str] = None,
    ) -> None:
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.zone_type: ZoneType = zone_type
        self.max_drones: int = max_drones
        self.color: Optional[str] = color

        self.current_drones: List["Drone"] = []

    def has_capacity(self) -> bool:
        return len(self.current_drones) < self.max_drones

    def get_movement_cost(self) -> int:
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1


class Connection:
    def __init__(
        self,
        zone1: Zone,
        zone2: Zone,
        max_link_capacity: int = 1
    ) -> None:
        self.zone1: Zone = zone1
        self.zone2: Zone = zone2
        self.max_link_capacity: int = max_link_capacity

        self.active_transits: Dict["Drone", int] = {}

    def get_opponent(self, zone: Zone) -> Zone:

        if zone == self.zone1:
            return self.zone2
        return self.zone1

    def has_link_capacity(self) -> bool:

        return len(self.active_transits) < self.max_link_capacity


class Drone:
    def __init__(self, drone_id: int, start_zone: Zone) -> None:
        self.id: int = drone_id
        self.identifier: str = f"D{drone_id}"
        self.current_zone: Zone = start_zone

        self.in_transit_connection: Optional[Connection] = None
        self.target_zone: Optional[Zone] = None
        self.turns_remaining_in_transit: int = 0


class NetworkGraph:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.connections: List[Connection] = []
        self.adjacency_list: Dict[str, List[Tuple[Zone, Connection]]] = {}

        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        self.zones[zone.name] = zone
        self.adjacency_list[zone.name] = []

    def add_connection(
            self,
            zone1_name: str,
            zone2_name: str, max_link_capacity: int = 1) -> None:
        z1 = self.zones[zone1_name]
        z2 = self.zones[zone2_name]
        conn = Connection(z1, z2, max_link_capacity)
        self.connections.append(conn)
        self.adjacency_list[z1.name].append((z2, conn))
        self.adjacency_list[z2.name].append((z1, conn))
