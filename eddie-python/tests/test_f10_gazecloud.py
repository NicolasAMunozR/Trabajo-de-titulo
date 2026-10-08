import importlib.util
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / 'prototypes' / 'rad_funcionalidades' / 'demo_real_f10.py'


def test_demo_can_expose_gazecloud_fallback_helpers():
    spec = importlib.util.spec_from_file_location('demo_real_f10', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert hasattr(module, 'maybe_start_local_gazecloud_fallback')
    assert callable(module.maybe_start_local_gazecloud_fallback)
    assert hasattr(module, 'build_camera_gaze_server')
    assert callable(module.build_camera_gaze_server)
