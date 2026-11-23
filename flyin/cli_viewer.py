from typing import List
from simulation import TurnLog


class CLIViewer:

    @staticmethod
    def print_simulation_logs(logs: List[TurnLog]) -> None:
        for log in logs:
            print(log.to_string())

    @staticmethod
    def print_metrics(total_turns: int, total_drones: int) -> None:
        """Muestra metricas secundarias util para peer-evaluation."""
        print("\n--- Metricas de Rendimiento ---")
        print(f"Total de turnos: {total_turns}")
        print(f"Total de drones: {total_drones}")
        print(f"Promedio de drones movidos por turno:"
              f" {total_drones / total_turns:.2f}")
