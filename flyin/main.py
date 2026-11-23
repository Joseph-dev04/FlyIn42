import argparse
import sys
from typing import NoReturn

from cli_viewer import CLIViewer
from gui_viewer import PygameViewer
from parser import MapParser, ParsingError
from routing import Router


def error_exit(message: str, code: int = 1) -> NoReturn:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fly-in: Sistema de enrutamiento y simulación de drones."
    )
    parser.add_argument("map_file", type=str, help="Path to the map file .map")
    parser.add_argument(
        "--gui", action="store_true",
        help="Activate the interactive graphical interface using Pygame"
    )

    args = parser.parse_args()

    # Parsing
    map_parser = MapParser()
    try:
        graph, nb_drones = map_parser.parse_file(args.map_file)
    except (ParsingError, ValueError, FileNotFoundError) as exc:
        error_exit(str(exc))

    router = Router(graph)
    try:
        assignments = router.assign_paths_to_drones(nb_drones)
    except ValueError as exc:
        error_exit(f"Fallo en la planificación de rutas: {exc}")

    if args.gui:
        viewer = PygameViewer(graph, assignments)
        viewer.run()
    else:
        from simulation import SimulationEngine

        engine = SimulationEngine(graph, assignments)
        logs = engine.run_full_simulation()
        CLIViewer.print_simulation_logs(logs)
        CLIViewer.print_metrics(len(logs), nb_drones)


if __name__ == "__main__":
    main()
