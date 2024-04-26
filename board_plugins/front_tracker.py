
import sys
import os
import subprocess
import random
from functools import partial
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

sys.path.append('../')
import _utils

TASK_CELL_SIZE = 200

class TaskStatus():
    STORY = 1
    TODO = 2
    IN_PROGRESS = 3
    DONE = 4

STATUS_INPROGRESS = TaskStatus.IN_PROGRESS
STATUS_DONE = TaskStatus.DONE

class Task(object):

    def __init__(self, text, channel, linenum):
        super().__init__()
        self.text = text
        self.channel = channel
        self.channel.tasks.append(self)
        self.start_line_number = linenum

        self.ui_height = TASK_CELL_SIZE

    def __repr__(self):
        return f'{self.text} ({self.group.name}'

class Channel(object):

    def __init__(self, name, group):
        self.name = name
        self.group = group
        self.group.channels.append(self)
        self.tasks = []

        self.ui_width = TASK_CELL_SIZE

        self.extended = False

    def toggle_width(self):
        self.extended = not self.extended
        if self.extended:
            self.ui_width = TASK_CELL_SIZE*2
        else:
            self.ui_width = TASK_CELL_SIZE

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
                tb_text_lines = map(lambda x: x[1], tb)
                text = "\n".join(map(str.strip, tb_text_lines))
                start_line_num = tb[0][0] + 1
                task = Task(text, channel, start_line_num)
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
                if line_indent == 4:
                    # для тасок, между которыми нет зазора - минимум одна строка
                    task_buffer_to_task(task_buffer, current_channel)

                task_buffer.append((n, line))
            else:
                task_buffer_to_task(task_buffer, current_channel)

        task_buffer_to_task(task_buffer, current_channel)

    def __repr__(self):
        return f'{self.name} ({len(self.tasks())})'

def mousePressEvent(self, event):
    isLeftButton = event.button() == Qt.LeftButton
    if self.front_tracker_channel_under_mouse is not None and isLeftButton:
        pass
    if self.front_tracker_group_under_mouse is not None and isLeftButton:
        self.front_tracker_captured_group = self.front_tracker_group_under_mouse
        self.front_tracker_captured_channel = self.front_tracker_channel_under_mouse
    else:
        self.board_mousePressEventDefault(event)

def mouseMoveEvent(self, event):
    isLeftButton = event.buttons() == Qt.LeftButton
    if self.front_tracker_channel_under_mouse is not None and isLeftButton:
        pass
    elif self.front_tracker_group_under_mouse is not None and isLeftButton:
        pass
    else:
        self.board_mouseMoveEventDefault(event)

def mouseReleaseEvent(self, event):
    isLeftButton = event.button() == Qt.LeftButton
    if self.front_tracker_captured_group:
        gr = self.front_tracker_captured_group
        index_to_insert = self.front_tracker_current_group_insert_pos.index
        gr_index = self.front_tracker_data_groups.index(gr)

        if index_to_insert > gr_index:
            index_to_insert -= 1

        self.front_tracker_data_groups.remove(gr)
        self.front_tracker_data_groups.insert(index_to_insert, gr)

        self.front_tracker_captured_group = None
        self.front_tracker_captured_channel = None

    if self.front_tracker_channel_under_mouse is not None and isLeftButton:
        pass
    elif self.front_tracker_group_under_mouse is not None and isLeftButton:
        pass
    else:
        self.board_mouseReleaseEventDefault(event)
    self.update()

def wheelEvent(self, event):
    self.board_wheelEventDefault(event)


def mouseDoubleClickEvent(self, event):
    isLeftButton = event.button() == Qt.LeftButton
    if self.front_tracker_channel_under_mouse is not None and isLeftButton:
        self.front_tracker_channel_under_mouse.toggle_width()

