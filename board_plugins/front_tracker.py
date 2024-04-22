
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

    def __init__(self, text, channel):
        super().__init__()
        self.text = text
        self.channel = channel
        self.channel.tasks.append(self)

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
                tb.clear()


        current_channel = Channel('Default', self)
        task_buffer = []
        for line in lines:
            line = line.replace("\t", " "*4)
            line_indent = count_indent(line)
            if line_indent == 0:
                channel_name = line.strip()
                if channel_name:
                    current_channel = Channel(channel_name, self)
                    continue

            line = line.strip()
            if line:
                task_buffer.append(line)

            else:
                task_buffer_to_task(task_buffer, current_channel)

        task_buffer_to_task(task_buffer, current_channel)

    def __repr__(self):
        return f'{self.name} ({len(self.tasks)})'




def paintEvent(self, painter, event):

    if self.Globals.DEBUG or self.STNG_board_draw_grid:
        self.board_draw_grid(painter)

    painter.save()

    cursor_pos = self.mapFromGlobal(QCursor().pos())

    def set_font(size):
        font = painter.font()
        font.setPixelSize(size)
        painter.setFont(font)

    def draw_text_90(pos, text):
        transform = QTransform()
        pos = self.board_MapToViewport(pos)
        transform.translate(pos.x(), pos.y())
        transform.rotate(90)
        painter.setTransform(transform)
        painter.drawText(QPointF(5, -5), text)
        painter.resetTransform()

    def draw_group_name(offset, group):
        painter.save()
        painter.setPen(QPen(QColor(200, 50, 50)))
        align = Qt.AlignLeft
        group_name = group.name
        rect = painter.boundingRect(QRect(), align, group_name)
        rect.moveBottomLeft(self.board_MapToViewport(offset).toPoint())
        painter.drawText(rect, align, group_name)
        painter.restore()

    offset = QPointF(0, 0)

    CHANNEL_WIDTH = 200

    group_names_to_draw = []
    channel_names_to_draw = []
    task_cells_to_draw = []

    for n, group in enumerate(self.data_groups):

        group_names_to_draw.append((QPointF(offset), group))

        for i, channel in enumerate(group.channels):

            channel_names_to_draw.append((QPointF(offset), channel.name))
            task_cell_offset = QPointF(offset)

            for task in channel.tasks:

                a = QPointF(task_cell_offset)
                b = a + QPointF(CHANNEL_WIDTH, CHANNEL_WIDTH)
                a = self.board_MapToViewport(a)
                b = self.board_MapToViewport(b)
                task_cell_rect = QRectF(a, b)

                task_cells_to_draw.append((QRectF(task_cell_rect), task.text))
                task_cell_offset += QPointF(0, CHANNEL_WIDTH)

            offset += QPointF(CHANNEL_WIDTH, 0)





    a = self.board_MapToViewport(QPointF(0, 0))
    height = max(len(c.tasks) for g in self.data_groups for c in g.channels)*CHANNEL_WIDTH
    b = self.board_MapToViewport(offset+QPointF(0, height))
    rect = QRectF(a, b)

    painter.fillRect(rect, QColor(10, 10, 10, 220))
    painter.setPen(QPen(QColor(50, 50, 50), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(rect)

    painter.setPen(QPen(Qt.white, 1))

    for offset, group in group_names_to_draw:
        set_font(30)
        draw_group_name(offset, group)

    for offset, name in channel_names_to_draw:
        set_font(30)
        draw_text_90(offset, name)

    for task_cell_rect, text in task_cells_to_draw:
        set_font(20)
        painter.drawRect(task_cell_rect)
        task_cell_rect.adjust(10, 10, -10, -10)
        painter.drawText(task_cell_rect, Qt.AlignLeft, text)


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
