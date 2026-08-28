from core.shortcut_model import ShortcutProfilesModel
from vendor.Qt.QtCore import Qt
from vendor.Qt.QtGui import QColor, QFont, QKeySequence, QPalette
from vendor.Qt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class shortcutsClass(QDialog):
    def __init__(self, parent):
        super(shortcutsClass, self).__init__(parent)
        self.editor = parent
        self._entries = parent.shortcutEntries()
        self._entry_by_id = {entry['id']: entry for entry in self._entries}
        self._defaults = parent.defaultShortcutMapping()
        self._working = {}
        self._current_profile = ShortcutProfilesModel.DEFAULT_PROFILE
        self._dirty = False
        self._loading_profile = False

        self.setWindowTitle('Shortcut Manager')
        self.resize(920, 640)
        self.setMinimumSize(720, 480)
        self._build_ui()
        self._apply_parent_theme()
        self._reload_profiles(parent.activeShortcutProfile())
        self._fit_initial_geometry()
        self._center_on_editor()

    @staticmethod
    def _exec(dialog):
        method = getattr(dialog, 'exec', None) or getattr(dialog, 'exec_')
        return method()

    @staticmethod
    def _normalize(sequence):
        return QKeySequence(sequence).toString(QKeySequence.PortableText)

    def _apply_parent_theme(self, dialog=None):
        widget = dialog or self
        colors = getattr(self.editor, '_current_colors_cache', {})
        use_theme_font = colors.get('use_theme_font_on_menus', False)
        source_font = (
            getattr(self.editor, 'theme_font', self.editor.font())
            if use_theme_font else QApplication.font('QMenu')
        )
        font = QFont(source_font)
        try:
            font_size = int(colors.get('menu_text_size', colors.get('textsize', font.pointSize())))
        except (TypeError, ValueError):
            font_size = font.pointSize()
        if font_size > 0:
            font.setPointSize(font_size)

        window_value = colors.get('window', (50, 50, 50))
        background_value = colors.get('background', (40, 40, 40))
        alternate_value = colors.get('completer_alt_background', (65, 65, 65))
        text_value = colors.get('default', (210, 210, 210))
        muted_value = colors.get('tab_text', (128, 128, 128))
        selected_value = colors.get('selection_background', (85, 85, 85))

        def rgb(key, fallback):
            value = colors.get(key, fallback)
            return 'rgb({0}, {1}, {2})'.format(*value)

        window = rgb('window', (50, 50, 50))
        background = rgb('background', (40, 40, 40))
        alternate = rgb('completer_alt_background', (65, 65, 65))
        hover = rgb('completer_hover_background', (85, 85, 85))
        text = rgb('default', (210, 210, 210))
        muted = rgb('tab_text', (128, 128, 128))
        border = rgb('border', (85, 85, 85))
        selected = rgb('selection_background', (85, 85, 85))
        font_rule = "font-family: '%s';" % font.family() if font.family() else ''
        style = """
            QDialog { background-color: %(window)s; color: %(text)s; %(font_rule)s font-size: %(font_size)spt; }
            QLabel, QCheckBox { color: %(text)s; %(font_rule)s font-size: %(font_size)spt; }
            QLineEdit, QKeySequenceEdit, QComboBox, QListWidget, QTreeWidget {
                background-color: %(background)s;
                alternate-background-color: %(alternate)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                selection-background-color: %(selected)s;
                selection-color: %(text)s;
                %(font_rule)s font-size: %(font_size)spt;
            }
            QComboBox QAbstractItemView {
                background-color: %(background)s;
                alternate-background-color: %(alternate)s;
                color: %(text)s;
                selection-background-color: %(selected)s;
                selection-color: %(text)s;
                %(font_rule)s font-size: %(font_size)spt;
            }
            QHeaderView::section {
                background-color: %(window)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                padding: 3px;
                %(font_rule)s font-size: %(font_size)spt;
            }
            QPushButton {
                background-color: %(background)s;
                color: %(text)s;
                border: 1px solid %(border)s;
                padding: 6px 14px;
                %(font_rule)s font-size: %(font_size)spt;
            }
            QPushButton:hover { background-color: %(hover)s; }
            QPushButton:disabled { color: %(muted)s; }
        """ % {
            'window': window,
            'background': background,
            'alternate': alternate,
            'hover': hover,
            'text': text,
            'muted': muted,
            'border': border,
            'selected': selected,
            'font_rule': font_rule,
            'font_size': max(1, font_size),
        }
        widget.setFont(font)
        widget.setStyleSheet(self.editor.styleSheet() + style)
        palette = widget.palette()
        palette.setColor(QPalette.Window, QColor(*window_value))
        palette.setColor(QPalette.WindowText, QColor(*text_value))
        palette.setColor(QPalette.Base, QColor(*background_value))
        palette.setColor(QPalette.AlternateBase, QColor(*alternate_value))
        palette.setColor(QPalette.Text, QColor(*text_value))
        palette.setColor(QPalette.Button, QColor(*background_value))
        palette.setColor(QPalette.ButtonText, QColor(*text_value))
        palette.setColor(QPalette.Highlight, QColor(*selected_value))
        palette.setColor(QPalette.HighlightedText, QColor(*text_value))
        if hasattr(QPalette, 'PlaceholderText'):
            palette.setColor(QPalette.PlaceholderText, QColor(*muted_value))
        widget.setPalette(palette)
        for child in widget.findChildren(QWidget):
            child.setFont(font)
            child.setPalette(palette)

    @staticmethod
    def _set_help(widget, text):
        widget.setToolTip(text)
        widget.setStatusTip(text)

    def _button(self, text, help_text):
        button = QPushButton(text, self)
        self._set_help(button, help_text)
        return button

    def _build_ui(self):
        root = QVBoxLayout(self)

        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel('Profile:', self))
        self.profile_combo = QComboBox(self)
        self._set_help(self.profile_combo, 'Choose the shortcut configuration to view or edit')
        profile_row.addWidget(self.profile_combo, 1)
        self.save_as_button = self._button('Save As...', 'Save these shortcuts as a new profile')
        self.delete_profile_button = self._button('Delete', 'Delete the selected custom shortcut profile')
        profile_row.addWidget(self.save_as_button)
        profile_row.addWidget(self.delete_profile_button)
        root.addLayout(profile_row)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText('Search by action name, menu, or shortcut...')
        self.search_edit.setClearButtonEnabled(True)
        self._set_help(self.search_edit, 'Filter actions by name, menu path, or assigned key sequence')
        search_row.addWidget(self.search_edit, 1)
        for label, attribute, help_text in (
            ('Ctrl', 'ctrl_filter', 'Show shortcuts that use Ctrl'),
            ('Alt', 'alt_filter', 'Show shortcuts that use Alt'),
            ('Shift', 'shift_filter', 'Show shortcuts that use Shift'),
            ('Meta', 'meta_filter', 'Show shortcuts that use Meta or Command'),
            ('Unassigned', 'unassigned_filter', 'Show only actions without a shortcut'),
        ):
            checkbox = QCheckBox(label, self)
            self._set_help(checkbox, help_text)
            setattr(self, attribute, checkbox)
            search_row.addWidget(checkbox)
        root.addLayout(search_row)

        splitter = QSplitter(Qt.Horizontal, self)
        self.actions_tree = QTreeWidget(splitter)
        self.actions_tree.setHeaderLabels(['Action', 'Shortcuts', 'Menu'])
        self.actions_tree.setAlternatingRowColors(True)
        self.actions_tree.setRootIsDecorated(False)
        self.actions_tree.setSortingEnabled(False)
        header = self.actions_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.actions_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        details = QWidget(splitter)
        details_layout = QVBoxLayout(details)
        self.action_label = QLabel('Select an action', details)
        self.action_label.setWordWrap(True)
        details_layout.addWidget(self.action_label)
        self.shortcuts_list = QListWidget(details)
        self._set_help(self.shortcuts_list, 'Shortcuts assigned to the selected action')
        details_layout.addWidget(self.shortcuts_list, 1)

        shortcut_buttons = QHBoxLayout()
        self.add_button = self._button('Add...', 'Add another shortcut to the selected action')
        self.edit_button = self._button('Edit...', 'Replace the selected shortcut')
        self.remove_button = self._button('Remove', 'Remove the selected shortcut from this action')
        shortcut_buttons.addWidget(self.add_button)
        shortcut_buttons.addWidget(self.edit_button)
        shortcut_buttons.addWidget(self.remove_button)
        details_layout.addLayout(shortcut_buttons)

        self.reset_action_button = self._button(
            'Reset Action',
            'Restore the selected action to its default shortcuts',
        )
        details_layout.addWidget(self.reset_action_button)

        splitter.addWidget(self.actions_tree)
        splitter.addWidget(details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.result_label = QLabel('', self)
        footer.addWidget(self.result_label, 1)
        self.reset_all_button = self._button('Restore Defaults', 'Restore every action to the built-in shortcuts')
        self.save_button = self._button('Save and Apply', 'Save this profile and apply it immediately')
        self.cancel_button = self._button('Cancel', 'Close without saving these changes')
        footer.addWidget(self.reset_all_button)
        footer.addWidget(self.save_button)
        footer.addWidget(self.cancel_button)
        root.addLayout(footer)

        self.profile_combo.currentTextChanged.connect(self._profile_changed)
        self.save_as_button.clicked.connect(self._save_as)
        self.delete_profile_button.clicked.connect(self._delete_profile)
        self.search_edit.textChanged.connect(self._filter_actions)
        for checkbox in (
            self.ctrl_filter,
            self.alt_filter,
            self.shift_filter,
            self.meta_filter,
            self.unassigned_filter,
        ):
            checkbox.toggled.connect(self._filter_actions)
        self.actions_tree.currentItemChanged.connect(self._action_selected)
        self.shortcuts_list.currentRowChanged.connect(self._shortcut_selected)
        self.shortcuts_list.itemDoubleClicked.connect(lambda item: self._edit_shortcut())
        self.add_button.clicked.connect(self._add_shortcut)
        self.edit_button.clicked.connect(self._edit_shortcut)
        self.remove_button.clicked.connect(self._remove_shortcut)
        self.reset_action_button.clicked.connect(self._reset_action)
        self.reset_all_button.clicked.connect(self._reset_all)
        self.save_button.clicked.connect(self._save_and_apply)
        self.cancel_button.clicked.connect(self.reject)

    def _reload_profiles(self, selected):
        names = self.editor.shortcutProfileNames()
        canonical = next(
            (name for name in names if name.casefold() == (selected or '').casefold()),
            ShortcutProfilesModel.DEFAULT_PROFILE,
        )
        self._loading_profile = True
        self.profile_combo.clear()
        self.profile_combo.addItems(names)
        self.profile_combo.setCurrentText(canonical)
        self._loading_profile = False
        self._load_profile(canonical)

    def _load_profile(self, name):
        self._current_profile = name
        self._working = self.editor.shortcutProfileMapping(name)
        self._dirty = False
        self.delete_profile_button.setEnabled(name != ShortcutProfilesModel.DEFAULT_PROFILE)
        self._populate_actions()

    def _profile_changed(self, name):
        if self._loading_profile or name == self._current_profile:
            return
        if self._dirty and not self._confirm_discard('Switch profiles'):
            self._loading_profile = True
            self.profile_combo.setCurrentText(self._current_profile)
            self._loading_profile = False
            return
        self._load_profile(name)

    def _populate_actions(self):
        selected_id = self._selected_action_id()
        self.actions_tree.clear()
        selected_item = None
        for entry in self._entries:
            item = QTreeWidgetItem([
                entry['label'],
                ', '.join(self._working.get(entry['id'], [])),
                entry['menu'],
            ])
            item.setData(0, Qt.UserRole, entry['id'])
            self.actions_tree.addTopLevelItem(item)
            if entry['id'] == selected_id:
                selected_item = item
        self._resize_action_columns()
        self._filter_actions()
        if selected_item is not None and not selected_item.isHidden():
            self.actions_tree.setCurrentItem(selected_item)
        else:
            self._select_first_visible()

    def _resize_action_columns(self):
        header = self.actions_tree.header()
        for column in (0, 2):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            self.actions_tree.resizeColumnToContents(column)
            width = self.actions_tree.columnWidth(column)
            header.setSectionResizeMode(column, QHeaderView.Fixed)
            self.actions_tree.setColumnWidth(column, width)

    def _fit_initial_geometry(self):
        """Size the first view so the widest action, shortcut, and menu fit."""
        header = self.actions_tree.header()
        for column in range(3):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        for column in range(3):
            self.actions_tree.resizeColumnToContents(column)
        fixed_widths = {
            column: self.actions_tree.columnWidth(column)
            for column in (0, 2)
        }
        table_width = sum(self.actions_tree.columnWidth(column) for column in range(3))
        desired_width = table_width + 420
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            desired_width = min(desired_width, int(available.width() * 0.95))
            desired_height = min(max(self.height(), 640), int(available.height() * 0.9))
        else:
            desired_height = max(self.height(), 640)
        self.resize(max(self.minimumWidth(), desired_width), desired_height)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        for column, width in fixed_widths.items():
            self.actions_tree.setColumnWidth(column, width)

    def _center_on_editor(self):
        parent = self.parentWidget()
        if parent is None:
            screen = QApplication.primaryScreen()
            if screen is not None:
                self.move(screen.availableGeometry().center() - self.rect().center())
            return
        target = parent.frameGeometry().center() - self.rect().center()
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            target.setX(max(available.left(), min(target.x(), available.right() - self.width() + 1)))
            target.setY(max(available.top(), min(target.y(), available.bottom() - self.height() + 1)))
        self.move(target)

    def _filter_actions(self):
        query = self.search_edit.text().strip().casefold()
        modifier_tokens = []
        for checkbox, token in (
            (self.ctrl_filter, 'ctrl+'),
            (self.alt_filter, 'alt+'),
            (self.shift_filter, 'shift+'),
            (self.meta_filter, 'meta+'),
        ):
            if checkbox.isChecked():
                modifier_tokens.append(token)

        visible_count = 0
        selected_hidden = False
        for index in range(self.actions_tree.topLevelItemCount()):
            item = self.actions_tree.topLevelItem(index)
            action_id = item.data(0, Qt.UserRole)
            sequences = self._working.get(action_id, [])
            searchable = ' '.join((item.text(0), item.text(1), item.text(2))).casefold()
            visible = not query or query in searchable
            if visible and self.unassigned_filter.isChecked():
                visible = not sequences
            elif visible and modifier_tokens:
                visible = any(
                    all(token in sequence.casefold() for token in modifier_tokens)
                    for sequence in sequences
                )
            item.setHidden(not visible)
            if visible:
                visible_count += 1
            elif item is self.actions_tree.currentItem():
                selected_hidden = True

        self.result_label.setText(
            '{0} of {1} actions'.format(visible_count, self.actions_tree.topLevelItemCount())
        )
        if selected_hidden or self.actions_tree.currentItem() is None:
            self._select_first_visible()

    def _select_first_visible(self):
        for index in range(self.actions_tree.topLevelItemCount()):
            item = self.actions_tree.topLevelItem(index)
            if not item.isHidden():
                self.actions_tree.setCurrentItem(item)
                return
        self.actions_tree.setCurrentItem(None)
        self._action_selected(None)

    def _selected_action_id(self):
        item = self.actions_tree.currentItem()
        return item.data(0, Qt.UserRole) if item is not None else None

    def _action_selected(self, current, previous=None):
        action_id = current.data(0, Qt.UserRole) if current is not None else None
        entry = self._entry_by_id.get(action_id)
        self.action_label.setText(
            '<b>{0}</b><br>{1}'.format(entry['label'], entry['menu'])
            if entry else 'Select an action'
        )
        self.shortcuts_list.clear()
        if action_id:
            self.shortcuts_list.addItems(self._working.get(action_id, []))
        enabled = bool(action_id)
        self.add_button.setEnabled(enabled)
        self.reset_action_button.setEnabled(enabled)
        self._shortcut_selected(self.shortcuts_list.currentRow())

    def _shortcut_selected(self, row):
        enabled = row >= 0 and bool(self._selected_action_id())
        self.edit_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)

    def _sequence_dialog(self, title, current=''):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Press the new shortcut, then choose OK.', dialog))
        sequence_edit = QKeySequenceEdit(dialog)
        if current:
            sequence_edit.setKeySequence(QKeySequence(current))
        layout.addWidget(sequence_edit)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        ok_button = QPushButton('OK', dialog)
        cancel_button = QPushButton('Cancel', dialog)
        self._set_help(ok_button, 'Use the captured key sequence')
        self._set_help(cancel_button, 'Cancel shortcut assignment')
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        self._apply_parent_theme(dialog)
        if self._exec(dialog) != QDialog.Accepted:
            return None
        return self._normalize(sequence_edit.keySequence())

    def _add_shortcut(self):
        sequence = self._sequence_dialog('Add Shortcut')
        if sequence:
            self._assign_shortcut(sequence)

    def _edit_shortcut(self):
        row = self.shortcuts_list.currentRow()
        if row < 0:
            return
        current = self.shortcuts_list.item(row).text()
        sequence = self._sequence_dialog('Edit Shortcut', current)
        if sequence:
            self._assign_shortcut(sequence, row)

    def _assign_shortcut(self, sequence, replace_index=None):
        action_id = self._selected_action_id()
        if not action_id:
            return
        sequence = self._normalize(sequence)
        current = list(self._working.get(action_id, []))
        existing_index = current.index(sequence) if sequence in current else -1
        if existing_index >= 0 and existing_index != replace_index:
            self._show_message('Shortcut already assigned', 'This action already uses {0}.'.format(sequence))
            return

        conflicts = [
            other_id for other_id, sequences in self._working.items()
            if other_id != action_id and sequence in sequences
        ]
        if conflicts and not self._confirm_reassign(sequence, conflicts):
            return
        for other_id in conflicts:
            self._working[other_id] = [
                value for value in self._working.get(other_id, [])
                if value != sequence
            ]

        if replace_index is None:
            current.append(sequence)
        else:
            current[replace_index] = sequence
        self._working[action_id] = current
        self._mark_changed(action_id)

    def _confirm_reassign(self, sequence, conflicts):
        labels = [self._entry_by_id[action_id]['label'] for action_id in conflicts]
        message = QMessageBox(self)
        message.setWindowTitle('Shortcut Conflict')
        message.setIcon(QMessageBox.Warning)
        message.setText('{0} is already assigned to:\n\n{1}'.format(sequence, '\n'.join(labels)))
        message.setInformativeText('Reassign it and remove it from the other action?')
        reassign_button = message.addButton('Reassign', QMessageBox.AcceptRole)
        message.addButton('Cancel', QMessageBox.RejectRole)
        self._apply_parent_theme(message)
        self._exec(message)
        return message.clickedButton() is reassign_button

    def _remove_shortcut(self):
        action_id = self._selected_action_id()
        row = self.shortcuts_list.currentRow()
        if not action_id or row < 0:
            return
        sequences = list(self._working.get(action_id, []))
        del sequences[row]
        self._working[action_id] = sequences
        self._mark_changed(action_id)

    def _reset_action(self):
        action_id = self._selected_action_id()
        if action_id:
            self._working[action_id] = list(self._defaults.get(action_id, []))
            self._mark_changed(action_id)

    def _reset_all(self):
        self._working = {
            action_id: list(sequences)
            for action_id, sequences in self._defaults.items()
        }
        self._dirty = True
        self._populate_actions()

    def _mark_changed(self, selected_id):
        self._dirty = True
        for index in range(self.actions_tree.topLevelItemCount()):
            item = self.actions_tree.topLevelItem(index)
            action_id = item.data(0, Qt.UserRole)
            item.setText(1, ', '.join(self._working.get(action_id, [])))
            if action_id == selected_id:
                self.actions_tree.setCurrentItem(item)
        self._filter_actions()
        self._resize_action_columns()
        self._action_selected(self.actions_tree.currentItem())

    def _save_as(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle('New Shortcut Profile')
        dialog.setLabelText('Profile name:')
        dialog.setTextValue(
            '' if self._current_profile == ShortcutProfilesModel.DEFAULT_PROFILE
            else self._current_profile + ' Copy'
        )
        self._apply_parent_theme(dialog)
        if self._exec(dialog) != QInputDialog.Accepted:
            return False
        name = dialog.textValue().strip()
        if name.casefold() in {item.casefold() for item in self.editor.shortcutProfileNames()}:
            self._show_message('Profile already exists', 'Choose a different profile name.')
            return False
        try:
            self.editor.saveShortcutProfile(name, self._working, activate=False)
        except (OSError, ValueError) as error:
            self._show_message('Could not save profile', str(error))
            return False
        self._reload_profiles(name)
        return True

    def _save_and_apply(self):
        if self._current_profile == ShortcutProfilesModel.DEFAULT_PROFILE:
            if self._dirty and not self._save_as():
                return
            if self._current_profile == ShortcutProfilesModel.DEFAULT_PROFILE:
                self.editor.applyShortcutProfile(self._current_profile, persist=True)
                self.accept()
                return
        try:
            self.editor.saveShortcutProfile(self._current_profile, self._working, activate=True)
        except (OSError, ValueError) as error:
            self._show_message('Could not save profile', str(error))
            return
        self._dirty = False
        self.accept()

    def _delete_profile(self):
        if self._current_profile == ShortcutProfilesModel.DEFAULT_PROFILE:
            return
        if not self._confirm(
            'Delete Shortcut Profile',
            'Delete the profile "{0}"?'.format(self._current_profile),
        ):
            return
        try:
            self.editor.deleteShortcutProfile(self._current_profile)
        except (OSError, ValueError) as error:
            self._show_message('Could not delete profile', str(error))
            return
        self._reload_profiles(ShortcutProfilesModel.DEFAULT_PROFILE)

    def _show_message(self, title, text):
        message = QMessageBox(self)
        message.setWindowTitle(title)
        message.setIcon(QMessageBox.Warning)
        message.setText(text)
        message.addButton(QMessageBox.Ok)
        self._apply_parent_theme(message)
        self._exec(message)

    def _confirm(self, title, text):
        message = QMessageBox(self)
        message.setWindowTitle(title)
        message.setText(text)
        yes_button = message.addButton(QMessageBox.Yes)
        message.addButton(QMessageBox.Cancel)
        self._apply_parent_theme(message)
        self._exec(message)
        return message.clickedButton() is yes_button

    def _confirm_discard(self, title):
        return self._confirm(title, 'Discard the unsaved shortcut changes?')

    def reject(self):
        if self._dirty and not self._confirm_discard('Unsaved Changes'):
            return
        self._dirty = False
        super(shortcutsClass, self).reject()

    def closeEvent(self, event):
        if self._dirty and not self._confirm_discard('Unsaved Changes'):
            event.ignore()
            return
        self._dirty = False
        super(shortcutsClass, self).closeEvent(event)