def paintEvent(self, painter, event):

    if not self.front_tracker_data_groups:
        return

    self.front_tracker_channel_under_mouse = None
    self.front_tracker_group_under_mouse = None
    self.front_tracker_task_under_mouse = None

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

                if task_cell_rect.contains(cursor_pos):
                    self.front_tracker_task_under_mouse = task

            sch.setWidth(channel.ui_width*self.board_scale_x)
            sch.moveLeft(self.board_MapToViewport(offset).x())
            channel.ui_rect = sch
            if sch.contains(cursor_pos) and not self.front_tracker_captured_group:
                selection_rect_channel = QRectF(sch)
                self.front_tracker_channel_under_mouse = channel

            offset += QPointF(channel.ui_width, 0)


        group_end_offset = QPointF(offset)
        group_start_offset = self.board_MapToViewport(group_start_offset)
        group_end_offset = self.board_MapToViewport(group_end_offset)

        sgr = QRectF(sgr_base)
        sgr.setLeft(group_start_offset.x())
        sgr.setWidth(group_end_offset.x() - group_start_offset.x())
        group.ui_rect = sgr
        if sgr.contains(cursor_pos) and not self.front_tracker_captured_group:
            selection_rect_group = QRectF(sgr)
            self.front_tracker_group_under_mouse = group

    color = self.selection_color
    color.setAlpha(50)

    if selection_rect_group:
        painter.fillRect(selection_rect_group, color)

    if selection_rect_channel:
        color.setAlpha(100)
        painter.fillRect(selection_rect_channel, color)


    painter.setPen(QPen(Qt.white, 1))


    set_font(30)
    for offset, group in group_names_to_draw:
        draw_group_name(offset, group, self.board_scale_x)

    set_font(30)
    for offset, name in channel_names_to_draw:
        draw_text_90(offset, name)

    set_font(20)
    self_rect = self.rect()
    for task_cell_rect, text in task_cells_to_draw:
        if task_cell_rect.intersected(QRectF(self_rect)):
            painter.drawRect(task_cell_rect)
            task_cell_rect.adjust(10, 10, -10, -10)
            painter.drawText(task_cell_rect, Qt.AlignLeft, text)


    set_font(15)
    pos = self.rect().bottomLeft() + QPointF(50, -50)
    if self.front_tracker_channel_under_mouse is not None:
        data = self.front_tracker_channel_under_mouse
        painter.drawText(pos, f'Under Cursor Channel: {data}')
    if self.front_tracker_group_under_mouse is not None:
        pos += QPointF(0, -25)
        data = self.front_tracker_group_under_mouse
        painter.drawText(pos, f'Under Cursor Group: {data}')

    pos += QPointF(0, -25)
    painter.drawText(pos, f'Groups: {len(self.front_tracker_data_groups)}')

    if isGroupMovedToNewPlace(self, cursor_pos):

        data = defineInsertPositions(self)

        color2 = QColor(220, 20, 20)
        for ip in self.front_tracker_insert_positions:
            if ip.not_used:
                c = color
            else:
                c = color2
            painter.setPen(QPen(c, 5))
            painter.drawLine(ip.line)

        if data:
            hor_line = data[0]
            painter.drawLine(hor_line)

            for ip in self.front_tracker_insert_positions:
                if ip.ready:
                    c = color2
                else:
                    c = color
                painter.setPen(QPen(c, 40))
                painter.drawPoint(ip.intersection_point)

        painter.fillRect(self.front_tracker_captured_group.ui_rect, self.diagonal_lines_br)

    painter.restore()

def isGroupMovedToNewPlace(self, cursor_pos):
    cgrp = self.front_tracker_captured_group
    return cgrp and not cgrp.ui_rect.contains(cursor_pos)

def isChannelMovedToNewPlace(self, cursor_pos):
    cch = self.front_tracker_captured_channel
    return cch and cch.group.ui_rect.contains(cursor_pos) and not cch.ui_rect.contains(cursor_pos)

class InsertPos(object):

    __slots__ = ('index', 'topPoint', 'bottomPoint', 'ready', 'line', 'not_used', 'intersection_point', 'distance_to_cursor')

    def __init__(self, i, topPoint, bottomPoint):
        super().__init__()
        self.index = i
        self.topPoint = topPoint
        self.bottomPoint = bottomPoint
        self.ready = False
        self.not_used = False
        self.line = QLineF(self.topPoint, self.bottomPoint)

