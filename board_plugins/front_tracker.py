
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

    def __init__(self, text, channel):
        super().__init__()
        self.text = text
        self.channel = channel

    # def __init__(self, id, text, date, status, group, linked_tasks, image_paths, channel=None):
    #     super().__init__()
    #     self.id = id
    #     self.text = text
    #     self.group = group
    #     self.group.tasks.append(self)
    #     self.image_paths = image_paths
    #     self.date = date
    #     self.channel = channel
    #     self.linked_tasks = linked_tasks
    #     self.status = status

    def __repr__(self):
        return f'{self.text} ({self.group.name}'

class Channel(object):

    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.group.channels.append(self)
        self.tasks = []

    def __repr__(self):
        return f'{self.name} ({len(self.tasks)})'

class Group(object):

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.channels = list()

        filename = os.path.basename(filepath)
        parts = filename.split("_")
        start_slice_index = min(1, 1*(len(parts)-1)) # returns 0 when len = 1 and returns 1 when len > 1
        self.name = " ".join(parts[start_slice_index:]).strip()

        parts = self.name.split(".")
        self.name = ".".join(parts[:-1]) 

        self.parse_file()

    def parse_file(self):
        lines = []
        with open(self.filepath, 'r', encoding='utf8') as file:
            data = file.read()
            lines = data.split("\n")
        if lines:
            self.parse_lines(lines)

    def parse_lines(self, lines):

        def count_indent(text):
            level = 0
            for n, c in enumerate(text):
                if c == " ":
                    level += 1
                else:
                    break
            return level

        def task_buffer_to_task(tb, channel):
            if tb:
                text = "\n".join(map(str.strip, tb))
                task = Task(text, channel)
                tb = []


        current_channel = Channel('Default', self)
        task_buffer = []
        for line in lines:
            line = line.replace("\t", " "*4)
            line_indent = count_indent(line)
            if line_indent == 0:
                channel_name = line.strip()

                if channel_name:
                    current_channel = Channel(channel_name, self)
            else:
                line = line.strip()
                if line:
                    task_buffer.append(line)
                else:
                    task_buffer_to_task(task_buffer, current_channel)

    def __repr__(self):
        return f'{self.name} ({len(self.tasks)})'




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

    font = painter.font()
    font.setPixelSize(30)
    painter.setFont(font)

    def draw_text_90(pos, text):
        transform = QTransform()
        transform.translate(pos.x(), pos.y())
        transform.rotate(90)
        painter.setTransform(transform)
        painter.drawText(QPointF(5, -5), text)
        painter.resetTransform()


    painter.setPen(QPen(Qt.white, 1))
    offset = QPointF(0, 0)
    for n, group in enumerate(self.data_groups):
        draw_text_90(self.board_MapToViewport(offset+QPointF(0, -100)), group.name)

        for i, channel in enumerate(group.channels):
            draw_text_90(self.board_MapToViewport(offset), channel.name)            
            offset += QPointF(200, 0)


    painter.restore()

def check_exclude(obj_name, files_to_exclude):
    b1 = obj_name in files_to_exclude
    b2 = False
    for line in files_to_exclude:
        if obj_name.lower().startswith(line.lower()):
            b2 = True
            # print(f'{line}, {obj_name}')
            break
    return not (b1 or b2)

def preparePluginBoard(self, plugin_info):
    cf = self.LibraryData().current_folder()
    board = cf.board

    self.data_groups = []

    exts = ('.txt', '.md')
    exts = ('.txt')
    folders_to_scan_filepath = self.get_user_data_filepath('front_tracker.data.txt')
    exclude_files_filepath = self.get_user_data_filepath('front_tracker.exclude.data.txt')

    with open(exclude_files_filepath, 'r', encoding='utf8') as file:
        data = ""
        data = file.read()
        lines = data.split('\n')
        files_to_exclude = list(filter(lambda x: bool(x.strip()), lines))

    data = ""
    with open(folders_to_scan_filepath, 'r', encoding='utf8') as file:
        data = file.read()
        paths = data.split("\n")
        for path in paths:
            if os.path.exists(path):
                for obj_name in os.listdir(path):
                    obj_path = os.path.join(path, obj_name)
                    if os.path.isfile(obj_path) and obj_name.lower().endswith(exts) and check_exclude(obj_name, files_to_exclude):
                        self.data_groups.append(Group(obj_path))

            else:
                self.show_center_label(f'Путь {path} не найден в файловой системе!', error=True)

        self.board_origin = QPointF(0, 0)
        self.update()

def register(board_obj, plugin_info):
    plugin_info.name = 'FRONT TRACKER'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
