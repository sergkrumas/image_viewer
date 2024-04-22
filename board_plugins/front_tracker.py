
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

def paintEvent(self, painter, event):
    self.board_draw_main_default(painter, event)

    painter.save()

    offset = QPointF(300, 300)
    a = self.board_MapToViewport(offset)
    b = self.board_MapToViewport(offset*10)
    rect = QRectF(a, b)
    painter.fillRect(rect, QColor(20, 20, 20, 220))

    painter.restore()



def preparePluginBoard(self, plugin_info):
    pass






def register(board_obj, plugin_info):
    plugin_info.name = 'FRONT TRACKER'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
