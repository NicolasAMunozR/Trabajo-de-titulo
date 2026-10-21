"""Dependency-injection contract for plugins that consume camera frames."""
from abc import ABC, abstractmethod

from contracts.i_camera_sensor import ICameraSensor


class ICameraFrameConsumer(ABC):
    """Receives its frame source from the orchestrator, never opens a camera."""

    @abstractmethod
    def set_camera_sensor(self, sensor: ICameraSensor) -> None:
        """Bind the configured camera sensor before plugin initialization."""
        raise NotImplementedError
