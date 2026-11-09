# Dependencias de contratos de inyección de dependencias para plugins que consumen resultados de ciclo.
from abc import ABC, abstractmethod


class ICycleResultConsumer(ABC):
    # Recibe los resultados acumulados por el orquestador para un ciclo.

    @abstractmethod
    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        # Consume los resultados de los plugins que se ejecutaron antes en este ciclo.
        raise NotImplementedError
