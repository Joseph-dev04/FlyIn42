import re
from typing import Dict, Tuple

from domain import NetworkGraph, Zone, ZoneType


class ParsingError(Exception):
    def __init__(self, line_number: int, message: str) -> None:
        super().__init__(f"Error de parsing en la línea"
                         f"{line_number}: {message}")
        self.line_number = line_number


class MapParser:

    LINE_PATTERN = re.compile(r"^\s*([a-zA-Z0-9_]+):\s*(.+)$")
    METADATA_PATTERN = re.compile(r"\[(.*?)\]")
    INVALID_NAME_CHARS = re.compile(r"[\s\-]")

    def __init__(self) -> None:
        self.graph = NetworkGraph()
        self.nb_drones: int = 0
        self._parsed_connections: set[Tuple[str, str]] = set()

    def parse_file(self, file_path: str) -> Tuple[NetworkGraph, int]:
        with open(file_path, "r", encoding="utf-8") as file:
            for line_idx, raw_line in enumerate(file, start=1):

                line = raw_line.split("#")[0].strip()
                if not line:
                    continue

                if self.nb_drones == 0 and not self.graph.zones:
                    if line.startswith("nb_drones:"):
                        self.nb_drones = self._parse_nb_drones(line, line_idx)
                        continue
                    else:
                        raise ParsingError(line_idx, "The first non-empty line"
                                           "must be 'nb_drones: <numero>'")

                match = self.LINE_PATTERN.match(line)
                if not match:
                    raise ParsingError(line_idx, f"Invalid line syntax:{line}")

                prefix, content = match.group(1), match.group(2).strip()
                self._process_line_type(prefix, content, line_idx)

        self._validate_final_graph()
        return self.graph, self.nb_drones

    def _parse_nb_drones(self, line: str, line_num: int) -> int:
        parts = line.split(":")
        if len(parts) != 2:
            raise ParsingError(line_num, "Incorrect format for nb_drones")
        try:
            val = int(parts[1].strip())
            if val <= 0:
                raise ParsingError(line_num, "The number of drones must be"
                                   "a positive integer.")
            return val
        except ValueError:
            raise ParsingError(line_num, f"Invalid drone value:"
                               f" '{parts[1].strip()}'")

    def _process_line_type(self,
                           prefix: str, content: str, line_num: int) -> None:
        if prefix in ("start_hub", "end_hub", "hub"):
            self._parse_zone(prefix, content, line_num)
        elif prefix == "connection":
            self._parse_connection(content, line_num)
        else:
            raise ParsingError(line_num, f"Unknown prefix: '{prefix}'")

    def _extract_metadata(self, content: str) -> Tuple[str, Dict[str, str]]:
        meta_match = self.METADATA_PATTERN.search(content)
        metadata_dict: Dict[str, str] = {}

        if meta_match:
            raw_meta = meta_match.group(1).strip()
            tokens = raw_meta.split()
            for token in tokens:
                if "=" in token:
                    k, v = token.split("=", 1)
                    metadata_dict[k] = v
                else:
                    metadata_dict["zone"] = token

            base_content = content[:meta_match.start()].strip()
        else:
            base_content = content.strip()

        return base_content, metadata_dict

    def _parse_zone(self, prefix: str, content: str, line_num: int) -> None:
        base_content, metadata = self._extract_metadata(content)
        tokens = base_content.split()

        if len(tokens) != 3:
            raise ParsingError(line_num, f"Definition of invalid zone."
                               f"It was expected '<nombre> <x> <y>', "
                               f"was obtained '{base_content}'")

        name, x_str, y_str = tokens[0], tokens[1], tokens[2]

        if self.INVALID_NAME_CHARS.search(name):
            raise ParsingError(line_num, f"The name of the area '{name}' "
                               f"must not contain spaces or hyphens")

        if name in self.graph.zones:
            raise ParsingError(line_num, f"Duplicate zone name: '{name}'")

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise ParsingError(line_num, f"Invalid coordinates for the zone"
                               f" '{name}': ({x_str}, {y_str})")

        zone_type_str = metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError:
            raise ParsingError(line_num, f"Invalid zone type:"
                               f"'{zone_type_str}'")

        max_drones = 1
        if "max_drones" in metadata:
            try:
                max_drones = int(metadata["max_drones"])
                if max_drones <= 0:
                    raise ParsingError(line_num, "max_drones must be "
                                       "a positive integer")
            except ValueError:
                raise ParsingError(line_num, f"Valor de max_drones invalid"
                                   f": '{metadata['max_drones']}'")

        color = metadata.get("color", None)

        zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=zone_type,
            max_drones=max_drones,
            color=color
        )

        if prefix == "start_hub":
            if self.graph.start_hub is not None:
                raise ParsingError(line_num, "More than one has"
                                   "been defined 'start_hub'")
            self.graph.start_hub = zone
        elif prefix == "end_hub":
            if self.graph.end_hub is not None:
                raise ParsingError(line_num, "More than one has"
                                   " been defined 'end_hub'")
            self.graph.end_hub = zone

        self.graph.add_zone(zone)

    def _parse_connection(self, content: str, line_num: int) -> None:
        base_content, metadata = self._extract_metadata(content)

        if "-" not in base_content:
            raise ParsingError(line_num, f"Invalid connection format"
                               f": '{base_content}'. It was expected"
                               " 'zona1-zona2'")

        z1_name, z2_name = base_content.split("-", 1)
        z1_name, z2_name = z1_name.strip(), z2_name.strip()

        if z1_name not in self.graph.zones:
            raise ParsingError(line_num, f"The area of origin '{z1_name}'"
                               " it does not exist")
        if z2_name not in self.graph.zones:
            raise ParsingError(line_num, f"The area of origin '{z2_name}'"
                               " it does not exist")

        edge_pair = tuple(sorted([z1_name, z2_name]))
        if edge_pair in self._parsed_connections:
            raise ParsingError(line_num, f"Duplicate connection"
                               f" between '{z1_name}' and '{z2_name}'")
        self._parsed_connections.add(edge_pair)

        max_link_capacity = 1
        if "max_link_capacity" in metadata:
            try:
                max_link_capacity = int(metadata["max_link_capacity"])
                if max_link_capacity <= 0:
                    raise ParsingError(line_num, "max_link_capacity must"
                                       " be a positive integer")
            except ValueError:
                raise ParsingError(line_num, f"Value max_link_capacity invalid"
                                   f": '{metadata['max_link_capacity']}'")

        self.graph.add_connection(z1_name, z2_name, max_link_capacity)

    def _validate_final_graph(self) -> None:
        if self.graph.start_hub is None:
            raise ValueError("The file did not specify any 'start_hub'")
        if self.graph.end_hub is None:
            raise ValueError("The file did not specify any 'end_hub'")
