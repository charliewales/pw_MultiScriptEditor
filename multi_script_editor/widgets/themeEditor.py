import json
import os

from core.settings_model import SettingsModel, ThemesModel
from vendor.Qt.QtCore import QSize, Qt, QTimer
from vendor.Qt.QtGui import QColor, QFont, QIcon, QPixmap
from vendor.Qt.QtWidgets import (
    QAction,
    QApplication,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFontDialog,
    QInputDialog,
    QLabel,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStatusBar,
)
from widgets import themeEditor_UIs as ui
from widgets.tabWidget import tabWidgetClass

from .pythonSyntax import design


class themeEditorClass(QDialog, ui.Ui_themeEditor):
    def __init__(self, parent = None, desk=None):
        super(themeEditorClass, self).__init__(parent)
        self.setupUi(self)
        self.preview_main_window = QMainWindow(self)
        self.preview_main_window.setWindowFlags(Qt.Widget)

        self.preview_menubar = QMenuBar(self.preview_main_window)
        self.preview_menu_file = QMenu("File", self.preview_menubar)
        self.preview_menu_file.addAction("Open")
        self.preview_menu_file.addAction("Save")
        self.preview_menubar.addMenu(self.preview_menu_file)

        self.preview_menu_edit = QMenu("Edit", self.preview_menubar)
        self.preview_menu_edit.addAction("Undo")
        self.preview_menu_edit.addAction("Redo")
        self.preview_menubar.addMenu(self.preview_menu_edit)
        self.preview_main_window.setMenuBar(self.preview_menubar)

        self.preview_statusbar = QStatusBar(self.preview_main_window)
        self.lbl_msg = QLabel("")
        self.lbl_lang = QLabel("Python")
        self.lbl_wrap = QLabel("Wrap: OFF")
        self.lbl_lines = QLabel("52 lines")
        self.lbl_cursor = QLabel("Ln 1, Col 1")

        for lbl in (self.lbl_msg, self.lbl_cursor, self.lbl_lines, self.lbl_lang, self.lbl_wrap):
            lbl.setStyleSheet("padding: 0 5px;")
            self.preview_statusbar.addPermanentWidget(lbl)

        self.preview_main_window.setStatusBar(self.preview_statusbar)

        self.preview_tab_widget = tabWidgetClass(self.preview_main_window)
        self.preview_tab_widget.addNewTab("Active Tab", defaultText, make_current=False)
        self.preview_tab_widget.addNewTab("Inactive Tab", defaultText, make_current=False)
        self.preview_tab_widget.setCurrentIndex(0)

        self.preview_main_window.setCentralWidget(self.preview_tab_widget)
        self.preview_ly.addWidget(self.preview_main_window)

        self.preview_twd = self.preview_tab_widget.widget(0).edit
        self.preview_twd2 = self.preview_tab_widget.widget(1).edit

        self.preview_twd.setEnabled(False)
        self.preview_twd2.setEnabled(False)
        self.preview_twd.wordWrap(False)
        self.preview_twd2.wordWrap(False)

        self.preview_twd.set_bookmarks([8])
        self.preview_twd2.set_bookmarks([8])
        self.splitter.setSizes([280, 800])
        self.s = SettingsModel()
        self.t_model = ThemesModel()
        self.colors_lwd.itemDoubleClicked.connect(self.getNewColor)
        self.colors_lwd.setContextMenuPolicy(Qt.CustomContextMenu)
        self.colors_lwd.customContextMenuRequested.connect(self.openColorMenu)
        self.save_btn.clicked.connect(self.saveTheme)
        self.del_btn.clicked.connect(self.deleteTheme)
        self.export_btn.clicked.connect(self.exportTheme)
        self.import_btn.clicked.connect(self.importTheme)
        self.themeList_cbb.currentIndexChanged.connect(self.updateColors)
        self.apply_btn.clicked.connect(self.apply)
        self.choose_font_btn.clicked.connect(self.chooseFont)

        self.choose_font_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.choose_font_btn.customContextMenuRequested.connect(self.showFontContextMenu)
        self.apply_btn.setText('Ok')

        self.cancel_btn = QPushButton("Cancel", self)
        self.horizontalLayout_2.addWidget(self.cancel_btn)
        self.cancel_btn.clicked.connect(self.cancel)

        self.textSize_spb.valueChanged.connect(self.updateExample)
        self.textSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.textSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.lineNumbersSize_spb.valueChanged.connect(self.updateExample)
        self.lineNumbersSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lineNumbersSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.menuSize_spb.valueChanged.connect(self.updateExample)
        self.menuSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.menuSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.tabRadius_spb.valueChanged.connect(self.updateExample)
        self.tabRadius_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabRadius_spb.customContextMenuRequested.connect(self.openTabRadiusMenu)
        self.tabSize_spb.valueChanged.connect(self.updateExample)
        self.tabSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.outlineSize_spb.valueChanged.connect(self.updateExample)
        self.outlineSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outlineSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.outputSize_spb.valueChanged.connect(self.updateExample)
        self.outputSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.outputSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.statusBarSize_spb.valueChanged.connect(self.updateExample)
        self.statusBarSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.statusBarSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.symbolsSize_spb.valueChanged.connect(self.updateExample)
        self.symbolsSize_spb.setContextMenuPolicy(Qt.CustomContextMenu)
        self.symbolsSize_spb.customContextMenuRequested.connect(self.openSizeMenu)
        self.completerFont_cb.stateChanged.connect(self.updateExample)
        self.menuFont_cb.stateChanged.connect(self.updateExample)
        self.outlineFont_cb.stateChanged.connect(self.updateExample)
        self.symbolsFont_cb.stateChanged.connect(self.updateExample)
        self.statusBarFont_cb.stateChanged.connect(self.updateExample)
        self.tabFont_cb.stateChanged.connect(self.updateExample)
        self.custom_font_data = None
        self.fillUI()
        self.updateUI()
        self.updateColors()

        # Adjust height to fit all items
        row_height = self.colors_lwd.sizeHintForRow(0)
        if row_height <= 0:
            row_height = 25

        list_needed_height = self.colors_lwd.count() * row_height
        needed_height = list_needed_height + 200

        ideal_height = needed_height

        desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None
        if desk:
            screen_rect = desk.availableGeometry(self.parent() if self.parent() else self)
            ideal_height = min(ideal_height, screen_rect.height() - 100)

        self.resize(1100, ideal_height)
        self.setMinimumHeight(min(needed_height, ideal_height))

        self.preview_twd.completer.updateCompleteList()
        self.namespace={}

        # Ensure style is reapplied correctly after dialog is shown
        QTimer.singleShot(0, self.updateExample)

    def get_settings(self):
        if self.parent() and hasattr(self.parent(), '_current_settings'):
            return self.parent()._current_settings
        return self.s.read_settings()

    def get_theme_settings(self):
        return self.t_model.read_settings()

    def save_settings(self, settings):
        if self.parent() and hasattr(self.parent(), 'save_settings_requested'):
            self.parent().save_settings_requested.emit(settings)
        else:
            self.s.write_settings(settings)

    def save_theme_settings(self, theme_settings):
        self.t_model.write_settings(theme_settings)

    def _apply_parent_theme_font(self, widget):
        parent = self.parent()
        font = getattr(parent, 'theme_font', None) if parent else None
        if not font:
            return
        widget.setFont(font)
        widget.setStyleSheet(f"* {{ font-family: '{font.family()}'; }}")
        if hasattr(widget, 'buttons'):
            for btn in widget.buttons():
                btn.setFont(font)

    def fillUI(self, restore=None):
        self.themeList_cbb.blockSignals(True)
        try:
            if restore is None:
                restore = self.themeList_cbb.currentText()
            settings = self.get_settings()
            theme_settings = self.get_theme_settings()
            self.themeList_cbb.clear()
            for t in sorted(design.predefinedThemes.keys()):
                self.themeList_cbb.addItem(t)
            if theme_settings.get('colors'):
                added_separator = False
                for x in sorted(theme_settings.get('colors')):
                    if x not in design.predefinedThemes:
                        if not added_separator:
                            self.themeList_cbb.insertSeparator(self.themeList_cbb.count())
                            added_separator = True
                        self.themeList_cbb.addItem(x)
            if not restore:
                restore = settings.get('theme')
            if restore:
                index = self.themeList_cbb.findText(restore)
                if index >= 0:
                    self.themeList_cbb.setCurrentIndex(index)
                elif self.themeList_cbb.count():
                    self.themeList_cbb.setCurrentIndex(0)
            elif self.themeList_cbb.count():
                self.themeList_cbb.setCurrentIndex(0)
        finally:
            self.themeList_cbb.blockSignals(False)

    def updateColors(self):
        curTheme = self.themeList_cbb.currentText()
        if curTheme in design.predefinedThemes:
            self.del_btn.setEnabled(0)
        else:
            self.del_btn.setEnabled(1)

        colors = design.getColors(curTheme)

        self.colors_lwd.clear()
        default_font_size = self.get_settings().get('font', {}).get('pointSize', 12)

        font_mult = 0.9
        font_size_controls = (
            (self.textSize_spb, 'textsize', int(default_font_size * font_mult)),
            (self.lineNumbersSize_spb, 'line_numbers_text_size', max(1, int(default_font_size * 0.8))),
            (self.menuSize_spb, 'menu_text_size', int(default_font_size * font_mult)),
            (self.tabRadius_spb, 'tab_radius', 12),
            (self.tabSize_spb, 'tab_text_size', int(default_font_size * font_mult)),
            (self.outlineSize_spb, 'outline_text_size', int(default_font_size * font_mult)),
            (self.outputSize_spb, 'output_text_size', int(default_font_size * font_mult)),
            (self.symbolsSize_spb, 'symbols_text_size', int(default_font_size * font_mult)),
            (self.statusBarSize_spb, 'status_bar_text_size', int(default_font_size * font_mult)),
        )
        for control, key, default in font_size_controls:
            control.blockSignals(True)
            try:
                control.setValue(int(colors[key]) if key in colors else default)
            finally:
                control.blockSignals(False)

        font_option_controls = (
            (self.completerFont_cb, 'use_theme_font_on_completer', True),
            (self.menuFont_cb, 'use_theme_font_on_menus', False),
            (self.outlineFont_cb, 'use_theme_font_on_outline', True),
            (self.symbolsFont_cb, 'use_theme_font_on_symbols', True),
            (self.statusBarFont_cb, 'use_theme_font_on_status_bar', False),
            (self.tabFont_cb, 'use_theme_font_on_tab_label', True),
        )
        for control, key, default in font_option_controls:
            control.blockSignals(True)
            try:
                control.setChecked(bool(colors.get(key, default)))
            finally:
                control.blockSignals(False)

        self.choose_font_btn.setEnabled(True)
        if curTheme in design.predefinedThemes:
            default_font = self.get_settings().get('font', {})
            font_family = default_font.get('family', 'monospace')
            font_size = default_font.get('pointSize', 12)
            self.font_name_label.setText("{} {}".format(font_family, font_size))
            self.custom_font_data = None
        else:
            if 'font' in colors and colors['font']:
                self.custom_font_data = colors['font']
                self.font_name_label.setText("{} {}".format(self.custom_font_data.get('family', 'Default'), self.custom_font_data.get('pointSize', 10)))
            else:
                self.custom_font_data = None
                self.font_name_label.setText("Default (from Options)")

        self._current_colors_cache = colors
        for x in sorted(colors.keys()):
            if not isinstance(colors[x], (list, tuple)):
                continue
            item = QListWidgetItem(x)
            pix = QPixmap(QSize(16,16))
            pix.fill(QColor(*colors[x]))
            item.setIcon(QIcon(pix))
            item.setData(32, colors[x])
            self.colors_lwd.addItem(item)
        self.updateExample()

    def updateExample(self):
        colors = self.getCurrentColors()

        font_data = colors.get('font')
        if not font_data:
            font_data = self.get_settings().get('font', {})

        if font_data:
            font = QFont(
                font_data.get('family', ''),
                max(1, font_data.get('pointSize', 10)),
                font_data.get('weight', -1),
                font_data.get('italic', False)
            )
        else:
            font = QFont()

        if hasattr(self, 'preview_tab_widget'):
            self.preview_tab_widget._tab_text_size = colors.get('tab_text_size')
            self.preview_tab_widget.apply_tab_style(colors)
            if font_data and hasattr(self.preview_tab_widget, 'set_start_font'):
                self.preview_tab_widget.set_start_font(font_data)
            for i in range(self.preview_tab_widget.count()):
                w = self.preview_tab_widget.widget(i)
                w.edit.applyPreviewStyle(colors)
                if hasattr(w, 'lineNum'):
                    w.lineNum.update()

            if colors.get('use_theme_font_on_menus', False) and font_data:
                menu_font = QFont(font.family(), colors.get('menu_text_size', 10), font.weight(), font.italic())
                self.preview_menubar.setFont(menu_font)
                self.preview_menu_file.setFont(menu_font)
                self.preview_menu_edit.setFont(menu_font)
            else:
                self.preview_menubar.setFont(QApplication.font("QMenu"))
                self.preview_menu_file.setFont(QApplication.font("QMenu"))
                self.preview_menu_edit.setFont(QApplication.font("QMenu"))

            if colors.get('use_theme_font_on_status_bar', False) and font_data:
                status_font = QFont(font.family(), colors.get('status_bar_text_size', 10), font.weight(), font.italic())
                self.preview_statusbar.setFont(status_font)
                for lbl in (self.lbl_msg, self.lbl_cursor, self.lbl_lines, self.lbl_lang, self.lbl_wrap):
                    lbl.setFont(status_font)
            else:
                self.preview_statusbar.setFont(QApplication.font("QStatusBar"))
                for lbl in (self.lbl_msg, self.lbl_cursor, self.lbl_lines, self.lbl_lang, self.lbl_wrap):
                    lbl.setFont(QApplication.font("QStatusBar"))

            main_style = design.applyColorToMainStyle(colors)
            if main_style:
                if font.family():
                    main_style += f"\nQLabel, QComboBox, QPushButton, QListWidget, QSpinBox, QCheckBox, QGroupBox {{ font-family: '{font.family()}'; }}"
                if self.styleSheet() != main_style:
                    self.setStyleSheet(main_style)
        else:
            self.preview_twd.applyPreviewStyle(colors)
            if font_data and hasattr(self.preview_twd, 'set_start_font'):
                self.preview_twd.set_start_font(font_data)

    def getCurrentColors(self):
        colors = getattr(self, '_current_colors_cache', {}).copy()
        for i in range(self.colors_lwd.count()):
            item = self.colors_lwd.item(i)
            colors[item.text()] = item.data(32)
        colors['textsize'] = max(1, self.textSize_spb.value())
        colors['line_numbers_text_size'] = max(1, self.lineNumbersSize_spb.value())
        colors['menu_text_size'] = max(1, self.menuSize_spb.value())
        colors['tab_radius'] = self.tabRadius_spb.value()
        colors['tab_text_size'] = max(1, self.tabSize_spb.value())
        colors['outline_text_size'] = max(1, self.outlineSize_spb.value())
        colors['output_text_size'] = max(1, self.outputSize_spb.value())
        colors['status_bar_text_size'] = max(1, self.statusBarSize_spb.value())
        colors['symbols_text_size'] = max(1, self.symbolsSize_spb.value())
        colors['use_theme_font_on_completer'] = self.completerFont_cb.isChecked()
        colors['use_theme_font_on_menus'] = self.menuFont_cb.isChecked()
        colors['use_theme_font_on_outline'] = self.outlineFont_cb.isChecked()
        colors['use_theme_font_on_symbols'] = self.symbolsFont_cb.isChecked()
        colors['use_theme_font_on_status_bar'] = self.statusBarFont_cb.isChecked()
        colors['use_theme_font_on_tab_label'] = self.tabFont_cb.isChecked()
        if hasattr(self, 'custom_font_data') and self.custom_font_data is not None:
            colors['font'] = self.custom_font_data
        return colors

    def showFontContextMenu(self, pos):
        menu = QMenu(self)
        reset_action = menu.addAction("Reset to default")
        action = menu.exec_(self.choose_font_btn.mapToGlobal(pos))
        if action == reset_action:
            self.resetFont()

    def resetFont(self):
        settings = self.get_settings()

        global_font_data = settings.get('font', {})
        if not global_font_data:
            if self.parent() and hasattr(self.parent(), 'tab') and self.parent().tab.count() > 0:
                editor_font = self.parent().tab.widget(0).edit.font()
                global_font_data = {
                    "family": editor_font.family(),
                    "pointSize": editor_font.pointSize(),
                    "weight": editor_font.weight(),
                    "italic": editor_font.italic()
                }

        self.custom_font_data = global_font_data
        if global_font_data:
            self.font_name_label.setText("{} {}".format(global_font_data.get('family', 'monospace'), global_font_data.get('pointSize', 10)))
        else:
            self.font_name_label.setText("Default")

        self._resetAllFontSizes()
        self.updateExample()

    def chooseFont(self):
        if hasattr(self, 'custom_font_data') and self.custom_font_data:
            init_font = QFont(
                self.custom_font_data.get('family', ''),
                self.custom_font_data.get('pointSize', 10),
                self.custom_font_data.get('weight', -1),
                self.custom_font_data.get('italic', False)
            )
        else:
            settings = self.get_settings()
            font_data = settings.get('font', {})
            if font_data:
                init_font = QFont(
                    font_data.get('family', ''),
                    font_data.get('pointSize', 10),
                    font_data.get('weight', -1),
                    font_data.get('italic', False)
                )
            else:
                init_font = QFont()

        font_dialog = QFontDialog(self)
        font_dialog.setCurrentFont(init_font)
        font_dialog.resize(self.width() * 0.8, self.height() * 0.7)
        if hasattr(font_dialog, 'exec'):
            accept_dialog = getattr(font_dialog, 'exec')()
        else:
            accept_dialog = font_dialog.exec_()

        if accept_dialog:
            font = font_dialog.currentFont()
            font_data = {
                "family": font.family(),
                "pointSize": font.pointSize(),
                "weight": font.weight(),
                "italic": font.italic()
            }
            self.font_name_label.setText("{} {}".format(font.family(), font.pointSize()))
            self.custom_font_data = font_data
            self._resetAllFontSizes()
            self.updateExample()

    def getNewColor(self):
        items = self.colors_lwd.selectedItems()
        if items:
            item = items[0]
            init = QColor(*item.data(32))
            color = QColorDialog.getColor(init ,self)
            if color.isValid():
                newColor = (color.red(), color.green(), color.blue())
                item.setData(32, newColor)
                pix = QPixmap(QSize(16,16))
                pix.fill(QColor(*newColor))
                item.setIcon(QIcon(pix))
                self.updateExample()

    def openColorMenu(self, position):
        item = self.colors_lwd.itemAt(position)
        if item:
            menu = QMenu(self)
            reset_action = QAction("Reset to default", self)
            reset_action.triggered.connect(lambda checked=False, i=item: self.resetColorToDefault(i))
            menu.addAction(reset_action)
            menu.exec_(self.colors_lwd.viewport().mapToGlobal(position))

    def resetColorToDefault(self, item):
        color_name = item.text()
        if color_name in design.defaultColors:
            default_color = design.defaultColors[color_name]
            item.setData(32, default_color)
            pix = QPixmap(QSize(16,16))
            pix.fill(QColor(*default_color))
            item.setIcon(QIcon(pix))
            self.updateExample()

    def openSizeMenu(self, position):
        sender = self.sender()
        if not sender:
            return
        menu = QMenu(self)
        ratio_1 = (None,)
        ratio_08 = (self.lineNumbersSize_spb,)
        ratio = 1.0 if sender in ratio_1 else (0.8 if sender in ratio_08 else 0.9)
        ratio_str = "100%" if ratio == 1.0 else ("80%" if ratio == 0.8 else "90%")
        reset_action = QAction(f"Reset to Default ({ratio_str} of font)", self)
        reset_action.triggered.connect(lambda checked=False, s=sender, r=ratio: self.resetSizeToDefault(s, r))
        menu.addAction(reset_action)
        menu.exec_(sender.mapToGlobal(position))

    def resetSizeToDefault(self, spb, ratio):
        pts = self._getBaseFontPointSize()
        spb.setValue(max(1, int(pts * ratio)))
        self.updateExample()

    def openTabRadiusMenu(self, position):
        menu = QMenu(self)
        reset_action = QAction("Reset to default", self)
        reset_action.triggered.connect(self.resetTabRadiusToDefault)
        menu.addAction(reset_action)
        menu.exec_(self.tabRadius_spb.mapToGlobal(position))

    def resetTabRadiusToDefault(self):
        if 'tab_radius' in design.defaultColors:
            self.tabRadius_spb.setValue(design.defaultColors['tab_radius'])
            self.updateExample()



    def _getBaseFontPointSize(self):
        colors = self.getCurrentColors()
        font_data = colors.get('font')
        if not font_data:
            font_data = self.get_settings().get('font', {})
        if font_data:
            return max(1, font_data.get('pointSize', 10))
        return 10

    def _resetAllFontSizes(self):
        pts = self._getBaseFontPointSize()
        font_mult = 0.9
        font_size_controls = (
            (self.textSize_spb, font_mult),
            (self.lineNumbersSize_spb, 0.8),
            (self.menuSize_spb, font_mult),
            (self.outlineSize_spb, font_mult),
            (self.outputSize_spb, font_mult),
            (self.statusBarSize_spb, font_mult),
            (self.tabSize_spb, font_mult),
            (self.symbolsSize_spb, font_mult),
        )

        for control, _ in font_size_controls:
            control.blockSignals(True)
        try:
            for control, multiplier in font_size_controls:
                control.setValue(max(1, int(pts * multiplier)))
        finally:
            for control, _ in font_size_controls:
                control.blockSignals(False)

    def saveTheme(self):
        text = self.themeList_cbb.currentText() or 'NewTheme'
        dlg = QInputDialog(self)
        dlg.setWindowTitle('Theme name')
        dlg.setLabelText('Enter Theme name')
        dlg.setTextValue(text)
        self._apply_parent_theme_font(dlg)
        ok = dlg.exec_() == QInputDialog.Accepted
        name = dlg.textValue().strip() if ok else ""
        if name:
            if name in design.predefinedThemes:
                name = name + ' (Custom)'
            theme_settings = self.get_theme_settings()
            if 'colors' in theme_settings:
                if name in theme_settings['colors']:
                    if not self.yes_no_question(
                        'Replace existing?',
                        QMessageBox.No,
                    ):
                        return False

            colors = self.getCurrentColors()
            if 'colors' in theme_settings:
                theme_settings['colors'][name] = colors
            else:
                theme_settings['colors'] = {name: colors}
            self.save_theme_settings(theme_settings)

            # If the main window caches colors we need to apply them there too
            settings = self.get_settings()
            if 'colors' in settings:
                settings['colors'][name] = colors

            self.fillUI(name)
            self.updateUI()
            if self.parent() and hasattr(self.parent(), 'applyTheme'):
                self.parent().applyTheme(name)
                if hasattr(self.parent(), 'fillThemeMenu'):
                    self.parent().fillThemeMenu()
            return True
        return False

    def deleteTheme(self):
        text = self.themeList_cbb.currentText()
        if text:
            curr_idx = self.themeList_cbb.currentIndex()
            prev_theme = None
            for idx in range(curr_idx - 1, -1, -1):
                item_text = self.themeList_cbb.itemText(idx)
                if item_text and item_text.strip():
                    prev_theme = item_text
                    break

            if self.yes_no_question(
                'Remove current theme?',
                QMessageBox.No,
            ):
                name = self.themeList_cbb.currentText()
                theme_settings = self.get_theme_settings()
                if 'colors' in theme_settings:
                    if name in theme_settings['colors']:
                        del theme_settings['colors'][name]
                        self.save_theme_settings(theme_settings)

                        settings = self.get_settings()
                        if 'colors' in settings and name in settings['colors']:
                            del settings['colors'][name]
                            self.save_settings(settings)

                        self.fillUI(prev_theme)
                        self.updateUI()
                        self.updateColors()
                        if self.parent() and hasattr(self.parent(), 'applyTheme'):
                            new_name = self.themeList_cbb.currentText()
                            if new_name:
                                self.parent().applyTheme(new_name)
                        if self.parent() and hasattr(self.parent(), 'fillThemeMenu'):
                            self.parent().fillThemeMenu()

    def exportTheme(self):
        name = self.themeList_cbb.currentText()
        if not name:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Theme", name + ".json", "JSON Files (*.json)")
        if path:
            colors = self.getCurrentColors()
            try:
                with open(path, 'w') as f:
                    json.dump(colors, f, indent=4)
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText("Could not export theme:\n" + str(e))
                self._apply_parent_theme_font(msg_box)
                msg_box.exec_()

    def importTheme(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Theme", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r') as f:
                    colors = json.load(f)

                # Extract filename without extension to use as theme name
                base_name = os.path.basename(path)
                name, _ = os.path.splitext(base_name)

                dlg = QInputDialog(self)
                dlg.setWindowTitle('Theme name')
                dlg.setLabelText('Enter Theme name')
                dlg.setTextValue(name)
                self._apply_parent_theme_font(dlg)
                ok = dlg.exec_() == QInputDialog.Accepted
                name_input = dlg.textValue().strip() if ok else ""
                if name_input:
                    name = name_input
                    if name in design.predefinedThemes:
                        name = name + ' (Custom)'

                    theme_settings = self.get_theme_settings()
                    if 'colors' in theme_settings:
                        if name in theme_settings['colors']:
                            if not self.yes_no_question(
                                'Replace existing?',
                                QMessageBox.No,
                            ):
                                return

                    if 'colors' in theme_settings:
                        theme_settings['colors'][name] = colors
                    else:
                        theme_settings['colors'] = {name: colors}

                    self.save_theme_settings(theme_settings)

                    settings = self.get_settings()
                    if 'colors' in settings:
                        settings['colors'][name] = colors

                    self.fillUI(name)
                    self.updateUI()
                    self.updateColors()
                    if self.parent() and hasattr(self.parent(), 'fillThemeMenu'):
                        self.parent().fillThemeMenu()
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle("Error")
                msg_box.setText("Could not import theme:\n" + str(e))
                self._apply_parent_theme_font(msg_box)
                msg_box.exec_()

    def updateUI(self):
        if not self.themeList_cbb.count():
            self.apply_btn.setEnabled(0)
        else:
            self.apply_btn.setEnabled(1)

    def apply(self):
        if self.hasUnsavedChanges():
            if not self.saveTheme():
                return
        else:
            name = self.themeList_cbb.currentText()
            if name:
                settings = self.get_settings()
                settings['theme'] = name
                self.save_settings(settings)
                if self.parent() and hasattr(self.parent(), 'applyTheme'):
                    self.parent().applyTheme(name)
        self.close()

    def cancel(self):
        self.close()

    def hasUnsavedChanges(self):
        curTheme = self.themeList_cbb.currentText()
        if not curTheme:
            return False

        current_colors = self.getCurrentColors()
        saved_colors = design.getColors(curTheme)

        for k, v in current_colors.items():
            saved_v = saved_colors.get(k)
            if saved_v is None:
                return True

            if isinstance(v, list):
                v = tuple(v)
            if isinstance(saved_v, list):
                saved_v = tuple(saved_v)

            if v != saved_v:
                return True

        return False

    def closeEvent(self, event):
        if getattr(self, '_force_close', False):
            event.accept()
            return

        if self.hasUnsavedChanges():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Unsaved Changes')
            msg_box.setText("You may have unsaved changes.\nDo you want to save them before closing?")
            self._apply_parent_theme_font(msg_box)
            save_btn = msg_box.addButton("Save", QMessageBox.AcceptRole)
            discard_btn = msg_box.addButton("Discard", QMessageBox.DestructiveRole)
            msg_box.addButton("Cancel", QMessageBox.RejectRole)
            msg_box.exec_()

            if msg_box.clickedButton() == save_btn:
                if self.saveTheme():
                    event.accept()
                else:
                    event.ignore()
            elif msg_box.clickedButton() == discard_btn:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super(themeEditorClass, self).keyPressEvent(event)

    def current(self):
        pass
        # print self.colors_lwd.selectedItems()[0].data(32)

    def yes_no_question(self, question, default_button=QMessageBox.Yes):
        msg_box = QMessageBox(self)
        msg_box.setText(question)
        msg_box.setWindowTitle('?')
        self._apply_parent_theme_font(msg_box)
        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        no_button = msg_box.addButton("No", QMessageBox.NoRole)
        button = yes_button if default_button == QMessageBox.Yes else no_button
        msg_box.setDefaultButton(button)
        button.setFocus()
        msg_box.exec_()
        return msg_box.clickedButton() == yes_button

defaultText = r'''@decorator(param=1)
def f(x):
    """ Syntax Highlighting Demo
        @param x Parameter"""
    s = ("Test", 2+3, {'a': 'b'}, x)   # Comment
    print s[0].lower()

class Foo:
    def __init__(self):
        string = 'newline'
        self.makeSense(whatever=1)

    def makeSense(self, whatever):
        self.sense = whatever

x = len('abc')
print(f.__doc__)
'''


if __name__ == '__main__':
    app = QApplication([])
    w = themeEditorClass()
    w.show()
    colors = design.getColors(w.get_settings().get('theme', 'Multi Script Editor'))
    main_style = design.applyColorToMainStyle(colors)
    if main_style:
        w.setStyleSheet(main_style)
    app.exec_()
