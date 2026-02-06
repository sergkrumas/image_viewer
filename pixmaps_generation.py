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

from _utils import *

def generate_pixmaps(Globals, SettingsWindow):
    print('start generating pixmaps')
    THUMBNAIL_WIDTH = Globals.THUMBNAIL_WIDTH

    Globals.NULL_PIXMAP = QPixmap()

    DEFAULT_THUMBNAIL = QPixmap(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
    DEFAULT_THUMBNAIL.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(DEFAULT_THUMBNAIL)
    painter.setPen(Qt.gray)
    font = painter.font()
    font.setPixelSize(THUMBNAIL_WIDTH)
    painter.setFont(font)
    painter.setBrush(Qt.NoBrush)
    painter.drawText(QRect(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH), Qt.AlignCenter, "⧖")
    painter.end()

    if SettingsWindow.get_setting_value('draw_default_thumbnail'):
        Globals.DEFAULT_THUMBNAIL = DEFAULT_THUMBNAIL

    ERROR_PREVIEW_PIXMAP = QPixmap(200, 200)
    ERROR_PREVIEW_PIXMAP.fill(Qt.black)
    painter = QPainter()
    painter.begin(ERROR_PREVIEW_PIXMAP)
    painter.setPen(QPen(Qt.red, 5))
    r = ERROR_PREVIEW_PIXMAP.rect().adjusted(20, 20, -20, -20)
    painter.drawLine(r.topLeft(), r.bottomRight())
    painter.drawLine(r.bottomLeft(), r.topRight())
    painter.end()
    Globals.ERROR_PREVIEW_PIXMAP = ERROR_PREVIEW_PIXMAP

    NOT_SUPPORTED_PIXMAP = QPixmap(200, 200)
    NOT_SUPPORTED_PIXMAP.fill(Qt.black)
    painter = QPainter()
    painter.begin(NOT_SUPPORTED_PIXMAP)
    painter.setPen(QPen(Qt.red, 5))
    font = painter.font()
    font.setPixelSize(100)
    painter.setFont(font)
    r = NOT_SUPPORTED_PIXMAP.rect().adjusted(20, 20, -20, -20)
    # painter.drawLine(r.topLeft(), r.bottomRight())
    # painter.drawLine(r.bottomLeft(), r.topRight())
    painter.drawText(NOT_SUPPORTED_PIXMAP.rect(), Qt.AlignCenter | Qt.AlignVCenter, "?!")
    painter.end()
    Globals.NOT_SUPPORTED_PIXMAP = NOT_SUPPORTED_PIXMAP


    WIDTH = 50
    FAV_BIG_ICON = QPixmap(WIDTH, WIDTH)
    FAV_BIG_ICON.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(FAV_BIG_ICON)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
    start_angle = -0.34
    w = WIDTH-10
    points = []
    for i in range(5):
        points.append(QPointF(
            5+w*(0.5 + 0.5 * math.cos(start_angle + 0.8 * i * 3.14)),
            5+w*(0.5 + 0.5 * math.sin(start_angle + 0.8 * i * 3.14))
        ))
    poly = QPolygonF(points)
    painter.setPen(Qt.NoPen)
    color = QColor(0xFF, 0xA0, 0x00)
    painter.setBrush(color)
    painter.drawPolygon(poly, fillRule=Qt.WindingFill)
    painter.end()
    Globals.FAV_BIG_ICON = FAV_BIG_ICON


    WIDTH = 50
    TAG_BIG_ICON = QPixmap(WIDTH, WIDTH)
    TAG_BIG_ICON.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(TAG_BIG_ICON)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
    painter.setPen(QPen(Qt.white, 1))
    font = painter.font()
    font.setPixelSize(WIDTH-5)
    painter.setFont(font)
    painter.drawText(TAG_BIG_ICON.rect(), Qt.AlignCenter | Qt.AlignVCenter, "#")
    painter.end()
    Globals.TAG_BIG_ICON = TAG_BIG_ICON


    WIDTH = 50
    COMMENTS_BIG_ICON = QPixmap(WIDTH, WIDTH)
    COMMENTS_BIG_ICON.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(COMMENTS_BIG_ICON)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

    path1 = QPainterPath()
    path2 = QPainterPath()    
    radius = 10
    rect = COMMENTS_BIG_ICON.rect().adjusted(5, 5, -5, -15)
    path1.addRoundedRect(QRectF(rect), radius, radius)

    points = [
        QPointF(25, 25),
        QPointF(25, WIDTH-5),
        QPointF(40, 25),
    ]
    poly = QPolygonF(points)
    path2.addPolygon(poly)


    painter.setBrush(QBrush(Qt.white))
    pen = QPen(Qt.white, 3)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)

    path = path1.united(path2)
    painter.drawPath(path)


    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(Qt.black, 5))
    y = int(WIDTH/2.5)
    for point in [
            QPoint(WIDTH//2, y) - QPoint(10, 0),
            QPoint(WIDTH//2, y),
            QPoint(WIDTH//2, y) + QPoint(10, 0),
                ]:
        painter.drawPoint(point)

    painter.end()
    Globals.COMMENTS_BIG_ICON = COMMENTS_BIG_ICON




    MINIMIZE_ICON = QPixmap(100, 100)
    MINIMIZE_ICON.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(MINIMIZE_ICON)

    r = QRect(QPoint(0, 0), MINIMIZE_ICON.size())
    painter.setBrush(Qt.NoBrush)

    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)


    OFFSET = 5
    RADIUS = 30
    r = r.adjusted(OFFSET, OFFSET, -OFFSET, -OFFSET)

    painter.setPen(QPen(QColor(150, 150, 150, 127), 8))

    pen = painter.pen()
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)

    path = QPainterPath()
    path.addRoundedRect(QRectF(r), 20, 20)


    use_cubic = False
    path = QPainterPath()
    p = r.center()
    p.setX(r.left())
    path.moveTo(p)
    p.setY(r.top()+RADIUS)
    path.lineTo(p)
    p = r.topLeft()
    p += QPointF(RADIUS, 0)
    c = r.topLeft()
    if use_cubic:
        path.cubeTo(c, c, p)
    else:
        path.quadTo(c, p)
    p = r.topRight()
    p -= QPointF(RADIUS, 0)
    path.lineTo(p)
    c = r.topRight()
    p = r.topRight() + QPointF(0, RADIUS)
    if use_cubic:
        path.cubeTo(c, c, p)
    else:
        path.quadTo(c, p)
    p = r.bottomRight() - QPointF(0, RADIUS)
    path.lineTo(p)
    c = r.bottomRight()
    p = r.bottomRight() - QPointF(RADIUS, 0)
    if use_cubic:
        path.cubeTo(c, c, p)
    else:
        path.quadTo(c, p)
    p = r.center()
    p.setY(r.bottomLeft().y())
    path.lineTo(p)
    painter.drawPath(path)


    path2 = QPainterPath()
    c = r.center()
    HS = MINIMIZE_ICON.size().width()/2
    r2 = QRectF(c+QPointF(-HS, 0), c+QPointF(0, HS))
    r2.adjust(OFFSET, OFFSET*2, -OFFSET*2, -OFFSET)
    path2.addRoundedRect(r2, 10, 10)
    painter.drawPath(path2)


    path3 = QPainterPath()
    c = r.center()
    HR = RADIUS/2
    HR23 = RADIUS*2/3
    path3.moveTo(c - QPointF(0, HR))
    path3.lineTo(c)
    path3.lineTo(c + QPointF(HR, 0))
    path3.moveTo(c + QPointF(3, -3))
    path3.lineTo(c + QPointF(HR23, -HR23))

    painter.drawPath(path3)

    painter.end()
    Globals.MINIMIZE_ICON = MINIMIZE_ICON.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)


    print('finish generating pixmaps')



