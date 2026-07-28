from vendor.Qt.QtCore import QPoint, QRect, Qt
from vendor.Qt.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QGuiApplication,
    QPainter,
    QPalette,
    QPen,
    QPolygon,
)
from vendor.Qt.QtWidgets import QApplication, QWidget


class lineNumberBarClass(QWidget):
    def __init__(self, edit, parent=None):
        QWidget.__init__(self, parent)

        if hasattr(QApplication, 'desktop'):
            desktop = QApplication.desktop()
            screen_resolution = desktop.screenGeometry()
        else:
            screen_resolution = QGuiApplication.primaryScreen().geometry()
        width = screen_resolution.width()

        self.font_size_mult = 1.0
        if width > 2560:
            self.font_size_mult = 1.5

        self.edit = edit
        self.highest_line = 0
        self.setMinimumWidth(45)
        self.bg = None
        self.setMouseTracking(True)

    def enterEvent(self, event):
        self.update()
        QWidget.enterEvent(self, event)

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
        
        width = max(55, text_width + 30)
        
        if self.width() != width:
            self.setFixedWidth(width)
            
        if hasattr(self.edit, '_highlight_color_cache') and self.edit._highlight_color_cache:
            self.bg = QColor.fromRgb(*self.edit._highlight_color_cache)
        else:
            bg = self.palette().brush(QPalette.Normal, QPalette.Window).color().toHsv()
            v = bg.value()
            if v > 20:
                v = int(bg.value() * 0.8)
            else:
                v = int(bg.value() * 1.1)
            self.bg = QColor.fromHsv(bg.hue(), bg.saturation(), v)
        QWidget.update(self, *args)

    def paintEvent(self, event):
        contents_y = self.edit.verticalScrollBar().value()
        page_bottom = contents_y + self.edit.viewport().height()
        current_block = self.edit.document().findBlock(self.edit.textCursor().position())
        painter = QPainter(self)
        
        # Get the first visible block
        cursor = self.edit.cursorForPosition(QPoint(0, 0))
        block = cursor.block()
        
        # Start a bit earlier to handle any partially visible block
        if block.previous().isValid():
            block = block.previous()
            
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
        color = painter.pen().color()
        if hasattr(self.edit, '_line_num_text_cache') and self.edit._line_num_text_cache:
            color = QColor.fromRgb(*self.edit._line_num_text_cache)
        painter.setFont(font)
        painter.setPen(color)
        align = Qt.AlignRight | Qt.AlignVCenter
        is_plaintextedit = hasattr(self.edit, 'blockBoundingGeometry')
        
        vp_offset = 0
        if self.edit and hasattr(self.edit, 'viewport') and self.edit.viewport():
            vp_offset = self.edit.y() + self.edit.viewport().y() - self.y()

        while block.isValid():
            if not block.isVisible():
                block = block.next()
                continue
                
            actual_line_number = block.blockNumber() + 1
            
            if is_plaintextedit:
                block_rect = self.edit.blockBoundingGeometry(block).translated(self.edit.contentOffset())
                pos_y = block_rect.top() + vp_offset
                layout_h = block.layout().boundingRect().height() if block.layout() and block.layout().boundingRect().height() > 0 else 0
                block_height = layout_h if layout_h > 0 else block_rect.height()
                if pos_y > self.edit.viewport().height() + vp_offset:
                    break
                if pos_y + block_height < vp_offset:
                    block = block.next()
                    continue
            else:
                # The top left position of the block in the document
                block_rect = self.edit.document().documentLayout().blockBoundingRect(block)
                pos_y = block_rect.top() - contents_y + vp_offset
                block_height = block_rect.height()
                
                # Check if the position of the block is outside of the visible area.
                if block_rect.top() > page_bottom:
                    break
                if block_rect.top() + block_height < contents_y:
                    block = block.next()
                    continue

            # Draw highlight for the current block
            if block == current_block:
                painter.setPen(Qt.NoPen)
                if self.bg is not None:
                    painter.setBrush(QBrush(self.bg))
                    top_y = int(round(pos_y))
                    bottom_y = int(round(pos_y + block_height))
                    painter.drawRect(QRect(0,
                            top_y,
                            self.width(),
                            bottom_y - top_y))
                painter.setPen(QPen(color))

            # Draw error indicator if this line has a syntax error
            if hasattr(self.edit, 'syntax_errors') and actual_line_number in self.edit.syntax_errors:
                painter.setBrush(QBrush(QColor("red")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(3, round(pos_y) + int(block_height / 2) - 3, 6, 6)
                painter.setPen(QPen(color))

            # Draw bookmark indicator
            data = block.userData()
            is_bookmarked = data and getattr(data, 'bookmarked', False)
            is_block_hovered = (block.blockNumber() == getattr(self, 'hover_block_number', -1))
            is_bookmark_hovered = is_block_hovered and getattr(self, 'hover_in_bookmark_area', False)

            if is_bookmarked or is_bookmark_hovered:
                if hasattr(self.edit, 'hgl') and hasattr(self.edit.hgl, 'colors') and self.edit.hgl.colors:
                    bg_tuple = self.edit.hgl.colors.get('bookmark', self.edit.hgl.colors.get('string', (245, 165, 18)))
                else:
                    bg_tuple = (245, 165, 18)

                brush_color = QColor(*bg_tuple)
                if not is_bookmarked and is_bookmark_hovered:
                    brush_color.setAlpha(100)

                painter.setBrush(QBrush(brush_color))
                painter.setPen(Qt.NoPen)
                cy = round(pos_y) + int(block_height / 2)
                p1 = QPoint(5, cy - 6)
                p2 = QPoint(13, cy - 6)
                p3 = QPoint(13, cy + 6)
                p4 = QPoint(9, cy + 3)
                p5 = QPoint(5, cy + 6)
                painter.drawPolygon(QPolygon([p1, p2, p3, p4, p5]))
                painter.setPen(QPen(color))

            # Draw line number text
            rec = QRect(18,
                        round(pos_y),
                        self.width() - 36,
                        round(block_height))
            painter.drawText(rec, align, str(actual_line_number))

            # Draw folding chevron
            is_fold_start = False
            is_folded = False
            if hasattr(self.edit, 'folding_regions'):
                is_fold_start = block.blockNumber() in self.edit.folding_regions
                data = block.userData()
                is_folded = data and getattr(data, 'folded', False)

            is_in_folding_hover = getattr(self, 'hover_in_folding_area', False)
            showing_bookmark = is_bookmarked or is_bookmark_hovered
            
            draw_chevron = False
            if is_fold_start:
                if is_in_folding_hover:
                    draw_chevron = True
                elif is_folded and not showing_bookmark:
                    draw_chevron = True

            if draw_chevron:
                cx = self.width() - 8
                cy = round(pos_y) + int(block_height / 2)
                
                chevron_pen = QPen(color, 1.5)
                chevron_pen.setCapStyle(Qt.RoundCap)
                chevron_pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(chevron_pen)
                
                if is_folded:
                    # Right-pointing chevron (collapsed)
                    p1 = QPoint(cx - 2, cy - 3)
                    p2 = QPoint(cx + 2, cy)
                    p3 = QPoint(cx - 2, cy + 3)
                    painter.drawPolyline([p1, p2, p3])
                else:
                    # Down-pointing chevron (expanded)
                    p1 = QPoint(cx - 3, cy - 2)
                    p2 = QPoint(cx, cy + 2)
                    p3 = QPoint(cx + 3, cy - 2)
                    painter.drawPolyline([p1, p2, p3])
                
                painter.setPen(QPen(color))

            block = block.next()
            
        painter.end()
        QWidget.paintEvent(self, event)

    def mouseMoveEvent(self, event):
        click_y = event.y()
        contents_y = self.edit.verticalScrollBar().value()
        cursor = self.edit.cursorForPosition(QPoint(0, 0))
        block = cursor.block()
        if block.previous().isValid():
            block = block.previous()
            
        vp_offset = 0
        if self.edit and hasattr(self.edit, 'viewport') and self.edit.viewport():
            vp_offset = self.edit.y() + self.edit.viewport().y() - self.y()

        hover_block = -1
        is_plaintextedit = hasattr(self.edit, 'blockBoundingGeometry')
        while block.isValid():
            if not block.isVisible():
                block = block.next()
                continue
                
            if is_plaintextedit:
                block_rect = self.edit.blockBoundingGeometry(block).translated(self.edit.contentOffset())
                pos_y = block_rect.top() + vp_offset
                layout_h = block.layout().boundingRect().height() if block.layout() and block.layout().boundingRect().height() > 0 else 0
                block_height = layout_h if layout_h > 0 else block_rect.height()
            else:
                block_rect = self.edit.document().documentLayout().blockBoundingRect(block)
                pos_y = block_rect.top() - contents_y + vp_offset
                block_height = block_rect.height()
                
            if pos_y <= click_y <= pos_y + block_height:
                hover_block = block.blockNumber()
                break
            block = block.next()

        hover_in_bookmark_area = (event.x() < 20)
        hover_in_folding_area = (event.x() > self.width() - 20)

        changed = False
        if getattr(self, 'hover_block_number', -1) != hover_block:
            self.hover_block_number = hover_block
            changed = True
        if getattr(self, 'hover_in_bookmark_area', False) != hover_in_bookmark_area:
            self.hover_in_bookmark_area = hover_in_bookmark_area
            changed = True
        if getattr(self, 'hover_in_folding_area', False) != hover_in_folding_area:
            self.hover_in_folding_area = hover_in_folding_area
            changed = True

        if changed:
            self.update()
        QWidget.mouseMoveEvent(self, event)

    def leaveEvent(self, event):
        self.hover_block_number = -1
        self.hover_in_bookmark_area = False
        self.hover_in_folding_area = False
        self.update()
        QWidget.leaveEvent(self, event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            click_y = event.y()
            contents_y = self.edit.verticalScrollBar().value()
            cursor = self.edit.cursorForPosition(QPoint(0, 0))
            block = cursor.block()
            if block.previous().isValid():
                block = block.previous()
                
            vp_offset = 0
            if self.edit and hasattr(self.edit, 'viewport') and self.edit.viewport():
                vp_offset = self.edit.y() + self.edit.viewport().y() - self.y()

            is_plaintextedit = hasattr(self.edit, 'blockBoundingGeometry')
            while block.isValid():
                if not block.isVisible():
                    block = block.next()
                    continue
                    
                if is_plaintextedit:
                    block_rect = self.edit.blockBoundingGeometry(block).translated(self.edit.contentOffset())
                    pos_y = block_rect.top() + vp_offset
                    layout_h = block.layout().boundingRect().height() if block.layout() and block.layout().boundingRect().height() > 0 else 0
                    block_height = layout_h if layout_h > 0 else block_rect.height()
                else:
                    block_rect = self.edit.document().documentLayout().blockBoundingRect(block)
                    pos_y = block_rect.top() - contents_y + vp_offset
                    block_height = block_rect.height()
                    
                if pos_y <= click_y <= pos_y + block_height:
                    # Check if click is on the right side (chevron / folding region)
                    if event.x() > self.width() - 20:
                        block_num = block.blockNumber()
                        if hasattr(self.edit, 'folding_regions') and block_num in self.edit.folding_regions:
                            recursive = bool(event.modifiers() & Qt.ShiftModifier)
                            self.edit.toggle_fold(block_num, recursive=recursive)
                            self.update()
                            return
                    elif event.x() < 20:
                        # Toggle bookmark on left margin click
                        block_num = block.blockNumber()
                        if hasattr(self.edit, 'toggle_bookmark'):
                            self.edit.toggle_bookmark(block_num)
                            self.update()
                            return
                    break
                block = block.next()
        QWidget.mousePressEvent(self, event)

    def eventFilter(self, object, event):
        # Update the line numbers for all events on the text edit and the viewport.
        # This is easier than connecting all necessary signals.
        if object in (self.edit, self.edit.viewport()):
            self.update()
            return False
        return QWidget.eventFilter(object, event)
