import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / 'multi_script_editor'))

from core.settings_model import SettingsModel  # noqa: E402


class SettingsModelTests(unittest.TestCase):
    def test_independent_changes_are_merged(self):
        with tempfile.TemporaryDirectory() as folder:
            original_folder = SettingsModel._get_user_pref_folder
            try:
                SettingsModel._get_user_pref_folder = lambda _model: folder
                SettingsModel._cached_settings = None
                first = SettingsModel()
                second = SettingsModel()
                first_settings = first.read_settings().copy()
                second_settings = second.read_settings().copy()
                first_settings['wrap'] = False
                second_settings['out_wrap'] = False
                first.write_settings(first_settings)
                second.write_settings(second_settings)
                saved = second.read_settings_from_disk()
            finally:
                SettingsModel._get_user_pref_folder = original_folder
                SettingsModel._cached_settings = None

        self.assertFalse(saved['wrap'])
        self.assertFalse(saved['out_wrap'])


if __name__ == '__main__':
    unittest.main()
