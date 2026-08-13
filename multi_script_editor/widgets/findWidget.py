from vendor.Qt.QtCore import QEvent, Qt, QTimer, Signal
from vendor.Qt.QtGui import QIcon
from vendor.Qt.QtWidgets import QCheckBox, QWidget
from icons import icons
from widgets import findWidget_UIs as ui


class findWidgetClass(QWidget, ui.Ui_findReplace):
    searchSignal = Signal(str, bool)
    replaceSignal = Signal(list, bool)
    replaceAllSignal = Signal(list, bool)

    def __init__(self, parent, anchor_widget=None, font=None):
        super(findWidgetClass, self).__init__(parent)
        self.setupUi(self)
        self._anchor_widget = anchor_widget or parent
        self._font = font
        self.setWindowFlags(Qt.Widget)
        self.setMinimumWidth(260)
        self.setObjectName("findReplaceOverlay")
        self._setup_vscode_style()
        self.find_le.setFocus()
        self._anchor_widget.installEventFilter(self)
        self.find_le.installEventFilter(self)
        self.replace_le.installEventFilter(self)

        #connect
        self.find_btn.clicked.connect(self.search)
        self.replace_btn.clicked.connect(self.replace)
        self.replaceAll_btn.clicked.connect(self.replaceAll)

        self.case_cb = QCheckBox("Aa", self)
        self.case_cb.setStatusTip("Match case")
        self.case_cb.setToolTip(self.case_cb.statusTip())
        self.gridLayout.addWidget(self.case_cb, 2, 0, 1, 1)

        self._apply_theme_font()
        self._move_to_anchor()

    def _setup_vscode_style(self):
        self.verticalLayout.setContentsMargins(8, 8, 8, 8)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(6)
        self.find_le.setPlaceholderText("Find")
        self.replace_le.setPlaceholderText("Replace")
        self.find_btn.setText("")
        self.find_btn.setIcon(QIcon(icons.get("down", "")))
        self.find_btn.setStatusTip("Find next match")
        self.find_btn.setToolTip(self.find_btn.statusTip())
        self.replace_btn.setText("")
        self.replace_btn.setIcon(QIcon(icons.get("replace", "")))
        self.replace_btn.setStatusTip("Replace current match")
        self.replace_btn.setToolTip(self.replace_btn.statusTip())
        self.replaceAll_btn.setText("")
        self.replaceAll_btn.setIcon(QIcon(icons.get("docs", "")))
        self.replaceAll_btn.setStatusTip("Replace all matches (Ctrl+Enter)")
        self.replaceAll_btn.setToolTip(self.replaceAll_btn.statusTip())
        for btn in (self.find_btn, self.replace_btn, self.replaceAll_btn):
            btn.setFixedSize(24, 22)
            btn.setIconSize(btn.size())

    def _apply_theme_font(self):
        font = self._font
        main_window = self.window()
        if font is None:
            font = getattr(main_window, 'current_outline_font', None)
        if font is None:
            font = getattr(main_window, 'theme_font', None)
        if font is None and self._anchor_widget is not None:
            parent = getattr(self._anchor_widget, 'p', None)
            font = getattr(parent, 'current_outline_font', None)
            if font is None:
                font = getattr(parent, 'theme_font', None)
        if font is None:
            return
        self.setFont(font)
        for child in self.findChildren(QWidget):
            child.setFont(font)

    def _move_to_anchor(self):
        if not self._anchor_widget:
            return
        margin = 10
        self.setFixedWidth(min(380, max(260, self._anchor_widget.width() - margin * 2)))
        x = max(margin, self._anchor_widget.width() - self.width() - margin)
        self.move(x, margin)

    def eventFilter(self, obj, event):
        event_type = event.type()
        if (
            obj in (self.find_le, self.replace_le)
            and event_type == QEvent.KeyPress
            and event.key() == Qt.Key_Tab
            and self.replace_le.isVisible()
        ):
            (self.replace_le if obj == self.find_le else self.find_le).setFocus()
            return True
        submit_event = (
            obj in (self.find_le, self.replace_le)
            and event_type in (QEvent.KeyPress, QEvent.ShortcutOverride)
            and event.key() in (Qt.Key_Return, Qt.Key_Enter)
        )
        if submit_event and event_type == QEvent.ShortcutOverride:
            event.accept()
            return True
        if submit_event:
            if obj == self.find_le:
                self.search()
            elif event.modifiers() & Qt.ControlModifier:
                self.replaceAll()
            else:
                self.replace()
            return True
        if obj == self._anchor_widget and event_type in (QEvent.Resize, QEvent.Show):
            self._move_to_anchor()
        return super(findWidgetClass, self).eventFilter(obj, event)

    def showEvent(self, event):
        self._move_to_anchor()
        super(findWidgetClass, self).showEvent(event)

    def setReplaceEnabled(self, state):
        for widget in (self.replace_le, self.replace_btn, self.replaceAll_btn):
            widget.setVisible(state)
            widget.setEnabled(state)
        self.adjustSize()
        self._move_to_anchor()

    def search(self):
        self.searchSignal.emit(self.find_le.text(), self.case_cb.isChecked())
        QTimer.singleShot(10, self.find_le.setFocus)

    def replace(self):
        find = self.find_le.text()
        rep = self.replace_le.text()
        self.replaceSignal.emit([find, rep], self.case_cb.isChecked())
        QTimer.singleShot(10, self.replace_le.setFocus)

    def replaceAll(self):
        find = self.find_le.text()
        rep = self.replace_le.text()
        self.replaceAllSignal.emit([find, rep], self.case_cb.isChecked())
        QTimer.singleShot(10, self.replace_le.setFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super(findWidgetClass, self).keyPressEvent(event)
