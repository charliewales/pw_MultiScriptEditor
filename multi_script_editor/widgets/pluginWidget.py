from vendor.Qt.QtCore import Qt, Signal
from vendor.Qt.QtGui import QFontMetrics
from vendor.Qt.QtWidgets import QListWidgetItem
from widgets.searchPopupWidget import SearchPopupWidget


class PluginWidget(SearchPopupWidget):
    pluginSelected = Signal(object)  # emits the plugin instance

    def __init__(self, plugins, parent=None, center_widget=None, qss=None, font=None, colors=None):
        super(PluginWidget, self).__init__(parent, center_widget, qss, font, colors, placeholder_text="Search plugin to execute...")

        self.plugins = plugins  # Dict of {key: plugin_inst}

        # Calculate dynamic size
        fm = QFontMetrics(font) if font else QFontMetrics(self.font())
        max_text_width = 0
        for name in self.plugins.keys():
            w = fm.horizontalAdvance(name) if hasattr(fm, 'horizontalAdvance') else fm.width(name)
            if w > max_text_width:
                max_text_width = w
                
        self.resize_and_move(max_text_width)
        self.populate_list("")

    def populate_list(self, filter_text):
        self.list_widget.clear()
        filter_text = filter_text.lower()

        for name, plugin_inst in sorted(self.plugins.items()):
            if filter_text in name.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, plugin_inst)
                
                # set tooltip from plugin description
                description = getattr(plugin_inst, 'description', '')
                if description:
                    item.setToolTip(description)

                if self._font:
                    item.setFont(self._font)
                self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def on_item_clicked(self, item):
        plugin_inst = item.data(Qt.UserRole)
        self.pluginSelected.emit(plugin_inst)
        self.accept()

    def handle_enter(self):
        item = self.list_widget.currentItem()
        if item:
            plugin_inst = item.data(Qt.UserRole)
            self.pluginSelected.emit(plugin_inst)
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.handle_enter()
        else:
            super(PluginWidget, self).keyPressEvent(event)
