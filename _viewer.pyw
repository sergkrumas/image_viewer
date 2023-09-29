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

import pureref, tagging, help_text

from library_data import (LibraryData, FolderData, ImageData, LibraryModeImageColumn,
                                                                            ThumbnailsThread)
import comments


from pixmaps_generation import generate_pixmaps
from settings_handling import SettingsWindow
from control_panel import ControlPanel
from app_copy_prevention import ServerOrClient

from win32con import VK_CAPITAL, VK_NUMLOCK, VK_SCROLL
from ctypes import windll

import itertools

try:
    noise = __import__("noise")
except:
    noise = None


class Globals():
    is_32bit_exe = platform.architecture()[0] == '32bit'
    main_window = None
    control_panel = None
    DEFAULT_THUMBNAIL = None
    FAV_BIG_ICON = None
    ERROR_PREVIEW_PIXMAP = None
    lite_mode = False # лайтовый (упрощённый) режим работы приложения
    force_full_mode = False # обычный режим со всеми фичами без ограничений
    do_not_show_start_dialog = False
    NO_SOCKETS_SERVER_FILENAME = "server.data"
    NO_SOCKETS_CLIENT_DATA_FILENAME = "dat.data"

    THUMBNAIL_WIDTH = 50
    AUGMENTED_THUBNAIL_INCREMENT = 20
    PREVIEW_WIDTH = 200
    USE_SOCKETS = True
    DEBUG = True

    VIEW_HISTORY_SIZE = 20

    is_path_exists = False

    AFTERCRASH = False
    CRASH_SIMULATOR = True

    USE_GLOBAL_LIST_VIEW_HISTORY = False

    started_from_sublime_text = False

    SECRET_HINTS_FILEPATH = "deep_secrets.txt"
    SESSION_FILENAME = "session.txt"
    FAV_FILENAME = "fav.txt"
    COMMENTS_FILENAME = "comments.txt"
    PUREREF_BOARDS_ROOT = "pureref_boards"
    TAGS_ROOT = "tags"
    USERROTATIONS_FILENAME = "viewer.ini"
    DEFAULT_PATHS_FILENAME = "default_paths.txt"

    MULTIROW_THUMBNAILS_PADDING = 30

    NULL_PIXMAP = None

    app_title = "Krumassan Image Viewer v0.90 Alpha by Sergei Krumas"
    github_repo = "https://github.com/sergkrumas/image_viewer"


