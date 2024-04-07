# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#  Author: Sergei Krumas (github.com/sergkrumas)
#
# ##### END GPL LICENSE BLOCK #####

import sys

from PyQt5.QtWidgets import (QApplication,)
from PyQt5.QtCore import (QPoint, QPointF, QRect, Qt, QRectF, QMarginsF)
from PyQt5.QtGui import (QPainterPath, QColor, QBrush, QPixmap, QPainter, QTransform, QFont, QPen,
                    QTextDocument, QAbstractTextDocumentLayout, QPalette, QTextCursor, QTextLine)

from _utils import (check_scancode_for,)




class BoardTextEditItemMixin():

	# elements means item
	# code copied from OXXXY Screenshoter
	# https://github.com/sergkrumas/oxxxy

    def board_DeactivateTextElement(self):
        if self.active_element:
            if self.active_element.type == self.BoardItem.types.ITEM_NOTE:
                self.active_element = None
                # не нужно вызывать здесь self.board_SetSelected(None),
                # потому что elementsDeactivateTextElement вызывается
                # в начале работы инструмента «выделение и перемещение»
                self.update()
                return True
        return False

    def board_TextElementSetParameters(self, elem):
        if elem.text_doc is not None:
            self.board_TextElementSetFont(elem)

    def board_TextElementGetFontPixelSize(self, elem):
        return int(20+10*elem.size)

    def board_TextElementInputEvent(self, event):
        ae = self.active_element
        if ae is None or ae.type != self.BoardItem.types.ITEM_NOTE:
            return

        if event.modifiers() == Qt.ControlModifier and check_scancode_for(event, "V"):
            text = ""
            app = QApplication.instance()
            cb = app.clipboard()
            mdata = cb.mimeData()
            if mdata and mdata.hasText():
                text = mdata.text()
        else:
            text = event.text()

        _cursor = QTextCursor(ae.text_doc)
        _cursor.setPosition(ae.text_doc_cursor_pos)

        if event.key() in [Qt.Key_Left, Qt.Key_Right]:
            if event.key() == Qt.Key_Left:
                ae.text_doc_cursor_pos -= 1
                ae.text_doc_cursor_pos = max(ae.text_doc_cursor_pos, 0)
            elif event.key() == Qt.Key_Right:
                ae.text_doc_cursor_pos += 1
                ae.text_doc_cursor_pos = min(ae.text_doc_cursor_pos, len(ae.text_doc.toPlainText()))
        elif event.key() == Qt.Key_Backspace:
            _cursor.deletePreviousChar()
            ae.text_doc_cursor_pos -= 1
        else:
            _cursor.beginEditBlock()
            _cursor.insertText(text)
            ae.text_doc_cursor_pos += len(text)
            _cursor.endEditBlock()

        # text_line = self.board_TextElementCurrentTextLine(_cursor)
        # print('text_line', text_line.lineNumber())
        ae.plain_text = ae.text_doc.toPlainText()
        if self.Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS:
            self.board_TextElementUpdateProxyPixmap(ae)

        self.board_TextElementRecalculateGabarit(ae)
        self.update_selection_bouding_box()

        self.update()

    def board_TextElementRecalculateGabarit(self, element):
        # обновление габаритов виджета трансформации

        s = element.text_doc.size()
        content_rect = QRectF(QPointF(0, 0), s)
        content_rect.moveCenter(element.item_position)
        element.start_point = content_rect.topLeft()
        element.end_point = content_rect.bottomRight()
        if False:
            element.item_scale_x = 1.0
            element.item_scale_y = 1.0
        element.calc_local_data()

    def board_GetPenFromElement(self, element):
        color = element.color
        size = element.size
        PEN_SIZE = 25
        pen = QPen(color, 1+PEN_SIZE*size)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen, color, size

    def board_TextElementDraw(self, painter, element):

        def tweakedDrawContents(text_document, _painter_, rect):
            # дефолтный drawContents не поддерживает изменение текста
            _painter_.save()
            ctx = QAbstractTextDocumentLayout.PaintContext()
            ctx.palette.setColor(QPalette.Text, _painter_.pen().color())
            # у нас всегда отображается всё, поэтому смысла в этом нет
            # if rect.isValid():
            #     _painter_.setClipRect(rect)
            #     ctx.clip = rect
            text_document.documentLayout().draw(_painter_, ctx)
            _painter_.restore()

        pen, color, size = self.board_GetPenFromElement(element)
        painter.setPen(pen)
        painter.setBrush(QBrush(color))

        text_doc = element.text_doc
        # рисуем сам текст
        tweakedDrawContents(text_doc, painter, None) # text_doc.drawContents(painter, QRectF())

    def board_TextElementUpdateProxyPixmap(self, element):
        element.proxy_pixmap = QPixmap(element.text_doc.size().toSize())
        element.proxy_pixmap.fill(Qt.transparent)
        p = QPainter()
        p.begin(element.proxy_pixmap)
        self.board_TextElementDraw(p, element)
        p.end()

    def board_TextElementCurrentTextLine(self, cursor):
        block = cursor.block()
        if not block.isValid():
            return QTextLine()

        layout = block.layout()
        if not layout:
            return QTextLine()

        relativePos = cursor.position() - block.position()
        return layout.lineForTextPosition(relativePos)

    def board_TextElementIsInputEvent(self, event):
        is_event = self.active_element is not None and self.active_element.type == self.BoardItem.types.ITEM_NOTE
        is_event = is_event and event.key() != Qt.Key_Escape
        is_event = is_event and event.key() not in [Qt.Key_Delete, Qt.Key_Insert, Qt.Key_Home, Qt.Key_End, Qt.Key_PageDown, Qt.Key_PageUp]
        is_event = is_event and (bool(event.text()) or (event.key() in [Qt.Key_Left, Qt.Key_Right]))
        is_event = is_event and ((not event.modifiers()) or \
                    (Qt.ShiftModifier == event.modifiers()) or \
                    (event.modifiers() == Qt.ControlModifier and check_scancode_for(event, "V")))
        return is_event

    def board_ImplantTextElement(self, elem):
        text_doc = QTextDocument()
        elem.text_doc = text_doc
        self.board_TextElementInit(elem)
        text_doc.setPlainText(elem.plain_text)

    def board_TextElementSetFont(self, element):
        font = QFont()
        font_pixel_size = self.board_TextElementGetFontPixelSize(element)
        font.setPixelSize(font_pixel_size)
        element.text_doc.setDefaultFont(font)

    def board_TextElementSetCursorPosByClick(self, event):
        ae = self.active_element
        if ae.draw_transform is not None:
            viewport_cursor_pos = event.pos()
            inv, ok = ae.draw_transform.inverted()
            if ok:
                pos = inv.map(viewport_cursor_pos)
                text_cursor_pos = ae.text_doc.documentLayout().hitTest(pos, Qt.FuzzyHit)
                ae.text_doc_cursor_pos = text_cursor_pos

    def board_TextElementInit(self, elem):
        text_doc = elem.text_doc
        self.board_TextElementSetFont(elem)
        text_doc.setTextWidth(-1)
        elem.text_doc_cursor_pos = 0
        text_doc.setDocumentMargin(50)

    def board_TextElementDrawOnCanvas(self, painter, element, final):
        if element.text_doc is not None:
            text_doc = element.text_doc

            size_obj = text_doc.size().toSize()
            height = size_obj.height()
            pos = element.local_end_point - QPointF(0, height)

            s = text_doc.size().toSize()

            # смещение к середине
            offset_x = s.width()/2
            offset_y = s.height()/2
            offset_translation = QTransform()
            offset_translation.translate(-offset_x, -offset_y)

        item_transform = element.get_transform_obj(board=self)
        if element.text_doc is not None:
            item_transform = offset_translation * item_transform
        element.draw_transform = item_transform
        painter.setTransform(item_transform)
        painter.save()

        if element.text_doc:
            text_doc = element.text_doc

            # подложка
            if True:
                painter.save()
                painter.setPen(Qt.NoPen)
                content_rect = QRect(QPoint(), s)

                path = QPainterPath()
                path.addRoundedRect(QRectF(content_rect), element.margin_value,
                    element.margin_value)
                painter.fillPath(path, QBrush(QColor(200, 200, 200)))
                painter.restore()

            # текст и курсор
            if self.Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS:
                if element.proxy_pixmap is None:
                    self.board_TextElementUpdateProxyPixmap(element)
                painter.drawPixmap(QPoint(0, 0), element.proxy_pixmap)
            else:
                self.board_TextElementDraw(painter, element)

            # рисуем курсор
            doc_layout = text_doc.documentLayout()
            cursor_pos = element.text_doc_cursor_pos
            block = text_doc.begin()
            end = text_doc.end()
            while block != end:
                # block_rect = doc_layout.blockBoundingRect(block)
                # painter.drawRect(block_rect)
                if self.active_element is element and not final:
                    if block.contains(cursor_pos):
                        local_cursor_pos = cursor_pos - block.position()
                        block.layout().drawCursor(painter, QPointF(0,0), local_cursor_pos, 1)
                block = block.next()

        painter.restore()
        painter.resetTransform()


# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
