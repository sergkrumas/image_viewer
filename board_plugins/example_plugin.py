






import sys
import math
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def get_pixels_in_radius_unit(self):
    CONST = 20
    return CONST*max(self.board_scale_x, self.board_scale_y)
    # return CONST

def build_rect_from_point(self, point, r=1.0):
    offset = QPointF(get_pixels_in_radius_unit(self)*r, get_pixels_in_radius_unit(self)*r)
    return QRectF(point-offset, point+offset)

def paintEvent(self, painter, event):
    painter.setBrush(self.checkerboard_br)
    painter.drawRect(self.rect())
    painter.setBrush(Qt.NoBrush)

    pen = QPen(QColor(255, 0, 0), 10)
    pen.setCapStyle(Qt.RoundCap)

    pen2 = QPen(QColor(220, 50, 50), 1)
    pen3 = QPen(QColor(220, 220, 220), 1)

    pen4 = QPen(QColor(220, 220, 220, 150), 1, Qt.DashLine)
    pen5 = QPen(QColor(50, 220, 50, 50), 1, Qt.DashLine)

    # окно может обновлятся в нижней части из-за обновления панели задач, которая там находится,
    # и нам нужно отслеживать этот момент и рисовать только при полном обновлении окна
    if self.rect() == event.rect():
        for key in list(self.bckg_rects.keys()):
            if self.bckg_rects[key] > 1:
                self.bckg_rects[key] -= 4
            else:
                self.bckg_rects.pop(key)
        cursor_pos = self.mapFromGlobal(QCursor().pos())
        SIZE = 125
        x = (cursor_pos.x() // SIZE) * SIZE
        y = (cursor_pos.y() // SIZE) * SIZE
        self.bckg_rects[(x,y)] = 255
        base = QColor(self.selection_color).darker(200)
        for key, alpha in self.bckg_rects.items():
            _x, _y = key
            bckg_rect = QRect(_x, _y, SIZE, SIZE)
            base.setAlpha(max(0, alpha))
            painter.fillRect(bckg_rect, base)



    tangent_pairs = self.tangent_pairs[:]
    if bool(QApplication.queryKeyboardModifiers() & Qt.ControlModifier) and self.tempPair is not None:
        ghost_circle = True
    else:
        ghost_circle = False

    if ghost_circle:
        tangent_pairs.extend((self.tempPair,))

    for c1, c2 in tangent_pairs:

        radius_max = max(c1.radius, c2.radius)
        radius_min = min(c1.radius, c2.radius)
        radius_diff = get_pixels_in_radius_unit(self)*(radius_max - radius_min)

        p1 = self.board_map_to_viewport(c1.position)
        p2 = self.board_map_to_viewport(c2.position)
        distance = math.hypot(p1.x()-p2.x(), p1.y() - p2.y())
        # distance = math.sqrt(math.pow(p1.x()-p2.x(), 2) + math.pow(p1.y() - p2.y(), 2))
        try:
            sinus_alpha = radius_diff/abs(distance)
        except ZeroDivisionError:
            continue


        painter.setPen(pen5)
        painter.drawLine(p1, p2)


        position_angle = math.atan2(p1.x()-p2.x(), p1.y() - p2.y())

        if c1.radius > c2.radius:
            factor = 1.0
        else:
            factor = -1.0

        def draw_tangent_points_and_lines(radians_angle):
            points_on_circles = []
            for n, c in enumerate((c1, c2)):

                center_pos = self.board_map_to_viewport(c.position)
                radius = c.radius

                radius_length = get_pixels_in_radius_unit(self)*radius
                x = math.cos(radians_angle)*radius_length
                y = math.sin(radians_angle)*radius_length
                radius_vector = QPointF(x, y)
                point_on_circle = center_pos + radius_vector
                points_on_circles.append(point_on_circle)

                # точки
                painter.setPen(pen)
                painter.drawPoint(point_on_circle)
                # линия от точки касания к радиусу
                painter.setPen(pen4)
                painter.drawLine(point_on_circle, center_pos)

            painter.setPen(pen2)
            # непосредственно сама касательная линия
            painter.drawLine(QLineF(*points_on_circles))

            return points_on_circles

        try:
            radians_angle = math.asin(sinus_alpha)
        except:
            radians_angle = 0
        radians_angle += - position_angle - math.pi/2 - math.pi/2*factor
        draw_tangent_points_and_lines(radians_angle)

        try:
            # !!! отличается знаком минус
            radians_angle = - math.asin(sinus_alpha)
        except:
            radians_angle = 0
            # !!! отличается знаком плюс
        radians_angle += - position_angle + math.pi/2 - math.pi/2*factor
        draw_tangent_points_and_lines(radians_angle)




    circles = self.circles[:]

    if ghost_circle:
        circles.append(self.tempCircle)

    self.center_under_cursor = None
    for c in circles:
        center_point = self.board_map_to_viewport(c.position)
        radius = c.radius
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPoint(center_point)
        painter.setPen(pen3)
        rect = build_rect_from_point(self, center_point)
        painter.drawEllipse(build_rect_from_point(self, center_point, radius))
        painter.drawEllipse(rect)
        hover = rect.contains(self.mapFromGlobal(QCursor().pos()))
        if hover or self.drag_point != -1 and self.circles.index(c) == self.drag_point:
            brush = QBrush(QColor(220, 50, 50))
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawEllipse(rect)
            self.center_under_cursor = center_point
        r_text = radius*get_pixels_in_radius_unit(self)
        painter.setPen(QPen(Qt.green))
        painter.drawText(center_point, f'{r_text:.01f}')



    font = painter.font()
    font.setPixelSize(20)
    painter.setFont(font)
    painter.setPen(QPen(Qt.white))
    rect = QRect(0, 0, self.width(), 150)
    text = (
        "Наведя курсор мыши на меньшие круги колесом мыши можно регулировать радиус и перетаскивать с места на место;\n"
        "Поддерживаются отрицательные радиусы;\n"
        "Ctrl + ЛКМ позволяет добавить новую окружность и соединяет её с ближайшей окружностью"
    )
    painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter | Qt.TextWordWrap, text)

def mousePressEvent(self, event):
    cursor_pos = event.pos()
    breaked = False
    for index, c in enumerate(self.circles):
        point = self.board_map_to_viewport(c.position)
        rect = build_rect_from_point(self, point)
        if rect.contains(cursor_pos):
            self.drag_point = index
            self.start_pos = event.pos()
            self.oldpos = QPointF(c.position)
            breaked = True
            break
        else:
            self.drag_point = -1
    if not breaked:
        self.board_mousePressEventDefault(event)
    self.update()

def mouseMoveEvent(self, event):

    if self.drag_point != -1:
        if bool(event.modifiers() & Qt.ControlModifier):
            if self.circles:
                nearest_circle = None
                for c in self.circles:
                    l = self.board_map_to_viewport(c.position) - event.pos()
                    c._l = QVector2D(l).length()

                nearest_circle = list(sorted(self.circles, key=lambda x: x._l))[0]

                self.tempCircle.position = self.board_map_to_board(QPointF(event.pos()))
                self.tempPair = (self.tempCircle, nearest_circle)
            else:
                self.tempPair = None
        else:
            self.tempPair = None
            if self.drag_point != -1:
                delta = QPointF(self.start_pos - event.pos())
                delta.setX(delta.x()/self.board_scale_x)
                delta.setY(delta.y()/self.board_scale_y)
                self.circles[self.drag_point].position = self.oldpos - delta

        if not self.corner_buttons_cursor_glitch_fixer():
            if self.center_under_cursor is not None:
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    else:
        self.board_mouseMoveEventDefault(event)
    self.update()

def mouseReleaseEvent(self, event):

    if self.drag_point != -1:
        if bool(event.modifiers() & Qt.ControlModifier) and event.button() == Qt.LeftButton:
            if self.tempPair:
                newCircle = Circle(self.tempCircle.position, self.tempCircle.radius)
                self.circles.append(newCircle)
                self.tangent_pairs.append((newCircle, self.tempPair[1]))
                self.tempPair = None
    else:
        self.board_mouseReleaseEventDefault(event)
    self.drag_point = -1
    self.update()

def wheelEvent(self, event):
    cursor_pos = event.pos()
    value = event.angleDelta().y()/100/1.2

    breaked = False
    for index, c in enumerate(self.circles):
        point = self.board_map_to_viewport(c.position)
        rect = build_rect_from_point(self, point)
        if rect.contains(cursor_pos):
            self.circles[index].radius += value
            breaked = True
            break
    if not breaked:
        self.board_wheelEventDefault(event)
    self.update()

class Circle():
    def __init__(self, position, radius):
        self.position = position
        self.radius = radius

def pluginBoardInit(self, plugin_info):

    self.drag_point = -1
    self.oldpos = QPoint(0, 0)

    fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
    self.board_make_board_current(fd)

    W = self.rect().width()/30
    H = self.rect().height()/20

    P1 = QPointF(W*10, H*10)
    P2 = QPointF(W*20, H*10)

    P3 = QPointF(W*5, H*18)
    P4 = QPointF(W*7, H*4)

    self.tempPair = None
    self.tempCircle = Circle(QPointF(self.rect().center()), 5.0)

    self.circles = [
        Circle(P1, 8.0),
        Circle(P2, 5.0),
        Circle(P3, 10.0),
        Circle(P4, 9.0),
    ]
    self.tangent_pairs = [
        (self.circles[0], self.circles[1]),
        (self.circles[0], self.circles[2]),
        (self.circles[0], self.circles[3]),
    ]


    self.bckg_rects = dict()

    self.checkerboard_br = checkerboard_br = QBrush()
    pixmap = QPixmap(100, 100)
    pixmap.fill(Qt.transparent)
    painter_ = QPainter()
    painter_.begin(pixmap)
    painter_.setOpacity(0.05)
    painter_.fillRect(pixmap.rect(), Qt.gray)
    painter_.setBrush(QBrush(QColor(200, 200, 200)))
    painter_.setPen(Qt.NoPen)
    w = pixmap.width()
    path = QPainterPath()
    path.moveTo(w*0.0, w*0.0)
    path.lineTo(w*0.25, w*0.0)
    path.lineTo(w*1.0, w*0.75)
    path.lineTo(w*1.0, w*1.0)
    path.lineTo(w*0.75, w*1.0)
    path.lineTo(w*0.0, w*0.25)
    painter_.drawPath(path)
    path = QPainterPath()
    path.moveTo(w*0.0, w*0.75)
    path.lineTo(w*0.0, w*1.0)
    path.lineTo(w*0.25, w*1.0)
    painter_.drawPath(path)
    path = QPainterPath()
    path.moveTo(w*0.75, w*0.0)
    path.lineTo(w*1.0, w*0.0)
    path.lineTo(w*1.0, w*0.25)
    painter_.drawPath(path)
    painter_.end()
    checkerboard_br.setTexture(pixmap)





def register(board_obj, plugin_info):
    plugin_info.name = 'Example Plugin'

    plugin_info.pluginBoardInit = pluginBoardInit
    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

    plugin_info.wheelEvent = wheelEvent

    print(f'\tplugin {plugin_info.name} registred!')



if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw"])
    sys.exit()