def defineInsertPositions(self, clear=False):
    ips = self.front_tracker_insert_positions
    self.front_tracker_current_group_insert_pos = None
    ips.clear()
    if self.front_tracker_captured_group and not clear:
        group = self.front_tracker_captured_group
        groups = self.front_tracker_data_groups

        group_index = groups.index(group)

        # первые n позиций
        for i, gr in enumerate(groups):
            ip = InsertPos(i, gr.ui_rect.topLeft(), gr.ui_rect.bottomLeft())
            ips.append(ip)

        # n+1 позиция
        ip = InsertPos(i+1, gr.ui_rect.topRight(), gr.ui_rect.bottomRight())
        ips.append(ip)

        pos = self.mapFromGlobal(QCursor().pos())
        hor_line = QLineF(self.rect().topLeft(), self.rect().topRight())
        hor_line.translate(0, pos.y())

        for ip in ips:
            isp = ip.line.intersects(hor_line)
            isp = isp[1]
            ip.intersection_point = isp
            ip.distance_to_cursor = QVector2D(pos - isp).length()
            if ip.index in [group_index, group_index + 1]:
                ip.not_used = True

        ips = list(sorted(ips, key=lambda x: x.distance_to_cursor))
        if ips:
            _ip = ips[0]
            _ip.ready = True
            self.front_tracker_current_group_insert_pos = _ip
        else:
            self.front_tracker_current_group_insert_pos = None


        data = (hor_line, )
        return data

def check_exclude(obj_name, files_to_exclude):
    b1 = obj_name in files_to_exclude
    b2 = False
    for line in files_to_exclude:
        if obj_name.lower().startswith(line.lower()):
            b2 = True
            # print(f'{line}, {obj_name}')
            break
    return not (b1 or b2)

def openTaskInSublimeText(self, task):
    exe_filepath = self.front_tracker_sublime_text_filepath
    filepath = task.channel.group.filepath
    filepath_num = f"{filepath}:{task.start_line_number}"
    subprocess.Popen([exe_filepath, filepath_num])

def rescanData(self):
    preparePluginBoard(self, None, rescan=True)

def implantToContextMenu(self, contextMenu):
    if self.front_tracker_task_under_mouse:
        contextMenu.addSeparator()
        task = self.front_tracker_task_under_mouse
        open_task = contextMenu.addAction('Front Tracker: Open task in Sublime Text')
        open_task.triggered.connect(partial(openTaskInSublimeText, self, task))

    rescan = contextMenu.addAction('Front Tracker: Rescan')
    rescan.triggered.connect(partial(rescanData, self))

def contextMenu(self, event, contextMenu, checkboxes):
    # self.board_contextMenuDefault(event, contextMenu, checkboxes)
    implantToContextMenu(self, contextMenu)
    self.board_ContextMenuPluginsDefault(event, contextMenu)

def find_sublime_text_exe_filepath(self):
    if self.front_tracker_sublime_text_filepath is None:
        filepath =_utils.find_exe_file_in_opened_processes(exe_filename='sublime_text.exe')
        self.front_tracker_sublime_text_filepath = filepath
    return self.front_tracker_sublime_text_filepath

def restart_buffer_timer(self, callback):
    if self.front_tracker_buffer_timer is not None:
        self.front_tracker_buffer_timer.stop()

    self.front_tracker_buffer_timer = timer = QTimer()
    timer.setInterval(300)
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.start()

def keyPressEvent(self, event):
    self.board_keyPressEventDefault(event)

def keyReleaseEvent(self, event):
    if event.key() == Qt.Key_K:
        callback = partial(print, 'test')
        restart_buffer_timer(self, callback)
    else:
        self.board_keyReleaseEventDefault(event)

def watcherFileChangedFiltered(self):
    buffer = self.front_tracker_path_buffer
    buffer = list(set(buffer))
    print(buffer)
    self.front_tracker_path_buffer = []

def _watcherFileChanged(self, path):
    # Sublime Text сохраняет файл по-разному:
    # 1) может сразу сохранить файл или 2) может сначала сохранить его с нулевым размером, а потом уже сохранить с контентом.
    # Во втором случае уведомление присылается два раза, но желательно избежать реакции на каждое из них,
    # прореагировав только на последнее. Для этого приходится заводить одноразовый таймер и сбрасывать его при необходимости.
    self.front_tracker_path_buffer.append(path)
    restart_buffer_timer(self, partial(watcherFileChangedFiltered, self))
    # print(f'watcher: {path} {time.time()}')

