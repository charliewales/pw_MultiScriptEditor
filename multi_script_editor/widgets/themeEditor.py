import os
from vendor.Qt.QtCore import QSize, Qt
from vendor.Qt.QtGui import QColor, QIcon, QPixmap
from vendor.Qt.QtWidgets import QApplication, QColorDialog, QDialog, QInputDialog, QLineEdit, QListWidgetItem, QMessageBox, QMenu, QAction
from widgets import themeEditor_UIs as ui
from core.settings_model import SettingsModel
from .pythonSyntax import design
from .pythonSyntax import syntaxHighLighter
from . import inputWidget


class themeEditorClass(QDialog, ui.Ui_themeEditor):
    def __init__(self, parent = None, desk=None):
        super(themeEditorClass, self).__init__(parent)
        self.setupUi(self)
        from widgets.tabWidget import tabWidgetClass
        self.preview_tab_widget = tabWidgetClass(self)
        self.preview_tab_widget.addNewTab("Active Tab", defaultText, make_current=False)
        self.preview_tab_widget.addNewTab("Inactive Tab", defaultText, make_current=False)
        self.preview_tab_widget.setCurrentIndex(0)
        
        self.preview_ly.addWidget(self.preview_tab_widget)
        
        self.preview_twd = self.preview_tab_widget.widget(0).edit
        self.preview_twd2 = self.preview_tab_widget.widget(1).edit
        
        self.preview_twd.setEnabled(False)
        self.preview_twd2.setEnabled(False)
        self.preview_twd.wordWrap(False)
        self.preview_twd2.wordWrap(False)
        self.splitter.setSizes([280, 500])
        self.s = SettingsModel()
        self.colors_lwd.itemDoubleClicked.connect(self.getNewColor)
        self.colors_lwd.setContextMenuPolicy(Qt.CustomContextMenu)
        self.colors_lwd.customContextMenuRequested.connect(self.openColorMenu)
        self.save_btn.clicked.connect(self.saveTheme)
        self.del_btn.clicked.connect(self.deleteTheme)
        self.themeList_cbb.currentIndexChanged.connect(self.updateColors)
        self.apply_btn.clicked.connect(self.apply)
        self.apply_btn.setText('Close')
        self.textSize_spb.valueChanged.connect(self.updateExample)
        self.fillUI()
        self.updateUI()
        self.updateColors()
        
        # Adjust height to fit all items
        row_height = self.colors_lwd.sizeHintForRow(0)
        if row_height <= 0:
            row_height = 25
            
        list_needed_height = self.colors_lwd.count() * row_height
        needed_height = list_needed_height + 200
        
        parent_height = self.parent().height() if self.parent() else 1000
        ideal_height = max(int(parent_height * 0.7), needed_height)
        
        desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None
        if desk:
            screen_rect = desk.availableGeometry(self.parent() if self.parent() else self)
            ideal_height = min(ideal_height, screen_rect.height() - 100)
            
        parent_width = self.parent().width() if self.parent() else 1000
        
        self.resize(int(parent_width * 0.8), ideal_height)
        self.setMinimumHeight(min(needed_height, ideal_height))
        
        self.preview_twd.completer.updateCompleteList()
        self.namespace={}

    def get_settings(self):
        if self.parent() and hasattr(self.parent(), '_current_settings'):
            return self.parent()._current_settings
        return self.s.read_settings()

    def save_settings(self, settings):
        if self.parent() and hasattr(self.parent(), 'save_settings_requested'):
            self.parent().save_settings_requested.emit(settings)
        else:
            self.s.write_settings(settings)

    def fillUI(self, restore=None):
        if restore is None:
            restore = self.themeList_cbb.currentText()
        settings = self.get_settings()
        self.themeList_cbb.clear()
        for t in sorted(design.predefinedThemes.keys()):
            self.themeList_cbb.addItem(t)
        if settings.get('colors'):
            added_separator = False
            for x in settings.get('colors'):
                if x not in design.predefinedThemes:
                    if not added_separator:
                        self.themeList_cbb.insertSeparator(self.themeList_cbb.count())
                        added_separator = True
                    self.themeList_cbb.addItem(x)
        if not restore:
            restore = settings.get('theme')
        if restore:
            index = self.themeList_cbb.findText(restore)
            self.themeList_cbb.setCurrentIndex(index)
        self.updateExample()

    def updateColors(self):
        curTheme = self.themeList_cbb.currentText()
        if curTheme in design.predefinedThemes:
            self.del_btn.setEnabled(0)
        else:
            self.del_btn.setEnabled(1)
            
        colors = design.getColors(curTheme)

        self.colors_lwd.clear()

        # Update text size (or default to 11 if not present)
        self.textSize_spb.blockSignals(True)
        if 'textsize' in colors:
            self.textSize_spb.setValue(int(colors['textsize']))
        else:
            self.textSize_spb.setValue(11)
        self.textSize_spb.blockSignals(False)

        for x in sorted(colors.keys()):
            if x == 'textsize':
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
        if hasattr(self, 'preview_tab_widget'):
            self.preview_tab_widget.apply_tab_style(colors)
            for i in range(self.preview_tab_widget.count()):
                w = self.preview_tab_widget.widget(i)
                w.edit.applyPreviewStyle(colors)
        else:
            self.preview_twd.applyPreviewStyle(colors)

    def getCurrentColors(self):
        colors = {}
        for i in range(self.colors_lwd.count()):
            item = self.colors_lwd.item(i)
            colors[item.text()] = item.data(32)
        colors['textsize'] = self.textSize_spb.value()
        return colors

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
        from widgets.pythonSyntax.design import defaultColors
        if color_name in defaultColors:
            default_color = defaultColors[color_name]
            item.setData(32, default_color)
            pix = QPixmap(QSize(16,16))
            pix.fill(QColor(*default_color))
            item.setIcon(QIcon(pix))
            self.updateExample()

    def saveTheme(self):
        text = self.themeList_cbb.currentText() or 'NewTheme'
        name = QInputDialog.getText(self, 'Theme name', 'Enter Theme name', QLineEdit.Normal, text)
        if name[1]:
            name = name[0]
            if name in design.predefinedThemes:
                name = name + ' (Custom)'
            settings = self.get_settings()
            if 'colors' in settings:
                if name in settings['colors']:
                    if not self.yes_no_question('Replace exists?'):
                        return

            colors = self.getCurrentColors()
            if 'colors' in settings:
                settings['colors'][name] = colors
            else:
                settings['colors'] = {name: colors}
            self.save_settings(settings)
            self.fillUI(name)
            self.updateUI()
            if self.parent() and hasattr(self.parent(), 'applyTheme'):
                self.parent().applyTheme(name)
                if hasattr(self.parent(), 'fillThemeMenu'):
                    self.parent().fillThemeMenu()

    def deleteTheme(self):
        text = self.themeList_cbb.currentText()
        if text:
            if self.yes_no_question('Remove current theme?'):
                name = self.themeList_cbb.currentText()
                settings = self.get_settings()
                if 'colors' in settings:
                    if name in settings['colors']:
                        del settings['colors'][name]
                        self.save_settings(settings)
                        self.fillUI(False)
                        self.updateUI()

    def updateUI(self):
        if not self.themeList_cbb.count():
            self.apply_btn.setEnabled(0)
        else:
            self.apply_btn.setEnabled(1)

    def apply(self):
        name = self.themeList_cbb.currentText()
        if name:
            settings = self.get_settings()
            settings['theme'] = name
            self.save_settings(settings)
            if self.parent() and hasattr(self.parent(), 'applyTheme'):
                self.parent().applyTheme(name)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.ignore()
        else:
            super(themeEditorClass, self).keyPressEvent(event)

    def current(self):
        pass
        # print self.colors_lwd.selectedItems()[0].data(32)

    def yes_no_question(self, question):
        msg_box = QMessageBox(self)
        msg_box.setText(question)
        yes_button = msg_box.addButton("Yes", QMessageBox.YesRole)
        no_button = msg_box.addButton("No", QMessageBox.NoRole)
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
    qss = os.path.join(os.path.dirname(os.path.dirname(__file__)),'style', 'style.css')
    if os.path.exists(qss):
        w.setStyleSheet(open(qss).read())
    app.exec_()