class MainWindow(QMainWindow, UtilsMixin):

    UPPER_SCALE_LIMIT = 100.0
    LOWER_SCALE_LIMIT = 0.01
    BOTTOM_PANEL_HEIGHT = 160 - 40
    LIMIT_SECONDS = 1.1
    CORNER_BUTTON_RADIUS = 50

    LIBRARY_FOLDER_ITEM_HEIGHT = 140
    TOP_FIELD_HEIGHT = BOTTOM_FIELD_HEIGHT = 0

    hint_text = ""
    secret_hints_list = []

    START_HINT_AT_SCALE_VALUE = 40.0

    secret_pic = None
    secret_p = None

    LOADING_MULT = 1 #5

    LOADING_TEXT = (
        "ЗАГРУЗКА",       # RU
        "LADE DATEN",     # DE
        "CHARGEMENT",     # FR
        "CARICAMENTO",    # IT
        "LOADING",        # EN
        "CARGANDO",       # ES
    )*LOADING_MULT

    class pages():
        START_PAGE = 'STARTPAGE'
        VIEWER_PAGE = 'VIEWERPAGE'
        PUREREF_PAGE = 'PUREREFPAGE'
        LIBRARY_PAGE = 'LIBRARYPAGE'

        @classmethod
        def all(cls):
            return [
                cls.START_PAGE,
                cls.VIEWER_PAGE,
                cls.PUREREF_PAGE,
                cls.LIBRARY_PAGE
            ]

    class label_type():
        FRAME_NUMBER = 'FRAMENUMBER'
        PLAYSPEED = 'PLAYSPEED'
        SCALE = 'SCALE'

        @classmethod
        def all(cls):
            return [
                cls.FRAME_NUMBER,
                cls.PLAYSPEED,
                cls.SCALE,
            ]

    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasImage():
            event.accept()
        else:
            event.ignore()

    # def dragMoveEvent(self, event):
    #     if event.mimeData().hasUrls():
    #         event.setDropAction(Qt.CopyAction)
    #         event.accept()
    #     else:
    #         event.ignore()

    def dropEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasImage():
            image = QImage(event.mimeData().imageData())
            image.save("data.png")
        elif event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

            paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = str(url.toLocalFile())
                    # if not os.path.isdir(path):
                    #     path = os.path.dirname(path)
                    paths.append(path)
                else:
                    print(url.url())
            all_but_last = paths[:-1]
            last_path = paths[-1:]
            to_print = f'Drop Event Data {paths}'
            print(to_print)
            for path in all_but_last:
                LibraryData().handle_input_data(path, pre_load=True)
            for path in last_path:
                LibraryData().handle_input_data(path)
            self.update()
        else:
            event.ignore()

    def update_threads_info(self, data):
        if data:
            done = data.current == data.count
            self.threads_info[data.id] = (done, f"{data.current}/{data.count} {data.ui_name}")
        self.update()

    def over_corner_button(self, corner_attr="topRight", big=False):
        btn_rect = self.get_corner_button_rect(corner_attr=corner_attr, big=big)
        top_right_corner = getattr(self.rect(), corner_attr)()
        diff = top_right_corner - self.mapped_cursor_pos()
        distance = math.sqrt(pow(diff.x(), 2) + pow(diff.y(), 2))
        client_area = self.rect().intersected(btn_rect)
        n = 4 if big else 1
        case1 = distance < self.CORNER_BUTTON_RADIUS*n
        case2 = client_area.contains(self.mapped_cursor_pos())
        return case2 and case1

    def handle_menu_item_click(self):
        curpos = self.mapFromGlobal(QCursor().pos())
        for page, rect in self.corner_menu_items:
            if rect.contains(curpos):
                self.change_page(page)

    def over_corner_menu_item(self, corner_attr="topRight"):
        curpos = self.mapFromGlobal(QCursor().pos())
        for page, rect in self.corner_menu_items:
            if rect.contains(curpos):
                return True
        return False

    def over_corner_menu(self, corner_attr="topRight"):
        return self.over_corner_button(corner_attr=corner_attr, big=True)

    def get_corner_button_rect(self, corner_attr="topRight", big=False):
        top_right_corner = getattr(self.rect(), corner_attr)()
        n = 4 if big else 1
        radius = self.CORNER_BUTTON_RADIUS*n
        btn_rect = QRectF(
            top_right_corner.x() - radius,
            top_right_corner.y() - radius,
            radius*2,
            radius*2,
        ).toRect()
        return btn_rect

    def draw_corner_button(self, painter, corner_attr="topRight"):
        btn_rect = self.get_corner_button_rect(corner_attr=corner_attr)
        top_right_corner = getattr(self.rect(), corner_attr)()
        diff = top_right_corner - self.mapped_cursor_pos()

        if self.over_corner_button(corner_attr=corner_attr):
            painter.setOpacity(.6)
        else:
            painter.setOpacity(.3)

        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(btn_rect)

        # код для отрисовки креста правой кнопки
        _value = self.CORNER_BUTTON_RADIUS/2-5
        cross_pos = top_right_corner + QPointF(-_value, _value).toPoint()

        painter.setPen(QPen(Qt.white, 4, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.white, Qt.SolidPattern))
        painter.setOpacity(1.0)
        _value = int(self.CORNER_BUTTON_RADIUS/8)
        painter.drawLine(
            cross_pos.x()-_value,
            cross_pos.y()-_value,
            cross_pos.x()+_value,
            cross_pos.y()+_value
        )
        painter.drawLine(
            cross_pos.x()+_value,
            cross_pos.y()-_value,
            cross_pos.x()-_value,
            cross_pos.y()+_value
        )

        oldfont = painter.font()
        font = QFont(painter.font())
        font.setPixelSize(20)
        font.setWeight(1900)
        painter.setFont(font)
        # код для отрисовки угловой кнопки
        corner_char = self.current_page[0]
        r = QRect(QPoint(0, 0), btn_rect.bottomRight()-QPoint(20, 20))
        painter.drawText(r, Qt.AlignBottom | Qt.AlignRight, corner_char)
        painter.setFont(oldfont)

    def draw_corner_menu(self, painter, corner_attr="topRight"):
        self.corner_menu_items = []

        btn_rect = self.get_corner_button_rect(corner_attr=corner_attr, big=True)
        top_right_corner = getattr(self.rect(), corner_attr)()
        diff = top_right_corner - self.mapped_cursor_pos()

        if self.over_corner_button(corner_attr=corner_attr):
            self.corner_menu[corner_attr] = True
        elif not self.over_corner_button(corner_attr=corner_attr, big=True):
            self.corner_menu[corner_attr] = False

        if self.corner_menu.get(corner_attr, False):
            painter.setOpacity(.5)
        else:
            # painter.setOpacity(.0)
            return

        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(btn_rect)

        painter.setOpacity(.8)

        points = []
        r = self.CORNER_BUTTON_RADIUS*3
        for i in range(3):
            degree90 = math.pi/2
            step = degree90*1/3
            angle = step*i
            add = step/2
            # add = step/4
            x = r*math.cos(angle+add)
            y = r*math.sin(angle+add)
            point = QPointF(x, y).toPoint()
            points.append(point)

        painter.setPen(QPen(Qt.white, 5))
        painter.setBrush(Qt.NoBrush)

        oldfont = painter.font()
        font = QFont(painter.font())
        font.setPixelSize(20)
        font.setWeight(1900)
        painter.setFont(font)

        pages = self.pages.all()
        pages.remove(self.current_page)
        points = reversed(points)

        for page, point in zip(pages, points):
            # painter.drawPoint(point)
            # код для отрисовки угловой кнопки
            r = QRect(QPoint(0, 0), QPoint(50, 30))
            r.moveCenter(point)
            self.corner_menu_items.append((page, r))

            cursor_pos = self.mapFromGlobal(QCursor().pos())
            if r.contains(cursor_pos):
                painter.setOpacity(1.0)
                label_rect = QRect(r.topLeft(), r.bottomRight() + QPoint())
                label_rect.setWidth(200)
                text = page
                text_rect = label_rect
            else:
                painter.setOpacity(.8)
                text = page[0]
                text_rect = r
            # painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, text)
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

        painter.setFont(oldfont)

        painter.setOpacity(1.0)

    def prepare_secret_hints(self):
        if not self.secret_hints_list:
            data = ""
            root = os.path.dirname(__file__)
            filepath = os.path.join(root, "user_data", Globals.SECRET_HINTS_FILEPATH)
            create_pathsubfolders_if_not_exist(os.path.dirname(filepath))
            out = []
            if os.path.exists(filepath):
                with open(filepath, encoding="utf8") as file:
                    data = file.read()
                for data_item in data.split("\n\n"):
                    data_item = data_item.strip()
                    if data_item:
                        out.append(data_item)
            self.secret_hints_list = out

    def activate_or_reset_secret_hint(self):
        if not self.secret_hints_list:
            raise "no data"
        if not self.STNG_show_deep_secrets_at_zoom:
            return

        if self.image_scale > self.START_HINT_AT_SCALE_VALUE:
            if not self.hint_text:
                rect = self.rect()
                self.hint_text = random.choice(self.secret_hints_list)

                self.secret_width = rect.width()
                self.secret_height = rect.height()

                w1 = self.secret_width/2
                w2 = self.secret_height/2
                self.hint_center_position = QPointF(w1, w2).toPoint()

                self.secret_pic = QPixmap(self.secret_width, self.secret_height)
                self.secret_p = QPainter()
                self.secret_p.begin(self.secret_pic)
                font = self.secret_p.font()
                font.setPixelSize(30)
                font.setWeight(1900)
                self.secret_p.setPen(QPen(Qt.white))
                self.secret_p.setFont(font)
                r = QRect(0, 0, self.secret_width, self.secret_height)
                self.secret_p.drawText(r, Qt.AlignCenter | Qt.TextWordWrap | Qt.AlignHCenter, self.hint_text)
                self.secret_p.end()

        if self.image_scale < self.START_HINT_AT_SCALE_VALUE:
            if self.hint_text:
                self.hint_text = ""
                self.hint_center_position = QPoint(0, 0)

    def draw_secret_hint(self, painter):
        if not self.secret_hints_list:
            raise "no data"

        if not self.hint_text:
            return

        if not self.frameless_mode:
            return

        a = max(self.START_HINT_AT_SCALE_VALUE, self.image_scale)-self.START_HINT_AT_SCALE_VALUE
        b = 100.0 - self.START_HINT_AT_SCALE_VALUE
        factor = a/b
        START_VALUE = 0.0
        END_VALUE = 0.5
        painter.setOpacity(START_VALUE+factor*(END_VALUE-START_VALUE))

        hint_rect = self.get_secret_hint_rect()
        painter.drawPixmap(hint_rect, self.secret_pic, QRectF(self.secret_pic.rect()))
        painter.setOpacity(1.0)

    def set_window_title(self, text):
        if text:
            self.setWindowTitle(f"{text} - {Globals.app_title}")
        else:
            self.setWindowTitle(f"{Globals.app_title}")

    def toggle_stay_on_top(self):
        if not self.frameless_mode:
            self.stay_on_top = not self.stay_on_top
            self.set_window_style()
            self.show()

    def __init__(self, *args, frameless_mode=True, **kwargs):
        self.frameless_mode = frameless_mode
        self.stay_on_top = False
        self.handling_input = False

        if SettingsWindow.get_setting_value("hide_on_app_start"):
            self.need_for_init_after_call_from_tray = True
        else:
            self.need_for_init_after_call_from_tray = False
        super().__init__(*args, **kwargs)

        self.set_loading_text()

        self.prepare_secret_hints()

        self.set_window_title("")
        self.set_window_style()

        self.current_page = self.pages.VIEWER_PAGE

        self.transformations_allowed = True
        self.animated = False
        self.image_translating = False
        self.image_center_position = QPointF(0, 0)
        self.image_rotation = 0
        self.image_scale = 1.0

        self.pixmap = None

        self.threads_info = {}

        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)

        self.secret_width = 0
        self.secret_height = 0

        self.movie = None
        self.invalid_movie = False

        self.CENTER_LABEL_TIME_LIMIT = 2
        self.center_label_time = time.time() - self.CENTER_LABEL_TIME_LIMIT - 1
        self.center_label_info_type = self.label_type.SCALE
        self.center_label_error = False

        SettingsWindow.settings_init(self)

        self.setMouseTracking(True)
        self.installEventFilter(self)
        self.setAcceptDrops(True)

        self.previews_list_active_item = None
        self.previews_list = None

        self.region_zoom_in_init()

        self.contextMenuActivated = False

        self.help_infopanel = False

        self.error = False

        self.invert_image = False

        self.animation_tasks = []
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(20)
        self.animation_timer.timeout.connect(self.do_properties_animation_on_timer)
        self.animation_timer_work_timestamp = time.time()

        self.block_paginating = False

        self.hint_center_position = QPoint(0, 0)

        self._key_pressed = False
        self._key_unreleased = False

        self.two_monitors_wide = False

        self.left_button_pressed = False

        self.comment_data = None
        self.comment_data_candidate = None

        self.noise_time = 0.0

        self.image_rect = QRectF()

        self.corner_menu = dict()
        self.corner_menu_items = []

        self.context_menu_stylesheet = """
        QMenu{
            padding: 0px;
            font-size: 18px;
            font-weight: bold;
            font-family: 'Consolas';
        }
        QMenu::item {
            padding: 10px;
            background: #303940;
            color: rgb(230, 230, 230);
        }
        QMenu::icon {
            padding-left: 15px;
        }
        QMenu::item:selected {
            background-color: rgb(253, 203, 54);
            color: rgb(50, 50, 50);
            border-left: 2px dashed #303940;
        }
        QMenu::separator {
            height: 1px;
            background: gray;
        }
        QMenu::item:checked {
        }
        """

        pureref.init(self)
        tagging.init(self)

    # def changeEvent(self, event):
    #     if event.type() == QEvent.WindowStateChange:
    #         if self.windowState() & Qt.WindowMaximized:
    #             self.frameless_mode = True
    #             self.set_window_style()
    #         else:
    #             self.frameless_mode = True
    #             self.set_window_style()

    def is_viewer_page_active(self):
        return self.current_page == self.pages.VIEWER_PAGE

    def is_library_page_active(self):
        return self.current_page == self.pages.LIBRARY_PAGE

    def is_start_page_active(self):
        return self.current_page == self.pages.START_PAGE

    def is_pureref_page_active(self):
        return self.current_page == self.pages.PUREREF_PAGE

    def cycle_change_page(self):
        pages = self.pages.all()
        pages_shifted = self.pages.all()
        pages_shifted.append(pages_shifted.pop(0))
        for page, next_page in itertools.cycle(zip(pages, pages_shifted)):
            if page == self.current_page:
                break
        self.change_page(next_page)

    def change_page(self, requested_page):
        # if self.is_viewer_page_active() and page == self.pages.LIBRARY_PAGE:
        #     self.prepare_library_page()
        # if self.is_library_page_active() and page == self.pages.VIEWER_PAGE:
        #     self.prepare_viewer_page()
        CP = Globals.control_panel

        def cancel_fullscreen_on_control_panel():
            if CP is not None:
                if CP.fullscreen_flag:
                    CP.do_toggle_fullscreen()


        if self.current_page == requested_page:
            return

        if self.handling_input:
            return

        if self.current_page == self.pages.VIEWER_PAGE:
            self.region_zoom_in_cancel()
            LibraryData().before_current_image_changed()
            cancel_fullscreen_on_control_panel()

        elif self.current_page == self.pages.PUREREF_PAGE:
            cancel_fullscreen_on_control_panel()
            LibraryData().save_board_data()



        if requested_page == self.pages.LIBRARY_PAGE:
            LibraryData().update_current_folder_columns()
            self.autoscroll_set_or_reset()
            Globals.control_panel.setVisible(False)
            self.previews_list_active_item = None
            for folder_data in LibraryData().folders:
                images_data = folder_data.images_list
                ThumbnailsThread(folder_data, Globals, run_from_library=True).start()
            self.transformations_allowed = False

        elif requested_page == self.pages.VIEWER_PAGE:
            self.viewer_reset() # для показа сообщения о загрузке
            LibraryData().after_current_image_changed()
            Globals.control_panel.setVisible(True)
            LibraryData().add_current_image_to_view_history()
            cf = LibraryData().current_folder()
            ThumbnailsThread(cf, Globals).start()
            self.transformations_allowed = True

        elif requested_page == self.pages.START_PAGE:
            Globals.control_panel.setVisible(False)
            self.transformations_allowed = False

        elif requested_page == self.pages.PUREREF_PAGE:
            Globals.control_panel.setVisible(True)
            self.transformations_allowed = True
            LibraryData().load_board_data()



        if self.current_page == self.pages.START_PAGE and requested_page == self.pages.VIEWER_PAGE:
            self.restore_image_transformations()

        self.current_page = requested_page

    def interpolate_values(self, start_value, end_value, factor):
        if isinstance(start_value, (float, int)):
            value = fit(factor, 0.0, 1.0, start_value, end_value)
        elif isinstance(start_value, QPoint):
            value_x = fit(factor, 0.0, 1.0, start_value.x(), end_value.x())
            value_y = fit(factor, 0.0, 1.0, start_value.y(), end_value.y())
            value = QPoint(int(value_x), int(value_y))
        elif isinstance(start_value, QPointF):
            value_x = fit(factor, 0.0, 1.0, start_value.x(), end_value.x())
            value_y = fit(factor, 0.0, 1.0, start_value.y(), end_value.y())
            value = QPointF(float(value_x), float(value_y))
        elif isinstance(start_value, QRect):
            value_x = fit(factor, 0.0, 1.0, start_value.left(), end_value.left())
            value_y = fit(factor, 0.0, 1.0, start_value.top(), end_value.top())
            value_r = fit(factor, 0.0, 1.0, start_value.right(), end_value.right())
            value_b = fit(factor, 0.0, 1.0, start_value.bottom(), end_value.bottom())
            value = QRect(QPoint(int(value_x), int(value_y)), QPoint(int(value_r), int(value_b)))
        elif isinstance(start_value, QRectF):
            value_x = fit(factor, 0.0, 1.0, start_value.left(), end_value.left())
            value_y = fit(factor, 0.0, 1.0, start_value.top(), end_value.top())
            value_r = fit(factor, 0.0, 1.0, start_value.right(), end_value.right())
            value_b = fit(factor, 0.0, 1.0, start_value.bottom(), end_value.bottom())
            value = QRectF(QPointF(value_x, value_y), QPointF(value_r, value_b))
        elif isinstance(start_value, QColor):
            value_r = fit(factor, 0.0, 1.0, start_value.red(), end_value.red())
            value_g = fit(factor, 0.0, 1.0, start_value.green(), end_value.green())
            value_b = fit(factor, 0.0, 1.0, start_value.blue(), end_value.blue())
            value = QColor(int(value_r), int(value_g), int(value_b))
        else:
            raise Exception("type of 'start_value' is ", type(start_value))
        return value

    def get_animation_task_class(self):

        class AnimationTask(QTimer):
            def __init__(self, parent, anim_id, is_task_new, easing, duration, anim_tracks, callback_on_finish, callback_on_start):
                super().__init__()

                self.main_window = parent
                self.anim_id = anim_id
                self.anim_tracks = anim_tracks
                self.is_task_new = is_task_new
                self.easing = easing
                self.on_finish_animation_callback = callback_on_finish
                self.on_start_animation_callback = callback_on_start
                self.animation_duration = duration

                self._at_first_step = False
                self.animation_allowed = True

                self.main_window.animation_tasks.append(self)

            def evaluation_step(self):

                if not self.animation_allowed:
                    return
                if not self._at_first_step:
                    self.at_start_timestamp = time.time()
                    self._at_first_step = True
                    if self.on_start_animation_callback:
                        self.on_start_animation_callback()
                    if self.is_task_new:
                        old_anim_tracks = self.anim_tracks[:]
                        self.anim_tracks.clear()
                        # обновление значений на текущие, ведь удалённый ранее таймер с тем же anim_id уже изменил текущее значение
                        for attr_host, attr_name, start_value, end_value, callback_func in old_anim_tracks:
                            start_value = getattr(attr_host, attr_name)
                            self.anim_tracks.append((attr_host, attr_name, start_value, end_value, callback_func))

                t = fit(
                    time.time(),
                    self.at_start_timestamp,
                    self.at_start_timestamp + self.animation_duration,
                    0.0,
                    1.0
                )
                factor = self.easing.valueForProgress(min(1.0, max(0.0, t)))
                for attr_host, attr_name, start_value, end_value, callback_func in self.anim_tracks:
                    value = self.main_window.interpolate_values(start_value, end_value, factor)
                    setattr(attr_host, attr_name, value)
                    callback_func()
                if self.animation_duration < (time.time() - self.at_start_timestamp):
                    if self.on_finish_animation_callback:
                        self.on_finish_animation_callback()
                    self.animation_allowed = False
                    self.main_window.animation_tasks.remove(self)
                    print("animation task closed")

        return AnimationTask

    def do_properties_animation_on_timer(self):
        for animation_task in self.animation_tasks:
            animation_task.evaluation_step()
            self.animation_timer_work_timestamp = time.time()
        if time.time() - self.animation_timer_work_timestamp > 10.0:
            print("animation timer stopped")
            self.animation_timer.stop()

    def animate_properties(self, anim_tracks, anim_id=None, callback_on_finish=None, callback_on_start=None, duration=0.2, easing=QEasingCurve.OutCubic):
        AnimationTask = self.get_animation_task_class()
        is_task_new = False
        if anim_id is not None:
            for anim_task in self.animation_tasks[:]:
                if anim_task.anim_id == anim_id:
                    anim_task.stop()
                    anim_task.animation_allowed = False
                    # if anim_task in self.animation_tasks:
                    self.animation_tasks.remove(anim_task)
                    is_task_new = True
        animation_task = AnimationTask(self, anim_id, is_task_new, QEasingCurve(easing), duration, anim_tracks, callback_on_finish, callback_on_start)
        animation_task.evaluation_step() # first call before timer starts!
        self.animation_timer.start()

    def update_thumbnails_row_relative_offset(self, folder_data, only_set=False):

        if folder_data is None:
            folder_data = LibraryData().current_folder()

        THUMBNAIL_WIDTH = Globals.THUMBNAIL_WIDTH
        before_index = folder_data.before_index
        new_index = folder_data.get_current_index()

        now_offset = folder_data.relative_thumbnails_row_offset_x

        before_offset = -THUMBNAIL_WIDTH*before_index
        new_offset = -THUMBNAIL_WIDTH*new_index
        if self.isThumbnailsRowSlidingAnimationEffectAllowed() and (not only_set) and (not now_offset == new_offset):
            self.animate_properties(
                [
                    (folder_data, "relative_thumbnails_row_offset_x", before_offset, new_offset, Globals.control_panel.update),
                ],
                anim_id="thumbnails_row",
                duration=0.8,
                # easing=QEasingCurve.OutQuad
                # easing=QEasingCurve.OutQuart
                # easing=QEasingCurve.OutQuint
                easing=QEasingCurve.OutCubic
            )
        else:
            relative_offset_x = -THUMBNAIL_WIDTH*new_index
            folder_data.relative_thumbnails_row_offset_x = relative_offset_x

    def region_zoom_in_init(self, full=True):
        self.input_rect = None
        self.projected_rect = None
        self.orig_scale = None
        self.orig_pos = None
        self.zoom_region_defined = False
        self.zoom_level = 1.0
        self.region_zoom_in_input_started = False
        self.input_rect_animated = None
        if full:
            self.region_zoom_break_activated = False

    def region_zoom_in_cancel(self):
        if self.input_rect:
            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "image_center_position", self.image_center_position, self.orig_pos, self.update),
                        (self, "image_scale", self.image_scale, self.orig_scale, self.update)
                    ],
                    anim_id="region_zoomn",
                    duration=0.4,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.image_scale = self.orig_scale
                self.image_center_position = self.orig_pos
            self.region_zoom_in_init()
            self.update()
            self.show_center_label(self.label_type.SCALE)
            # self.setCursor(Qt.ArrowCursor)

    def build_input_rect(self):
        if self.INPUT_POINT1 and self.INPUT_POINT2:
            self.input_rect = build_valid_rect(self.INPUT_POINT1, self.INPUT_POINT2)
            self.projected_rect = fit_rect_into_rect(self.input_rect, self.rect())
            w = self.input_rect.width() or self.projected_rect.width()
            self.zoom_level = self.projected_rect.width()/w
            self.input_rect_animated = self.input_rect

    def do_region_zoom(self):
        if self.input_rect.width() != 0:
            # scale = 1/self.image_scale

            # 0. подготовка
            input_center = self.input_rect.center()
            self.input_rect_animated = QRect(self.input_rect)
            before_pos = QPointF(self.image_center_position)
            image_center = QPointF(self.image_center_position)

            # 1. сдвинуть изображение так, чтобы позиция input_center оказалась в центре окна
            diff = self.rect().center() - input_center
            pos = self.image_center_position + diff
            self.image_center_position = pos

            # 2. увеличить относительно центра окна на factor с помощью функции
            # которая умеет увеличивать масштаб
            factor = self.projected_rect.width()/self.input_rect.width()
            scale, center_pos = self.do_scale_image(1.0, override_factor=factor)

            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "image_center_position", before_pos, center_pos, self.update),
                        (self, "image_scale", self.image_scale, scale, self.update),
                        (self, "input_rect_animated", self.input_rect_animated, self.projected_rect, self.update)
                    ],
                    anim_id="region_zoom",
                    duration=0.8,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.image_center_position = center_pos
                self.image_scale = scale
            self.show_center_label(self.label_type.SCALE)

    def region_zoom_in_mousePressEvent(self, event):
        if not self.zoom_region_defined:
            self.region_zoom_in_input_started = True
            self.INPUT_POINT1 = event.pos()
            self.input_rect = None
            self.orig_scale = self.image_scale
            self.orig_pos = self.image_center_position
            # self.setCursor(Qt.CrossCursor)

    def region_zoom_in_UX_breaker_start(self, event):
        if Globals.control_panel:
            if Globals.control_panel.frameGeometry().contains(event.pos()):
                self.region_zoom_in_init(full=False)
                if not self.region_zoom_break_activated:
                    self.region_zoom_break_activated = True
                    pos = self.mapToGlobal(self.INPUT_POINT1)
                    Globals.control_panel.selection_MousePressEvent(event, override=pos)
                else:
                    Globals.control_panel.selection_MouseMoveEvent(event)

    def region_zoom_in_mouseMoveEvent(self, event):
        if (not self.zoom_region_defined) and not self.region_zoom_break_activated:
            self.INPUT_POINT2 = event.pos()
            self.build_input_rect()
            self.region_zoom_in_UX_breaker_start(event)
        if self.region_zoom_break_activated:
            self.region_zoom_in_UX_breaker_start(event)

    def region_zoom_in_mouseReleaseEvent(self, event):
        if (not self.zoom_region_defined) and not self.region_zoom_break_activated:
            self.INPUT_POINT2 = event.pos()
            self.build_input_rect()
            if self.INPUT_POINT1 and self.INPUT_POINT2:
                self.zoom_region_defined = True
                self.do_region_zoom()
            else:
                self.region_zoom_in_cancel()
            self.region_zoom_in_input_started = False

    def region_zoom_in_UX_breaker_finish(self, event):
        if self.region_zoom_break_activated:
            self.region_zoom_break_activated = False
            Globals.control_panel.selection_MouseReleaseEvent(event)
            self.region_zoom_in_init()

    def region_zoom_in_draw(self, painter):
        if self.input_rect:
            painter.setBrush(Qt.NoBrush)
            input_rect = self.input_rect
            projected_rect = self.projected_rect
            # if not self.zoom_region_defined:
            #     painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
            #     painter.drawRect(input_rect)
            painter.setPen(QPen(Qt.white, 1))
            if not self.zoom_region_defined or self.input_rect_animated:
                if True:
                    painter.drawLine(self.input_rect_animated.topLeft(),
                                                                        projected_rect.topLeft())
                    painter.drawLine(self.input_rect_animated.topRight(),
                                                                        projected_rect.topRight())
                    painter.drawLine(self.input_rect_animated.bottomLeft(),
                                                                    projected_rect.bottomLeft())
                    painter.drawLine(self.input_rect_animated.bottomRight(),
                                                                    projected_rect.bottomRight())
                else:
                    painter.drawLine(projected_rect.topLeft(), projected_rect.bottomRight())
                    painter.drawLine(projected_rect.bottomLeft(), projected_rect.topRight())
            if not self.zoom_region_defined:
                value = math.ceil(self.zoom_level*100)
                text = f"{value:,}%".replace(',', ' ')
                font = painter.font()
                font.setPixelSize(14)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, text)
            if self.input_rect_animated:
                painter.drawRect(self.input_rect_animated)
                painter.drawRect(projected_rect)
            if self.zoom_region_defined:
                painter.setOpacity(0.8)
                painter.setClipping(True)
                r = QPainterPath()
                r.addRect(QRectF(self.rect()))
                r.addRect(QRectF(projected_rect))
                painter.setClipPath(r)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(Qt.black))
                painter.drawRect(self.rect())
                painter.setClipping(False)
                painter.setOpacity(1.0)

    def update_for_center_label_fade_effect(self):
        delta = time.time() - self.center_label_time
        if delta < self.CENTER_LABEL_TIME_LIMIT:
            self.update()

    def correct_scale(self):
        # корректировка скейла для всех картинок таким образом
        # чтобы каждая занимала максимум экранного пространства
        # и при этом умещалась полностью независимо от размера
        size_rect = self.get_rotated_pixmap(force_update=True).rect()
        target_rect = self.rect()
        target_rect.adjust(0, 50, 0, -50)
        projected_rect = QRectF(fit_rect_into_rect(size_rect, target_rect))
        self.image_scale = projected_rect.width()/size_rect.width()

    def restore_image_transformations(self, correct=True):
        self.image_rotation = self.image_data.image_rotation
        # self.get_rotated_pixmap(force_update=True)
        self.image_scale = 1.0
        self.image_center_position = self.get_center_position()
        self.hint_center_position = QPoint(0, 0)

        if correct:
            self.correct_scale()

    def generate_info_pixmap(self, label, text, size=1000, no_background=False):

        if not self.image_data.is_supported_filetype:
            if LibraryData.is_text_file(self.image_data.filepath):
                with open(self.image_data.filepath, "rb") as file:
                    text = file.read(500).decode("utf-8", "ignore") + "..."

                    label = ""

        pxm = QPixmap(size, size)
        p = QPainter()
        p.begin(pxm)

        p.setRenderHint(QPainter.HighQualityAntialiasing, True)
        p.fillRect(QRect(0, 0, size, size), QBrush(QColor(0, 0, 0)))

        p.setPen(Qt.NoPen)
        if not no_background:
            gradient = QLinearGradient(QPointF(0, size/2).toPoint(), QPoint(0, size))
            gradient.setColorAt(1.0, Qt.red)
            gradient.setColorAt(0.0, Qt.yellow)
            brush = QBrush(gradient)
            points = QPolygonF([
                QPoint(size//2, size//2),
                QPoint(size//2, size//2) + QPoint(size//40*3, size//8)*1.4,
                QPoint(size//2, size//2) + QPoint(-size//40*3, size//8)*1.4,
            ])
            pp = QPainterPath()
            pp.addPolygon(points)
            p.fillPath(pp, brush)
            p.setBrush(QBrush(Qt.black))
            p.drawRect(size//2-10, size//2-10 + 150, 20, 20)
            points = QPolygonF([
                QPoint(size//2+15, size//2-15 + 60),
                QPoint(size//2-15, size//2-15 + 60),
                QPoint(size//2-10, size//2+75 + 60),
                QPoint(size//2+10, size//2+75 + 60),
            ])
            p.drawPolygon(points)

        p.setPen(QColor(255, 0, 0))
        font = p.font()
        font.setPixelSize(50)
        font.setWeight(1900)
        p.setFont(font)
        r = QRectF(0, size/2, size, size/2).toRect()
        p.drawText(r, Qt.AlignCenter | Qt.TextWordWrap, label.upper())
        p.setPen(QColor(255, 0, 0))
        font = p.font()
        font.setPixelSize(20)
        font.setWeight(100)
        font.setFamily("Consolas")
        p.setFont(font)
        p.setPen(QColor(255, 255, 255))
        p.drawText(QRect(0, 0, size, size-50).adjusted(20, 20, -20, -20), Qt.TextWordWrap, text)

        p.end()
        return pxm

    def is_animated_file_valid(self):
        self.movie.jumpToFrame(0)
        self.animation_stamp()
        fr = self.movie.frameRect()
        if fr.width() == 0 or fr.height() == 0:
            self.invalid_movie = True
            self.error_pixmap_and_reset("Невозможно\nотобразить", "Файл повреждён")

    def show_animated(self, filepath):
        if filepath is not None:
            self.invalid_movie = False
            self.movie = QMovie(filepath)
            self.movie.setCacheMode(QMovie.CacheAll)
            self.image_filepath = filepath
            self.transformations_allowed = True
            self.is_animated_file_valid()
        else:
            if self.movie:
                self.movie.deleteLater()
                self.movie = None

    def animation_stamp(self):
        self.frame_delay = self.movie.nextFrameDelay()
        self.frame_time = time.time()

    def tick_animation(self):
        delta = (time.time() - self.frame_time) * 1000
        is_playing = not self.image_data.anim_paused
        is_animation = self.movie.frameCount() > 1
        if delta > self.frame_delay and is_playing and is_animation:
            self.movie.jumpToNextFrame()
            self.animation_stamp()
            self.frame_delay = self.movie.nextFrameDelay()
            self.pixmap = self.movie.currentPixmap()
            self.get_rotated_pixmap(force_update=True)

    def show_static(self, filepath, pass_=1):
        # pixmap = QPixmap(filepath)
        pixmap = load_image_respect_orientation(filepath)
        if pixmap and not (pixmap.width() == 0 or pixmap.height() == 0):
            self.pixmap = pixmap
            self.image_filepath = filepath
            self.transformations_allowed = True
        else:
            if pass_ == 2:
                raise Exception("Error during openning")
            else:
                # for corrupted instagram .webp files
                to_print = f"trying to convert '{filepath}' ..."
                print(to_print)
                Image.open(filepath).save(filepath)
                self.show_static(filepath, pass_=2)

    def error_pixmap_and_reset(self, title, msg, no_background=False):
        self.error = True
        self.pixmap = self.generate_info_pixmap(title, msg, no_background=no_background)
        self.image_filepath = None
        self.transformations_allowed = False
        self.animated = False
        self.restore_image_transformations(correct=False)

    def viewer_reset(self, simple=False):
        self.pixmap = None
        self.image_filepath = None
        self.transformations_allowed = False
        self.animated = False
        self.svg_rendered = False
        self.rotated_pixmap = None
        self.copied_from_clipboard = False
        self.comment_data = None
        self.comment_data_candidate = None
        self.show_animated(None)
        if not simple:
            self.set_loading_text()
            main_window = Globals.main_window
            main_window.update()
            processAppEvents()

    def set_loading_text(self):
        # self.loading_text = random.choice(self.LOADING_TEXT)
        self.loading_text = "\n".join(self.LOADING_TEXT)

    def show_image(self, image_data, only_set_thumbnails_offset=False):
        # reset
        self.rotated_pixmap = None
        self.image_data = image_data
        self.copied_from_clipboard = False
        filepath = self.image_data.filepath
        self.viewer_reset(simple=True)
        # setting new image
        is_gif_file = lambda fp: fp.lower().endswith(".gif")
        is_webp_file = lambda fp: fp.lower().endswith(".webp")
        is_svg_file = lambda fp: fp.lower().endswith((".svg", ".svgz"))
        is_avif_file = lambda fp: fp.lower().endswith((".avif", ".heif", ".heic"))
        is_supported_file = LibraryData.is_interest_file(filepath)
        self.error = False
        if filepath == "":
            self.error_pixmap_and_reset("Нет изображений", "", no_background=True)
        else:
            if not is_supported_file:
                self.error_pixmap_and_reset("Невозможно\nотобразить",
                                                    "Этот файл не поддерживается")
            else:
                try:
                    _gif_file = is_gif_file(filepath)
                    _webp_animated_file = is_webp_file(filepath)
                    _webp_animated_file = _webp_animated_file and is_webp_file_animated(filepath)
                    if _gif_file or _webp_animated_file:
                        self.show_animated(filepath)
                        self.animated = True
                    elif is_svg_file(filepath):
                        self.image_filepath = filepath
                        self.transformations_allowed = True
                        self.pixmap = load_svg(filepath,
                                                    scale_factor=self.image_data.svg_scale_factor)
                        self.svg_rendered = True
                    else:
                        self.show_static(filepath)
                except:
                    self.error_pixmap_and_reset(
                        "Невозможно отобразить\nподдерживаемый тип файла", traceback.format_exc())
        if not self.error:
            self.read_image_metadata(image_data)
        self.restore_image_transformations()
        self.update_thumbnails_row_relative_offset(image_data.folder_data, only_set=only_set_thumbnails_offset)
        self.set_window_title(self.current_image_details())
        if not self.error:
            comments.check_lost_image_and_update_base(image_data)
        self.update()

    def read_image_metadata(self, image_data):
        if not image_data.image_metadata:
            if SettingsWindow.get_setting_value('show_image_metadata'):
                image_data.image_metadata = read_meta_info(image_data.filepath)
                out = []
                for key, data in dict(image_data.image_metadata).items():
                    data_ = data
                    # if isinstance(data, bytes):
                    #     # data = "BYTES"
                    #     data_ = data.decode('unicode_escape')
                    text = f'{key} : {data_}'
                    out.append(text)
                image_data.image_metadata_info = "\n".join(out)
            else:
                image_data.image_metadata = dict()
                image_data.image_metadata_info = ""

    def current_image_details(self):
        w, h = None, None
        if (self.animated and self.pixmap) or self.pixmap:
            w = self.pixmap.width()
            h = self.pixmap.height()
        if self.animated or self.pixmap:
            name = os.path.basename(self.image_data.filepath)
            if w and h:
                try:
                    n = LibraryData().current_folder()._index + 1
                    l = len(LibraryData().current_folder().images_list)
                    return f"{name} ({w}x{h}) [{n}/{l}]"
                except:
                    pass
            return f"{name} - broken file"
        else:
            return "Загрузка"

    def get_rotated_pixmap(self, force_update=False):
        if self.rotated_pixmap is None or force_update:
            rm = QTransform()
            if not self.error: # не поворачиваем пиксмапы с инфой об ошибке
                rm.rotate(self.image_rotation)
            if self.pixmap is None and self.animated:
                self.pixmap = self.movie.currentPixmap()
            self.rotated_pixmap = self.pixmap.transformed(rm)
        return self.rotated_pixmap

    def get_image_viewport_rect(self, debug=False, od=None):
        im_rect = QRectF()
        if self.pixmap or self.invalid_movie or self.animated:
            if self.pixmap:
                pixmap = self.get_rotated_pixmap()
                orig_width = pixmap.rect().width()
                orig_height = pixmap.rect().height()
            else:
                orig_width = orig_height = 1000
        else:
            orig_width = 0
            orig_height = 0
        im_rect.setLeft(0)
        im_rect.setTop(0)
        if self.error:
            image_scale = 1.0
            self.image_center_position = self.get_center_position()
        else:
            image_scale = self.image_scale
            if od is not None:
                image_scale = od[1]
        new_width = orig_width*image_scale
        new_height = orig_height*image_scale
        icp = self.image_center_position
        if od is not None:
            icp = od[0]
        pos = icp - QPointF(new_width/2, new_height/2)
        if debug:
            to_print = f'{pos} {new_width} {new_height}'
            print(to_print)
        im_rect.moveTo(pos)
        im_rect.setWidth(new_width)
        im_rect.setHeight(new_height)
        return im_rect

    def get_secret_hint_rect(self):
        hint_rect = QRectF()
        # new_width = self.secret_width/20*(self.image_scale - self.START_HINT_AT_SCALE_VALUE)
        # new_height = self.secret_height/20*(self.image_scale - self.START_HINT_AT_SCALE_VALUE)
        new_width = self.secret_width*self.image_scale/100
        new_height = self.secret_height*self.image_scale/100
        pos = self.hint_center_position - QPointF(new_width/2, new_height/2)
        hint_rect.moveTo(pos)
        hint_rect.setWidth(new_width)
        hint_rect.setHeight(new_height)
        return hint_rect

    def resizeEvent(self, event):
        if Globals.control_panel:
            Globals.control_panel.place_and_resize()
        self.image_center_position -= QPointF(
            (event.oldSize().width() - event.size().width())/2,
            (event.oldSize().height() - event.size().height())/2,
        )

        if self.is_library_page_active() or True:
            LibraryData().update_current_folder_columns()

        SettingsWindow.center_if_on_screen()
        comments.CommentWindow.center_if_on_screen()

        self.update()
        # здесь по возможности ещё должен быть и скейл относительно центра.
        # self.update()

    def threads_info_watcher(self):
        keys = []
        for n, item in enumerate(self.threads_info.items()):
            done, string = item[1]
            if done:
                keys.append(item[0])
        for key in keys:
            self.threads_info.pop(key)
        for thread in ThumbnailsThread.threads_pool:
            if thread.isFinished():
                ThumbnailsThread.threads_pool.remove(thread)

    def on_timer(self):
        self.update_for_center_label_fade_effect()
        self.threads_info_watcher()
        if not Globals.USE_SOCKETS:
            ServerOrClient.retrieve_server_data(open_request)
        if self.STNG_show_noise_cells and noise:
            self.noise_time += 0.005
            self.update()
        if self.animated:
            self.tick_animation()

    def is_cursor_over_image(self):
        return self.cursor_in_rect(self.get_image_viewport_rect())

        # event = QKeyEvent(QEvent.KeyRelease, Qt.Key_Tab, Qt.NoModifier, 0, 0, 0)
        # app = QApplication.instance()
        # app.sendEvent(self, event)

    def isLeftClickAndCtrl(self, event):
        return event.buttons() == Qt.LeftButton and event.modifiers() == Qt.ControlModifier

    def isLeftClickAndCtrlShift(self, event):
        return event.buttons() == Qt.LeftButton \
                             and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier)

    def get_comment_rect_info(self):
        rect = build_valid_rect(self.COMMENT_RECT_INPUT_POINT1, self.COMMENT_RECT_INPUT_POINT2)
        im_rect = self.get_image_viewport_rect()
        screen_delta1 = rect.topLeft() - im_rect.topLeft()
        screen_delta2 = rect.bottomRight() - im_rect.topLeft()

        left = screen_delta1.x()/im_rect.width()
        top = screen_delta1.y()/im_rect.height()

        right = screen_delta2.x()/im_rect.width()
        bottom = screen_delta2.y()/im_rect.height()

        return left, top, right, bottom

    def image_comment_mousePressEvent(self, event):
        cf = LibraryData().current_folder()
        ci = cf.current_image()
        if ci:
            self.COMMENT_RECT_INPUT_POINT1 = event.pos()
            self.COMMENT_RECT_INPUT_POINT2 = event.pos()
            if self.comment_data_candidate:
                self.comment_data = self.comment_data_candidate
                self.image_comment_update_rect(event)
            else:
                left, top, right, bottom = self.get_comment_rect_info()
                self.comment_data = comments.CommentData.create_comment(ci, left, top, right, bottom)
        self.update()

    def image_comment_update_rect(self, event):
        if self.comment_data is not None:
            self.COMMENT_RECT_INPUT_POINT2 = event.pos()
            left, top, right, bottom = self.get_comment_rect_info()
            self.comment_data.left = left
            self.comment_data.top = top
            self.comment_data.right = right
            self.comment_data.bottom = bottom
        self.update()

    def image_comment_mouseMoveEvent(self, event):
        self.image_comment_update_rect(event)
        self.update()

    def image_comment_mouseReleaseEvent(self, event):
        self.image_comment_update_rect(event)
        comments.store_comments_list()
        if self.comment_data_candidate is None:
            comments.CommentWindow().show(self.comment_data, 'new')
        self.comment_data = None
        self.comment_data_candidate = None
        self.update()

    def mousePressEventStartPage(self, event):

        if event.button() == Qt.LeftButton:
            path = input_path_dialog("", exit=False)
            if path:
                LibraryData().handle_input_data(path)
                self.update()
        elif event.button() == Qt.RightButton:
            self.open_settings_window()

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            if self.over_corner_button():
                self.require_window_closing()
                return

            elif self.over_corner_button(corner_attr="topLeft"):
                self.cycle_change_page()
                return

            elif self.over_corner_menu(corner_attr="topLeft"):
                self.handle_menu_item_click()
                return




        if self.is_pureref_page_active():
            pureref.mousePressEvent(self, event)

        elif self.is_start_page_active():
            self.mousePressEventStartPage(event)
            self.update()

        elif self.is_library_page_active():
            if self.folders_list:
                for item_rect, item_data in self.folders_list:
                    if item_rect.contains(event.pos()):
                        # здесь устанавливаем текующую папку
                        LibraryData().choose_that_folder(item_data)

            if self.previews_list:
                for item_rect, item_data in self.previews_list:
                    if item_rect.contains(event.pos()):
                        LibraryData().show_that_preview_on_viewer_page(item_data)


        elif self.is_viewer_page_active():
            if self.tagging_overlay_mode:
                tagging.main_mousePressEvent(self, event)
                return

            if event.button() == Qt.LeftButton:
                self.left_button_pressed = True

            if self.isLeftClickAndCtrl(event):
                self.region_zoom_in_mousePressEvent(event)

            elif self.isLeftClickAndCtrlShift(event):
                self.image_comment_mousePressEvent(event)

            if self.transformations_allowed:
                if self.is_cursor_over_image():
                    self.image_translating = True
                    self.oldCursorPos = self.mapped_cursor_pos()
                    self.oldElementPos = self.image_center_position
                    self.update()

            ready_to_view = self.is_viewer_page_active() and not self.handling_input
            cursor_not_over_image = not self.is_cursor_over_image()
            not_ctrl_pressed = not self.isLeftClickAndCtrl(event)

            cases = (
                ready_to_view,
                cursor_not_over_image,
                self.frameless_mode,
                self.STNG_doubleclick_toggle,
                not self.isLeftClickAndCtrl(event),
            )
            if all(cases):
                self.toggle_to_frame_mode()




        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):

        if self.is_pureref_page_active():
            pureref.mouseMoveEvent(self, event)

        elif self.is_start_page_active():
            self.update()
            return

        elif self.is_viewer_page_active():
            curpos = self.mapFromGlobal(QCursor().pos())
            if not self.tagging_sidebar_visible:
                self.tagging_sidebar_visible = tagging.get_tiny_sidebar_rect(self).contains(curpos)
            else:
                self.tagging_sidebar_visible = tagging.get_sidebar_rect(self).contains(curpos)

            if self.tagging_overlay_mode:
                tagging.main_mouseMoveEvent(self, event)
                return

            if self.isLeftClickAndCtrl(event) or self.region_zoom_in_input_started:
                self.region_zoom_in_mouseMoveEvent(event)
            elif self.isLeftClickAndCtrlShift(event) or self.comment_data:
                self.image_comment_mouseMoveEvent(event)
            elif event.buttons() == Qt.LeftButton:
                if self.transformations_allowed and self.image_translating:
                    new =  self.oldElementPos - (self.oldCursorPos - self.mapped_cursor_pos())
                    old = self.image_center_position
                    self.hint_center_position += new-old
                    self.image_center_position = new

        elif self.is_library_page_active():
            if event.buttons() == Qt.NoButton:
                if self.previews_list:
                    ai = self.previews_list_active_item
                    over_active_item = False
                    if ai:
                        r = self.previews_active_item_rect(ai[0])
                        over_active_item = r.contains(event.pos())
                    if not over_active_item:
                        self.previews_list_active_item = None
                        for item_rect, item_data in self.previews_list:
                            if item_rect.contains(event.pos()):
                                self.previews_list_active_item = (item_rect, item_data)
        self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):

        if self.is_pureref_page_active():
            pureref.mouseReleaseEvent(self, event)

        elif self.is_start_page_active():
            return

        elif self.is_viewer_page_active():
            if self.tagging_overlay_mode:
                tagging.main_mouseReleaseEvent(self, event)
                return
            if event.button() == Qt.LeftButton:
                self.left_button_pressed = False
            if self.isLeftClickAndCtrl(event) or self.region_zoom_in_input_started:
                self.region_zoom_in_mouseReleaseEvent(event)
            elif self.isLeftClickAndCtrlShift(event) or self.comment_data is not None:
                self.image_comment_mouseReleaseEvent(event)
            elif event.button() == Qt.LeftButton:
                if self.transformations_allowed:
                    self.image_translating = False
                    self.update()

        self.update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.is_library_page_active():
            pass
        elif self.is_start_page_active():
            return
        elif self.is_viewer_page_active():
            if self.is_cursor_over_image():
                if self.frameless_mode:
                    self.toggle_image_pos_and_scale()
                elif self.STNG_doubleclick_toggle:
                    self.toggle_to_frameless_mode()

    def eventFilter(self, obj, event):
        if self.is_library_page_active():
            if event.type() == QEvent.MouseButtonDblClick:
                if self.folders_list:
                    for item_rect, item_data in self.folders_list:
                        if item_rect.contains(event.pos()):
                            # здесь выходим со страницы библиотеки
                            self.change_page(self.pages.VIEWER_PAGE)
                            self.update()
                            # break
                            return True
        elif self.is_viewer_page_active():
            if event.type() in [QEvent.MouseButtonRelease] and obj is self:
                # в region_zoom_in_mouseReleaseEvent это не срабатывает,
                # видимо потому, что кнопка мыши отпущена над окном-ребёнком
                self.region_zoom_in_UX_breaker_finish(event)
                return False
        return False

    def toggle_to_frame_mode(self):
        f_geometry = self.frameGeometry()
        geometry = self.geometry()
        self.frameless_mode = False
        self.hide()
        self.set_window_style()
        # здесь нельзя использовать show(), только showNormal,
        # потому что после show() окно не сразу даёт себя ресайзить,
        # и даёт ресайзить себя только после перетаскивания мышкой за область заголовка окна,
        # при этом при перетаскивании окно увеличивается до бывших увеличенных размеров,
        # что нежелательно
        self.showNormal()
        r = self.get_image_viewport_rect()
        if r.width() == 0:
            # случай, когда на экране отображется надпись "загрузка"
            # т.е. handling_input == True
            r = QRect(0, 0, 500, 270)
            r.moveCenter(f_geometry.center())
        pos = r.topLeft()
        # для того чтобы на всех мониторах всё вело себя предсказуемо, а именно
        # при переходе из полноэкранного режима в оконный режим
        pos += QPoint(f_geometry.left(), f_geometry.top()) # monitor offset
        self.image_center_position = QPointF(
            self.rect().width()/2,
            self.rect().height()/2
        ).toPoint()
        self.hint_center_position = QPointF(
            self.rect().width()/2,
            self.rect().height()/2
        ).toPoint()
        # setGeometry вместо resize и move и мерцания исчезают полностью
        if True:
            size = QSizeF(r.width(), r.height())
            self.setGeometry(QRectF(pos, size).toRect())
        else:
            self.resize(r.width(), r.height())
            self.move(pos)
        # При переключении во frame_mode приложение не получает сообщения об отпускании
        # кнопки мыши, потому что позиция клика уже будет находится за пределами окна.
        # И поэтому программа будет считать, что левая кнопка мыши все ещё нажата,
        # пока пользователь не нажмёт и отожмёт её снова.
        # И хоть PyQt все ещё будет думать, что левая кнопка мыши не отжата,
        # инфу об этом я вынес в переменную self.left_button_pressed
        # и сам здесь управляю её значением, чтобы не возникло никаких залипаний
        # при использовании программы.
        self.left_button_pressed = False
        self.update()

    def toggle_to_frameless_mode(self):
        f_geometry = self.frameGeometry()
        geometry = self.geometry()
        self.hide()
        # По какой-то неведомой причине разница между
        # f_geometry.top() и geometry.top() равна 31, а не 11
        # Но чтобы был нужный эффект необходимо прибавлять именно 11, а не 31.
        # Никак не смог вывести почему именно величина в 11 пикселей даёт эффект,
        # эта величина подобрана экспериментально.
        # Будет не очень хорошо, если на другом компьютере тут будет несоответствие.
        # ... и почему для X составляющей не нужны никакие коррективы, а только для Y?
        if self.animated:
            MAGIC_CONST = 12
        else:
            MAGIC_CONST = 11
        self.image_center_position += QPointF(f_geometry.left(), f_geometry.top()+MAGIC_CONST)
        self.hint_center_position += QPointF(f_geometry.left(), f_geometry.top()+MAGIC_CONST)
        self.frameless_mode = True
        self.set_window_style()
        self.showMaximized()
        desktop = QDesktopWidget()
        self.image_center_position -= QPointF(desktop.screenGeometry(self).topLeft())
        self.hint_center_position -= QPointF(desktop.screenGeometry(self).topLeft())
        self.update()

    def get_center_position(self):
        return QPointF(
            self.frameGeometry().width()/2,
            self.frameGeometry().height()/2
        )

    def toggle_image_pos_and_scale(self):
        default_scale = self.image_scale == 1.0
        default_pos = self.image_center_position == self.get_center_position()

        # для случая, когда картинку не масштабировали,
        # а просто переместили в сторону
        if default_scale and not default_pos:
            self.restore_image_transformations()
            return

        if default_pos or default_scale:
            new_rect = self.frameGeometry()
            new_bottom = self.frameGeometry().height() - self.BOTTOM_PANEL_HEIGHT
            new_rect.setHeight(new_bottom)
            self.image_center_position = QPoint(
                int(new_rect.width()/2),
                int(new_rect.height()/2)
            )
            r = self.get_image_viewport_rect()
            self.image_scale = new_rect.height() / r.height()
        else:
            self.restore_image_transformations()

    def autoscroll_set_or_reset(self):
        H = self.LIBRARY_FOLDER_ITEM_HEIGHT
        content_height = H * len(LibraryData().all_folders())
        if content_height > self.rect().height():
            capacity = self.rect().height()/H
            offset_by_center = int(capacity/2)
            # вычисление сдвига
            _offset = -H*(LibraryData()._index-offset_by_center)
            # ограничители сдвига
            content_height -= self.rect().height()
            content_height += self.BOTTOM_FIELD_HEIGHT
            _offset = max(-content_height, _offset)
            _offset = min(self.TOP_FIELD_HEIGHT, _offset)
            LibraryData().folderslist_scroll_offset = _offset
        else:
            LibraryData().folderslist_scroll_offset = 0

    def wheelEventLibraryMode(self, scroll_value, event):
        curpos = self.mapFromGlobal(QCursor().pos())
        right_column = QRect(self.rect())
        right_column.setRight(int(self.rect().width()/2))
        H = self.LIBRARY_FOLDER_ITEM_HEIGHT
        if right_column.contains(curpos):
            content_height = H * len(LibraryData().all_folders())
            _offset = LibraryData().folderslist_scroll_offset
            if content_height > self.rect().height():
                _offset += int(scroll_value*200)
                # вычитаем видимую часть из высоты всего контента
                content_height -= self.rect().height()
                # задаём отступ внизу списка
                content_height += self.BOTTOM_FIELD_HEIGHT
                # ограничение при скроле в самом низу списка
                _offset = max(-content_height, _offset)
                # ограничение при скроле в самому верху списка
                # и задаём отступ вверху списка
                _offset = min(self.TOP_FIELD_HEIGHT, _offset)
                LibraryData().folderslist_scroll_offset = _offset
        else:
            cf = LibraryData().current_folder()
            if cf.columns:
                content_height = max(col.height for col in cf.columns)
                if content_height > self.rect().height():
                    cf.previews_scroll_offset += int(scroll_value*200)
                    content_height -= self.rect().height()
                    content_height += self.BOTTOM_FIELD_HEIGHT
                    _offset = cf.previews_scroll_offset
                    _offset = max(-content_height, _offset)
                    _offset = min(self.TOP_FIELD_HEIGHT, _offset)
                    cf.previews_scroll_offset = _offset
                    self.reset_previews_active_item_on_scrolling(event)
        self.update()

    def reset_previews_active_item_on_scrolling(self, event):
        current_item = None
        for item_rect, item_data in self.previews_list:
            if item_rect.contains(event.pos()):
                current_item = (item_rect, item_data)
        if current_item != self.previews_list_active_item:
            # обнуляем выделенную мышкой превьюшку,
            # если под мышкой уже находится другая превьюшка
            self.previews_list_active_item = None

    def is_control_panel_under_mouse(self):
        if Globals.control_panel is not None:
            if Globals.control_panel.isVisible():
                if Globals.control_panel.underMouse():
                    return True
        return False

    def wheelEvent(self, event):

        if self.check_thumbnails_fullscreen():
            self.update()
            return

        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier
        control_panel_undermouse = self.is_control_panel_under_mouse()

        if self.is_pureref_page_active():
            pureref.wheelEvent(self, event)

        elif self.is_start_page_active():
            return

        elif self.is_library_page_active():
            self.wheelEventLibraryMode(scroll_value, event)

        elif self.is_viewer_page_active():

            if self.tagging_overlay_mode:
                tagging.main_wheelEvent(self, event)
                return

            if ctrl and (not shift) and self.STNG_zoom_on_mousewheel:
                self.do_scroll_images_list(scroll_value)
            if self.left_button_pressed and self.animated:
                self.do_scroll_playbar(scroll_value)
                self.show_center_label(self.label_type.FRAME_NUMBER)
            if shift and ctrl and self.animated:
                self.do_scroll_playspeed(scroll_value)
                self.show_center_label(self.label_type.PLAYSPEED)
            if no_mod and self.STNG_zoom_on_mousewheel and (not self.left_button_pressed) and (not control_panel_undermouse):
                self.do_scale_image(scroll_value)
            elif no_mod and not self.left_button_pressed:
                self.do_scroll_images_list(scroll_value)

    def do_scroll_playspeed(self, scroll_value):
        if not self.animated:
            return
        speed_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200]
        index = speed_values.index(int(self.movie.speed()))
        if index == len(speed_values)-1 and scroll_value > 0:
            pass
        elif index == 0 and scroll_value < 0:
            pass
        else:
            if scroll_value < 0:
                index -=1
            if scroll_value > 0:
                index +=1
        self.movie.setSpeed(speed_values[index])

    def do_scroll_playbar(self, scroll_value):
        if not self.animated:
            return
        frames_list = list(range(0, self.movie.frameCount()))
        if scroll_value > 0:
            pass
        else:
            frames_list = list(reversed(frames_list))
        frames_list.append(0)
        i = frames_list.index(self.movie.currentFrameNumber()) + 1
        self.movie.jumpToFrame(frames_list[i])
        self.pixmap = self.movie.currentPixmap()
        self.get_rotated_pixmap(force_update=True)

    def do_scroll_images_list(self, scroll_value):
        if scroll_value > 0:
            LibraryData().show_next_image()
        elif scroll_value < 0:
            LibraryData().show_previous_image()

    def set_original_scale(self):
        self.image_scale = 1.0
        self.update()

    def do_scale_image(self, scroll_value, cursor_pivot=True, override_factor=None):

        if not self.transformations_allowed:
            return

        if not override_factor:
            self.region_zoom_in_cancel()

        if self.image_scale >= self.UPPER_SCALE_LIMIT-0.001:
            if scroll_value > 0.0:
                return

        if self.image_scale <= self.LOWER_SCALE_LIMIT:
            if scroll_value < 0.0:
                return

        animated_zoom_enabled = self.isAnimationEffectsAllowed() and self.STNG_animated_zoom

        before_scale = self.image_scale

        # эти значения должны быть вычислены до изменения self.image_scale
        r = self.get_image_viewport_rect()
        now_image_rect = QRectF(r)
        p1 = r.topLeft()
        p2 = r.bottomRight()

        t = self.get_secret_hint_rect()
        t1 = t.topLeft()
        t2 = t.bottomRight()

        if not override_factor:

            if self.STNG_legacy_image_scaling:
                # старый глючный метод со скачками зума, но зато работает уже очень долго

                if self.image_scale > 1.0: # если масштаб больше нормального
                    factor = self.image_scale/self.UPPER_SCALE_LIMIT
                    if scroll_value < 0.0:
                        self.image_scale -= 0.1 + 8.5*factor #0.2
                    else:
                        self.image_scale += 0.1 + 8.5*factor #0.2

                else: # если масштаб меньше нормального
                    if scroll_value < 0.0:
                        self.image_scale -= 0.05 #0.1
                    else:
                        self.image_scale += 0.05 #0.1

            else:
                # Здесь надо задавать image_scale в зависимости от
                # новой ширины или длины картинки, высчитаннной в процентах
                # от старой длины или ширины.
                # Дельта колеса мыши будет определять лишь уменьшение или увеличение

                _pixmap_rect = self.get_rotated_pixmap().rect()
                _viewport_rect = self.get_image_viewport_rect()
                viewport_width = _viewport_rect.width()
                _height = _viewport_rect.height()

                # чем больше scale_speed, тем больше придётся крутить колесо мыши
                if animated_zoom_enabled:
                    scale_speed = 2.5
                else:
                    scale_speed = 5

                if scroll_value < 0.0:
                    _new_width = viewport_width*(scale_speed-1)/scale_speed
                    self.image_scale = _new_width/_pixmap_rect.width()
                else:
                    _new_width = viewport_width*scale_speed/(scale_speed-1)
                    # предохранитель от залипания
                    if _new_width - float(viewport_width) < 10.0:
                        _new_width = float(viewport_width) + 10.0
                    self.image_scale = _new_width/_pixmap_rect.width()

        self.image_scale = min(max(self.LOWER_SCALE_LIMIT, self.image_scale),
                                                                    self.UPPER_SCALE_LIMIT)
        delta = before_scale - self.image_scale

        pixmap_rect = self.get_rotated_pixmap().rect()
        orig_width = pixmap_rect.width()
        orig_height = pixmap_rect.height()

        if override_factor:
            pivot = QPointF(self.rect().center())
        else:
            if cursor_pivot:
                if r.contains(self.mapped_cursor_pos()):
                    pivot = QPointF(self.mapped_cursor_pos())
                else:
                    pivot = QPointF(self.rect().center())
            else:
                pivot = QPointF(self.image_center_position)

        p1 = p1 - pivot
        p2 = p2 - pivot
        t1 = t1 - pivot
        t2 = t2 - pivot

        if False:
            factor = (1.0 - delta)
            # delta  -->  factor
            #  -0.1  -->  1.1: больше 1.0
            #  -0.2  -->  1.2: больше 1.0
            #   0.2  -->  0.8: меньше 1.0
            #   0.1  -->  0.9: меньше 1.0
            # Единственный недостаток factor = (1.0 - delta) в том,
            # что он увеличивает намного больше, чем должен:
            # из-за этого постоянно по факту превышается UPPER_SCALE_LIMIT.
            # Вариант ниже как раз призван устранить этот недостаток.
            # Хотя прелесть factor = (1.0 - delta) в том,
            # что не нужно создавать хитровыебанные дельты с множителями,
            # как это сделано чуть выше.
        else:
            # x от p2 будет всегда больше, чем x от p1 в силу того,
            # что p1 это верхний левый угол прямоугольника, а p2 это нижний правый угол того же прямоугольника,
            # и начало системы координат всегда находится ближе к p1
            current_width = abs(p2.x() - p1.x())
            # предохранитель на всякий случай
            current_width = max(1.0, current_width)

            # Переменную factor стоило бы называть delta_factor,
            # потому что увеличение или уменьшение масштаба всегда идёт от текущего значения масштабирования;
            # здесь image_scale содержит уже новое значение;
            factor = 1.0 - (before_scale - self.image_scale)*orig_width/current_width
            # переменная factor используется как множитель. Если множитель больше 1.0, то будет увеличение,
            # а если меньше 1.0 и не меньше, и не равен 0.0, то будет уменьшение.
            # 1.0 в начале выражения выстален именно для того, чтобы определить начальное значение,
            # которое либо уменьшается стремясь к 0.0, либо увеличивается до бесконечности.
            # Но как правило, благодаря print(factor) удалось узнать, что
            # в factor оказываются только значения 1.6 и 0.6 для увеличения и уменьшения соответственно
            # и проще можно было бы написать
            # if scroll_value > 0:
            #     factor = 1.6
            # else:
            #     factor = 0.6
            # главное чтобы эти значения были обратными друг другу. И наверно так и стоило написать,
            # но в самом начале разработки, торопясь, я изменял image_scale напрямую,
            # а не задавал image_scale как отношение новой длины к старой длине,
            # отсюда и ненужные усложнения в коде

            if Globals.DEBUG:
                scale_delta_factor = factor
                print(f'scale_delta_factor = {scale_delta_factor:.2f}')

        if override_factor:
            factor = override_factor

        p1 = QPointF(p1.x()*factor, p1.y()*factor)
        p2 = QPointF(p2.x()*factor, p2.y()*factor)
        t1 = QPointF(t1.x()*factor, t1.y()*factor)
        t2 = QPointF(t2.x()*factor, t2.y()*factor)

        p1 = p1 + pivot
        p2 = p2 + pivot
        t1 = t1 + pivot
        t2 = t2 + pivot

        # здесь задаём размер и положение
        new_width = abs(p2.x() - p1.x())
        new_height = abs(p2.y() - p1.y())

        image_scale = new_width / orig_width
        image_center_position = (p1 + p2)/2

        # end
        if override_factor:
            return image_scale, image_center_position.toPoint()
        else:

            if animated_zoom_enabled:

                def update_function():
                    self.image_scale = self.image_rect.width()/self.get_rotated_pixmap().width()
                    self.image_center_position = QPointF(self.image_rect.center())
                    self.update()

                if (before_scale < 1.0 and image_scale > 1.0) or (before_scale > 1.0 and image_scale < 1.0):
                    print("scale is clamped to 100%")
                    image_scale = 1.0

                wanna_image_rect = self.get_image_viewport_rect(od=(image_center_position, image_scale))
                self.animate_properties(
                    [
                        (self, "image_rect", now_image_rect, wanna_image_rect, update_function),
                    ],
                    anim_id="zoom",
                    duration=0.7,
                    # easing=QEasingCurve.OutQuad
                    # easing=QEasingCurve.OutQuart
                    # easing=QEasingCurve.OutQuint
                    easing=QEasingCurve.OutCubic
                )

            else:

                if self.image_scale == 100.0 and image_scale < 100.0 and scroll_value > 0.0:
                    # Предохранитель от постепенного заплыва картинки в сторону верхнего левого угла
                    # из-за кручения колеса мыши в область ещё большего увеличения
                    # Так происходит, потому что переменная image_scale при этом чуть меньше 100.0
                    pass
                else:
                    self.image_scale = image_scale

                viewport_rect = self.get_image_viewport_rect()
                is_vr_small = viewport_rect.width() < 150 or viewport_rect.height() < 150
                if before_scale < self.image_scale and is_vr_small:
                    self.image_center_position = QPoint(QCursor().pos())
                else:
                    self.image_center_position = image_center_position.toPoint()

                self.hint_center_position = ((t1 + t2)/2).toPoint()

        self.show_center_label(self.label_type.SCALE)

        self.activate_or_reset_secret_hint()

        self.update()

    def scale_label_opacity(self):
        delta = time.time() - self.center_label_time
        if delta < self.CENTER_LABEL_TIME_LIMIT:
            d = 6 # remap 1.0 to 0.0 in time, make it faster
            d1 = 1.0/d
            d2 = 1.0*d
            value = min(max(0.0, self.CENTER_LABEL_TIME_LIMIT-delta), d1) * d2
            return value
        else:
            return 0.0

    def scale_label_color(self):
        delta = time.time() - self.center_label_time
        if delta < 0.5:
            return fit(delta, 0.0, 0.5, 0.0, 1.0)
        else:
            return 1.0

    def draw_center_label(self, painter, text, large=False):
        painter.resetTransform()
        def set_font(pr):
            font = pr.font()
            old_font = pr.font() #copy
            if large:
                # font.setPixelSize(self.rect().height()//8)
                font.setPixelSize(40)
            else:
                font.setPixelSize(17)
            font.setWeight(1900)
            # font.setFamily("Consolas")
            # font.setWeight(900)
            pr.setFont(font)
            return old_font

        pic = QPicture()
        p = QPainter(pic)
        set_font(p)
        # if not large: #debug
        #   text = "{text}\n{Globals.control_panel.window_opacity:.2f}"
        r = self.rect()
        brect = p.drawText(r.x(), r.y(), r.width(), r.height(), Qt.AlignCenter, text)
        p.end()
        del p
        del pic

        # backplate
        opacity = self.scale_label_opacity()
        if not large:
            painter.setOpacity(0.6*opacity)
            # calculate rect of the backplate
            RADIUS = 5
            path = QPainterPath()
            offset = 5
            r = brect.adjusted(-offset, -offset+2, offset, offset-2)
            r = QRectF(r)
            path.addRoundedRect(r, RADIUS, RADIUS)
            # draw rounded backplate
            if self.center_label_error:
                c = QColor(0, 0, 0)
            else:
                c = QColor(80, 80, 80)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(c))
            painter.drawPath(path)
            # back to normal
            painter.setOpacity(1.0*opacity)

        old_font = set_font(painter)

        if large:
            # c = QColor("#e1db74")
            # c.setAlphaF(0.4)
            c = QColor(Qt.white)
            c.setAlphaF(0.9)
            painter.setPen(QPen(c))
            painter.setOpacity(1.0)
        else:
            if self.center_label_error:
                end_value = QColor(QColor(200, 0, 0))
            else:
                end_value = QColor(Qt.white)
            color = self.interpolate_values(
                QColor(0xFF, 0xA0, 0x00),
                end_value,
                self.scale_label_color()
            )
            painter.setPen(color)
            painter.setOpacity(opacity)
        painter.drawText(brect, Qt.AlignCenter, text)
        painter.setOpacity(1.0)

        painter.setFont(old_font)

    def paintEvent(self, event):

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # draw darkened translucent background
        if self.frameless_mode:
            if self.is_library_page_active():
                painter.setOpacity(self.STNG_library_page_transparency)
            else:
                painter.setOpacity(self.STNG_viewer_page_transparency)
            painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            painter.drawRect(self.rect())
            painter.setOpacity(1.0)
        else:
            painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            painter.drawRect(self.rect())

        # draw current page
        if self.is_library_page_active():
            self.draw_library(painter)

        elif self.is_start_page_active():
            self.draw_startpage(painter)

        elif self.is_viewer_page_active():
            self.draw_content(painter)
            self.region_zoom_in_draw(painter)

        elif self.is_pureref_page_active():
            pureref.draw(self, painter)

        # draw page menu
        self.draw_corner_menu(painter, corner_attr="topLeft")
        # draw close button
        self.draw_corner_button(painter)
        # draw page button
        self.draw_corner_button(painter, corner_attr="topLeft")

        # draw thumbnails making progress
        self.draw_threads_info(painter)

        self.draw_32bit_warning(painter)

        self.draw_console_output(painter)

        # debug only
        # painter.setPen(QPen(Qt.red))
        # painter.drawLine(self.rect().topLeft(), self.rect().bottomRight())
        # painter.drawLine(self.rect().bottomLeft(), self.rect().topRight())

        self.draw_noise_cells(painter)

        painter.end()

    def draw_noise_cells(self, painter):
        if noise and self.STNG_show_noise_cells:
            SIZE = 150
            x_num = math.ceil(self.rect().width() / SIZE)
            y_num = math.ceil(self.rect().height() / SIZE)
            x_offset = (self.rect().width() % SIZE)
            y_offset = (self.rect().height() % SIZE)
            painter.setBrush(QBrush(Qt.black))
            painter.setPen(Qt.NoPen)
            for x in range(x_num):
                for y in range(y_num):
                    value = noise.snoise3(x, y, self.noise_time, octaves=4)
                    value *= 0.3
                    rect = QRect(x*SIZE - x_offset, y*SIZE - y_offset, SIZE, SIZE)
                    if rect.contains(self.mapFromGlobal(QCursor().pos())):
                        value = 0.0
                    painter.setOpacity(value)
                    painter.drawRect(rect)
            painter.setOpacity(1.0)

    def draw_startpage(self, painter):
        def set_font_size(size, bold):
            font = painter.font()
            if bold:
                font.setWeight(1900)
            else:
                font.setWeight(300)
            font.setPixelSize(size)
            painter.setFont(font)

        rect1 = self.rect()
        rect2 = self.rect()
        H = self.rect().height()
        H2 = int(H/2)
        rect2.moveTop(H2+100)
        rect2.setBottom(H)
        set_font_size(70, True)
        painter.setPen(QPen(Qt.white))
        text = "ПЕРЕТАЩИ СЮДА ФАЙЛ ИЛИ ПАПКУ С ФАЙЛАМИ"
        painter.drawText(rect1, Qt.TextWordWrap | Qt.AlignCenter, text)

        set_font_size(25, False)
        text = "или кликни левой кнопкой мыши, чтобы открыть диалог"
        text += "\n\nКлик правой кнопкой — открыть окно настроек"

        if Globals.lite_mode:
            text += "\n\n[программа запущена в лайтовом (упрощённом) режиме]"
        else:
            text += "\n\n\n\n[программа запущена в обычном режиме]"

        painter.drawText(rect2, Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignTop, text)

    def draw_32bit_warning(self, painter):
        if Globals.is_32bit_exe:
            text = (
                "Программа была запущена из 32bit-го интерпретатора Python,"
                "из-за чего сейчас имеет ограничение по потребляемой памяти до 1.5GB"
                "\n и рискует зависнуть при подходе значения потребляемой памяти к 1.5GB."
                "\nДля увеличения доступной памяти надо запуститься из 64bit-го интерпретатора!"
            )
            painter.drawText(self.rect(), Qt.TextWordWrap | Qt.AlignTop | Qt.AlignHCenter, text)

    def draw_threads_info(self, painter):
        # threads info
        font = painter.font()
        font.setPixelSize(13)
        painter.setFont(font)
        for n, item in enumerate(self.threads_info.items()):
            status, string = item[1]
            painter.drawText(QPoint(5, self.rect().height()-10-30*n), string)

    def draw_console_output(self, painter):
        font = painter.font()
        font.setFamily('Consolas')
        font.setPixelSize(18)
        painter.setFont(font)
        if SettingsWindow.get_setting_value('show_console_output'):
            for n, (timestamp, message) in enumerate(HookConsoleOutput.get_messages()):
                painter.drawText(QPoint(255, 50+10*n), message)

    def get_center_x_position(self):
        return int(self.rect().width()/2)

    def draw_library(self, painter):
        def set_font(pr):
            old_font = pr.font()
            font = QFont(pr.font())
            font.setPixelSize(20)
            font.setWeight(1900)
            font.setFamily("Consolas")
            pr.setFont(font)
            return old_font
        H = self.LIBRARY_FOLDER_ITEM_HEIGHT
        old_font = set_font(painter)

        CENTER_OFFSET = 80
        CENTER_X_POSITION = self.get_center_x_position()

        # left column
        LEFT_COL_WIDTH = CENTER_X_POSITION-CENTER_OFFSET
        left_col_check_rect = QRect(0, 0, LEFT_COL_WIDTH, self.rect().height())

        scroll_offset = LibraryData().folderslist_scroll_offset
        self.folders_list = []
        for n, folder_data in enumerate(LibraryData().all_folders()):
            thumb = folder_data.get_current_thumbnail()
            tw = Globals.THUMBNAIL_WIDTH
            thumb_size = min(tw, tw)
            thumb_ui_size = thumb_size*2
            item_rect = QRect(
                10, int(scroll_offset + 20+H*n),
                LEFT_COL_WIDTH, int(thumb_ui_size+20)
            )
            self.folders_list.append((item_rect, folder_data))
            if LibraryData().current_folder() == folder_data:
                painter.setOpacity(0.3)
                painter.setBrush(QBrush(QColor(0xFF, 0xA0, 0x00)))
                painter.drawRect(item_rect)
                painter.setOpacity(1.0)

            painter.setPen(QPen(QColor(Qt.white)))
            left = 50 + thumb_ui_size
            text_rect = QRect(left, int(scroll_offset + 50+n*H), LEFT_COL_WIDTH-left, 200)
            images_list_len = len(folder_data.images_list)
            text = f"{images_list_len} {folder_data.folder_path}"
            painter.drawText(text_rect, Qt.AlignLeft, text)
            text_rect = QRect(left, int(scroll_offset + 24+n*H), LEFT_COL_WIDTH-left, 200)
            text = folder_data.get_current_image_name()
            painter.drawText(text_rect, Qt.AlignLeft, text)

            if folder_data.images_list:
                ControlPanel.thumbnails_drawing(
                    self, painter, folder_data,
                    pos_x=50+thumb_ui_size,
                    pos_y=scroll_offset + 50+n*H,
                    library_page_rect=left_col_check_rect,
                    draw_mirror=False
                )
            source = QRect(0, 0, tw, tw)
            target = QRect(30, int(scroll_offset + 30+H*n), thumb_ui_size, thumb_ui_size)
            w = thumb_size
            h = thumb_size
            x = (tw - w)/2
            y = (tw - h)/2
            source_rect = QRectF(QPointF(x, y), QSizeF(thumb_size, thumb_size)).toRect()
            painter.drawPixmap(target, thumb or Globals.NULL_PIXMAP, source_rect)

        painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # right column
        self.previews_list = []
        RIGHT_COLUMN_LEFT = CENTER_X_POSITION+CENTER_OFFSET
        RIGHT_COLUMN_WIDTH = self.rect().width() - RIGHT_COLUMN_LEFT
        right_col_check_rect = QRect(RIGHT_COLUMN_LEFT, 0, RIGHT_COLUMN_WIDTH,
                                                                        self.rect().height())
        cf = LibraryData().current_folder()
        columns = cf.columns
        if columns:
            column_width = cf.column_width
            painter.setPen(QPen(QColor(Qt.gray)))
            offset = (self.rect().width()/2 - column_width*len(columns))/2
            painter.setBrush(QBrush(Qt.black))
            painter.setPen(Qt.NoPen)
            main_offset_y = 20 + cf.previews_scroll_offset
            for n, col in enumerate(columns):
                offset_x = self.rect().width()/2 + column_width*n + offset
                offset_x = int(offset_x)
                offset_y = main_offset_y
                offset_y = int(offset_y)
                for im_data in col.images:
                    w = im_data.preview_size.width()
                    h = im_data.preview_size.height()
                    r = QRect(offset_x, offset_y, w, h)
                    r.adjust(1, 1, -1, -1)
                    painter.drawRect(r) #for images with transparent layer
                    self.previews_list.append((r, im_data))
                    pixmap = im_data.preview
                    painter.drawPixmap(r, pixmap)
                    offset_y += h

            if self.previews_list_active_item:
                item_rect, item_data = self.previews_list_active_item
                item_rect = self.previews_active_item_rect(item_rect)
                painter.drawRect(item_rect) #for images with transparent layer
                draw_shadow(
                    self,
                    painter,
                    item_rect, 10,
                    webRGBA(QColor(0, 0, 0, 100)),
                    webRGBA(QColor(0, 0, 0, 0))
                )
                painter.drawPixmap(item_rect, item_data.preview)

                if not hasattr(item_data, "library_cache_version"):
                    item_data.library_cache_version = load_image_respect_orientation(
                                                                        item_data.filepath)
                cached = item_data.library_cache_version
                if cached:
                    source_rect = cached.rect()
                    main_rect = QRectF(0, 0, self.rect().width()/2, self.rect().height()).toRect()
                    projected = fit_rect_into_rect(source_rect, main_rect)
                    painter.setOpacity(0.8)
                    painter.drawRect(main_rect)
                    painter.setOpacity(1.0)
                    if cached.width() != 0:
                        painter.drawPixmap(projected, cached, source_rect)
                    else:
                        painter.setPen(QPen(Qt.white))
                        error_msg = f'Ошибка\n {item_data.filename}'
                        painter.drawText(main_rect, Qt.AlignCenter, error_msg)
        else:
            painter.setPen(QPen(QColor(Qt.white)))
            if LibraryData().current_folder().images_list:
                text = "Подождите"
            else:
                text = "Нет изображений"
            painter.drawText(right_col_check_rect, Qt.AlignCenter, text)

        self.draw_middle_line(painter)

        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.draw_library_scrollbars(painter)

        painter.setFont(old_font)

    def draw_library_scrollbars(self, painter):
        CXP = self.get_center_x_position()

        WIDTH = 10
        OFFSET_FROM_CENTER = 5
        left_scrollbar_rect = QRect(CXP-(WIDTH+OFFSET_FROM_CENTER), 0, WIDTH, self.rect().height())
        right_scrollbar_rect = QRect(CXP+OFFSET_FROM_CENTER, 0, WIDTH, self.rect().height())

        # рисовать или не рисовать
        draw_left_scrollbar = False
        draw_right_scrollbar = False
        content_height_left = self.LIBRARY_FOLDER_ITEM_HEIGHT * len(LibraryData().all_folders())
        draw_left_scrollbar = content_height_left > self.rect().height()
        cf = LibraryData().current_folder()
        if cf.columns:
            content_height_right = max(col.height for col in cf.columns)
            draw_right_scrollbar = content_height_right > self.rect().height()

        painter.setOpacity(0.1)
        if draw_left_scrollbar:
            painter.fillRect(left_scrollbar_rect, Qt.white)
        if draw_right_scrollbar:
            painter.fillRect(right_scrollbar_rect, Qt.white)
        painter.setOpacity(0.5)

        if draw_left_scrollbar:
            factor = self.rect().height()/(content_height_left-self.rect().height())
            factor = min(1.0, factor)
            left_bar_height = int(factor*self.rect().height())

            offset = LibraryData().folderslist_scroll_offset
            if offset == 0:
                left_bar_y = 0
            else:
                y_factor = abs(offset)/(content_height_left-self.rect().height())
                y_factor = min(1.0, y_factor)
                left_bar_y = (self.rect().height()-left_bar_height)*y_factor
            # left_bar_y += 20
            left_bar_y = int(left_bar_y)

            left_bar_rect = QRect(CXP-(WIDTH+OFFSET_FROM_CENTER), left_bar_y, WIDTH,
                                                                                left_bar_height)

            path = QPainterPath()
            path.addRoundedRect(QRectF(left_bar_rect), 5, 5)
            painter.fillPath(path, Qt.white)

        if draw_right_scrollbar:
            factor = self.rect().height()/(content_height_right-self.rect().height())
            factor = min(1.0, factor)
            right_bar_height = int(factor*self.rect().height())

            offset = cf.previews_scroll_offset
            if offset == 0:
                right_bar_y = 0
            else:
                y_factor = abs(offset)/(content_height_right-self.rect().height())
                y_factor = min(1.0, y_factor)
                right_bar_y = (self.rect().height()-right_bar_height)*y_factor
            # right_bar_y += 20
            right_bar_y = int(right_bar_y)

            right_bar_rect = QRect(CXP+OFFSET_FROM_CENTER, right_bar_y, WIDTH, right_bar_height)

            path = QPainterPath()
            path.addRoundedRect(QRectF(right_bar_rect), 5, 5)
            painter.fillPath(path, Qt.white)

        painter.setOpacity(1.0)

    def draw_middle_line(self, painter):
        color = Qt.gray
        component_value = 30
        color = QColor(component_value, component_value, component_value)
        painter.setPen(QPen(color, 1))
        painter.drawLine(
          QPointF(self.rect().width()/2, 0).toPoint(),
          QPointF(self.rect().width()/2, self.rect().height()).toPoint()
        )

    def previews_active_item_rect(self, rect):
        new_w = rect.width() + 40
        new_h = int((new_w/rect.width())*rect.height())
        r = QRect(0, 0, new_w, new_h)
        r.moveCenter(rect.center())
        return r

    def draw_content(self, painter):

        # draw image
        if self.pixmap or self.invalid_movie:
            im_rect = self.get_image_viewport_rect()

            # 1. DRAW SHADOW
            OFFSET = 15
            shadow_rect = QRectF(im_rect)
            shadow_rect = shadow_rect.adjusted(OFFSET, OFFSET, -OFFSET, -OFFSET)
            draw_shadow(
                self,
                painter,
                shadow_rect, 30,
                webRGBA(QColor(0, 0, 0, 140)),
                webRGBA(QColor(0, 0, 0, 0))
            )

            # 2. DRAW CHECKERBOARD
            checkerboard_br = QBrush()
            pixmap = QPixmap(40, 40)
            painter_ = QPainter()
            painter_.begin(pixmap)
            painter_.fillRect(QRect(0, 0, 40, 40), QBrush(Qt.white))
            painter_.setPen(Qt.NoPen)
            painter_.setBrush(QBrush(Qt.gray))
            painter_.drawRect(QRect(0, 0, 20, 20))
            painter_.drawRect(QRect(20, 20, 20, 20))
            painter_.end()
            checkerboard_br.setTexture(pixmap)
            painter.setBrush(checkerboard_br)
            painter.drawRect(im_rect)
            painter.setBrush(Qt.NoBrush)

            # 3. DRAW IMAGE
            pixmap = self.get_rotated_pixmap()
            painter.drawPixmap(im_rect, pixmap, QRectF(pixmap.rect()))
            if self.invert_image:
                cm = painter.compositionMode()
                painter.setCompositionMode(QPainter.RasterOp_NotDestination)
                                                                #RasterOp_SourceXorDestination
                painter.setPen(Qt.NoPen)
                # painter.setBrush(Qt.green)
                # painter.setBrush(Qt.red)
                # painter.setBrush(Qt.yellow)
                painter.setBrush(Qt.white)
                painter.drawRect(im_rect)
                painter.setCompositionMode(cm)

            # draw cyberpunk
            if self.STNG_show_cyberpunk:
                draw_cyberpunk_corners(self, painter, im_rect)
            # draw thirds
            if self.STNG_show_thirds:
                draw_thirds(self, painter, im_rect)
            # draw image center
            if self.STNG_show_image_center:
                self.draw_center_point(painter, self.image_center_position)

            self.draw_secret_hint(painter)

            # draw center label
            self.draw_center_label_main(painter)

        elif self.movie:
            pass
        else:
            self.draw_center_label(painter, self.loading_text, large=True)

        # draw animation progressbar
        if self.movie:
            r = self.get_image_viewport_rect()
            progress_width = r.width() * self.movie.currentFrameNumber()/self.movie.frameCount()
            progress_bar_rect = QRectF(r.left(), r.bottom(), int(progress_width), 10)
            painter.setBrush(QBrush(Qt.green))
            painter.setPen(Qt.NoPen)
            painter.drawRect(progress_bar_rect)

        self.draw_comments(painter)

        self.draw_view_history_row(painter)

        self.draw_image_metadata(painter)

        tagging.draw_tags_sidebar_overlay(self, painter)
        tagging.draw_main(self, painter)

    def draw_center_label_main(self, painter):
        if self.image_center_position:
            if self.center_label_info_type == self.label_type.SCALE:
                value = math.ceil(self.image_scale*100)
                # "{:.03f}"
                text = f"{value:,}%".replace(',', ' ')
            elif self.center_label_info_type == self.label_type.PLAYSPEED and self.animated:
                speed = self.movie.speed()
                text = f"speed {speed}%"
            elif self.center_label_info_type == self.label_type.FRAME_NUMBER and self.animated:
                frame_num = self.movie.currentFrameNumber()+1
                frame_count = self.movie.frameCount()
                text = f"frame {frame_num}/{frame_count}"
            else:
                text = self.center_label_info_type
            self.draw_center_label(painter, text)        

    def draw_comments(self, painter):

        old_pen = painter.pen()
        old_brush = painter.brush()

        for comment in comments.get_comments_for_image():
            painter.setPen(QPen(Qt.yellow, 1))
            painter.setBrush(Qt.NoBrush)
            im_rect = self.get_image_viewport_rect()

            base_point = im_rect.topLeft()

            # abs is for backwards compatibility
            screen_left = base_point.x() + im_rect.width()*abs(comment.left)
            screen_top = base_point.y() + im_rect.height()*abs(comment.top)

            screen_right = base_point.x() + im_rect.width()*abs(comment.right)
            screen_bottom = base_point.y() + im_rect.height()*abs(comment.bottom)

            comment_rect = QRectF(
                QPointF(screen_left, screen_top),
                QPointF(screen_right, screen_bottom)
            ).toRect()
            comment.screen_rect = comment_rect
            cursor_inside = comment_rect.contains(self.mapFromGlobal(QCursor().pos()))
            if cursor_inside:
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(0.5)
            painter.drawRect(comment_rect)
            painter.setOpacity(1.0)

            text_to_draw = f'{comment.date_str}\n{comment.date_edited_str}\n{comment.text}'
            rect = painter.drawText(QRect(), Qt.AlignLeft, text_to_draw)

            if cursor_inside:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(Qt.black))
                rect.moveTopLeft(comment_rect.bottomLeft())
                painter.drawRect(rect)
                painter.setPen(QPen(Qt.white))
                painter.drawText(rect, Qt.AlignLeft, text_to_draw)

        painter.setPen(old_pen)
        painter.setBrush(old_brush)

    def draw_image_metadata(self, painter):
        cf = LibraryData().current_folder()
        ci = cf.current_image()
        out = []
        if SettingsWindow.get_setting_value('show_image_metadata') and ci.image_metadata:
            output_rect = self.rect()
            h2 = int(self.rect().height()*3/4)
            output_rect.setTop(h2)
            output_rect.setLeft(output_rect.left() + 100)
            output_rect.setRight(output_rect.right() - 100)
            output_rect.setBottom(output_rect.bottom() - 50)

            painter.setOpacity(1.0)
            painter.setPen(QPen(Qt.white))
            painter.drawText(output_rect, Qt.AlignLeft, ci.image_metadata_info)

    def draw_view_history_row(self, painter):
        viewed_list = LibraryData().get_viewed_list()
        offset = 5
        padding = self.CORNER_BUTTON_RADIUS*2
        rect = QRect(QPoint(padding, 0), QPoint(self.rect().width()-padding, Globals.THUMBNAIL_WIDTH+20+offset))
        CP = Globals.control_panel
        c1 = CP is not None and not CP.fullscreen_flag
        c2 = rect.contains(self.mapFromGlobal(QCursor().pos()))
        if all((c1, c2, viewed_list)):
            cur_image = LibraryData().current_folder().current_image()
            if cur_image in viewed_list:
                index = viewed_list.index(cur_image)
                ControlPanel.thumbnails_drawing(
                    self,
                    painter,
                    viewed_list,
                    pos_x=0,
                    pos_y=1,
                    current_index=index,
                    draw_mirror=False,
                    additional_y_offset=offset
                )
            old_pen = painter.pen()
            painter.setPen(QPen(Qt.white))
            painter.drawText(rect, Qt.AlignCenter | Qt.AlignBottom, "история просмотра")
            painter.setPen(old_pen)

    def draw_center_point(self, painter, pos):
        painter.setPen(QPen(Qt.green, 5, Qt.SolidLine))
        painter.drawPoint(pos)

    def closeEvent(self, event):
        event.accept()

    def close(self):
        super().close()

    def animated_or_not_animated_close(self, callback_on_finish):
        if self.isAnimationEffectsAllowed() and not self.is_library_page_active():
            self.animate_properties(
                [(self, "image_scale", self.image_scale, 0.01, self.update)],
                callback_on_finish=callback_on_finish
            )
        else:
            self.close()

    def require_window_closing(self):
        if Globals.lite_mode:
            self.animated_or_not_animated_close(QApplication.instance().exit)
        elif SettingsWindow.get_setting_value('hide_to_tray_on_close'):
            self.hide()
        else:
            self.animated_or_not_animated_close(QApplication.instance().exit)

    def show_center_label(self, info_type, error=False):
        self.center_label_error = error
        self.center_label_info_type = info_type
        if info_type not in self.label_type.all():
            # текстовые сообщения показываем дольше
            self.CENTER_LABEL_TIME_LIMIT = 5
        else:
            self.CENTER_LABEL_TIME_LIMIT = 2
        # show center label on screen
        self.center_label_time = time.time()

    def hide_center_label(self):
        self.center_label_time = time.time() - self.CENTER_LABEL_TIME_LIMIT

    def check_scroll_lock(self):
        return windll.user32.GetKeyState(VK_SCROLL)

    def isThumbnailsRowSlidingAnimationEffectAllowed(self):
        return self.isAnimationEffectsAllowed()

    def isAnimationEffectsAllowed(self):
        if self._key_unreleased:
            # если одна из клавиш для перелистывания картинок зажата и не отпускается,
            # то отменяем анимацию, чтобы анимация не отнимала время
            # print('отмена анимации', time.time())
            return False
        # print('продолжение анимации')
        return self.STNG_effects

    def isBlockedByAnimation(self):
        return self.isAnimationEffectsAllowed() and self.block_paginating

    def keyReleaseEvent(self, event):
        # isAutoRepeat даёт отфильтровать ненужные срабатывания
        # иначе при зажатой клавише keyReleaseEvent будет генерироваться без конца

        if self.check_thumbnails_fullscreen():
            return

        if not event.isAutoRepeat():
            self._key_pressed = False
            self._key_unreleased = False
        # print('keyReleaseEvent')
        key = event.key()
        if key == Qt.Key_Tab:
            self.cycle_change_page()
        if self.is_library_page_active():
            if key == Qt.Key_Up:
                LibraryData().choose_previous_folder()
            elif key == Qt.Key_Down:
                LibraryData().choose_next_folder()
        else:
            if self.is_start_page_active():
                return
            if self.check_scroll_lock():
                if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
                    length = 1.0
                    if event.modifiers() & Qt.ShiftModifier:
                        length *= 20.0
                    if key == Qt.Key_Up:
                        delta =  QPoint(0, 1) * length
                    elif key == Qt.Key_Down:
                        delta =  QPoint(0, -1) * length
                    elif key == Qt.Key_Left:
                        delta =  QPoint(1, 0) * length
                    elif key == Qt.Key_Right:
                        delta =  QPoint(-1, 0) * length
                    self.image_center_position += delta
                    self.update()
            else:
                if key == Qt.Key_Up:
                    main_window = Globals.main_window
                    main_window.do_scale_image(0.05, cursor_pivot=False)
                elif key == Qt.Key_Down:
                    main_window = Globals.main_window
                    main_window.do_scale_image(-0.05, cursor_pivot=False)
                elif key == Qt.Key_Right:
                    if event.modifiers() & Qt.AltModifier:
                        LibraryData().show_viewed_image_next()
                    elif event.modifiers() & Qt.ControlModifier and self.frameless_mode:
                        self.toggle_monitor('right')
                    elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                        LibraryData().show_next_image()
                elif key == Qt.Key_Left:
                    if event.modifiers() & Qt.AltModifier:
                        LibraryData().show_viewed_image_prev()
                    elif event.modifiers() & Qt.ControlModifier and self.frameless_mode:
                        self.toggle_monitor('left')
                    elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                        LibraryData().show_previous_image()
        self.update()

    def check_thumbnails_fullscreen(self):
        CP = Globals.control_panel
        if CP is not None and CP.fullscreen_flag:
            return True
        return False

    def cancel_thumbnails_fullscreen(self):
        CP = Globals.control_panel
        if CP is not None and CP.fullscreen_flag:
            CP.do_toggle_fullscreen()

    def keyPressEvent(self, event):
        key = event.key()

        if self.check_thumbnails_fullscreen():
            if key == Qt.Key_Escape:
                self.cancel_thumbnails_fullscreen()
                self.update()

            return

        if self._key_pressed:
            self._key_unreleased = True # зажата
        self._key_pressed = True # нажата
        # print('keyPressEvent')
        if key == Qt.Key_Escape:
            if self.contextMenuActivated:
                self.contextMenuActivated = False
            elif self.input_rect:
                self.region_zoom_in_cancel()
            elif SettingsWindow.isWindowVisible:
                SettingsWindow.instance.hide()
            else:
                self.require_window_closing()
        elif key == Qt.Key_F1:
            help_text.toggle_infopanel(self)
        elif event.nativeScanCode() == 0x29:
            self.open_settings_window()

        if self.is_library_page_active():
            if key == Qt.Key_Backtab:
                LibraryData().choose_doom_scroll()
            elif key == Qt.Key_Delete:
                LibraryData().delete_current_folder()
            elif check_scancode_for(event, "U"):
                LibraryData().update_current_folder()
        else:
            if self.is_start_page_active():
                return
            if key == Qt.Key_Backtab:
                LibraryData().choose_doom_scroll()
            elif key == Qt.Key_Delete:
                LibraryData().delete_current_image()
            elif key == Qt.Key_Home:
                LibraryData().jump_to_first()
            elif key == Qt.Key_End:
                LibraryData().jump_to_last()
            elif key == Qt.Key_Space:
                if self.animated:
                    im_data = self.image_data
                    im_data.anim_paused = not im_data.anim_paused
                self.update()
            elif check_scancode_for(event, ("W", "S", "A", "D")):
                length = 1.0
                if event.modifiers() & Qt.ShiftModifier:
                    length *= 20.0
                if check_scancode_for(event, "W"):
                    delta =  QPoint(0, 1) * length
                elif check_scancode_for(event, "S"):
                    delta =  QPoint(0, -1) * length
                elif check_scancode_for(event, "A"):
                    delta =  QPoint(1, 0) * length
                elif check_scancode_for(event, "D"):
                    delta =  QPoint(-1, 0) * length
                self.image_center_position += delta
                self.update()
            elif check_scancode_for(event, "Y"):
                if self.frameless_mode:
                    self.toggle_to_frame_mode()
                else:
                    self.toggle_to_frameless_mode()
            elif check_scancode_for(event, "F"):
                Globals.control_panel.manage_favorite_list()
            elif check_scancode_for(event, "C"):
                self.show_image_center = not self.show_image_center
                self.update()
            elif check_scancode_for(event, "D"):
                self.STNG_show_thirds = not self.STNG_show_thirds
                self.update()
            elif check_scancode_for(event, "T"):
                tagging.toggle_overlay(self)
                self.update()
            elif check_scancode_for(event, "I"):
                self.invert_image = not self.invert_image
                self.update()
            elif check_scancode_for(event, "G"):
                self.toggle_test_animation()
            elif check_scancode_for(event, "K"):
                pass
            elif check_scancode_for(event, "R"):
                self.start_inframed_image_saving(event)
            elif check_scancode_for(event, "M"):
                self.mirror_current_image(event.modifiers() & Qt.ControlModifier)
            elif check_scancode_for(event, "P"):
                self.toggle_stay_on_top()
                self.update()
            elif check_scancode_for(event, "U"):
                LibraryData().update_current_folder()
        self.update()

    def toggle_test_animation(self):
        if self.isAnimationEffectsAllowed():
            icp = self.image_center_position
            new_image_scale = self.image_scale + self.image_scale*0.5
            self.animate_properties(
                [
                    (self, "image_center_position", icp, icp+QPoint(100, 0), self.update),
                    (self, "image_scale", self.image_scale, new_image_scale, self.update),
                ]
            )
        else:
            self.show_center_label('Отмена!\nАнимационные эффекты отключены в настройках', error=True)

    def mirror_current_image(self, ctrl_pressed):
        if self.pixmap:
            tm = QTransform()
            if ctrl_pressed:
                tm = tm.scale(1, -1)
            else:
                tm = tm.scale(-1, 1)
            self.rotated_pixmap = self.get_rotated_pixmap().transformed(tm)
            self.update()

    def start_inframed_image_saving(self, event):
        shift_pressed = event.modifiers() & Qt.ShiftModifier
        ctrl_pressed = event.modifiers() & Qt.ControlModifier
        self.save_inframed_image(shift_pressed, ctrl_pressed)

    def save_inframed_image(self, use_screen_scale, reset_path):
        if not self.image_data.filepath or self.error:
            self.show_center_label("Невозможно сохранить: нет файла или файл не найден", error=True)
            return
        path = self.image_data.filepath
        pixmap = self.get_rotated_pixmap()
        save_pixmap = QPixmap(self.size())
        save_pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(save_pixmap)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        im_rect = self.get_image_viewport_rect()
        painter.drawPixmap(im_rect.toRect(), pixmap)
        painter.end()
        if self.zoom_region_defined:
            zoomed_region = self.projected_rect.intersected(im_rect.toRect())
            save_pixmap = save_pixmap.copy(zoomed_region)
        name, ext = os.path.splitext(os.path.basename(path))
        if not ext.lower().endswith((".png", ".jpg", ".jpeg",)):
            ext = ".png"
        formated_datetime = datetime.datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        rootpath = SettingsWindow.get_setting_value("inframed_folderpath")
        if reset_path:
            _path = self.set_path_for_saved_pictures(rootpath)
            if _path:
                rootpath = _path
        new_path = os.path.abspath(os.path.join(rootpath, f"{formated_datetime}{ext}"))
        if not use_screen_scale:
            factor = 1/self.image_scale
            save_pixmap = save_pixmap.transformed(QTransform().scale(factor, factor),
                                                                        Qt.SmoothTransformation)
        save_pixmap.save(new_path)
        self.show_center_label(f"Изображение сохранено в\n{new_path}")

    def set_path_for_saved_pictures(self, init_path):
        msg = "Выберите папку, в которую будут складываться картинки"
        path = QFileDialog.getExistingDirectory(None, msg, init_path)
        if os.path.exists(path):
            rootpath = str(path)
            SettingsWindow.set_setting_value('inframed_folderpath', rootpath)
            return rootpath
        return None

    def save_image_as(self, _format):
        content_filepath = self.image_filepath
        if self.pixmap:
            if self.copied_from_clipboard:
                pixmap = self.get_rotated_pixmap()
            else:
                pixmap = self.pixmap
        elif self.animated:
            pixmap = self.get_rotated_pixmap()
        image = pixmap.toImage()
        path, ext = os.path.splitext(content_filepath)
        content_filepath = f"{path}.{_format}"
        filepath = QFileDialog.getSaveFileName(
            None, "Сохранение файла",
            content_filepath, None
        )
        image.save(filepath[0], _format)

    def do_toggle_two_monitors_wide(self):
        if self.two_monitors_wide:

            pos = QPoint(0, 0)
            size = QSize(int(self.rect().width()/2), self.rect().height())
            self.setGeometry(QRect(pos, size))

            self.two_monitors_wide = False
        else:
            pos = QPoint(0, 0)
            size = QSize(self.rect().width()*2, self.rect().height())
            self.setGeometry(QRect(pos, size))

            self.two_monitors_wide = True

    def toggle_monitor(self, direction):
        if not self.two_monitors_wide:
            desktop = QDesktopWidget()
            for i in range(0, desktop.screenCount()):
                r = desktop.screenGeometry(screen=i)
                center = self.frameGeometry().center()
                if r.contains(center):
                    break
            if direction == "right":
                i += 1
            elif direction == "left":
                i -= 1
            if i > desktop.screenCount()-1:
                i = 0
            elif i < 0:
                i = desktop.screenCount()-1

            d_rect = desktop.screenGeometry(screen=i)
            size = QSize(self.rect().width(), self.rect().height())
            pos = d_rect.topLeft()
            self.setGeometry(QRect(pos, size))

        self.update()

    def copy_to_clipboard(self):
        if self.pixmap:
            if self.copied_from_clipboard:
                pixmap = self.get_rotated_pixmap()
            else:
                pixmap = self.pixmap
            QApplication.clipboard().setPixmap(pixmap)
        else:
            label_msg = 'Отмена! Функция не реализована для анимационного контента'
            self.show_center_label(label_msg, error=True)

    def paste_from_clipboard(self):
        if self.pixmap:
            new_pixmap = QPixmap.fromImage(QApplication.clipboard().image())
            if new_pixmap.width() != 0:
                self.copied_from_clipboard = True
                self.pixmap = new_pixmap
                self.get_rotated_pixmap(force_update=True)
                self.restore_image_transformations()
                self.show_center_label("вставлено")
        self.update()

    def get_selected_comment(self, event):
        image_comments = comments.get_comments_for_image()
        selected_comment = None
        if image_comments and hasattr(image_comments[0], "screen_rect"):
            for comment in image_comments:
                if comment.screen_rect.contains(event.pos()):
                    selected_comment = comment
                    break
        return selected_comment

    def contextMenuChangeSVGScale(self):
        contextMenu = QMenu()
        contextMenu.setStyleSheet(self.context_menu_stylesheet)

        factors = [1, 5, 10, 20, 30, 40, 50, 80, 100]
        actions = []
        current_factor = self.image_data.svg_scale_factor
        for factor in factors:
            action = contextMenu.addAction(f"x{factor}")
            action.setCheckable(True)
            action.setChecked(factor==current_factor)
            actions.append((action, factor))

        cur_action = contextMenu.exec_(QCursor().pos())
        self.contextMenuActivated = False
        if cur_action is not None:
            for (action, factor) in actions:
                if cur_action == action:
                    self.image_data.svg_scale_factor = factor
                    self.show_image(self.image_data)
                    self.get_rotated_pixmap(force_update=True)
                    w = self.pixmap.width()
                    h = self.pixmap.height()
                    text = f"{w}x{h}"
                    self.show_center_label(text)

    def contextMenuEvent(self, event):
        contextMenu = QMenu()
        contextMenu.setStyleSheet(self.context_menu_stylesheet)

        self.contextMenuActivated = True
        if self.is_library_page_active():
            folder_data = None
            if self.folders_list:
                for item_rect, item_data in self.folders_list:
                    if item_rect.contains(event.pos()):
                        folder_data = item_data
            if folder_data and not folder_data.fav:
                action_title = f"Открыть папку \"{folder_data.folder_path}\" в копии"
                open_separated = contextMenu.addAction(action_title)
                toggle_two_monitors_wide = None
                if self.frameless_mode:
                    if self.two_monitors_wide:
                        text = "Вернуть окно в монитор"
                    else:
                        text = "Развернуть окно на два монитора"
                    toggle_two_monitors_wide = contextMenu.addAction(text)
                rerun_extended_mode = None
                if not Globals.lite_mode:
                    rerun_extended_mode = contextMenu.addAction("Перезапуск (для сброса лишней памяти)")

                action = contextMenu.exec_(self.mapToGlobal(event.pos()))
                self.contextMenuActivated = False
                if action is not None:
                    if action == open_separated:
                        open_in_separated_app_copy(folder_data)
                    elif action == toggle_two_monitors_wide:
                        self.do_toggle_two_monitors_wide()
                    elif action == rerun_extended_mode:
                        do_rerun_in_extended_mode(self.is_library_page_active())
        else:
            show_in_gchrome = None
            show_in_explorer = None
            place_at_center = None
            go_to_folder = None
            save_as_png = None
            save_as_jpg = None
            go_to_folder = None
            copy_to_cp = None
            copy_from_cp = None
            toggle_two_monitors_wide = None

            delete_comment = None
            change_comment_text = None
            change_comment_borders = None

            crash_simulator = None

            change_svg_scale = None

            copy_image_metadata = None

            rerun_in_extended_mode = None
            rerun_extended_mode = None

            run_unsupported_file = None

            minimize_window = contextMenu.addAction("Свернуть")

            contextMenu.addSeparator()

            if Globals.CRASH_SIMULATOR:
                crash_simulator = contextMenu.addAction("Крашнуть приложение (для дебага)...")

            open_settings = contextMenu.addAction("Настройки...")

            contextMenu.addSeparator()

            if not self.is_pureref_page_active():

                if self.image_data and not self.image_data.is_supported_filetype:
                    run_unsupported_file = contextMenu.addAction("Открыть неподдерживаемый файл...")

                contextMenu.addSeparator()

                sel_comment = self.get_selected_comment(event)
                if sel_comment:
                    action_text = f'Редактировать текст комента "{sel_comment.get_title()}"'
                    change_comment_text = contextMenu.addAction(action_text)

                    action_text = f'Переопределить границы комента "{sel_comment.get_title()}"'
                    change_comment_borders = contextMenu.addAction(action_text)

                    action_text = f'Удалить комент "{sel_comment.get_title()}"'
                    delete_comment = contextMenu.addAction(action_text)

                    contextMenu.addSeparator()

                ci = LibraryData().current_folder().current_image()
                if ci.image_metadata:
                    copy_image_metadata = contextMenu.addAction("Скопировать метаданные в буферобмена")

            contextMenu.addSeparator()

            if not self.is_pureref_page_active():
                open_in_sep_app = contextMenu.addAction("Открыть в отдельной копии")
                if not self.error:
                    show_in_explorer = contextMenu.addAction("Найти на диске")
                    show_in_gchrome = contextMenu.addAction("Открыть в Google Chrome")
                    place_at_center = contextMenu.addAction("Вернуть картинку в центр окна")

            if self.frameless_mode:
                text = "Переключиться в оконный режим"
            else:
                text = "Переключиться в полноэкранный режим"
            toggle_frame_mode = contextMenu.addAction(text)
            if self.frameless_mode:
                if self.two_monitors_wide:
                    text = "Вернуть окно в монитор"
                else:
                    text = "Развернуть окно на два монитора"
                toggle_two_monitors_wide = contextMenu.addAction(text)

            if not self.is_pureref_page_active():
                if Globals.lite_mode:
                    contextMenu.addSeparator()
                    rerun_in_extended_mode = contextMenu.addAction("Перезапустить в обычном режиме")
                else:
                    contextMenu.addSeparator()
                    rerun_extended_mode = contextMenu.addAction("Перезапуск (для сброса лишней памяти)")

            contextMenu.addSeparator()

            if not self.is_pureref_page_active():
                if self.svg_rendered:
                    text = "Изменить разрешение растеризации SVG-файла..."
                    change_svg_scale = contextMenu.addAction(text)
                    contextMenu.addSeparator()

                if not self.error:
                    save_as_png = contextMenu.addAction("Сохранить в .png...")
                    save_as_jpg = contextMenu.addAction("Сохранить в .jpg...")
                    copy_to_cp = contextMenu.addAction("Копировать в буфер обмена")
                    copy_from_cp = contextMenu.addAction("Вставить из буфера обмена")
                    if LibraryData().current_folder().fav:
                        contextMenu.addSeparator()
                        action_title = "Перейти из избранного в папку с этим изображением"
                        go_to_folder = contextMenu.addAction(action_title)

            action = contextMenu.exec_(self.mapToGlobal(event.pos()))
            self.contextMenuActivated = False
            if action is not None:
                if action == show_in_explorer:
                    Globals.control_panel.show_in_folder()
                elif action == crash_simulator:
                    1 / 0
                elif action == run_unsupported_file:
                    import win32api
                    win32api.ShellExecute(0, "open", self.image_data.filepath, None, ".", 1)
                elif action == minimize_window:
                    Globals.main_window.showMinimized()
                elif action == show_in_gchrome:
                    main_window = Globals.main_window
                    if main_window.image_filepath:
                        open_in_google_chrome(main_window.image_filepath)
                elif action == toggle_two_monitors_wide:
                    self.do_toggle_two_monitors_wide()
                elif action == place_at_center:
                    self.restore_image_transformations()
                    self.update()
                elif action == toggle_frame_mode:
                    if self.frameless_mode:
                        self.toggle_to_frame_mode()
                    else:
                        self.toggle_to_frameless_mode()
                elif action == open_settings:
                    self.open_settings_window()
                elif action == save_as_png:
                    self.save_image_as("png")
                elif action == save_as_jpg:
                    self.save_image_as("jpg")
                elif action == go_to_folder:
                    LibraryData().go_to_folder_of_current_image()
                elif action == copy_to_cp:
                    self.copy_to_clipboard()
                elif action == copy_from_cp:
                    self.paste_from_clipboard()
                elif action == open_in_sep_app:
                    open_in_separated_app_copy(LibraryData().current_folder())
                elif action == delete_comment:
                    sel_comment = self.get_selected_comment(event)
                    if sel_comment:
                        comments.delete_comment(sel_comment)
                        self.update()
                elif action == change_comment_text:
                    sel_comment = self.get_selected_comment(event)
                    if sel_comment:
                        comments.CommentWindow().show(sel_comment, 'edit')
                elif action == change_comment_borders:
                    sel_comment = self.get_selected_comment(event)
                    if sel_comment:
                        self.comment_data_candidate = sel_comment
                elif action == copy_image_metadata:
                    QApplication.clipboard().setText(ci.image_metadata_info)
                elif action == change_svg_scale:
                    self.contextMenuChangeSVGScale()
                elif action == rerun_in_extended_mode:
                    do_rerun_in_extended_mode(False)
                elif action == rerun_extended_mode:
                    do_rerun_in_extended_mode(self.is_library_page_active())

    def closeEvent(self, event):
        if Globals.DEBUG:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def open_settings_window(self):
        window = SettingsWindow(self)
        if window.isVisible():
            window.hide()
        else:
            window.show()
            window.activateWindow()


def choose_start_option_callback(do_start_server, path):
    if Globals.force_full_mode:
        ret = QMessageBox.No
    else:
        if Globals.do_not_show_start_dialog:
            # запускаем лайтоый (упрощённый) режим
            ret = QMessageBox.Yes
        else:
            # иначе по дефолту не запускаем, но обязательно спрашиваем
            ret = QMessageBox.No
            if not Globals.started_from_sublime_text:
                if os.path.exists(path):
                    ret = QMessageBox.question(None,
                        "Вопрос",
                        'Не обнаружено запущенной копии приложения.\n\n'
                        f"Запуститься в лайтовом (упрощённом) режиме?",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Close,
                        )
    if ret == QMessageBox.Yes:
        print("Rerun from choose_start_option_callback...")
        start_lite_process(path)
        sys.exit(0)
    elif ret == QMessageBox.No:
        # finally start server
        do_start_server()
    elif ret == QMessageBox.Close:
        sys.exit(0)

def open_request(path):
    LibraryData().handle_input_data(path)
    MW = Globals.main_window
    if MW.frameless_mode:
        MW.showMaximized()
    else:
        MW.show()
    MW.activateWindow()
    to_print = f'retrieved data: {path}'
    print(to_print)

def input_path_dialog(path, exit=True):
    if os.path.exists(path):
        pass
    else:
        path = str(QFileDialog.getExistingDirectory(None, "Выбери папку с пикчами"))
        if not path and exit:
            QMessageBox.critical(None, "Ошибочка",
                                            "Ну раз ничего не выбрал, то я закрываюсь.\nПака")
            sys.exit()
    return path

def show_system_tray(app, icon):
    sti = QSystemTrayIcon(app)
    sti.setIcon(icon)
    app.setProperty("stray_icon", sti)


    ICON_HEIGHT = 32
    # список оффестов иконки для получения для бесшовной анимации
    offsets = list(range(0, ICON_HEIGHT+1))
    offsets.extend(list(range(-ICON_HEIGHT, 0)))
    opm = QPixmap(icon.pixmap(icon.actualSize(QSize(ICON_HEIGHT, ICON_HEIGHT))))
    offsets = itertools.cycle(offsets)
    def tray_icon_animation_step():
        offset = next(offsets)
        pm = QPixmap(opm.width(), opm.height())
        pm.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pm)
        painter.drawPixmap(QPoint(offset, 0), opm)
        painter.end()
        icon_frame = QIcon(pm)
        sti.setIcon(icon_frame)

    def tray_icon_animation_reset():
        sti.setIcon(icon)

    app.setProperty('tray_icon_animation_step', tray_icon_animation_step)
    app.setProperty('tray_icon_animation_reset', tray_icon_animation_reset)

    @pyqtSlot()
    def on_trayicon_activated(reason):
        MW = Globals.main_window
        if reason == QSystemTrayIcon.Trigger:
            if MW.frameless_mode:
                MW.showMaximized()
                if MW.need_for_init_after_call_from_tray:
                    MW.need_for_init_after_call_from_tray = False
                    MW.restore_image_transformations()
                    MW.update()
            else:
                MW.showNormal()
            MW.activateWindow()
        if reason == QSystemTrayIcon.Context:
            menu = QMenu()
            process = psutil.Process(os.getpid())
            mb_size = process.memory_info().rss / 1024 / 1024
            memory_status = f'Memory allocated ~{mb_size:0.2f} MB'
            memory = menu.addAction(memory_status)
            menu.addSeparator()
            quit = menu.addAction('Quit')
            action = menu.exec_(QCursor().pos())
            if action == quit:
                app = QApplication.instance()
                app.quit()
            elif action == memory:
                msg = "Эта команда должна удалять лишние объекты,\nсейчас она этого не делает"
                QMessageBox.critical(None, "NotImplemented", msg)
        return
    sti.activated.connect(on_trayicon_activated)
    sti.setToolTip("\n".join((Globals.app_title, Globals.github_repo)))
    sti.show()
    return sti

def get_crashlog_filepath():
    return os.path.join(os.path.dirname(__file__), "crash.log")

def excepthook(exc_type, exc_value, exc_tb):
    # пишем инфу о краше
    if type(exc_tb) is str:
        traceback_lines = exc_tb
    else:
        traceback_lines = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    # locale.setlocale(locale.LC_ALL, "russian")
    datetime_string = time.strftime("%A, %d %B %Y %X").capitalize()
    spaces = " "*15
    dt = f"{spaces} {datetime_string} {spaces}"
    dashes = "-"*len(dt)
    dt_framed = f"{dashes}\n{dt}\n{dashes}\n"
    with open(get_crashlog_filepath(), "a+", encoding="utf8") as crash_log:
        crash_log.write("\n"*10)
        crash_log.write(dt_framed)
        crash_log.write("\n")
        crash_log.write(traceback_lines)
    print(traceback_lines)
    if not Globals.USE_SOCKETS:
        ServerOrClient.remove_server_data()
    app = QApplication.instance()
    stray_icon = app.property("stray_icon")
    if stray_icon:
        stray_icon.hide()
    if not Globals.DEBUG:
        _restart_app(aftercrash=True)
    sys.exit()

def _restart_app(aftercrash=False):
    if aftercrash:

        filepath = None
        try:
            filepath = LibraryData().current_folder().current_image().filepath
        except:
            pass
        if filepath is not None:
            subprocess.Popen([sys.executable, sys.argv[0], filepath, "-aftercrash"])
        else:
            subprocess.Popen([sys.executable, sys.argv[0], "-aftercrash"])
    else:
        filepath = None
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
        if not os.path.exists(filepath):
            filepath = None
        if filepath is not None:
            subprocess.Popen([sys.executable, sys.argv[0], filepath])
        else:
            subprocess.Popen([sys.executable, sys.argv[0]])

def exit_threads():
    if not Globals.USE_SOCKETS:
        ServerOrClient.remove_server_data()
    # принудительно глушим все потоки, что ещё работают
    for thread in ThumbnailsThread.threads_pool:
        thread.terminate()
        # нужно вызывать terminate вместо exit

def start_lite_process(path):
    if Globals.DEBUG:
        app_path = __file__
    else:
        app_path = sys.argv[0]
    args = [sys.executable, app_path, path, "-lite"]
    subprocess.Popen(args)

def do_rerun_in_extended_mode(is_on_library_page):
    path = LibraryData.get_content_path(LibraryData().current_folder())
    if Globals.DEBUG:
        app_path = __file__
    else:
        app_path = sys.argv[0]
    args = [sys.executable, app_path, path, "-extended"]
    if is_on_library_page:
        args.append("-forcelibrarypage")
    subprocess.Popen(args)
    app = QApplication.instance()
    app.exit()

def open_in_separated_app_copy(folder_data):
    content_path = LibraryData.get_content_path(folder_data)
    if content_path is not None:
        # если есть второй монитор, то уводим окно на него,
        # перемещая для этого курсор
        desktop = QDesktopWidget()
        screen_num = desktop.screenNumber(Globals.main_window)
        for i in range(0, desktop.screenCount()):
            if i != screen_num:
                r = desktop.screenGeometry(screen=i)
                QCursor().setPos(r.center())
                break
        start_lite_process(content_path)
    else:
        msg = "Ни изображение, ни папка, в которой оно находится, не существуют"
        QMessageBox.critical(None, "Отмена!", msg)

def get_predefined_path_if_started_from_sublimeText():
    process = psutil.Process(os.getpid())
    cmdline = process.cmdline()
    if "-u" in cmdline:
        print('started from sublime text')
        # run from sublime_text
        Globals.started_from_sublime_text = True
        default_paths_txt = os.path.join(os.path.dirname(__file__), "user_data",
                                                        Globals.DEFAULT_PATHS_FILENAME)
        create_pathsubfolders_if_not_exist(os.path.dirname(default_paths_txt))
        if os.path.exists(default_paths_txt):
            with open(default_paths_txt, "r", encoding="utf8") as file:
                data = file.read() or None
                if data:
                    paths = list(filter(bool, data.split("\n")))
                    if paths:
                        path = paths[-1]
                        print("\tdefault path is set")
    else:
        path = ""
        Globals.started_from_sublime_text = False
    return path

class HookConsoleOutput:
    messages = []
    def __init__(self):
        self.console = sys.stdout
        # self.file = open('file.txt', 'w')

    def write(self, message):
        if self.console:
            self.console.write(message)
        type(self).messages.insert(0, (time.time(), message))
        type(self).messages = type(self).messages[:100]
        # self.file.write(message)

    def flush(self):
        if self.console:
            self.console.flush()
        # self.file.flush()

    @classmethod
    def get_messages(cls):
        l = []
        for timestamp, msg in cls.messages:
            if (time.time() - timestamp) < 10:
                l.append((timestamp, msg))
        return reversed(l)

def _main():

    os.chdir(os.path.dirname(__file__))
    sys.excepthook = excepthook
    pid = os.getpid()
    arguments = ", ".join(sys.argv)
    print(f'Proccess ID: {pid} {arguments}')

    if not Globals.DEBUG:
        RERUN_ARG = '-rerun'
        # Этот перезапуск с аргументом -rerun нужен для борьбы с идиотским проводником Windows,
        # который зачем-то запускает два процесса, и затем они держатся запущенными только для того,
        # чтобы работал один единственный процесс. У меня же всё традиционно, поэтому обязательный перезапуск.
        if (RERUN_ARG not in sys.argv) and ("-aftercrash" not in sys.argv):
            subprocess.Popen([sys.executable, *sys.argv, RERUN_ARG])
            sys.exit()

    if sys.argv[0].lower().endswith("_viewer.pyw"):
        Globals.DEBUG = True
    else:
        Globals.DEBUG = False

    sys.stdout = HookConsoleOutput()

    path = get_predefined_path_if_started_from_sublimeText()

    SettingsWindow.globals = Globals
    SettingsWindow.load_from_disk()

    Globals.do_not_show_start_dialog = SettingsWindow.get_setting_value("do_not_show_start_dialog")

    app = QApplication(sys.argv)
    app.aboutToQuit.connect(exit_threads)

    # задание иконки для таскбара
    myappid = 'sergei_krumas.image_viewer.client.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app_icon = QIcon()
    path_icon = os.path.abspath(os.path.join(".", "..", "icons/image_viewer.ico"))
    if not os.path.exists(path_icon) or True:
        path_icon = os.path.join(os.path.dirname(__file__), "image_viewer.ico")
    app_icon.addFile(path_icon)
    app.setWindowIcon(app_icon)

    frameless_mode = True and SettingsWindow.get_setting_value("show_fullscreen")
    # разбор аргументов
    parser = argparse.ArgumentParser()
    parser.add_argument('path', nargs='?', default=None)
    parser.add_argument('-lite', help="", action="store_true")
    parser.add_argument('-full', help="", action="store_true")
    parser.add_argument('-frame', help="", action="store_true")
    parser.add_argument('-forcelibrarypage', help="", action="store_true")
    parser.add_argument('-rerun', help="", action="store_true")
    parser.add_argument('-aftercrash', help="", action="store_true")
    args = parser.parse_args(sys.argv[1:])
    # print(args)
    if args.path:
        path = args.path
    if args.frame:
        frameless_mode = False
    if args.aftercrash:
        Globals.AFTERCRASH = True
    Globals.lite_mode = args.lite
    Globals.force_full_mode = args.full

    if Globals.lite_mode:
        app_icon = QIcon()
        path_icon = os.path.join(os.path.dirname(__file__), "image_viewer_lite.ico")
        app_icon.addFile(path_icon)
        app.setWindowIcon(app_icon)
        app.setQuitOnLastWindowClosed(True)

    if Globals.AFTERCRASH:
        filepath = get_crashlog_filepath()
        msg0 = f"Информация о краше сохранена в файл\n\t{filepath}"
        msg = f"Программа аварийно завершила работу! Application crash! \n{msg0}\n\nПерезапустить? Restart app?"
        ret = QMessageBox.question(None, 'Fatal Error!', msg, QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            _restart_app()
        sys.exit(0)

    ServerOrClient.globals = Globals

    if not Globals.lite_mode:
        if Globals.USE_SOCKETS:
            path = ServerOrClient.server_or_client_via_sockets(
                path,
                open_request,
                choose_start_option_callback,
            )
        else:
            path = ServerOrClient.server_or_client_via_files(path, input_path_dialog)

    Globals.is_path_exists = os.path.exists(path)

    generate_pixmaps(Globals, SettingsWindow)

    # создание иконки в трее
    sti = None
    if not Globals.lite_mode:
        sti = show_system_tray(app, app_icon)

    # инициализация библиотеки
    LibraryData.globals = Globals
    LibraryData.FolderData = FolderData
    # загрузка данных библиотеки
    lib = LibraryData()
    # создание элементов интерфейса
    MainWindow.globals = Globals
    MainWindow.LibraryData = LibraryData
    MW = Globals.main_window = MainWindow(frameless_mode=frameless_mode)
    if frameless_mode:
        MW.resize(800, 540) # размеры для случая, когда оно будет минимизировано через Win+KeyDown
        if not SettingsWindow.get_setting_value("hide_on_app_start"):
            MW.showMaximized()
    else:
        MW.show()
        MW.resize(800, 540)
    MW.setWindowIcon(app_icon)
    # Нужно для того, чтобы иконка показалась в таскбаре.
    # И нужно это делать до того как будет показана панель миниатюр.
    if not os.path.exists(path):
        MW.current_page = MW.pages.START_PAGE
        MW.update()
    app.processEvents()
    # создание панели управления
    ControlPanel.globals = Globals
    ControlPanel.LibraryData = LibraryData
    ControlPanel.SettingsWindow = SettingsWindow
    CP = Globals.control_panel = ControlPanel(MW)
    CP.show()
    # обработка входящих данных
    if path:
        LibraryData().handle_input_data(path)
    if args.forcelibrarypage:
        MW.change_page(MW.pages.LIBRARY_PAGE)

    # вход в петлю обработки сообщений
    exit_code = app.exec()
    if sti:
        sti.hide()
    sys.exit(exit_code)

def main():
    try:
        _main()
    except Exception as e:
        excepthook(type(e), e, traceback.format_exc())

if __name__ == '__main__':
    main()
