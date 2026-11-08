"""Contract for plugins that consume outputs produced earlier in a cycle."""
from abc import ABC, abstractmethod


class ICycleResultConsumer(ABC):
    """Receives the results accumulated by the orchestrator for one cycle."""

    @abstractmethod
    def consume_cycle_results(self, results: dict[str, dict]) -> None:
        """Consume outputs from plugins executed earlier in this cycle."""
        raise NotImplementedError
