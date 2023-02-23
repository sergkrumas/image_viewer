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

    print('finish generating pixmaps')
