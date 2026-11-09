# Dependencias de contratos de inyección de dependencias para plugins que consumen resultados de ciclo.
from abc import ABC, abstractmethod

class ICycleResultConsumer(ABC):
    # Recibe los resultados acumulados por el orquestador para un ciclo.
    @abstractmethod
    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        # Consume los resultados de un ciclo del orquestador. Cada resultado es un diccionario con la clave del plugin y su resultado.
        raise NotImplementedError
