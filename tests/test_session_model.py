import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "multi_script_editor"
sys.path.insert(0, str(PACKAGE_ROOT))

from core import session_model  # noqa: E402
from widgets.tabWidget import tabWidgetClass  # noqa: E402


class SessionModelTests(unittest.TestCase):
    def test_user_preference_folder_is_resolved_once(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(session_model, "SettingsModel") as settings_model:
                settings_model.return_value._get_user_pref_folder.return_value = folder

                model = session_model.SessionModel()
                model.getBackupPath()
                model.getBackupPath()
                model.getSessionsFolder()
                model.getSessionsFolder()

            settings_model.assert_called_once_with()
            self.assertEqual(
                model.path,
                os.path.normpath(os.path.join(folder, session_model.sessionFilename)),
            )
            self.assertEqual(
                model.getBackupPath(),
                os.path.normpath(os.path.join(folder, session_model.backupFilename)),
            )

    def test_tabs_saved_by_two_models_are_merged_once(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(session_model, "SettingsModel") as settings_model:
                settings_model.return_value._get_user_pref_folder.return_value = folder
                first = session_model.SessionModel()
                second = session_model.SessionModel()

            first.writeSession([{'name': 'CW', 'text': 'carlos'}])
            second.readSession()
            second.writeSession([
                {'name': 'CW', 'text': 'carlos'},
                {'name': 'Other', 'text': 'other'},
            ])

            self.assertEqual(
                [('CW', 'carlos'), ('Other', 'other')],
                [(tab['name'], tab['text']) for tab in first.readSession()],
            )

    def test_loading_a_duplicated_session_keeps_one_identical_tab(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(session_model, "SettingsModel") as settings_model:
                settings_model.return_value._get_user_pref_folder.return_value = folder
                model = session_model.SessionModel()

            model._write_json(model.path, [
                {'name': 'CW', 'text': 'carlos'},
                {'name': 'CW', 'text': 'carlos'},
            ])

            self.assertEqual(1, len(model.readSession()))

    def test_identical_new_tabs_keep_distinct_session_ids(self):
        tabs = session_model.SessionModel._merge_session_tabs(
            [],
            [
                {'name': 'New Tab', 'text': '', 'session_id': 'first'},
                {'name': 'New Tab', 'text': '', 'session_id': 'second'},
            ],
            [],
        )

        self.assertEqual(['first', 'second'], [tab['session_id'] for tab in tabs])

    def test_session_tab_names_are_read_without_restoring_the_session(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(session_model, "SettingsModel") as settings_model:
                settings_model.return_value._get_user_pref_folder.return_value = folder
                model = session_model.SessionModel()

            model._write_json(model.path, [{'name': 'New Tab 4'}])

            self.assertEqual(['New Tab 4'], model.getSessionTabNames())

    def test_new_tab_name_uses_open_and_saved_tab_numbers(self):
        tabs = SimpleNamespace(
            count=lambda: 2,
            tabText=lambda index: ['New Tab 1', 'New Tab 3'][index],
            p=SimpleNamespace(
                _presenter=SimpleNamespace(
                    session_model=SimpleNamespace(
                        getSessionTabNames=lambda: ['New Tab 4']
                    )
                )
            ),
        )

        self.assertEqual(
            'New Tab 5', tabWidgetClass._next_untitled_tab_name(tabs)
        )



if __name__ == "__main__":
    unittest.main()
