
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *




def get_plugin_data_filepath(self):
    return self.get_user_data_filepath('front_tracker.data.txt')

def paintEvent(self, painter, event):

    if self.Globals.DEBUG or self.STNG_board_draw_grid:
        self.board_draw_grid(painter)

    painter.save()

    offset = QPointF(400, 300)
    a = self.board_MapToViewport(QPointF(0, 0))
    b = self.board_MapToViewport(offset*10)
    rect = QRectF(a, b)

    painter.fillRect(rect, QColor(10, 10, 10, 220))
    painter.setPen(QPen(QColor(50, 50, 50), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(rect)

    for n, text in enumerate(self.data_groups):
        text = os.path.basename(text)
        pos = self.board_MapToViewport(QPointF(0, 50*n))
        painter.drawText(pos, text)

    painter.restore()

def preparePluginBoard(self, plugin_info):
    cf = self.LibraryData().current_folder()
    board = cf.board

    self.data_groups = []

    exts = ('.txt', '.md')
    exts = ('.txt')
    plugin_data_filepath = get_plugin_data_filepath(self)
    data = ""
    with open(plugin_data_filepath, 'r', encoding='utf8') as file:
        data = file.read()
    if data != "":
        lines = data.split('\n')
        folder_to_parse_files_in = lines[0]
        if os.path.exists(folder_to_parse_files_in):
            for obj_name in os.listdir(folder_to_parse_files_in):
                obj_path = os.path.join(folder_to_parse_files_in, obj_name)
                if os.path.isfile(obj_path) and obj_name.lower().endswith(exts):
                    self.data_groups.append(obj_path)
        else:
            self.show_center_label(f'Путь, заданный в {plugin_data_filepath}, не найден в файловой системе!', error=True)
    else:
        self.show_center_label(f'В файле {plugin_data_filepath} не задан путь к папке с файлами!', error=True)



def register(board_obj, plugin_info):
    plugin_info.name = 'FRONT TRACKER'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
