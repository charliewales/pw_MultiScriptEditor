from vendor.Qt.QtCore import QRect, Qt, QPoint
from vendor.Qt.QtGui import QBrush, QColor, QPainter, QPalette, QPen, QGuiApplication, QFontMetrics
from vendor.Qt.QtWidgets import QApplication, QWidget

class lineNumberBarClass(QWidget):
    def __init__(self, edit, parent=None):
        QWidget.__init__(self, parent)

        if hasattr(QApplication, 'desktop'):
            desktop = QApplication.desktop()
            screen_resolution = desktop.screenGeometry()
        else:
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
        self.highest_line = self.edit.document().blockCount()
        font = self.edit.font()
        
        pt_size = font.pointSizeF()
        if pt_size > 0:
            if hasattr(self.edit, '_line_num_size_cache') and self.edit._line_num_size_cache is not None:
                font.setPointSizeF(float(self.edit._line_num_size_cache))
            else:
                font.setPointSizeF(max(1.0, pt_size * 0.8))
        else:
            px_size = font.pixelSize()
            if px_size > 0:
                if hasattr(self.edit, '_line_num_size_cache') and self.edit._line_num_size_cache is not None:
                    font.setPixelSize(self.edit._line_num_size_cache)
                else:
                    font.setPixelSize(max(1, int(px_size * 0.8)))
        
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(str(self.highest_line) + "0") if hasattr(fm, 'horizontalAdvance') else fm.width(str(self.highest_line) + "0")
        
        width = max(30, text_width + 10)
        
        if self.width() != width:
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
        
        font = self.edit.font()
        
        pt_size = font.pointSizeF()
        if pt_size > 0:
            if hasattr(self.edit, '_line_num_size_cache') and self.edit._line_num_size_cache is not None:
                font.setPointSizeF(float(self.edit._line_num_size_cache))
            else:
                font.setPointSizeF(max(1.0, pt_size * 0.8))
        else:
            px_size = font.pixelSize()
            if px_size > 0:
                if hasattr(self.edit, '_line_num_size_cache') and self.edit._line_num_size_cache is not None:
                    font.setPixelSize(self.edit._line_num_size_cache)
                else:
                    font.setPixelSize(max(1, int(px_size * 0.8)))
        
        # update fm for paint
        font_metrics = QFontMetrics(font)
        
        offset = font_metrics.ascent() + font_metrics.descent()*0.7
        color = painter.pen().color()
        if hasattr(self.edit, '_line_num_text_cache') and self.edit._line_num_text_cache:
            color = QColor.fromRgb(*self.edit._line_num_text_cache)
        painter.setFont(font)
        painter.setPen(color)
        align = Qt.AlignRight | Qt.AlignVCenter
        is_plaintextedit = hasattr(self.edit, 'blockBoundingGeometry')
        while block.isValid():
            line_count += 1
            
            if is_plaintextedit:
                block_rect = self.edit.blockBoundingGeometry(block).translated(self.edit.contentOffset())
                pos_y = block_rect.top()
                block_height = block_rect.height()
                if pos_y > self.edit.viewport().height():
                    break
                if pos_y + block_height < 0:
                    block = block.next()
                    continue
            else:
                # The top left position of the block in the document
                block_rect = self.edit.document().documentLayout().blockBoundingRect(block)
                pos_y = block_rect.top() - contents_y
                block_height = block_rect.height()
                
                # Check if the position of the block is outside of the visible area.
                if block_rect.top() > page_bottom:
                    break
                if block_rect.top() + block_height < contents_y:
                    block = block.next()
                    continue

            rec = QRect(0,
                        round(pos_y),
                        self.width() - 5,
                        round(block_height))

            # draw line rect
            if block == current_block:
                painter.setPen(Qt.NoPen)
                # Only draw background if self.bg has been initialized
                if self.bg is not None:
                    painter.setBrush(QBrush(self.bg))
                    painter.drawRect(QRect(0,
                            round(pos_y),
                            self.width(),
                            round(block_height) ))
                # restore color
                painter.setPen(QPen(color))

            # draw error indicator if this line has a syntax error
            if hasattr(self.edit, 'syntax_errors') and line_count in self.edit.syntax_errors:
                painter.setBrush(QBrush(QColor("red")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(3, round(pos_y) + int(block_height / 2) - 3, 6, 6)
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
