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
from PyQt5.QtCore import (QPoint, QPointF, QRect, Qt, QRectF, QMarginsF, QTimer)
from PyQt5.QtGui import (QPainterPath, QColor, QBrush, QPixmap, QPainter, QTransform, QFont, QPen,
                    QTextDocument, QAbstractTextDocumentLayout, QPalette, QTextCursor, QTextLine)

from _utils import (check_scancode_for,)

from colorpicker import ColorPicker


class BoardTextEditItemMixin():

	# "element" means "item"
	# code copied from OXXXY Screenshoter
	# https://github.com/sergkrumas/oxxxy


    def board_TextElementInitModule(self):
        self.board_ni_text_cursor = None
        self.board_ni_selection_rects = []

        self.blinkingCursorTimer = QTimer()
        self.blinkingCursorTimer.setInterval(600)
        self.blinkingCursorTimer.timeout.connect(self.board_TextElementCursorBlinkingCycleHandler)
        self.blinkingCursorTimer.start()
        self.blinkingCursorHidden = False

        self.board_ni_colors_buttons = None
        self.board_ni_inside_op_ongoing = False
        self.board_ni_ts_dragNdrop_ongoing = False
        self.board_ni_ts_dragNdrop_cancelled = False
        self.board_ni_temp_cursor_pos = 0
        self.board_ni_temp_start_cursor_pos = None

    def board_TextElementResetColorsButtons(self):
        self.board_ni_colors_buttons = None        

    def board_TextElementTextSelectionDragNDropOngoing(self):
        return self.board_ni_ts_dragNdrop_ongoing and not self.board_ni_ts_dragNdrop_cancelled

    def board_TextElementCancelTextSelectionDragNDrop(self):
        self.board_ni_ts_dragNdrop_cancelled = True
        self.board_cursor_setter()

    def board_TextElementCursorBlinkingCycleHandler(self):
        ae = self.active_element
        if ae is not None and ae.type == self.BoardItem.types.ITEM_NOTE:
            self.blinkingCursorHidden = not self.blinkingCursorHidden
            self.update()

    def board_TextElementDeactivateEditMode(self):
        if self.board_TextElementIsActiveElement():
            if self.active_element.editing:
                self.active_element.editing = False
                self.board_ni_text_cursor = None
                self.board_ni_selection_rects = []
                # self.active_element = None
                # не нужно вызывать здесь self.board_SetSelected(None),
                # потому что elementsDeactivateTextElement вызывается
                # в начале работы инструмента «выделение и перемещение»
                self.update()
                return True
        return False

    def board_TextElementActivateEditMode(self, elem):
        self.active_element = elem
        self.board_ni_text_cursor = QTextCursor(elem.text_doc)
        self.board_ni_text_cursor.select(QTextCursor.Document)
        elem.editing = True
        self.board_TextElementDefineSelectionRects()

    def board_TextElementIsElementActiveElement(self, elem):
        if elem and elem.type == self.BoardItem.types.ITEM_NOTE:
            return True
        return False

    def board_TextElementIsActiveElement(self):
        return self.board_TextElementIsElementActiveElement(self.active_element)

    def board_TextElementGetFontPixelSize(self, elem):
        return int(20+10*elem.size)

    # def board_TextElementCurrentTextLine(self, cursor):
    #     block = cursor.block()
    #     if not block.isValid():
    #         return QTextLine()

    #     layout = block.layout()
    #     if not layout:
    #         return QTextLine()

    #     relativePos = cursor.position() - block.position()
    #     return layout.lineForTextPosition(relativePos)

    def board_TextElementKeyPressEventHandler(self, event):
        key = event.key()

        if self.board_TextElementIsInputEvent(event):
            self.board_TextElementInputEvent(event)
            self.is_board_text_input_event = True
            return True

        if key == Qt.Key_Control:
            # for note item selection drag&drop
            self.board_cursor_setter()
            return False

        return False

    def board_TextElementInputEvent(self, event):
        ae = self.active_element
        if not (self.board_TextElementIsActiveElement() and ae.editing):
            return

        if self.board_ni_ts_dragNdrop_ongoing or \
            self.board_ni_ts_dragNdrop_cancelled:
            return

        ctrl = bool(event.modifiers() & Qt.ControlModifier)
        shift = bool(event.modifiers() & Qt.ShiftModifier)

        if ctrl and check_scancode_for(event, "V"):
            text = ""
            app = QApplication.instance()
            cb = app.clipboard()
            mdata = cb.mimeData()
            if mdata and mdata.hasText():
                text = mdata.text()
        else:
            text = event.text()

        _cursor = self.board_ni_text_cursor

        if event.key() in [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]:
            if shift:
                move_mode = QTextCursor.KeepAnchor
            else:
                move_mode = QTextCursor.MoveAnchor

            if event.key() == Qt.Key_Left:
                if ctrl:
                    _cursor.movePosition(QTextCursor.PreviousWord, move_mode)
                else:
                    new_pos = max(_cursor.position()-1, 0)
                    _cursor.setPosition(new_pos, move_mode)

            elif event.key() == Qt.Key_Right:
                if ctrl:
                    _cursor.movePosition(QTextCursor.NextWord, move_mode)
                else:
                    new_pos = min(_cursor.position()+1, len(ae.text_doc.toPlainText()))
                    _cursor.setPosition(new_pos, move_mode)

            elif event.key() == Qt.Key_Up:
                if not ctrl:
                    move_mode = QTextCursor.MoveAnchor
                _cursor.movePosition(QTextCursor.Up, move_mode)

            elif event.key() == Qt.Key_Down:
                if not ctrl:
                    move_mode = QTextCursor.MoveAnchor
                _cursor.movePosition(QTextCursor.Down, move_mode)

            self.blinkingCursorHidden = False

        elif event.key() == Qt.Key_Backspace:
            _cursor.deletePreviousChar()
        elif ctrl and check_scancode_for(event, "Z"):
            if ae.text_doc:
                ae.text_doc.undo()
        elif ctrl and check_scancode_for(event, "Y"):
            if ae.text_doc:
                ae.text_doc.redo()
        else:
            _cursor.beginEditBlock()
            _cursor.insertText(text)
            _cursor.endEditBlock()

        # text_line = self.board_TextElementCurrentTextLine(_cursor)
        # print('text_line', text_line.lineNumber())
        self.board_TextElementUpdateAfterInput()

    def board_TextElementUpdateAfterInput(self):
        ae = self.active_element
        ae.plain_text = ae.text_doc.toPlainText()
        if self.Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS:
            self.board_TextElementUpdateProxyPixmap(ae)

        self.board_TextElementRecalculateGabarit(ae)
        self.board_TextElementDefineSelectionRects()
        self.update_selection_bouding_box()

        self.update()

    def board_TextElementRecalculateGabarit(self, element):
        # обновление габаритов виджета трансформации

        s = element.text_doc.size()
        content_rect = QRectF(QPointF(0, 0), s)
        content_rect.moveCenter(element.position)
        element.start_point = content_rect.topLeft()
        element.end_point = content_rect.bottomRight()
        if False:
            element.scale_x = 1.0
            element.scale_y = 1.0
        element.calc_local_data()

    def board_GetPenFromElement(self, element):
        color = element.font_color
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
        text_opacity = color.alpha()/255
        painter.setOpacity(text_opacity)
        tweakedDrawContents(text_doc, painter, None) # text_doc.drawContents(painter, QRectF())
        painter.setOpacity(1.0)

    def board_TextElementUpdateProxyPixmap(self, element):
        element.proxy_pixmap = QPixmap(element.text_doc.size().toSize())
        element.proxy_pixmap.fill(Qt.transparent)
        p = QPainter()
        p.begin(element.proxy_pixmap)
        self.board_TextElementDraw(p, element)
        p.end()

    def board_TextElementIsInputEvent(self, event):
        ae = self.active_element
        redo_undo = check_scancode_for(event, "Z") or check_scancode_for(event, "Y")
        is_event = self.board_TextElementIsActiveElement() and ae.editing
        is_event = is_event and event.key() != Qt.Key_Escape
        is_event = is_event and event.key() not in [Qt.Key_Delete, Qt.Key_Insert, Qt.Key_Home, Qt.Key_End, Qt.Key_PageDown, Qt.Key_PageUp]
        is_event = is_event and (bool(event.text()) or (event.key() in [Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down]))
        is_event = is_event and ((not event.modifiers()) or \
                    ((Qt.ShiftModifier | Qt.ControlModifier) & event.modifiers() ) or \
                    (event.modifiers() == Qt.ControlModifier and ( check_scancode_for(event, "V")) or redo_undo ))
        return is_event

    def board_TextElementAttributesInitOnCreation(self, elem):
        self.board_TextElementSetDefaults(elem)
        elem.calc_local_data()
        self.board_ImplantTextElement(elem)
        self.board_TextElementRecalculateGabarit(elem)
        self.board_TextElementActivateEditMode(elem)

    def board_ImplantTextElement(self, elem):
        text_doc = QTextDocument()
        elem.text_doc = text_doc
        self.board_TextElementInit(elem)
        text_doc.setPlainText(elem.plain_text)

    def board_TextElementSetDefaults(self, elem, plain_text=None):
        if plain_text is None:
            elem.plain_text = 'Note'
        else:
            elem.plain_text = plain_text
        elem.size = 10.0
        elem.margin_value = 5
        elem.proxy_pixmap = None
        elem.editing = False
        elem.font_color = QColor(self.selection_color)
        elem.backplate_color = QColor(0, 0, 0, 0)
        elem.start_point = elem.position
        elem.end_point = elem.position + QPointF(200, 50)

    def board_TextElementSetFont(self, element):
        font = QFont()
        font_pixel_size = self.board_TextElementGetFontPixelSize(element)
        font.setPixelSize(font_pixel_size)
        element.text_doc.setDefaultFont(font)

    def board_TextElementHitTest(self, event):
        ae = self.active_element
        if ae.draw_transform is not None and ae.editing:
            viewport_cursor_pos = event.pos()
            inv, ok = ae.draw_transform.inverted()
            if ok:
                pos = inv.map(viewport_cursor_pos)
                text_cursor_pos = ae.text_doc.documentLayout().hitTest(pos, Qt.FuzzyHit)
                return text_cursor_pos
        return None

    def board_TextElementInit(self, elem):
        text_doc = elem.text_doc
        self.board_TextElementSetFont(elem)
        text_doc.setTextWidth(-1)
        text_doc.setDocumentMargin(80)

    def board_TextElementIsCursorInsideTextElement(self, event):
        ae = self.active_element
        if self.board_TextElementIsActiveElement():
            if ae.get_selection_area(board=self).containsPoint(event.pos(), Qt.WindingFill):
                return True
        return False

    def board_TextElementGetABFromTextCursor(self):
        poss = [self.board_ni_text_cursor.selectionStart(), self.board_ni_text_cursor.selectionEnd()]
        a = min(*poss)
        b = max(*poss)
        return a, b

    def board_TextElementStartSelection(self, event):
        if event.button() == Qt.LeftButton:
            ae = self.active_element
            if self.board_TextElementIsActiveElement() and ae.editing:
                hit_test_result = self.board_TextElementHitTest(event)
                a, b = self.board_TextElementGetABFromTextCursor()
                if hit_test_result is not None and a <= hit_test_result <= b and abs(b-a) > 0:
                    # drag start
                    print(f'drag start {abs(b-a)}')
                    self.board_ni_temp_cursor_pos = hit_test_result
                    self.board_ni_temp_start_cursor_pos = hit_test_result
                else:
                    # default start
                    print(f'default start')
                    hit_test_result = self.board_TextElementHitTest(event)
                    self.board_ni_text_cursor.setPosition(hit_test_result)
                    self.board_ni_ts_dragNdrop_ongoing = False
                    self.board_ni_temp_start_cursor_pos = None
        self.board_TextElementDefineSelectionRects()

    def board_TextElementEndSelection(self, event, finish=False):
        # код переусложнён, так как он обрабатывает как MouseMove, так и MouseRelease
        ae = self.active_element
        ctrl = event.modifiers() & Qt.ControlModifier
        if self.board_TextElementIsActiveElement() and ae.editing:
            hit_test_result = self.board_TextElementHitTest(event)
            if self.board_ni_ts_dragNdrop_ongoing and not self.board_ni_ts_dragNdrop_cancelled:
                if finish:
                    _cursor = self.board_ni_text_cursor
                    text_to_copy = _cursor.selectedText()
                    temp_cursor_pos = self.board_ni_temp_cursor_pos
                    a, b = self.board_TextElementGetABFromTextCursor()
                    selection_center_pos = int(a + (b - a)/2)
                    if text_to_copy:
                        if ctrl:
                            # копирование
                            _cursor.setPosition(temp_cursor_pos)
                            _cursor.beginEditBlock()
                            _cursor.insertText(text_to_copy)
                            _cursor.endEditBlock()
                        else:
                            # перенос
                            if a < temp_cursor_pos < b:
                                # сбрасывается внутрь выделения, отмена
                                pass
                            else:
                                # если выделение находится дальше
                                # чем позиция для переноса,
                                # то коректировка нужна.
                                # в противном случае она необходима
                                if selection_center_pos > temp_cursor_pos:
                                    pass
                                if selection_center_pos < temp_cursor_pos:
                                    temp_cursor_pos -= len(text_to_copy)

                                _cursor.deletePreviousChar()
                                _cursor.setPosition(temp_cursor_pos)
                                _cursor.beginEditBlock()
                                _cursor.insertText(text_to_copy)
                                _cursor.endEditBlock()
                        self.board_TextElementUpdateAfterInput()
                    self.board_ni_ts_dragNdrop_ongoing = False
                    self.board_ni_temp_start_cursor_pos = None
                    self.board_ni_temp_cursor_pos = None
                else:
                    self.board_ni_temp_cursor_pos = hit_test_result
                    self.blinkingCursorHidden = False
            else:
                if self.board_ni_temp_start_cursor_pos:
                    cursor_moved_a_bit = abs(hit_test_result - self.board_ni_temp_start_cursor_pos) > 0
                    if cursor_moved_a_bit:
                        self.board_ni_ts_dragNdrop_ongoing = True
                    elif finish:
                        self.board_ni_text_cursor.setPosition(hit_test_result, QTextCursor.MoveAnchor)
                else:
                    self.board_ni_text_cursor.setPosition(hit_test_result, QTextCursor.KeepAnchor)

        if finish:
            self.board_ni_ts_dragNdrop_ongoing = False
            self.board_ni_temp_start_cursor_pos = None
            self.board_ni_ts_dragNdrop_cancelled = False
        self.board_TextElementDefineSelectionRects()
        self.update()

    def board_TextElementSelectionMousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.board_TextElementStartSelection(event)
        self.update()

    def board_TextElementSelectionMouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.board_TextElementEndSelection(event)
        self.update()

    def board_TextElementSelectionMouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.board_TextElementEndSelection(event, finish=True)
            # tc = self.board_ni_text_cursor
            # out = f'{tc.selectionEnd()} {tc.selectionStart()}'
            # print(out)
        self.update()

    def board_TextElementDefineSelectionRects(self):
        self.board_ni_selection_rects = []

        ae = self.active_element
        if not (self.board_TextElementIsActiveElement() and ae.editing):
            return

        if self.board_ni_text_cursor.anchor() != self.board_ni_text_cursor.position():
            block = ae.text_doc.begin()
            end = ae.text_doc.end()
            docLayout = ae.text_doc.documentLayout()
            while block != end:
                if not block.text():
                    block = block.next()
                    continue

                blockRect = docLayout.blockBoundingRect(block)
                blockX = blockRect.x()
                blockY = blockRect.y()

                it = block.begin()
                while not it.atEnd():
                    fragment = it.fragment()

                    blockLayout = block.layout()
                    fragPos = fragment.position() - block.position()
                    fragEnd = fragPos + fragment.length()


                    start_frg = fragment.contains(self.board_ni_text_cursor.selectionStart())
                    end_frg = fragment.contains(self.board_ni_text_cursor.selectionEnd())
                    middle_frg = fragment.position() > self.board_ni_text_cursor.selectionStart() and fragment.position() + fragment.length() <= self.board_ni_text_cursor.selectionEnd()

                    if start_frg or end_frg or middle_frg:
                        if start_frg:
                            fragPos = self.board_ni_text_cursor.selectionStart() - block.position()
                        if end_frg:
                            fragEnd = self.board_ni_text_cursor.selectionEnd() - block.position()

                        while True:
                            line = blockLayout.lineForTextPosition(fragPos)
                            if line.isValid():
                                x, _ = line.cursorToX(fragPos)
                                right, lineEnd = line.cursorToX(fragEnd)
                                rect = QRectF(blockX + x, blockY + line.y(), right - x, line.height())
                                self.board_ni_selection_rects.append(rect)
                                if lineEnd != fragEnd:
                                    fragPos = lineEnd
                                else:
                                    break
                            else:
                                break
                    it += 1
                block = block.next()

    def board_TextElementDrawSelectionRects(self, painter):
        l = len(self.board_ni_selection_rects)
        for n, r in enumerate(self.board_ni_selection_rects):
            alpha = max(35, int(255*n/l))
            painter.fillRect(r, QColor(200, 50, 50, alpha))

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
            painter.save()
            painter.setPen(Qt.NoPen)
            content_rect = QRect(QPoint(), s)

            path = QPainterPath()
            path.addRoundedRect(QRectF(content_rect), element.margin_value,
                element.margin_value)
            painter.fillPath(path, QBrush(element.backplate_color))
            painter.restore()

            # рисуем текст
            if self.Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS:
                if element.proxy_pixmap is None:
                    self.board_TextElementUpdateProxyPixmap(element)
                painter.drawPixmap(QPoint(0, 0), element.proxy_pixmap)
            else:
                self.board_TextElementDraw(painter, element)

            # рисуем прямоугольники выделения
            if element.editing:
                self.board_TextElementDrawSelectionRects(painter)

            # рисуем курсор
            if element.editing and not self.blinkingCursorHidden:
                doc_layout = text_doc.documentLayout()
                if self.board_ni_ts_dragNdrop_ongoing:
                    cursor_pos = self.board_ni_temp_cursor_pos
                else:
                    cursor_pos = self.board_ni_text_cursor.position()
                block = text_doc.begin()
                end = text_doc.end()
                while block != end:
                    # block_rect = doc_layout.blockBoundingRect(block)
                    # painter.drawRect(block_rect)
                    if self.active_element is element and not final:
                        if block.contains(cursor_pos):
                            local_cursor_pos = cursor_pos - block.position()
                            block.layout().drawCursor(painter, QPointF(0,0), local_cursor_pos, 6)
                    block = block.next()

        painter.restore()
        painter.resetTransform()


        if self.board_TextElementIsActiveElement() and element.editing:
            painter.save()
            element_bound_rect = element.get_selection_area(board=self).boundingRect()
            tl = element_bound_rect.topLeft() + QPointF(-10, 0)

            RECT_SIZE = 25
            button_rect = QRectF(0, 0, RECT_SIZE, RECT_SIZE)
            text_color_rect = QRectF(button_rect)
            backplate_color_rect = QRectF(button_rect)
            text_color_rect.moveTopRight(tl)
            tl += QPoint(0, RECT_SIZE + 5)
            backplate_color_rect.moveTopRight(tl)

            self.board_ni_colors_buttons = (text_color_rect, backplate_color_rect)
            for n, rect in enumerate(self.board_ni_colors_buttons):
                painter.setPen(QPen(self.selection_color, 1))
                if n == 0:
                    painter.setBrush(Qt.NoBrush)
                else:
                    backplate_color = QColor(element.backplate_color)
                    backplate_color.setAlpha(255)
                    painter.setBrush(QBrush(backplate_color))
                painter.drawRect(rect)

                font_color = element.font_color
                font_color.setAlpha(255)
                painter.setPen(QPen(font_color, 3))
                a1 = rect.topLeft() + QPoint(6, 6)
                a2 = rect.topRight() + QPoint(-6, 6)
                b1 = rect.center() + QPoint(0, -6)
                b2 = rect.center() + QPoint(0, 7)
                painter.drawLine(a1, a2)
                painter.drawLine(b1, b2)
            painter.restore()

    def board_TextElementCheckColorButtons(self, event):
        if self.board_ni_colors_buttons is not None:
            text_color_rect = self.board_ni_colors_buttons[0]
            backplate_color_rect = self.board_ni_colors_buttons[1]
            if text_color_rect.contains(event.pos()):
                return 0
            elif backplate_color_rect.contains(event.pos()):
                return 1
        return -1

    def board_TextElementColorButtonsHandlers(self, check_code):
        if check_code != -1:
            if check_code == 0:
                def callback(color_value):
                    self.active_element.font_color = color_value
                    self.board_TextElementUpdateProxyPixmap(self.active_element)
                    self.update()
                self.active_element.font_color = ColorPicker().getColor(QColor(self.active_element.font_color), callback=callback)
            elif check_code == 1:
                def callback(color_value):
                    self.active_element.backplate_color = color_value
                    self.board_TextElementUpdateProxyPixmap(self.active_element)
                    self.update()
                self.active_element.backplate_color = ColorPicker().getColor(QColor(self.active_element.backplate_color), callback=callback)
            self.board_TextElementUpdateProxyPixmap(self.active_element)
            self.update()

# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
