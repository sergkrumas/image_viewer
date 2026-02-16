

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

app = QApplication([])

def gen_pixmap(name):

    if name.startswith('switch_on'):
        color = Qt.green
        thumb_offset = QPoint(10, 0)
    elif name.startswith('switch_off'):
        color = Qt.gray
        thumb_offset = QPoint(-10, 0)

    pixmap = QPixmap(40, 20)
    pixmap.fill(Qt.transparent)
    p = QPainter()

    p.begin(pixmap)

    p.setRenderHint(QPainter.HighQualityAntialiasing, True)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    
    offset = 2
    rect = pixmap.rect().adjusted(offset, offset, -offset, -offset)
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), 10, 10)
    p.setBrush(QColor(50, 50, 50))
    p.setPen(QPen(QColor(20, 20, 20)))
    p.drawPath(path)


    rect.setWidth(10)
    rect.setHeight(10)

    p.setPen(Qt.NoPen)
    p.setBrush(color)
    rect.moveCenter(pixmap.rect().center()+thumb_offset)

    p.drawEllipse(rect)

    p.end()

    pixmap.save(name)


gen_pixmap('switch_on.png')
gen_pixmap('switch_off.png')
