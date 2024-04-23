
import sys
import os
import subprocess
import random
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

PIXEL_SIZE = 200

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

        self.ui_height = PIXEL_SIZE

    def __repr__(self):
        return f'{self.text} ({self.group.name}'

class Channel(object):

    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.group.channels.append(self)
        self.tasks = []

        self.ui_width = PIXEL_SIZE

        self.extended = False

    def toggle_width(self):
        self.extended = not self.extended
        if self.extended:
            self.ui_width = PIXEL_SIZE*2
        else:
            self.ui_width = PIXEL_SIZE

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

    def tasks(self):
        return [task for channel in self.channels for task in channel.tasks]

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

        min_line_indent = 100

        for n0, li in enumerate(lines):
            # заменяем таб на 4 пробела
            li = lines[n0] = li.replace("\t", " "*4)

            # считаем минимальный уровень индента для файла
            if li.strip():
                ci = count_indent(li)
                min_line_indent = min(min_line_indent, ci)

        # убираем из каждой строки первые min_line_indent символов,
        # чтобы алгоритм парсинга работал правильно с файлами разных отступов для групп
        for n1, li in enumerate(lines):
            li = lines[n1] = li[min_line_indent:]


        for n, line in enumerate(lines):
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
        return f'{self.name} ({len(self.tasks())})'


def mousePressEvent(self, event):
    isLeftButton = event.button() == Qt.LeftButton
    if self.front_tracker_channel_over_mouse is not None and isLeftButton:
        pass
    elif self.front_tracker_group_over_mouse is not None and isLeftButton:
        pass
    else:
        self.board_mousePressEventDefault(event)

def mouseMoveEvent(self, event):
    isLeftButton = event.buttons() == Qt.LeftButton
    if self.front_tracker_channel_over_mouse is not None and isLeftButton:
        pass
    elif self.front_tracker_group_over_mouse is not None and isLeftButton:
        pass
    else:
        self.board_mouseMoveEventDefault(event)

def mouseReleaseEvent(self, event):
    isLeftButton = event.button() == Qt.LeftButton
    if self.front_tracker_channel_over_mouse is not None and isLeftButton:
        self.front_tracker_channel_over_mouse.toggle_width()
    elif self.front_tracker_group_over_mouse is not None and isLeftButton:
        pass
    else:
        self.board_mouseReleaseEventDefault(event)

