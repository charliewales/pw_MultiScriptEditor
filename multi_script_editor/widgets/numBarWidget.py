from vendor.Qt.QtCore import QRect, Qt, QPoint
from vendor.Qt.QtGui import QBrush, QColor, QPainter, QPalette, QPen
from vendor.Qt.QtWidgets import QApplication, QWidget
import managers

class lineNumberBarClass(QWidget):
    def __init__(self, edit, parent=None):
        QWidget.__init__(self, parent)

        if hasattr(QApplication, 'desktop'):
            desktop = QApplication.desktop()
            screen_resolution = desktop.screenGeometry()
        else:
            from vendor.Qt.QtGui import QGuiApplication
            screen_resolution = QGuiApplication.primaryScreen().geometry()
        width, height = screen_resolution.width(), screen_resolution.height()

        self.font_size_mult = 1.0
        if width > 2560:
            self.font_size_mult = 1.5

        self.edit = edit
        self.highest_line = 0
        self.setMinimumWidth(30)
        self.bg = None

    def update(self, *args):
        '''
        Updates the number bar to display the current set of numbers.
        Also, adjusts the width of the number bar if necessary.
        '''
        # The + 4 is used to compensate for the current line being bold.
        self.highest_line = self.edit.document().blockCount()
        fontSize = self.edit.font().pointSize()
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(str(self.highest_line)) if hasattr(fm, 'horizontalAdvance') else fm.width(str(self.highest_line))
        width = ((text_width + 7))*(fontSize/13.0)
        if self.width() != width and width > 10:
            self.setFixedWidth(width)
        if hasattr(self.edit, '_highlight_color_cache') and self.edit._highlight_color_cache:
            self.bg = QColor.fromRgb(*self.edit._highlight_color_cache)
        else:
            bg = self.palette().brush(QPalette.Normal,QPalette.Window).color().toHsv()
            v = bg.value()
            if v > 20:
                v = int(bg.value()*0.8)
            else:
                v = int(bg.value()*1.1)
            self.bg = QColor.fromHsv(bg.hue(), bg.saturation(), v)
        self.setMinimumWidth(30)
        QWidget.update(self, *args)

    def paintEvent(self, event):
        contents_y = self.edit.verticalScrollBar().value()
        page_bottom = contents_y + self.edit.viewport().height()
        font_metrics = self.fontMetrics()
        current_block = self.edit.document().findBlock(self.edit.textCursor().position())
        painter = QPainter(self)
        
        # Get the first visible block
        cursor = self.edit.cursorForPosition(QPoint(0, 0))
        block = cursor.block()
        
        # Start a bit earlier to handle any partially visible block
        if block.previous().isValid():
            block = block.previous()
            
        line_count = block.blockNumber()
        
        # Iterate over all visible text blocks in the document.
        fontSize = self.edit.font().pointSize()*self.font_size_mult
        font = painter.font()
        font.setPixelSize(fontSize)
        offset = font_metrics.ascent() + font_metrics.descent()*0.7
        color = painter.pen().color()
        painter.setFont(font)
        align = Qt.AlignRight
        while block.isValid():
            line_count += 1
            # The top left position of the block in the document
            position = self.edit.document().documentLayout().blockBoundingRect(block).topLeft()
            # Check if the position of the block is outside of the visible area.
            if position.y() > page_bottom:
                break
            if position.y() + fontSize < contents_y:
                block = block.next()
                continue

            rec = QRect(0,
                        round(position.y()) - contents_y,
                        self.width()-5,
                        fontSize + offset)

            # draw line rect
            if block == current_block:
                painter.setPen(Qt.NoPen)
                # Only draw background if self.bg has been initialized
                if self.bg is not None:
                    painter.setBrush(QBrush(self.bg))
                    painter.drawRect(QRect(0,
                            round(position.y()) - contents_y,
                            self.width(),
                            fontSize + (offset/2) ))
                # restore color
                painter.setPen(QPen(color))

            # draw error indicator if this line has a syntax error
            if hasattr(self.edit, 'syntax_errors') and line_count in self.edit.syntax_errors:
                painter.setBrush(QBrush(QColor("red")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(3, round(position.y()) - contents_y + int(fontSize / 2) - 2, 6, 6)
                painter.setPen(QPen(color))

            # draw text
            painter.drawText(rec, align, str(line_count))
            # control points

            block = block.next()
        painter.end()
        QWidget.paintEvent(self, event)

    def eventFilter(self, object, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary singals.
        if object in (self.edit, self.edit.viewport()):
            self.update()
            return False
        return QWidget.eventFilter(object, event)
