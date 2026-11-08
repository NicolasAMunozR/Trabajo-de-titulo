"""Shared contract for camera and other frame-producing sensor adapters."""
from abc import abstractmethod
from typing import Optional, TypeAlias

import numpy as np
from numpy.typing import NDArray

from contracts.plugin_base import PluginBase

ImageArray: TypeAlias = NDArray[np.uint8]
CameraFrame: TypeAlias = ImageArray


class ICameraSensor(PluginBase):
    """Provides camera frames independently of the consumers that process them.

    A returned frame is a non-empty HxWx3 uint8 NumPy array in BGR order,
    matching OpenCV's native image format. ``None`` means that no frame was
    captured; implementations must not return generated data as a real sample.
    """

    @abstractmethod
    def capture_frame(self) -> Optional[CameraFrame]:
        """Capture one frame and make it the latest sample."""
        raise NotImplementedError

    @abstractmethod
    def get_latest_frame(self) -> Optional[CameraFrame]:
        """Return the frame captured during the current orchestrator cycle."""
        raise NotImplementedError