def paintEvent(self, painter, event):

    self.front_tracker_channel_over_mouse = None
    self.front_tracker_group_over_mouse = None

    painter.save()

    cursor_pos = self.mapFromGlobal(QCursor().pos())

    def set_font(size):
        font = painter.font()
        font.setPixelSize(size)
        painter.setFont(font)

    def draw_text_90(pos, text):
        transform = QTransform()
        pos = self.board_MapToViewport(pos)

        # для того, чтобы надпись оставалась на экране,
        # когда из-за зума или панорамирования она уехала в невидимую область
        font_pixel_size = painter.font().pixelSize() + 10
        if pos.y() < font_pixel_size:
            pos.setY(font_pixel_size)


        transform.translate(pos.x(), pos.y())
        transform.rotate(90)
        painter.setTransform(transform)
        painter.drawText(QPointF(5, -5), text)
        painter.resetTransform()

    def draw_group_name(offset, group, board_scale_x):
        painter.save()
        painter.setPen(QPen(QColor(200, 50, 50)))
        align = Qt.AlignLeft
        group_name = group.name
        rect = painter.boundingRect(QRect(), align, group_name)
        pos = self.board_MapToViewport(offset).toPoint()

        # для того, чтобы надпись оставалась на экране,
        # когда из-за зума или панорамирования она уехала в невидимую область
        font_pixel_size = painter.font().pixelSize() + 10
        if pos.y() < font_pixel_size:
            pos.setY(font_pixel_size)
        # то же самое, только теперь название группы будет видно если видно хоть один столбец этой группы
        current_group_width = sum(channel.ui_width for channel in group.channels)
        current_group_width *= board_scale_x
        if pos.x() < 0 and pos.x() > -current_group_width + rect.width():
            pos.setX(0)

        rect.moveBottomLeft(pos)
        painter.drawText(rect, align, group_name)
        painter.restore()

    offset = QPointF(0, 0)



    group_names_to_draw = []
    channel_names_to_draw = []
    task_cells_to_draw = []


    a = self.board_MapToViewport(QPointF(0, 0))
    width = sum(c.ui_width for g in self.front_tracker_data_groups for c in g.channels)
    height = max(sum(t.ui_height for t in c.tasks) for g in self.front_tracker_data_groups for c in g.channels)
    b = self.board_MapToViewport(QPointF(width, height))
    rect = QRectF(a, b)

    painter.fillRect(rect, QColor(10, 10, 10, 220))
    painter.setPen(QPen(QColor(50, 50, 50), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(rect)


    sch = QRectF(rect)
    selection_rect_channel = None


    sgr_base = QRectF(rect)
    sgr = QRectF(sgr_base)
    selection_rect_group = None

    for n, group in enumerate(self.front_tracker_data_groups):

        group_names_to_draw.append((QPointF(offset), group))

        group_start_offset = QPointF(offset)

        for i, channel in enumerate(group.channels):

            channel_names_to_draw.append((QPointF(offset), channel.name))
            task_cell_offset = QPointF(offset)

            for task in channel.tasks:

                a = QPointF(task_cell_offset)
                b = a + QPointF(channel.ui_width, task.ui_height)
                a = self.board_MapToViewport(a)
                b = self.board_MapToViewport(b)
                task_cell_rect = QRectF(a, b)

                task_cells_to_draw.append((QRectF(task_cell_rect), task.text))
                task_cell_offset += QPointF(0, task.ui_height)


            # !: step 1
            if sch:
                sch.setWidth(channel.ui_width*self.board_scale_x)                
                sch.moveLeft(self.board_MapToViewport(offset).x())
            # !: step 2
            offset += QPointF(channel.ui_width, 0)
            # !: step 3
            if sch and sch.contains(cursor_pos):
                selection_rect_channel = QRectF(sch)
                sch = None
                self.front_tracker_channel_over_mouse = channel



        group_end_offset = QPointF(offset)
        group_start_offset = self.board_MapToViewport(group_start_offset)
        group_end_offset = self.board_MapToViewport(group_end_offset)
        if sgr:
            sgr = QRectF(sgr_base)
            sgr.setLeft(group_start_offset.x())
            sgr.setWidth(group_end_offset.x() - group_start_offset.x())
        if sgr and sgr.contains(cursor_pos):
            selection_rect_group = QRectF(sgr)
            sgr = None
            self.front_tracker_group_over_mouse = group

    color = self.selection_color
    color.setAlpha(50)

    if selection_rect_group:
        painter.fillRect(selection_rect_group, color)

    if selection_rect_channel:
        color.setAlpha(100)
        painter.fillRect(selection_rect_channel, color)


    painter.setPen(QPen(Qt.white, 1))


    for offset, group in group_names_to_draw:
        set_font(30)
        draw_group_name(offset, group, self.board_scale_x)

    for offset, name in channel_names_to_draw:
        set_font(30)
        draw_text_90(offset, name)

    for task_cell_rect, text in task_cells_to_draw:
        set_font(20)
        painter.drawRect(task_cell_rect)
        task_cell_rect.adjust(10, 10, -10, -10)
        painter.drawText(task_cell_rect, Qt.AlignLeft, text)


    set_font(15)
    pos = self.rect().bottomLeft() + QPointF(50, -50)
    if self.front_tracker_channel_over_mouse is not None:
        painter.drawText(pos, str(self.front_tracker_channel_over_mouse))
    if self.front_tracker_group_over_mouse is not None:
        pos += QPointF(0, -50)
        painter.drawText(pos, str(self.front_tracker_group_over_mouse))

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

    self.front_tracker_data_groups = []
    self.front_tracker_channel_over_mouse = None
    self.front_tracker_group_over_mouse = None

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
                        self.front_tracker_data_groups.append(Group(obj_path))

            else:
                self.show_center_label(f'Путь {path} не найден в файловой системе!', error=True)

        self.board_origin = QPointF(500, 250)
        self.update()






def register(board_obj, plugin_info):
    plugin_info.name = 'FRONT TRACKER'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
