



import os, sys, time

import locale

from PyQt5.QtWidgets import (QSystemTrayIcon, QWidget, QMessageBox, QMenu, QGraphicsPixmapItem,
    QGraphicsScene, QFileDialog, QHBoxLayout, QCheckBox, QVBoxLayout, QTextEdit, QGridLayout,
    QPushButton, QGraphicsBlurEffect, QLabel, QApplication, QScrollArea, QDesktopWidget)
from PyQt5.QtCore import (QUrl, QMimeData, pyqtSignal, QPoint, QPointF, pyqtSlot, QRect, QEvent,
    QTimer, Qt, QSize, QRectF, QThread)
from PyQt5.QtGui import (QPainterPath, QColor, QKeyEvent, QMouseEvent, QBrush, QPixmap,
    QPaintEvent, QPainter, QWindow, QPolygon, QImage, QTransform, QPen, QLinearGradient,
    QIcon, QFont, QCursor, QPolygonF)


if __name__ == "__main__":


    app = QApplication(sys.argv)

    for i in range(99):

        i += 1


        # locale.setlocale(locale.LC_ALL, "russian")

        painter = QPainter()
        pixmap = QPixmap(200, 200)
        pixmap.fill(Qt.transparent)
        painter.begin(pixmap)

        if i % 2 == 0:
            color = QColor(150, 21, 150)
        else:
            color = QColor(13, 21, 32)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(pixmap.rect())
        painter.setPen(QPen(Qt.white))
        font = painter.font()
        font.setPixelSize(150)
        painter.setFont(font)

        rect = QRect(0, 0, pixmap.width(), pixmap.height())
        painter.setBrush(Qt.NoBrush)

        painter.drawText(rect, Qt.AlignCenter | Qt.AlignHCenter, str(i))

        painter.end()

        pixmap.save(f"{i:02}.jpeg")

    # QMessageBox.information(None, "Сообщение", "Выполнено")
    sys.exit()
