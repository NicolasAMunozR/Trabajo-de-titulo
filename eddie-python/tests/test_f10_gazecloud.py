import pytest

from hardware.eye_tracker import EyeTrackerPlugin


def test_eye_tracker_parses_gazecloud_message_without_hardware():
    plugin = EyeTrackerPlugin()
    plugin._store_message(
        '{"values":{"frame":{"avg":{"x":960,"y":540}}}}'
    )

    gaze = plugin.get_gaze_point()

    assert gaze is not None
    assert gaze.x == pytest.approx(0.5)
    assert gaze.y == pytest.approx(0.5)


def test_eye_tracker_discards_gaze_outside_screen():
    plugin = EyeTrackerPlugin()
    plugin._store_message('{"x":2200,"y":540}')

    assert plugin.get_gaze_point() is None