def preparePluginBoard(self, plugin_info, rescan=False):
    cf = self.LibraryData().current_folder()
    board = cf.board

    self.front_tracker_data_groups = []
    if not rescan:
        self.front_tracker_sublime_text_filepath = None
        self.front_tracker_watcher = QFileSystemWatcher(self)

    watcher_files = self.front_tracker_watcher.files()
    if watcher_files:
        self.front_tracker_watcher.removePaths(watcher_files)

    self.front_tracker_path_buffer = []

    self.front_tracker_channel_under_mouse = None
    self.front_tracker_group_under_mouse = None
    self.front_tracker_task_under_mouse = None

    self.front_tracker_buffer_timer = None

    self.front_tracker_captured_group = None
    self.front_tracker_captured_channel = None
    self.front_tracker_insert_positions = []

    exts = ('.txt', '.md')
    exts = ('.txt')
    folders_to_scan_filepath = self.get_boards_user_data_filepath('front_tracker.data.txt')

    with self.show_longtime_process_ongoing(self, 'Загрузка данных'):


        all_files_paths = []
        all_folders_paths = []
        files_to_exclude = []

        with open(folders_to_scan_filepath, 'r', encoding='utf8') as file:
            data = file.read()
            paths = data.split("\n")
            for path in paths:
                if os.path.isfile(path):
                    all_files_paths.append(path)
                elif os.path.isdir(path):
                    all_folders_paths.append(path)
                elif path.startswith("~"):
                    path = path[1:]
                    files_to_exclude.append(path)

        for path in all_folders_paths:
            if os.path.exists(path):
                for obj_name in os.listdir(path):
                    obj_path = os.path.join(path, obj_name)
                    if os.path.isfile(obj_path) and obj_name.lower().endswith(exts) and check_exclude(obj_name, files_to_exclude):
                        all_files_paths.append(obj_path)
            else:
                self.show_center_label(f'Путь {path} не найден в файловой системе!', error=True)

        for filepath in all_files_paths:
            self.front_tracker_data_groups.append(Group(filepath))

        self.front_tracker_watcher.addPaths(all_files_paths)

    if not rescan:
        find_sublime_text_exe_filepath(self)
        self.front_tracker_watcher.fileChanged.connect(partial(_watcherFileChanged, self))
        self.board_origin = QPointF(500, 250)

        self.diagonal_lines_br = diagonal_lines_br = QBrush()
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.transparent)
        painter_ = QPainter()
        painter_.begin(pixmap)
        painter_.setOpacity(0.1)
        painter_.fillRect(pixmap.rect(), Qt.gray)
        painter_.setBrush(QBrush(QColor(200, 200, 200)))
        painter_.setPen(Qt.NoPen)
        w = pixmap.width()
        path = QPainterPath()
        path.moveTo(w*0.0, w*0.0)
        path.lineTo(w*0.25, w*0.0)
        path.lineTo(w*1.0, w*0.75)
        path.lineTo(w*1.0, w*1.0)
        path.lineTo(w*0.75, w*1.0)
        path.lineTo(w*0.0, w*0.25)
        painter_.drawPath(path)
        path = QPainterPath()
        path.moveTo(w*0.0, w*0.75)
        path.lineTo(w*0.0, w*1.0)
        path.lineTo(w*0.25, w*1.0)
        painter_.drawPath(path)
        path = QPainterPath()
        path.moveTo(w*0.75, w*0.0)
        path.lineTo(w*1.0, w*0.0)
        path.lineTo(w*1.0, w*0.25)
        painter_.drawPath(path)
        painter_.end()
        diagonal_lines_br.setTexture(pixmap)



    self.update()





def register(board_obj, plugin_info):
    plugin_info.name = 'FRONT TRACKER'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

    plugin_info.wheelEvent = wheelEvent

    plugin_info.mouseDoubleClickEvent = mouseDoubleClickEvent

    plugin_info.keyPressEvent = keyPressEvent
    plugin_info.keyReleaseEvent = keyReleaseEvent

    plugin_info.contextMenu = contextMenu


if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
