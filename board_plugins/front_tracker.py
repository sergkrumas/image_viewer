
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class TaskStatus():
    STORY = 1
    TODO = 2
    IN_PROGRESS = 3
    DONE = 4


STATUS_INPROGRESS = TaskStatus.IN_PROGRESS
STATUS_DONE = TaskStatus.DONE

class Task(object):

    def is_done(self):
        return self.date is None

    def __init__(self, id, text, date, status, group, linked_tasks, image_paths, channel=None):
        super().__init__()
        self.id = id
        self.text = text
        self.group = group
        self.group.tasks.append(self)
        self.image_paths = image_paths
        self.date = date
        self.channel = channel
        self.linked_tasks = linked_tasks
        self.status = status

    def __repr__(self):
        return f'{self.text} ({self.group}'

class Group(object):

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.tasks = list()

        filename = os.path.basename(filepath)
        parts = filename.split("_")
        start_slice_index = min(1, 1*(len(parts)-1)) # returns 0 when len = 1 and returns 1 when len > 1
        self.name = " ".join(parts[start_slice_index:]).strip()

        parts = self.name.split(".")
        self.name = ".".join(parts[:-1]) 

    def __repr__(self):
        return f'{self.name} ({len(self.tasks)})'

    def channels(self):
        _channels = []
        for task in self.tasks:
            _channels.append(task.channel)
        _channels = list(reversed(list(set(_channels))))
        return _channels

    def todo_tasks_for_channel(self, channel):
        return [task for task in self.tasks if task.channel == channel and task.is_done()]

    def future_tasks_for_channel(self, channel):
        return [task for task in self.tasks if task.channel == channel and not task.is_done()]






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

    painter.setPen(QPen(Qt.white, 1))
    for n, group in enumerate(self.data_groups):
        transform = QTransform()
        pos = self.board_MapToViewport(QPointF(50*n, 0))
        transform.translate(pos.x(), pos.y())
        transform.rotate(90)
        painter.setTransform(transform)
        painter.drawText(QPointF(5, -5), group.name)
        painter.resetTransform()

        # CHANNEL_WIDTH = 200
        # GROUP_WIDTH = CHANNEL_WIDTH * len(group.channels())

        # for index, channel_name in enumerate(group.channels()):


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
                    self.data_groups.append(Group(obj_path))

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
