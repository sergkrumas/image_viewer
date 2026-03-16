

from _utils import *

from functools import lru_cache

class TOOLWINDOW_BUTTONSIDS():
    ALIGN_LEFT_EDGE = 0
    ALIGN_TOP_EDGE = 1
    ALIGN_RIGHT_EDGE = 2
    ALIGN_BOTTOM_EDGE = 3
    ALIGN_CENTER = 4
    ALIGN_MIDDLE = 5
    DISTRIBUTE_H = 6
    DISTRIBUTE_V = 7

    @classmethod
    def all(cls):
        if not hasattr(cls, 'all_list'):
            cls.all_list = []
            for attr_name in cls.__dict__:
                if not attr_name.startswith("__"):
                    attr_value = getattr(TOOLWINDOW_BUTTONSIDS, attr_name)
                    if isinstance(attr_value, int):
                        cls.all_list.append(attr_value)
            cls.all_list = tuple(sorted(cls.all_list))
        return cls.all_list

    @classmethod
    def names(cls):
        if not hasattr(cls, 'all_names'):
            cls.all_names = dict()
            for attr_name in cls.__dict__:
                if not attr_name.startswith("__") and attr_name.upper() == attr_name:
                    attr_value = getattr(TOOLWINDOW_BUTTONSIDS, attr_name)
                    if isinstance(attr_value, int):
                        cls.all_names[attr_value] = attr_name
        return cls.all_names

class ToolActions():
    ALIGN = 0
    DISTRIBUTE = 1

class ROW():

    def __init__(self, padding=10):
        self.elements = []
        self.padding = padding

class LBL():

    def __init__(self, text, painter):
        self.text = text
        self.alignment = Qt.AlignLeft
        self.content_rect = painter.boundingRect(QRect(), self.alignment, self.text)
        self.layout_rect = None

    def draw(self, painter):
        painter.drawText(self.layout_rect, self.alignment, self.text)

class SPACE():

    def __init__(self, width):
        self.content_rect = QRect(0, 0, width, 0)
        self.layout_rect = None

    def draw(self, painter):
        pass

class BTN():

    def __init__(self, btn_id, **kwargs):
        self.btn_id = btn_id
        self.content_rect = QRect(0, 0, 40, 40)
        self.layout_rect = None
        self.kwargs = kwargs

    def draw(self, painter):
        if self.btn_id is not None:
            painter.drawPixmap(self.layout_rect, ToolWindow.get_btn_pixmap(self.btn_id))

class RADIO_BTN():

    def __init__(self, btns, painter):
        self.alignment = Qt.AlignVCenter | Qt.AlignHCenter
        spacing_offset = QPoint(5, 0)
        _offset = QPoint(spacing_offset)
        self.index = 0
        self.radio_btns = []
        for radio_id, radio_name in btns.items():
            r = painter.boundingRect(QRect(), Qt.AlignLeft, radio_name)
            r.adjust(0, 0, 5, 5)
            r.moveTopLeft(r.topLeft() + _offset)
            self.radio_btns.append((radio_id, QRect(r), radio_name))
            _offset = r.bottomLeft()
        self.content_rect = QRect(QPoint(0, 0), r.bottomRight() + spacing_offset)
        self.layout_rect = None

    def click(self, pos):
        if self.layout_rect is None:
            return False
        for n, (radio_id, radio_rect, radio_name) in enumerate(self.radio_btns):
            radio_rect = QRect(radio_rect)
            radio_rect.moveTopLeft(radio_rect.topLeft() + self.layout_rect.topLeft())
            if radio_rect.contains(pos):
                self.index = n
                return True
        return False

    def get_active_radiobtn(self):
        return self.radio_btns[self.index]

    def get_active_id(self):
        return self.get_active_radiobtn()[0]

    def get_active_name(self):
        return self.get_active_radiobtn()[-1]

    def draw(self, painter):
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.layout_rect), 3, 3)
        painter.drawPath(path)
        offset = QPoint(5, 5)
        painter.setClipPath(path)
        painter.setClipping(True)
        for n, (radio_id, radio_rect, radio_name) in enumerate(self.radio_btns):
            radio_rect = QRect(radio_rect)
            radio_rect.moveTopLeft(radio_rect.topLeft() + self.layout_rect.topLeft())
            if n == self.index:
                painter.setPen(QPen(Qt.white, 1))
                backplate_rect = QRect(radio_rect)
                backplate_rect.setLeft(self.layout_rect.left())
                backplate_rect.setWidth(self.layout_rect.width())
                painter.fillRect(backplate_rect, QBrush(ToolWindow.BCKG))
            else:
                painter.setPen(QPen(Qt.black, 1))
            painter.drawText(radio_rect, self.alignment, radio_name)
        painter.setClipping(False)
        painter.restore()

