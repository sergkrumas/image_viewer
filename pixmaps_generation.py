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


def default_thumbnail(Globals, SettingsWindow):

    THUMBNAIL_WIDTH = Globals.THUMBNAIL_WIDTH
    DEFAULT_THUMBNAIL = QPixmap(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
    DEFAULT_THUMBNAIL.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(DEFAULT_THUMBNAIL)
    painter.setPen(Qt.gray)
    font = painter.font()
    font.setPixelSize(THUMBNAIL_WIDTH)
    painter.setFont(font)
    painter.setBrush(Qt.NoBrush)
    painter.drawText(QRect(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH), Qt.AlignCenter, "⧖") #hourglass
    painter.end()

    if SettingsWindow.get_setting_value('draw_default_thumbnail'):
        Globals.DEFAULT_THUMBNAIL = DEFAULT_THUMBNAIL

def error_preview_pixmap(Globals):

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

def not_supported_pixmap(Globals):

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

def fav_big_icon(Globals):

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

def tag_big_icon(Globals):

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

def comments_big_icon(Globals):

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

def minimize_icon(Globals):

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

    pen = QPen(QColor(255, 255, 255, 200), 8)
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

def null_pixmap(Globals):

    Globals.NULL_PIXMAP = QPixmap()

def lang_pixmap_begin(lang_rect):
    PIXMAP = QPixmap(lang_rect.size().toSize())
    PIXMAP.fill(Qt.transparent)
    painter = QPainter()
    painter.begin(PIXMAP)
    painter.setPen(QPen(Qt.gray, 1))
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
    painter.setRenderHint(QPainter.Antialiasing, True)
    return PIXMAP, painter

def lang_en_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    red = QColor(201, 7, 42)
    white = QColor(255, 255, 255)
    blue = QColor(0, 27, 105)

    painter.fillRect(lang_rect, red)

    offset = 10
    lang_rect.adjust(offset, 0, 0, -offset)
    painter.fillRect(lang_rect, white)
    offset = 8
    lang_rect.adjust(offset, 0, 0, -offset)
    painter.fillRect(lang_rect, blue)

    p1 = lang_rect.bottomLeft()
    p2 = lang_rect.topRight() + QPointF(lang_rect.width()/2, 0)

    painter.setClipping(True)
    painter.setClipRect(lang_rect)
    painter.setPen(QPen(white, 15))

    painter.drawLine(p1 + QPoint(0, 6), p2 + QPoint(0, 6))
    painter.setPen(QPen(red, 5))

    p1 += QPoint(0, 3)
    p2 += QPoint(0, 3)
    painter.drawLine(p1, p2)

    painter.setClipping(False)

    painter.end()
    Globals.lang_en_pixmap = PIXMAP

def lang_ru_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    white = QColor(255, 255, 255)
    blue = QColor(0, 54, 167)
    red = QColor(214, 39, 24)

    painter.fillRect(lang_rect, white)
    offset = lang_rect.height()/3
    lang_rect.adjust(0, offset, 0, 0)
    painter.fillRect(lang_rect, blue)
    lang_rect.adjust(0, offset, 0, 0)
    painter.fillRect(lang_rect, red)

    painter.end()
    Globals.lang_ru_pixmap = PIXMAP

def lang_de_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    schwarz = QColor(0, 0, 0)
    rot = QColor(222, 0, 0)
    gelb = QColor(255, 207, 0)

    painter.fillRect(lang_rect, schwarz)
    offset = lang_rect.height()/3
    lang_rect.adjust(0, offset, 0, 0)
    painter.fillRect(lang_rect, rot)
    lang_rect.adjust(0, offset, 0, 0)
    painter.fillRect(lang_rect, gelb)

    painter.end()
    Globals.lang_de_pixmap = PIXMAP

def lang_fr_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    blue =  QColor(0, 0, 146)
    white = QColor(255, 255, 255)
    red =  QColor(226, 0, 6)

    painter.fillRect(lang_rect, blue)
    offset = lang_rect.width()/3
    lang_rect.adjust(offset, 0, 0, 0)
    painter.fillRect(lang_rect, white)
    lang_rect.adjust(offset, 0, 0, 0)
    painter.fillRect(lang_rect, red)

    painter.end()
    Globals.lang_fr_pixmap = PIXMAP


def lang_it_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    green = QColor(0, 147, 68)
    white = QColor(255, 255, 255)
    red = QColor(207, 39, 52)

    painter.fillRect(lang_rect, green)
    offset = lang_rect.width()/3
    lang_rect.adjust(offset, 0, 0, 0)
    painter.fillRect(lang_rect, white)
    lang_rect.adjust(offset, 0, 0, 0)
    painter.fillRect(lang_rect, red)

    painter.end()
    Globals.lang_it_pixmap = PIXMAP

def lang_es_pixmap(Globals, lang_rect):

    PIXMAP, painter = lang_pixmap_begin(lang_rect)

    red = QColor(199, 3, 24)
    yellow = QColor(255, 197, 0)

    painter.fillRect(lang_rect, red)
    offset = lang_rect.height()/4
    lang_rect.adjust(0, offset, 0, 0)
    painter.fillRect(lang_rect, yellow)
    font = QFont()
    TEXT_HEIGHT = 18
    font.setPixelSize(TEXT_HEIGHT)
    font.setWeight(1500)
    painter.setFont(font)
    painter.setPen(Qt.black)
    painter.drawText(lang_rect.topLeft() + QPointF(0, offset + (offset*2 - TEXT_HEIGHT)/2), ' ES')
    lang_rect.adjust(0, offset*2, 0, 0)
    painter.fillRect(lang_rect, red)

    painter.end()
    Globals.lang_es_pixmap = PIXMAP

def generate_pixmaps(Globals, SettingsWindow):

    print('start generating pixmaps')

    null_pixmap(Globals)
    default_thumbnail(Globals, SettingsWindow)
    error_preview_pixmap(Globals)
    not_supported_pixmap(Globals)
    fav_big_icon(Globals)
    tag_big_icon(Globals)
    comments_big_icon(Globals)
    minimize_icon(Globals)

    lang_rect = QRectF(0, 0, 60, 60)
    lang_en_pixmap(Globals, QRectF(lang_rect))
    lang_ru_pixmap(Globals, QRectF(lang_rect))
    lang_de_pixmap(Globals, QRectF(lang_rect))
    lang_fr_pixmap(Globals, QRectF(lang_rect))
    lang_it_pixmap(Globals, QRectF(lang_rect))
    lang_es_pixmap(Globals, QRectF(lang_rect))

    print('finish generating pixmaps')
