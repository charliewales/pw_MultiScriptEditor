from vendor.Qt.QtCore import Qt, QEvent
from vendor.Qt.QtWidgets import QTextEdit, QPushButton, QApplication
from vendor.Qt.QtGui import QIcon
from core.settings_model import SettingsModel
from widgets.pythonSyntax import design
from icons import icons

class MarkdownPreviewEdit(QTextEdit):
    """
    A read-only QTextEdit subclass that overlays the input editor
    to render Markdown formatting using native setMarkdown().
    It auto-resizes along with the parent editor and closes when Esc is pressed.
    Includes a close button with a custom icon in the top-right corner.
    """
    def __init__(self, parent_editor):
        # The parent is the EditorTabContainer (parent_editor.parentWidget())
        super(MarkdownPreviewEdit, self).__init__(parent_editor.parentWidget())
        self.editor = parent_editor
        self.setReadOnly(True)
        self.setFrameShape(QTextEdit.NoFrame)

        # Copy geometry, stylesheet, and font from the editor to match style
        self.setGeometry(self.editor.geometry())
        self.setStyleSheet(self.editor.styleSheet())
        self.setFont(self.editor.font())

        # Fetch current theme colors and font from SettingsModel
        settings = SettingsModel().read_settings()
        theme = settings.get('theme', 'Multi Script Editor')
        colors = design.getColors(theme)

        tab_selected_text_color = colors.get('tab_selected_text', (200, 200, 200))
        highlight_line_color = colors.get('highlight_line', (85, 85, 85))
        window_color = colors.get("window", (85, 85, 85))

        # Resolve the active font family of the current theme based on tabFont_cb setting
        theme_font = colors.get('font')
        if not theme_font:
            theme_font = settings.get('font', {})

        use_theme_font = colors.get('use_theme_font_on_tab_label', True)
        if use_theme_font:
            font_family = theme_font.get('family', 'monospace')
        else:
            app_tab_font = QApplication.font("QTabBar")
            font_family = app_tab_font.family() or "sans-serif"

        # Resolve the exact tab font size like tabWidget.py
        tab_text_size = colors.get('tab_text_size', None)
        if tab_text_size is not None:
            custom_size = float(tab_text_size)
        elif 'textsize' in colors:
            custom_size = float(colors['textsize'])
        else:
            editor_font = parent_editor.font()
            pt_size = editor_font.pointSizeF()
            if pt_size > 0:
                custom_size = pt_size * 0.8
            else:
                px_size = editor_font.pixelSize()
                custom_size = px_size * 0.8 if px_size > 0 else 10.0

        # Helper to convert color tuple to CSS rgb() string
        def to_rgb_str(color_tuple):
            if isinstance(color_tuple, (list, tuple)):
                return "rgb({}, {}, {})".format(color_tuple[0], color_tuple[1], color_tuple[2])
            return str(color_tuple)

        fg_color = to_rgb_str(tab_selected_text_color)
        bg_color = to_rgb_str(highlight_line_color)
        wnd_color = to_rgb_str(window_color)

        # Create the close info button on top of the text edit area
        self.close_button = QPushButton(" Esc", self)
        self.close_button.setToolTip("Press Esc or click to exit markdown preview")
        self.close_button.clicked.connect(self.close_preview)

        # Set the "File > Quit" icon to the button
        if 'quit' in icons:
            self.close_button.setIcon(QIcon(icons['quit']))

        # Style the button with [tab_selected_text] for color, [highlight_line] for background,
        # current theme font family, and exact tab font size.
        self.close_button.setStyleSheet(
            """
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {wnd};
                border-radius: 4px;
                padding: 4px 10px;
                font-family: "{family}";
                font-size: {size}pt;
            }}
            QPushButton:hover {{
                background-color: {bg};
                border: 2px solid {fg};
                color: {fg};
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                background-color: {bg};
                opacity: 0.8;
            }}
        """.format(
                bg=bg_color,
                fg=fg_color,
                wnd=wnd_color,
                size=custom_size,
                family=font_family,
            )
        )
        self.close_button.adjustSize()

        # Listen to parent editor resize/visibility events to keep overlay synchronized
        self.editor.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.editor:
            if event.type() == QEvent.Resize:
                self.setGeometry(self.editor.geometry())
            elif event.type() == QEvent.Hide:
                self.hide()
            elif event.type() == QEvent.Show:
                self.show()
        return super(MarkdownPreviewEdit, self).eventFilter(obj, event)

    def resizeEvent(self, event):
        super(MarkdownPreviewEdit, self).resizeEvent(event)
        if hasattr(self, 'close_button'):
            # Place the button inside the viewport space (to avoid scrollbar overlap)
            margin = 15
            btn_w = self.close_button.width()
            x = self.viewport().width() - btn_w - margin
            y = margin
            self.close_button.move(x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_preview()
            return
        super(MarkdownPreviewEdit, self).keyPressEvent(event)

    def close_preview(self):
        # Safe cleanup of the event filter and widget destruction
        try:
            self.editor.removeEventFilter(self)
        except Exception:
            pass
        self.close()
        self.editor.setFocus()
        if hasattr(self.editor, 'markdown_preview_widget'):
            self.editor.markdown_preview_widget = None