class FIX():
    def __init__(self, height):
        self.height = height
        self.content_rect = QRect()
        self.layout_rect = None

    def draw(self, painter):
        pass

class AlignType():
    ALIGN_TO_VIEWPORT = 0
    ALIGN_TO_SELECTION = 1
    ALIGN_TO_WHOLE_BOARD = 2

    @classmethod
    def get_consts_and_their_names(cls):
        return {
            cls.ALIGN_TO_VIEWPORT: "Viewport",
            cls.ALIGN_TO_SELECTION: "Selection",
            cls.ALIGN_TO_WHOLE_BOARD: "Whole board",
        }

    @classmethod
    def all(cls):
        if not hasattr(cls, 'all_list'):
            cls.all_list = []
            for attr_name in dir(TOOLWINDOW_BUTTONSIDS):
                if attr_name.startswith("ALIGN_TO_"):
                    attr_value = getattr(TOOLWINDOW_BUTTONSIDS, attr_name)
                    if isinstance(attr_value, int):
                        cls.all_list.append(attr_value)
            cls.all_list = tuple(sorted(cls.all_list))
        return cls.all_list

class ToolWindow(QWidget):

    BORDER = QColor(31, 31, 31)
    BCKG = QColor(48, 48, 48)
    CONTENT = QColor(190, 190, 190)

    @classmethod
    @lru_cache(maxsize=9)
    def get_btn_pixmap(cls, btn_id):

        border = ToolWindow.BORDER
        bckg = ToolWindow.BCKG
        content = ToolWindow.CONTENT

        SIZE = 50
        BTN_RECT = QRectF(0, 0, SIZE, SIZE)

        pixmap = QPixmap(BTN_RECT.size().toSize())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        bckg_path = QPainterPath()
        bckg_path.addRoundedRect(BTN_RECT.adjusted(2, 2, -2, -2), 6, 6)
        painter.setPen(QPen(border, 2))
        painter.setBrush(QBrush(bckg))
        painter.drawPath(bckg_path)

        def draw_arrow(tip, start):
            content_color = content.lighter(200)
            diff = tip - start
            vert = False
            hor = False
            factor = 0
            if diff.x() == 0.0:
                vert = True
                if diff.y() > 0:
                    factor = -1
                else:
                    factor = 1
            elif diff.y() == 0.0:
                hor = True
                if diff.x() > 0:
                    factor = -1
                else:
                    factor = 1

            if vert:
                tip += QPointF(0, factor*6)
            elif hor:
                tip += QPointF(factor*6, 0)

            diff = QVector2D(diff).normalized().toPointF() * 4.0
            s1 = tip + QPointF(diff.y(), -diff.x()) - diff*1.1
            s2 = tip + QPointF(-diff.y(), diff.x()) - diff*1.1
            # line
            painter.setPen(QPen(content_color, 4))
            if vert:
                tip_m = tip - diff*.3
            elif hor:
                tip_m = tip - diff*.3
            painter.drawLine(tip_m, start)
            # tip
            pen = QPen(content_color, 3)
            pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(QBrush(content_color))
            arrow_tip_path = QPainterPath()
            arrow_tip_path.moveTo(tip)
            arrow_tip_path.lineTo(s1)
            arrow_tip_path.lineTo(s2)
            arrow_tip_path.lineTo(tip)
            painter.drawPath(arrow_tip_path)

        CR = BTN_RECT.adjusted(8, 8, -8, -8)
        painter.setPen(QPen(content, 4))
        if btn_id is None:
            pass

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_LEFT_EDGE:
            painter.drawLine(CR.topLeft(), CR.bottomLeft())
            draw_arrow(CR.topLeft()/2.0 + CR.bottomLeft()/2.0, CR.topRight()/2.0 + CR.bottomRight()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_TOP_EDGE:
            painter.drawLine(CR.topLeft(), CR.topRight())
            draw_arrow(CR.topLeft()/2.0 + CR.topRight()/2.0, CR.bottomLeft()/2.0 + CR.bottomRight()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_RIGHT_EDGE:
            painter.drawLine(CR.topRight(), CR.bottomRight())
            draw_arrow(CR.topRight()/2.0 + CR.bottomRight()/2.0, CR.topLeft()/2.0 + CR.bottomLeft()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_BOTTOM_EDGE:
            painter.drawLine(CR.bottomLeft(), CR.bottomRight())
            draw_arrow(CR.bottomLeft()/2.0 + CR.bottomRight()/2.0, CR.topLeft()/2.0 + CR.topRight()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_CENTER:
            painter.drawLine(CR.topLeft()/2.0 + CR.topRight()/2.0, CR.bottomLeft()/2.0 + CR.bottomRight()/2.0)
            draw_arrow(CR.center(), CR.topRight()/2.0 + CR.bottomRight()/2.0)
            draw_arrow(CR.center(), CR.topLeft()/2.0 + CR.bottomLeft()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.ALIGN_MIDDLE:
            painter.drawLine(CR.topLeft()/2.0 + CR.bottomLeft()/2.0, CR.topRight()/2.0 + CR.bottomRight()/2.0)
            draw_arrow(CR.center(), CR.topRight()/2.0 + CR.topLeft()/2.0)
            draw_arrow(CR.center(), CR.bottomRight()/2.0 + CR.bottomLeft()/2.0)

        elif btn_id == TOOLWINDOW_BUTTONSIDS.DISTRIBUTE_H:
            painter.drawLine(CR.topLeft(), CR.bottomLeft())
            painter.drawLine(CR.topRight(), CR.bottomRight())
            draw_arrow(CR.topRight()/2.0 + CR.bottomRight()/2.0, CR.center())
            draw_arrow(CR.topLeft()/2.0 + CR.bottomLeft()/2.0, CR.center())

        elif btn_id == TOOLWINDOW_BUTTONSIDS.DISTRIBUTE_V:
            painter.drawLine(CR.topLeft(), CR.topRight())
            painter.drawLine(CR.bottomLeft(), CR.bottomRight())
            draw_arrow(CR.topRight()/2.0 + CR.topLeft()/2.0, CR.center())
            draw_arrow(CR.bottomRight()/2.0 + CR.bottomLeft()/2.0, CR.center())

        painter.end()
        return pixmap

    def __init__(self):
        super().__init__()

        self.init_AD_toolbox_attrs()

        self.setMouseTracking(True)

    def init_AD_toolbox_attrs(self):
        self.AD_TOOLBOX = AD_TOOLBOX = type('AD_TOOLBOX', (), {})()
        AD_TOOLBOX.rows = []
        AD_TOOLBOX.current_row = None
        AD_TOOLBOX.layout_ready = False
        AD_TOOLBOX.visible = False
        AD_TOOLBOX.pos = QPoint(0, 0)
        AD_TOOLBOX.drag = False

    def layout(self, painter, spacing=20):

        def label(text):
            lbl = LBL(text, painter)
            self.AD_TOOLBOX.current_row.elements.append(lbl)
            return lbl

        def button(btn_id, **kwargs):
            btn = BTN(btn_id, **kwargs)
            self.AD_TOOLBOX.current_row.elements.append(btn)
            return btn

        def space(width=40):
            space = SPACE(width)
            self.AD_TOOLBOX.current_row.elements.append(space)
            return None

        def row():
            self.AD_TOOLBOX.current_row = ROW()
            self.AD_TOOLBOX.rows.append(self.AD_TOOLBOX.current_row)
            return self.AD_TOOLBOX.current_row

        def radioButton(btns):
            radio_btn = RADIO_BTN(btns, painter)
            self.AD_TOOLBOX.current_row.elements.append(radio_btn)
            return radio_btn

        def fix_top_by_label_height(height):
            fix = FIX(height)
            self.AD_TOOLBOX.current_row.elements.append(fix)
            return fix

        def update_bounding_layout_rect(blr, _b):
            self.blr.setTop(min(r.top() for r in _b))
            self.blr.setLeft(min(r.left() for r in _b))
            self.blr.setRight(max(r.right() for r in _b))
            self.blr.setBottom(max(r.bottom() for r in _b))

        def calc_layout():
            layout_spacing_offset = QPoint(spacing, spacing)
            offset = QPoint(0, 0)
            _b = []
            self.blr = QRect()
            for row in self.AD_TOOLBOX.rows:
                max_height = 0
                for el in row.elements:
                    max_height = max(max_height, el.content_rect.height())
                for el in row.elements:
                    if isinstance(el, FIX):
                        offset -= QPoint(row.padding, el.height + row.padding)
                    else:
                        el.layout_rect = QRect(el.content_rect)
                        el.layout_rect.moveTopLeft(QPoint(offset.x() + row.padding, offset.y() + row.padding))
                        offset.setX(el.layout_rect.right())
                        el.layout_rect.moveCenter(el.layout_rect.center() + layout_spacing_offset + self.AD_TOOLBOX.pos)
                        _b.append(QRect(el.layout_rect))
                offset += QPoint(0, max_height+10)
                update_bounding_layout_rect(self.blr, _b)
                offset.setX(0)

        def draw_layout():
            path = QPainterPath()
            blr = self.blr.adjusted(-5, -5, 5, 5)
            path.addRoundedRect(QRectF(blr), 10, 10)
            painter.drawPath(path)

            for row in self.AD_TOOLBOX.rows:
                for el in row.elements:
                    el.draw(painter)

        if not self.AD_TOOLBOX.layout_ready:
            row()
            label('Align:')
            row()
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_LEFT_EDGE, action=ToolActions.ALIGN)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_CENTER, action=ToolActions.ALIGN)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_RIGHT_EDGE, action=ToolActions.ALIGN)
            space()
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_TOP_EDGE, action=ToolActions.ALIGN)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_MIDDLE, action=ToolActions.ALIGN)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_BOTTOM_EDGE, action=ToolActions.ALIGN)

            row()
            label('Distribute:')
            row()
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_LEFT_EDGE, action=ToolActions.DISTRIBUTE)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_CENTER, action=ToolActions.DISTRIBUTE)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_RIGHT_EDGE, action=ToolActions.DISTRIBUTE)
            space()
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_TOP_EDGE, action=ToolActions.DISTRIBUTE)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_MIDDLE, action=ToolActions.DISTRIBUTE)
            button(TOOLWINDOW_BUTTONSIDS.ALIGN_BOTTOM_EDGE, action=ToolActions.DISTRIBUTE)

            row()
            lbl = label('Distribute spacing:')
            row()
            button(TOOLWINDOW_BUTTONSIDS.DISTRIBUTE_H, action=ToolActions.DISTRIBUTE)
            button(TOOLWINDOW_BUTTONSIDS.DISTRIBUTE_V, action=ToolActions.DISTRIBUTE)

            space(80)
            # это конечно костыль, но зато можно не переписывать огромную часть кода
            fix_top_by_label_height(lbl.content_rect.height())
            label('Align To:')
            radioButton(AlignType.get_consts_and_their_names())

            calc_layout()
            self.AD_TOOLBOX.layout_ready = True

        draw_layout()

    def is_toolbox_click(self, event):
        return self.AD_TOOLBOX.layout_ready and self.blr.contains(event.pos()) and not ToolWindow.layout_mouse(self, event)

    def layout_mouse(self, event):
        pos = event.pos()
        debug = isinstance(self, ToolWindow)
        if self.AD_TOOLBOX.layout_ready:
            for row in self.AD_TOOLBOX.rows:
                for el in row.elements:
                    if el.layout_rect:
                        lr = QRect(el.layout_rect)
                        if lr.contains(pos):
                            if isinstance(el, RADIO_BTN):
                                el.click(pos)
                                if debug:
                                    print(el.get_active_name())
                                return True
                            elif isinstance(el, BTN):
                                if debug:
                                    print(TOOLWINDOW_BUTTONSIDS.names()[el.btn_id], el.kwargs)
                                return True
        return False

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.fillRect(self.rect(), Qt.gray)
        self.layout(painter)
        painter.end()

        # self.debugPaintEvent(event)

    def debugPaintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), Qt.gray)
        BTN_WIDTH = 50
        x = 10
        y = 10
        for btn in TOOLWINDOW_BUTTONSIDS.all():
            r = QRect(x, y, BTN_WIDTH, BTN_WIDTH)
            y += BTN_WIDTH
            painter.drawPixmap(r.topLeft(), get_btn_pixmap(btn))
            painter.drawText(r.bottomRight() + QPoint(10, -10), str(btn))
        painter.end()

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        self.update()

    def mouseReleaseEvent(self, event):
        self.layout_mouse(event)


def main():
    app = QApplication([])

    window = ToolWindow()
    window.show()
    window.resize(1000, 800)

    app.exec()


if __name__ == '__main__':
    main()
