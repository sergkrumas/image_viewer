






import sys
import math
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

def build_rect_from_point(self, point, r=1.0):
    offset = QPointF(self.pixels_in_radius_unit*r, self.pixels_in_radius_unit*r).toPoint()
    return QRect(QPoint(point.toPoint()-offset), QPoint(point.toPoint()+offset))




def paintEvent(self, painter, event):


    painter.setBrush(self.checkerboard_br)
    painter.drawRect(self.rect())
    painter.setBrush(Qt.NoBrush)


    pen = QPen(QColor(255, 0, 0), 10)
    pen0 = QPen(QColor(0, 255, 255), 10)
    pen.setCapStyle(Qt.RoundCap)

    pen2 = QPen(QColor(255, 0, 0), 1)
    pen3 = QPen(QColor(0, 0, 0), 4)


    radius_max = max(self.radius_values)
    radius_min = min(self.radius_values)
    radius_diff = self.pixels_in_radius_unit*radius_max - self.pixels_in_radius_unit*radius_min

    p1 = self.center_position_values[0]
    p2 = self.center_position_values[1]
    distance = math.hypot(p1.x()-p2.x(), p1.y() - p2.y())
    # distance = math.sqrt(math.pow(p1.x()-p2.x(), 2) + math.pow(p1.y() - p2.y(), 2))
    sinus_alpha = radius_diff/abs(distance)

    point_under_cursor = None
    for point, r in zip(self.center_position_values, self.radius_values):
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPoint(point)
        painter.setPen(pen2)
        rect = build_rect_from_point(self, point)
        painter.drawEllipse(build_rect_from_point(self, point, r))
        painter.drawEllipse(rect)
        if rect.contains(self.mapFromGlobal(QCursor().pos())):
            brush = QBrush(QColor(255, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(brush)
            painter.drawEllipse(rect)
            point_under_cursor = point
        r_text = r*self.pixels_in_radius_unit
        painter.setPen(QPen(Qt.green))
        painter.drawText(point, f'{r_text}')


    if point_under_cursor is not None:
        self.setCursor(Qt.PointingHandCursor)
    else:
        self.setCursor(Qt.ArrowCursor)

    painter.setPen(pen2)
    painter.drawLine(self.center_position_values[0], self.center_position_values[1])


    position_angle = math.atan2(p1.x()-p2.x(), p1.y() - p2.y())

    if self.radius_values[0] > self.radius_values[1]:
        factor = 1.0
    else:
        factor = -1.0

    def draw_tangent_points(radians_angle):
        points_on_circles = []
        for n, (center_pos, radius) in enumerate(zip(self.center_position_values, self.radius_values)):

            radius_length = self.pixels_in_radius_unit*radius
            x = math.cos(radians_angle)*radius_length
            y = math.sin(radians_angle)*radius_length
            radius_vector = QPointF(x, y)
            point_on_circle = center_pos + radius_vector
            points_on_circles.append(point_on_circle)

            # точки
            painter.setPen(pen)
            painter.drawPoint(point_on_circle)
            painter.setPen(pen3)
            # линия от точки касания к радиусу
            painter.drawLine(point_on_circle, center_pos)

        # непосредственно сама касательная линия
        painter.drawLine(points_on_circles[0], points_on_circles[1])

        return points_on_circles

    try:
        radians_angle = math.asin(sinus_alpha)
    except:
        radians_angle = 0
    radians_angle += - position_angle - math.pi/2 - math.pi/2*factor
    draw_tangent_points(radians_angle)

    try:
        # !!! отличается знаком минус
        radians_angle = - math.asin(sinus_alpha)
    except:
        radians_angle = 0
        # !!! отличается знаком плюс
    radians_angle += - position_angle + math.pi/2 - math.pi/2*factor
    draw_tangent_points(radians_angle)



    font = painter.font()
    font.setPixelSize(20)
    painter.setFont(font)
    painter.setPen(QPen(Qt.white))
    rect = QRect(0, 0, self.width(), 150)
    text = ("Наведя курсор мыши на меньшие круги колесом мыши можно регулировать размер и перетаскивать с места на место;\n"
    "Поддерживаются отрицательные радиусы")
    painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter | Qt.TextWordWrap, text)


def mousePressEvent(self, event):
    cursor_pos = event.pos()
    for index, point in enumerate(self.center_position_values):
        rect = build_rect_from_point(self, point)
        if rect.contains(cursor_pos):
            self.drag_point = index
            self.start_pos = event.pos()
            self.oldpos = QPointF(point)
            break
        else:
            self.drag_point = -1
    self.update()

def mouseMoveEvent(self, event):
    if self.drag_point != -1:
        p = self.oldpos + (event.pos() - self.start_pos)
        self.center_position_values[self.drag_point] = p

    self.update()

def mouseReleaseEvent(self, event):
    self.drag_point = -1
    self.update()


def wheelEvent(self, event):
    cursor_pos = event.pos()
    value = event.angleDelta().y()/100/1.2
    # print(value)
    for index, point in enumerate(self.center_position_values):
        rect = build_rect_from_point(self, point)
        if rect.contains(cursor_pos):
            self.radius_values[index] += value
            self.update()
            break

    self.update()



def pluginBoardInit(self, plugin_info):

    self.drag_point = -1
    self.oldpos = QPoint(0, 0)

    fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
    self.board_make_board_current(fd)

    H2 = self.rect().height()/2
    W3 = self.rect().width()/3

    P1 = QPointF(W3, H2)
    P2 = QPointF(W3*2, H2)

    self.center_position_values = [P1, P2]
    self.radius_values = [8.0, 5.0]

    self.pixels_in_radius_unit = 20


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
    plugin_info.board = board_obj

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
