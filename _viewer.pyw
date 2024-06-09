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


from library_data import (LibraryData, FolderData, ImageData, BoardData, BoardNonAutoSerializedData,
                                                         LibraryModeImageColumn, ThumbnailsThread)
from board import BoardMixin
from help_text import HelpWidgetMixin
from commenting import CommentingMixin
from tagging import TaggingMixing
from slice_pipette_tool import SlicePipetteToolMixin

from pixmaps_generation import generate_pixmaps
from settings_handling import SettingsWindow
from control_panel import ControlPanel
from app_copy_prevention import ServerOrClient

from win32con import VK_CAPITAL, VK_NUMLOCK, VK_SCROLL
from ctypes import windll

import itertools
from functools import partial

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
    TAG_BIG_ICON = None
    COMMENTS_BIG_ICON = None
    NULL_PIXMAP = None
    ERROR_PREVIEW_PIXMAP = None
    lite_mode = False # лайтовый (упрощённый) режим работы приложения
    force_full_mode = False # обычный режим со всеми фичами без ограничений
    do_not_show_start_dialog = False
    is_path_exists = False
    started_from_sublime_text = False
    aftercrash = False

    DEBUG = True
    FORCE_FULL_DEBUG = False
    CRASH_SIMULATOR = True

    THUMBNAIL_WIDTH = 50
    AUGMENTED_THUBNAIL_INCREMENT = 20
    VIEW_HISTORY_SIZE = 20
    MULTIROW_THUMBNAILS_PADDING = 30
    PREVIEW_WIDTH = 200

    DISABLE_ITEM_DISTORTION_FIXER = True

    USE_GLOBAL_LIST_VIEW_HISTORY = False
    ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM = True
    USE_PIXMAP_PROXY_FOR_TEXT_ITEMS = True

    SECRET_HINTS_FILEPATH = "deep_secrets.txt"
    SESSION_FILENAME = "session.txt"
    FAV_FILENAME = "fav.txt"
    COMMENTS_FILENAME = "comments.txt"
    BOARDS_ROOT = "boards"
    TAGS_ROOT = "tags"
    USERROTATIONS_FILENAME = "viewer.ini"
    DEFAULT_PATHS_FILENAME = "default_paths.txt"

    app_title = "Krumassan Image Viewer v0.90 Alpha by Sergei Krumas"
    github_repo = "https://github.com/sergkrumas/image_viewer"

class BWFilterState():

    off = 0
    on_TRANSPARENT_BACKGROUND = 1
    on = 2

    @classmethod
    def cycle_toggle(cls, current_state):
        states = [cls.off, cls.on_TRANSPARENT_BACKGROUND, cls.on]
        cycled_states = itertools.cycle(states)
        for state in cycled_states:
            if current_state == state:
                break
        return next(cycled_states)

class MainWindow(QMainWindow, UtilsMixin, BoardMixin, HelpWidgetMixin, CommentingMixin, TaggingMixing, SlicePipetteToolMixin):

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
        BOARD_PAGE = 'BOARDPAGE'
        LIBRARY_PAGE = 'LIBRARYPAGE'

        @classmethod
        def all(cls):
            return [
                cls.START_PAGE,
                cls.VIEWER_PAGE,
                cls.BOARD_PAGE,
                cls.LIBRARY_PAGE
            ]

        @classmethod
        def name(cls, page_id):
            return {
                cls.START_PAGE: 'START',
                cls.VIEWER_PAGE: 'VIEWER',
                cls.BOARD_PAGE: 'BOARD',
                cls.LIBRARY_PAGE: 'LIBRARY',
            }.get(page_id)

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
        if self.is_board_page_active():
            self.board_dragEnterEvent(event)
        else:
            mime_data = event.mimeData()
            if mime_data.hasUrls() or mime_data.hasImage():
                event.accept()
            else:
                event.ignore()

    def dragMoveEvent(self, event):
        if self.is_board_page_active():
            self.board_dragMoveEvent(event)
        else:
            if event.mimeData().hasUrls():
                event.setDropAction(Qt.CopyAction)
                event.accept()
            else:
                event.ignore()

    def dropEvent(self, event):
        if self.is_board_page_active():
            self.board_dropEvent(event)
        else:
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
                all_but_last = paths[:-1]
                last_path = paths[-1:]
                if Globals.DEBUG:
                    to_print = f'Drop Event Data Local Paths: {paths}'
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
        distance = QVector2D(diff).length()
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

        for page_id, point in zip(pages, points):
            # painter.drawPoint(point)
            # код для отрисовки угловой кнопки
            r = QRect(QPoint(0, 0), QPoint(50, 30))
            r.moveCenter(point)
            self.corner_menu_items.append((page_id, r))

            cursor_pos = self.mapFromGlobal(QCursor().pos())
            page_name = self.pages.name(page_id)
            if r.contains(cursor_pos):
                painter.setOpacity(1.0)
                label_rect = QRect(r.topLeft(), r.bottomRight() + QPoint())
                label_rect.setWidth(200)
                text = page_name
                text_rect = label_rect
            else:
                painter.setOpacity(.8)
                text = page_name[0]
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
                self.hint_text = random.choice(self.secret_hints_list)

                rect = self.rect()
                self.secret_width = rect.width()
                self.secret_height = rect.height()

                rel = self.get_image_viewport_rect().topLeft() - QPoint(0, 0)
                x_rel = abs(rel.x())/self.get_image_viewport_rect().width()
                y_rel = abs(rel.y())/self.get_image_viewport_rect().height()
                self.secret_hint_top_left_pos_rel = QPointF(x_rel, y_rel)

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

    def draw_secret_hint(self, painter):
        if not self.secret_hints_list:
            raise "no data"

        if not self.hint_text:
            return

        if not self.frameless_mode:
            return

        opacity_val = fit(self.image_scale, self.START_HINT_AT_SCALE_VALUE, self.UPPER_SCALE_LIMIT, 0.0, 0.5)
        painter.setOpacity(opacity_val)

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

        self.Globals = Globals
        self.LibraryData = LibraryData
        self.ImageData = ImageData
        self.FolderData = FolderData
        self.BoardData = BoardData
        self.BoardNonAutoSerializedData = BoardNonAutoSerializedData

        if SettingsWindow.get_setting_value("hide_on_app_start"):
            self.need_for_init_after_call_from_tray = True
        else:
            self.need_for_init_after_call_from_tray = False
        super().__init__(*args, **kwargs)

        self.set_loading_text()

        self.prepare_secret_hints()

        self.set_window_title("")
        self.set_window_style()

        self.current_page = self.pages.START_PAGE

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

        self.setMouseTracking(True)
        self.installEventFilter(self)
        self.setAcceptDrops(True)

        self.gamepad = None
        self.gamepad_timer = None

        self.board_init()
        self.tagging_init()

        self.SettingsWindow = SettingsWindow
        SettingsWindow.settings_init(self)

        self.previews_list_active_item = None
        self.previews_list = None

        self.region_zoom_in_init()

        self.contextMenuActivated = False

        self.init_help_infopanel()

        self.error = False

        self.invert_image = False

        self.animation_tasks = []
        self.animation_timer = QTimer()
        self.animation_timer.setInterval(20)
        self.animation_timer.timeout.connect(self.do_properties_animation_on_timer)
        self.animation_timer_work_timestamp = time.time()

        self.block_paginating = False

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

        self.fullscreen_mode = False
        self.firstCall_showMaximized = True

        self.BW_filter_state = BWFilterState.off

        class CornerUIButtons():
            NO_BUTTON = 0
            LEFT_CORNER = 1
            RIGHT_CORNER = 2
            LEFT_CORNER_MENU = 3

        self.CornerUIButtons = CornerUIButtons
        self.corner_UI_button_pressed = self.CornerUIButtons.NO_BUTTON

        self.SPT_init()

        self.context_menu_stylesheet = """
        QMenu, QCheckBox{
            padding: 0px;
            font-size: 16px;
            font-weight: normal;
            font-family: 'Consolas';
        }
        QMenu::item, QCheckBox{
            padding: 10px;
            background: #303940;
            color: rgb(230, 230, 230);
        }
        QMenu::icon{
            padding-left: 15px;
        }
        QMenu::item:selected, QCheckBox:hover{
            background-color: rgb(253, 203, 54);
            color: rgb(50, 50, 50);
        }
        QMenu::item:checked, QCheckBox:checked{
            font-weight: bold;
            color: white;
            background: #304550;
        }
        QMenu::item:unchecked, QCheckBox:unchecked{
            background: #304550;
        }
        QMenu::item:checked:selected, QCheckBox:checked:hover{
            font-weight: bold;
            color: rgb(50, 50, 50);
            background-color: rgb(253, 203, 54);
        }
        QMenu::item:unchecked:selected, QCheckBox:unchecked:hover{
            color: rgb(50, 50, 50);
            background-color: rgb(253, 203, 54);
        }
        QMenu::item:disabled {
            background-color: #303940;
            color: black;
        }
        QMenu::separator {
            height: 1px;
            background: gray;
        }
        """

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

    def is_board_page_active(self):
        return self.current_page == self.pages.BOARD_PAGE

    def cycle_change_page(self):
        pages = self.pages.all()
        pages_shifted = self.pages.all()
        pages_shifted.append(pages_shifted.pop(0))
        for page, next_page in itertools.cycle(zip(pages, pages_shifted)):
            if page == self.current_page:
                break
        self.board_TextElementDeactivateEditMode()
        self.change_page(next_page)

    def change_page(self, requested_page, force=False):
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

        if self.handling_input and not force:
            self.update_control_panel_label_text()
            return

        if self.current_page == self.pages.VIEWER_PAGE:
            self.region_zoom_in_cancel()
            LibraryData().before_current_image_changed()
            cancel_fullscreen_on_control_panel()

        elif self.current_page == self.pages.BOARD_PAGE:
            self.board_region_zoom_do_cancel()
            cancel_fullscreen_on_control_panel()
            LibraryData().save_board_data()

        self.cancel_all_anim_tasks()
        self.hide_center_label()

        if requested_page == self.pages.LIBRARY_PAGE:
            LibraryData().update_current_folder_columns()
            self.autoscroll_set_or_reset()
            if Globals.control_panel is not None:
                Globals.control_panel.setVisible(False)
            self.previews_list_active_item = None
            for folder_data in LibraryData().folders:
                images_data = folder_data.images_list
                ThumbnailsThread(folder_data, Globals, run_from_library=True).start()
            self.transformations_allowed = False

        elif requested_page == self.pages.VIEWER_PAGE:
            self.recreate_control_panel(requested_page=self.pages.VIEWER_PAGE)
            self.viewer_reset() # для показа сообщения о загрузке
            LibraryData().after_current_image_changed()
            LibraryData().add_current_image_to_view_history()
            cf = LibraryData().current_folder()
            ThumbnailsThread(cf, Globals).start()
            self.transformations_allowed = True

        elif requested_page == self.pages.START_PAGE:
            if Globals.control_panel is not None:
                Globals.control_panel.setVisible(False)
            self.transformations_allowed = False

        elif requested_page == self.pages.BOARD_PAGE:
            self.recreate_control_panel(requested_page=self.pages.BOARD_PAGE)
            self.transformations_allowed = True
            LibraryData().load_board_data()



        if self.current_page == self.pages.START_PAGE and requested_page == self.pages.VIEWER_PAGE:
            self.restore_image_transformations()

        self.update_control_panel_label_text()

        self.current_page = requested_page
        self.update()

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

        class AnimationTask():
            def __init__(self, parent, anim_id, task_generation, easing, duration, anim_tracks, callback_on_finish, callback_on_start, user_data):
                super().__init__()

                self.main_window = parent
                self.anim_id = anim_id
                self.anim_tracks = anim_tracks
                self.task_generation = task_generation
                self.easing = easing
                self.on_finish_animation_callback = callback_on_finish
                self.on_start_animation_callback = callback_on_start
                self.animation_duration = duration
                self.user_data = user_data

                self.callback_args = []
                if anim_id == "zoom":
                    self.callback_args = [self]

                self._at_first_step = False
                self.animation_allowed = True

                self.main_window.animation_tasks.append(self)

            def stop(self, too_old=False):
                if self.animation_allowed:
                    self.animation_allowed = False
                    if self in self.main_window.animation_tasks:
                        self.main_window.animation_tasks.remove(self)
                    if self.on_finish_animation_callback and not too_old:
                        self.on_finish_animation_callback(*self.callback_args)
                    if too_old:
                        action = "terminated"
                    else:
                        action = "closed"
                    # self.evaluation_step(force=True)
                    msg = f'animation task {action}: {self.anim_id}'
                    print(msg)

            def evaluation_step(self, force=False):

                if (not self.animation_allowed) and not force:
                    return
                if not self._at_first_step:
                    self.at_start_timestamp = time.time()
                    self._at_first_step = True
                    if self.on_start_animation_callback:
                        self.on_start_animation_callback(*self.callback_args)
                    if self.task_generation > 0:
                        old_anim_tracks = self.anim_tracks[:]
                        self.anim_tracks.clear()
                        # обновление значений на текущие, ведь удалённый ранее таймер с тем же anim_id уже изменил текущее значение
                        for attr_host, attr_name, start_value, end_value, callback_func in old_anim_tracks:
                            if attr_host is None:
                                attr_host = self
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
                    if attr_host is None:
                        attr_host = self
                    setattr(attr_host, attr_name, value)
                    callback_func(*self.callback_args)
                if self.animation_duration < (time.time() - self.at_start_timestamp):
                    self.stop()

        return AnimationTask

    def do_properties_animation_on_timer(self):
        for animation_task in self.animation_tasks:
            animation_task.evaluation_step()
            self.animation_timer_work_timestamp = time.time()
        if time.time() - self.animation_timer_work_timestamp > 10.0:
            print("animation timer stopped")
            self.animation_timer.stop()

    def get_current_animation_tasks_id(self, anim_id):
        return [anim_task for anim_task in self.animation_tasks if anim_task.anim_id == anim_id]

    def get_current_animation_task_generation(self, anim_id=None):
        if anim_id is not None:
            for anim_task in self.animation_tasks[:]:
                if anim_task.anim_id == anim_id:
                    return anim_task.task_generation
        return 0

    def is_there_any_task_with_anim_id(self, anim_id):
        for anim_task in self.animation_tasks[:]:
            if anim_task.anim_id == anim_id:
                return True
        return False

    def cancel_all_anim_tasks(self):
        for anim_task in self.animation_tasks[:]:
            anim_task.stop(too_old=True)

    def animate_properties(self, anim_tracks,
                anim_id=None,
                callback_on_finish=None,
                callback_on_start=None,
                duration=0.2,
                easing=QEasingCurve.OutCubic,
                user_data=None,
            ):
        AnimationTask = self.get_animation_task_class()
        task_generation = 0
        if anim_id is not None:
            for anim_task in self.animation_tasks[:]:
                if anim_task.anim_id == anim_id and anim_task.animation_allowed:
                    default_generation = True

                    if anim_task.anim_id == "zoom" and (anim_task.user_data is not None) and (user_data is not None):
                        a = math.copysign(1.0, anim_task.user_data)
                        b = math.copysign(1.0, user_data)
                        if a != b:
                            default_generation = False

                    if default_generation:
                        task_generation = anim_task.task_generation + 1
                    else:
                        task_generation = 0
                    # msg = f'task generation {task_generation},   {user_data} {a} {b}'
                    # print(msg)
                    anim_task.stop(too_old=True)
        animation_task = AnimationTask(
            self,
            anim_id,
            task_generation,
            QEasingCurve(easing),
            duration,
            anim_tracks,
            callback_on_finish,
            callback_on_start,
            user_data
        )
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
        if self.isThumbnailsRowSlidingAnimationEffectAllowed() and (not only_set) and (not now_offset == new_offset) and (now_offset != 0):
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
                    anim_id="region_zoom_out",
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

    def region_zoom_build_input_rect(self):
        if self.INPUT_POINT1 and self.INPUT_POINT2:
            self.input_rect = build_valid_rect(self.INPUT_POINT1, self.INPUT_POINT2)
            self.projected_rect = fit_rect_into_rect(self.input_rect, self.rect())
            w = self.input_rect.width() or self.projected_rect.width()
            self.zoom_level = self.projected_rect.width()/w
            self.input_rect_animated = self.input_rect

    def region_zoom_do_zooming(self):
        if self.input_rect.width() != 0:
            # scale = 1/self.image_scale

            # 0. подготовка
            input_center = self.input_rect.center()
            self.input_rect_animated = QRect(self.input_rect)
            before_pos = QPointF(self.image_center_position)

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
                    anim_id="region_zoom_in",
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
            self.region_zoom_build_input_rect()
            self.region_zoom_in_UX_breaker_start(event)
        if self.region_zoom_break_activated:
            self.region_zoom_in_UX_breaker_start(event)

    def region_zoom_in_mouseReleaseEvent(self, event):
        if (not self.zoom_region_defined) and not self.region_zoom_break_activated:
            self.INPUT_POINT2 = event.pos()
            self.region_zoom_build_input_rect()
            if self.INPUT_POINT1 and self.INPUT_POINT2:
                self.zoom_region_defined = True
                self.region_zoom_do_zooming()
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

        if correct:
            self.correct_scale()

    def animation_stamp(self):
        movie = self.movie
        self.frame_delay = movie.nextFrameDelay()
        self.frame_time = time.time()

    def tick_animation(self):
        delta = (time.time() - self.frame_time) * 1000
        is_playing = not self.image_data.anim_paused
        movie = self.movie
        is_animation = movie.frameCount() > 1
        if delta > self.frame_delay and is_playing and is_animation:
            movie.jumpToNextFrame()
            self.animation_stamp()
            self.frame_delay = movie.nextFrameDelay()
            self.pixmap = movie.currentPixmap()
            self.get_rotated_pixmap(force_update=True)
            self.update()

    def is_animated_file_valid(self):
        movie = self.movie
        movie.jumpToFrame(0)
        self.animation_stamp()
        fr = movie.frameRect()
        if fr.isNull():
            self.invalid_movie = True
            self.animated = False
            self.error_pixmap_and_reset("Невозможно\nотобразить", "Файл повреждён")

    def show_animated(self, filepath, is_apng_file):
        if filepath is not None:
            self.invalid_movie = False
            self.image_filepath = filepath
            self.transformations_allowed = True
            self.animated = True
            if is_apng_file:
                self.movie = APNGMovie(filepath)
            else:
                self.movie = QMovie(filepath)
                self.movie.setCacheMode(QMovie.CacheAll)
            self.is_animated_file_valid()
        else:
            if self.movie:
                if isinstance(self.movie, QMovie):
                    self.movie.deleteLater()
                self.movie = None

    def show_svg(self, filepath):
        self.image_filepath = filepath
        self.transformations_allowed = True
        self.pixmap = load_svg(filepath, scale_factor=self.image_data.svg_scale_factor)
        self.svg_rendered = True

    def show_static(self, filepath, pass_=1):
        # pixmap = QPixmap(filepath)
        pixmap = load_image_respect_orientation(filepath)
        if pixmap and not pixmap.isNull():
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

    def show_image(self, image_data, only_set_thumbnails_offset=False):
        # reset
        self.rotated_pixmap = None
        self.image_data = image_data
        self.copied_from_clipboard = False
        filepath = self.image_data.filepath
        self.viewer_reset(simple=True)
        # setting new image
        self.error = False
        if filepath == "":
            self.error_pixmap_and_reset("Нет изображений", "", no_background=True)
        else:
            if not LibraryData().is_supported_file(filepath):
                filename = os.path.basename(filepath)
                self.error_pixmap_and_reset("Невозможно\nотобразить", f"Этот файл не поддерживается\n{filename}")
            else:
                try:
                    LibraryData().reset_apng_check_result()
                    animated = False or LibraryData().is_gif_file(filepath)
                    animated = animated or LibraryData().is_webp_file_animated(filepath)
                    animated = animated or LibraryData().is_apng_file_animated(filepath)
                    if animated:
                        self.show_animated(filepath, self.LibraryData().last_apng_check_result)
                    elif LibraryData().is_svg_file(filepath):
                        self.show_svg(filepath)
                    else:
                        self.show_static(filepath)
                except:
                    self.error_pixmap_and_reset("Файл повреждён", traceback.format_exc())
        if not self.error:
            self.read_image_metadata(image_data)
        self.restore_image_transformations()
        self.update_thumbnails_row_relative_offset(image_data.folder_data, only_set=only_set_thumbnails_offset)
        self.set_window_title(self.current_image_details())
        if self.error:
            self.tags_list = []
        else:
            self.tags_list = LibraryData().get_tags_for_image_data(image_data)
        self.update_control_panel_label_text()
        self.update()

    def error_pixmap_and_reset(self, title, message, no_background=False):
        self.error = True
        if not self.image_data.is_supported_filetype:
            if LibraryData.is_text_file(self.image_data.filepath):
                with open(self.image_data.filepath, "rb") as file:
                    message = file.read(500).decode("utf-8", "ignore") + "..."
                    title = ""
        self.pixmap = generate_info_pixmap(title, message, no_background=no_background)
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
        self.show_animated(None, False)
        if not simple:
            self.set_loading_text()
            main_window = Globals.main_window
            main_window.update()
            processAppEvents()

    def set_loading_text(self):
        # self.loading_text = random.choice(self.LOADING_TEXT)
        self.loading_text = "\n".join(self.LOADING_TEXT)

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
                movie = self.movie
                self.pixmap = movie.currentPixmap()
            self.rotated_pixmap = self.pixmap.transformed(rm)
        return self.rotated_pixmap

    def get_image_viewport_rect(self, debug=False, od=None):
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
        im_rect = QRectF(0, 0, new_width, new_height)
        im_rect.moveCenter(icp)
        return im_rect

    def get_secret_hint_rect(self):
        factor = self.image_scale/self.UPPER_SCALE_LIMIT
        new_width = self.secret_width*factor
        new_height = self.secret_height*factor
        rel = self.secret_hint_top_left_pos_rel
        r = self.get_image_viewport_rect()
        anchor_point = r.topLeft() + QPointF(r.width()*rel.x(), r.height()*rel.y()) + QPointF(new_width*2/3, new_height*2/3)
        pos = anchor_point
        hint_rect = QRectF(0, 0, new_width, new_height)
        hint_rect.moveTopLeft(pos)
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
        self.center_comment_window()

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

    def animate_noise_cells_effect(self):
        if self.STNG_show_noise_cells and noise:
            self.noise_time += 0.005
            self.update()

    def viewport_image_animation(self):
        if self.animated:
            self.tick_animation()

    def cursor_setter(self):
        CP = Globals.control_panel
        if self.isActiveWindow():
            if self.over_corner_menu_item():
                self.setCursor(Qt.PointingHandCursor)
            elif self.over_corner_button() or self.over_corner_button(corner_attr="topLeft"):
                self.setCursor(Qt.PointingHandCursor)
            elif self.is_library_page_active():
                if self.previews_list_active_item:
                    self.setCursor(Qt.PointingHandCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)

            elif self.is_viewer_page_active():
                if self.region_zoom_in_input_started:
                    self.setCursor(Qt.CrossCursor)
                elif CP and any(btn.underMouse() for btn in CP.buttons_list):
                    self.setCursor(Qt.PointingHandCursor)
                elif CP and CP.thumbnails_click(define_cursor_shape=True):
                    self.setCursor(Qt.PointingHandCursor)
                elif self.is_cursor_over_image() and \
                        (not self.is_library_page_active()) and \
                        not (CP and CP.globals.control_panel.underMouse()):
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            elif self.is_board_page_active():
                # курсор определяется в mouseMoveEvent
                pass
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def control_timer_handler(self):
        CP = Globals.control_panel
        if CP is not None:
            CP.control_panel_timer_handler()

    def on_timer(self):
        self.update_for_center_label_fade_effect()
        self.threads_info_watcher()
        self.control_timer_handler()

        if self.is_viewer_page_active():
            self.viewport_image_animation()

        elif self.is_board_page_active():
            self.board_timer_handler()

        self.animate_noise_cells_effect()

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

    def mousePressEventStartPage(self, event):

        if event.button() == Qt.LeftButton:
            path = input_path_dialog("", exit=False)
            if path:
                LibraryData().handle_input_data(path)
                self.update()
        elif event.button() == Qt.RightButton:
            self.open_settings_window()

    def ui_check_mouse_over_corners(self, event):
        if event.button() == Qt.LeftButton:
            if self.over_corner_button():
                return self.CornerUIButtons.RIGHT_CORNER
            elif self.over_corner_button(corner_attr="topLeft"):
                return self.CornerUIButtons.LEFT_CORNER
            elif self.over_corner_menu(corner_attr="topLeft"):
                return self.CornerUIButtons.LEFT_CORNER_MENU
        return self.CornerUIButtons.NO_BUTTON

    def ui_handle_corners_click(self, corner_button):
        if corner_button == self.CornerUIButtons.RIGHT_CORNER:
            self.require_window_closing()
        elif corner_button == self.CornerUIButtons.LEFT_CORNER:
            self.cycle_change_page()
        elif corner_button == self.CornerUIButtons.LEFT_CORNER_MENU:
            self.handle_menu_item_click()

    def mousePressEvent(self, event):

        self.context_menu_allowed = True

        corner_UI_button = self.ui_check_mouse_over_corners(event)
        if corner_UI_button > self.CornerUIButtons.NO_BUTTON:
            self.corner_UI_button_pressed = corner_UI_button
            return

        if self.SPT_check_mouse_event_inside_input_point(event):
            self.SPT_mousePressEvent(event)
            return

        if self.is_board_page_active():
            self.board_mousePressEvent(event)

        elif self.is_start_page_active():
            self.mousePressEventStartPage(event)
            self.update()

        elif self.is_library_page_active():
            if self.folders_list:
                for item_rect, item_data in self.folders_list:
                    if item_rect.contains(event.pos()):
                        # здесь устанавливаем текующую папку
                        LibraryData().make_folder_current(item_data)

            if self.previews_list:
                for item_rect, item_data in self.previews_list:
                    if item_rect.contains(event.pos()):
                        LibraryData().show_that_imd_on_viewer_page(item_data)


        elif self.is_viewer_page_active():
            if self.show_tags_overlay:
                self.tagging_main_mousePressEvent(self, event)
                return

            if event.button() == Qt.LeftButton:
                self.left_button_pressed = True

            if self.isLeftClickAndCtrl(event):
                self.region_zoom_in_mousePressEvent(event)

            elif self.isLeftClickAndCtrlShift(event):
                self.image_comment_mousePressEvent(event)

            if self.transformations_allowed:
                self.old_cursor_pos = self.mapped_cursor_pos()
                for anim_task in self.get_current_animation_tasks_id("zoom"):
                    anim_task.translation_delta_when_animation = QPointF(0, 0)
                if self.is_cursor_over_image():
                    self.image_translating = True
                    self.old_image_center_position = self.image_center_position
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

    def update_control_panel_label_text(self):
        CP = Globals.control_panel
        if CP is not None:
            CP.label_text_update()

    def mouseMoveEvent(self, event):

        self.cursor_setter()
        self.update_control_panel_label_text()

        if self.corner_UI_button_pressed > self.CornerUIButtons.NO_BUTTON:
            return

        if self.spt_input_point_dragging:
            self.SPT_mouseMoveEvent(event)
            return

        if self.is_board_page_active():
            self.board_mouseMoveEvent(event)

        elif self.is_start_page_active():
            self.update()
            return

        elif self.is_viewer_page_active():
            curpos = self.mapFromGlobal(QCursor().pos())
            if not self.tagging_sidebar_visible:
                self.tagging_sidebar_visible = self.get_tiny_sidebar_rect().contains(curpos)
            else:
                self.tagging_sidebar_visible = self.get_sidebar_rect().contains(curpos)
            if self.Globals.lite_mode:
                self.tagging_sidebar_visible = False

            self.tagging_sidebar_visible &= self.isActiveWindow()

            if self.show_tags_overlay:
                self.tagging_main_mouseMoveEvent(self, event)
                return

            if self.isLeftClickAndCtrl(event) or self.region_zoom_in_input_started:
                self.region_zoom_in_mouseMoveEvent(event)
            elif self.isLeftClickAndCtrlShift(event) or self.comment_data:
                self.image_comment_mouseMoveEvent(event)
            elif event.buttons() == Qt.LeftButton:
                if self.transformations_allowed and self.image_translating:
                    new =  self.old_image_center_position - (self.old_cursor_pos - self.mapped_cursor_pos())
                    old = self.image_center_position
                    if not self.is_there_any_task_with_anim_id("zoom"):
                        self.image_center_position = new
                    for anim_task in self.get_current_animation_tasks_id("zoom"):
                        anim_task.translation_delta_when_animation = self.mapped_cursor_pos() - self.old_cursor_pos

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

        if self.corner_UI_button_pressed > self.CornerUIButtons.NO_BUTTON:
            corner_UI_button = self.ui_check_mouse_over_corners(event)
            if corner_UI_button > self.CornerUIButtons.NO_BUTTON:
                self.ui_handle_corners_click(corner_UI_button)
            self.corner_UI_button_pressed = self.CornerUIButtons.NO_BUTTON
            return

        if self.spt_input_point_dragging:
            self.SPT_mouseReleaseEvent(event)
            return

        if self.is_board_page_active():
            self.board_mouseReleaseEvent(event)

        elif self.is_start_page_active():
            return

        elif self.is_viewer_page_active():
            if self.show_tags_overlay:
                self.tagging_main_mouseReleaseEvent(self, event)
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

                    for anim_task in self.get_current_animation_tasks_id("zoom"):
                        anim_task.translation_delta_when_animation_summary += anim_task.translation_delta_when_animation
                        anim_task.translation_delta_when_animation = QPointF(0, 0)

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
        elif self.is_board_page_active():
            if event.type() == QEvent.MouseButtonDblClick:
                if obj is self:
                    self.board_mouseDoubleClickEvent(event)
                    return True
        return False

    def toggle_to_frame_mode(self):
        f_geometry = self.frameGeometry()
        geometry = self.geometry()
        self.frameless_mode = False
        # self.hide() # вызов может спровоцировать закрытие всего приложения
        self.set_window_style()
        # здесь нельзя использовать show(), только showNormal,
        # потому что после show() окно не сразу даёт себя ресайзить,
        # и даёт ресайзить себя только после перетаскивания мышкой за область заголовка окна,
        # при этом при перетаскивании окно увеличивается до бывших увеличенных размеров,
        # что нежелательно
        self.showNormal()

        if self.is_viewer_page_active():
            r = self.get_image_viewport_rect()
        else:
            r = QRect(0, 0, 0, 0)
        if r.width() == 0:
            # случай, когда на экране отображется надпись "загрузка"
            # т.е. handling_input == True
            r = QRect(0, 0, 1800, 970)
            r.moveCenter(f_geometry.center())
        pos = r.topLeft()
        # для того чтобы на всех мониторах всё вело себя предсказуемо, а именно
        # при переходе из полноэкранного режима в оконный режим
        pos += QPoint(f_geometry.left(), f_geometry.top()) # monitor offset
        self.image_center_position = QPointF(
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
        old_pos = self.image_center_position
        global_offset = self.geometry().topLeft()
        self.frameless_mode = True
        self.set_window_style()
        self.showMaximized()
        desktop = QDesktopWidget()
        r = self.get_image_viewport_rect()
        w = r.width()
        h = r.height()
        # вычитаем, чтобы и на втором мониторе работало тоже
        global_offset -= self.frameGeometry().topLeft()
        self.image_center_position = old_pos + global_offset - self.get_center_position()
        self.update()

    def showMaximized(self):
        if False:
            # inherited
            super().showMaximized()
        else:
            desktop = QDesktopWidget()
            screens = QGuiApplication.screens()
            if self.firstCall_showMaximized:
                pos = QCursor().pos()
                self.firstCall_showMaximized = False
            else:
                pos = self.geometry().center()
            for n, screen in enumerate(screens):
                screen_geometry = screen.geometry()
                if screen_geometry.contains(pos):
                    geometry = screen_geometry
                    break
            if not self.fullscreen_mode:
                ag = desktop.availableGeometry()
                geometry.setHeight(ag.height())
                geometry.setWidth(ag.width())
            self.setGeometry(geometry)
        self.show()

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

        if self.is_board_page_active():
            self.board_wheelEvent(event)

        elif self.is_start_page_active():
            return

        elif self.is_library_page_active():
            self.wheelEventLibraryMode(scroll_value, event)

        elif self.is_viewer_page_active():

            if self.show_tags_overlay:
                self.tagging_main_wheelEvent(self, event)
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
        movie = self.movie
        speed = movie.speed()
        index = speed_values.index(int(speed))
        if index == len(speed_values)-1 and scroll_value > 0:
            pass
        elif index == 0 and scroll_value < 0:
            pass
        else:
            if scroll_value < 0:
                index -=1
            if scroll_value > 0:
                index +=1
        speed = speed_values[index]
        movie.setSpeed(speed)

    def do_scroll_playbar(self, scroll_value):
        if not self.animated:
            return
        movie = self.movie
        frames_list = list(range(0, movie.frameCount()))
        if scroll_value > 0:
            pass
        else:
            frames_list = list(reversed(frames_list))
        frames_list.append(0)
        i = frames_list.index(movie.currentFrameNumber()) + 1
        movie.jumpToFrame(frames_list[i])
        self.pixmap = movie.currentPixmap()
        self.get_rotated_pixmap(force_update=True)

    def do_scroll_images_list(self, scroll_value):
        if scroll_value > 0:
            LibraryData().show_next_image()
        elif scroll_value < 0:
            LibraryData().show_previous_image()

    def set_original_scale(self):
        self.image_scale = 1.0
        self.update()

    def do_scale_image(self, scroll_value, cursor_pivot=True, override_factor=None, slow=False):

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

        animated_zoom_enabled = self.isAnimationEffectsAllowed() and self.STNG_animated_zoom and not self._key_pressed

        if override_factor:
            factor = override_factor
        else:
            # чем больше scale_speed, тем больше придётся крутить колесо мыши
            # для одной и той же дельты увеличения или уменьшения
            if animated_zoom_enabled:
                gen = self.get_current_animation_task_generation(anim_id="zoom")
                # scale_speed = 2.5 - 1.4*(min(20, gen)/20)
                start_speed = 4.3
                scale_speed = start_speed - (start_speed-1.1)*(min(20, gen)/25)
                # msg = f'zoom generation: {gen}, result speed value: {scale_speed}'
                # print(msg)
            else:
                scale_speed = 5

            if slow:
                scale_speed = 20

            if scroll_value > 0:
                factor = scale_speed/(scale_speed-1)
            else:
                factor = (scale_speed-1)/scale_speed



        if override_factor:
            pivot = QPointF(self.rect().center())
        else:
            if cursor_pivot:
                if self.get_image_viewport_rect().contains(self.mapped_cursor_pos()):
                    pivot = QPointF(self.mapped_cursor_pos())
                else:
                    pivot = QPointF(self.rect().center())
            else:
                pivot = QPointF(self.image_center_position)




        before_scale = self.image_scale
        center_position = QPointF(self.image_center_position)
        scale = self.image_scale

        new_scale = scale * factor
        if (before_scale < 1.0 and new_scale > 1.0) or (before_scale > 1.0 and new_scale < 1.0):
            factor = 1.0/scale
            # print("scale is clamped to 100%")

        if new_scale > self.UPPER_SCALE_LIMIT:
            factor = self.UPPER_SCALE_LIMIT/scale

        center_position -= pivot
        center_position = QPointF(center_position.x()*factor, center_position.y()*factor)
        scale *= factor
        center_position += pivot


        # finish
        if override_factor:
            return scale, center_position

        if animated_zoom_enabled:

            def update_function(anim_task):
                self.image_scale = anim_task.image_rect.width()/self.get_rotated_pixmap().width()
                self.image_center_position = QPointF(anim_task.image_rect.center()) + anim_task.translation_delta_when_animation + anim_task.translation_delta_when_animation_summary
                self.activate_or_reset_secret_hint()
                self.show_center_label(self.label_type.SCALE)
                self.update()

                # msg = f'{anim_task.translation_delta_when_animation} {anim_task.translation_delta_when_animation_summary}'
                # print(msg)

            def on_start(anim_task):
                anim_task.translation_delta_when_animation = QPointF(0, 0)
                anim_task.translation_delta_when_animation_summary = QPointF(0, 0)
                anim_task.image_rect = self.get_image_viewport_rect()

            def on_finish(anim_task):
                self.old_cursor_pos = self.mapped_cursor_pos()
                self.old_image_center_position = self.image_center_position

            current_image_rect = self.get_image_viewport_rect()
            wanna_image_rect = self.get_image_viewport_rect(od=(center_position, scale))
            gen = self.get_current_animation_task_generation(anim_id="zoom")
            duration = fit(gen, 0, 20, 0.8, 1.2)
            self.animate_properties(
                [
                    (None, "image_rect", current_image_rect, wanna_image_rect, update_function),
                ],
                anim_id="zoom",
                duration=duration,
                # easing=QEasingCurve.OutQuad
                # easing=QEasingCurve.OutQuart
                # easing=QEasingCurve.OutQuint
                easing=QEasingCurve.OutCubic,
                callback_on_start=on_start,
                callback_on_finish=on_finish,
                user_data=scroll_value
            )

        else:

            self.image_scale = scale

            viewport_rect = self.get_image_viewport_rect()
            is_vr_small = viewport_rect.width() < 150 or viewport_rect.height() < 150
            if before_scale < self.image_scale and is_vr_small and not slow:
                self.image_center_position = QPointF(self.mapped_cursor_pos())
            else:
                self.image_center_position = center_position

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
        def set_font(pr):
            font = pr.font()
            if large:
                # font.setPixelSize(self.rect().height()//8)
                font.setPixelSize(40)
            else:
                font.setPixelSize(17)
            font.setWeight(1900)
            # font.setFamily("Consolas")
            # font.setWeight(900)
            pr.setFont(font)

        painter.save()
        set_font(painter)
        painter.setPen(QPen(Qt.white, 1)) # boundingRect returns zero QRect, if there's no pen
        brect = painter.boundingRect(self.rect(), Qt.AlignCenter, text)

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

        painter.restore()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        if self.BW_filter_state > 0:
            event_rect = self.rect()
            color_image = QImage(event_rect.size(), QImage.Format_ARGB32)
            color_image.fill(Qt.transparent)
            p = QPainter()
            p.begin(color_image)
            self._paintEvent(event, p)
            p.end()
            image = color_image.convertToFormat(QImage.Format_Grayscale16)
            if self.BW_filter_state == BWFilterState.on_TRANSPARENT_BACKGROUND:
                painter.drawImage(QPoint(0, 0), color_image)
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
            painter.drawImage(QPoint(0, 0), image)
            if self.BW_filter_state == BWFilterState.on_TRANSPARENT_BACKGROUND:
                painter.restore()
        else:
            self._paintEvent(event, painter)
            # if event.rect().height() < 500:
            #     painter.setPen(Qt.green)
            #     painter.drawLine(self.rect().bottomLeft(), self.rect().topRight())
        painter.end()

    def _paintEvent(self, event, painter):
        if Globals.ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # draw darkened translucent background
        if self.frameless_mode:
            if self.is_library_page_active():
                painter.setOpacity(self.STNG_library_page_transparency)
            elif self.is_board_page_active():
                painter.setOpacity(self.STNG_board_page_transparency)
            elif self.is_viewer_page_active():
                painter.setOpacity(self.STNG_viewer_page_transparency)
            elif self.is_start_page_active():
                painter.setOpacity(self.STNG_start_page_transparency)

            painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            painter.drawRect(self.rect())
            painter.setOpacity(1.0)
        else:
            painter.setBrush(QBrush(QColor(10, 10, 10), Qt.SolidPattern))
            painter.drawRect(self.rect())

        # draw current page
        if self.is_library_page_active():
            self.draw_library(painter)

        elif self.is_start_page_active():
            self.draw_startpage(painter)

        elif self.is_viewer_page_active():
            self.draw_content(painter)
            self.region_zoom_in_draw(painter)

        elif self.is_board_page_active():
            self.board_draw(painter, event)

        # draw center label
        self.draw_center_label_main(painter)

        # draw slice pipette tool
        self.SPT_draw_info(painter)

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
        FONT_HEIGHT = 17
        font.setPixelSize(FONT_HEIGHT)
        painter.setFont(font)
        painter.setBrush(QBrush(Qt.black))

        if SettingsWindow.get_setting_value('show_console_output'):
            n = 0
            for number, (timestamp, message) in enumerate(HookConsoleOutput.get_messages()):
                _message = message.strip()
                if not _message:
                    # оказывается, в сообщениях бывают пустые строки.
                    continue
                n += 1
                max_rect = QRect(0, 0, self.rect().width(), self.rect().height())
                alignment = Qt.AlignLeft
                text_rect = painter.boundingRect(max_rect, alignment, message)
                # text_rect.adjust(0, 0, 0, 100)
                painter.setOpacity(0.7)
                text_rect.moveTopLeft(QPoint(255, 50+n*(text_rect.height()+3)))
                painter.setPen(Qt.NoPen)
                painter.drawRect(text_rect.adjusted(-1, -1, 1, 1))
                painter.setOpacity(1.0)
                painter.setPen(QPen(Qt.white))
                painter.drawText(text_rect, alignment, message)

    def get_center_x_position(self):
        return int(self.rect().width()/2)

    def draw_library(self, painter):
        def set_font(pr):
            font = pr.font()
            font.setPixelSize(20)
            font.setWeight(1900)
            font.setFamily("Consolas")
            pr.setFont(font)
        H = self.LIBRARY_FOLDER_ITEM_HEIGHT
        painter.save()
        set_font(painter)

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
            text = folder_data.get_current_image_name()
            painter.drawText(text_rect, Qt.AlignLeft, text)

            text_rect = QRect(left, int(scroll_offset + 24+n*H), LEFT_COL_WIDTH-left, 200)
            images_list_len = len(folder_data.images_list)
            text = f"{images_list_len} {folder_data.folder_path}"
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
                    highres_svg = LibraryData().is_svg_file(item_data.filepath)
                    item_data.library_cache_version = load_image_respect_orientation(
                                        item_data.filepath, highres_svg=highres_svg)
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

        painter.restore()

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
            factor = self.rect().height()/content_height_left
            left_bar_height = int(factor*self.rect().height())

            offset = LibraryData().folderslist_scroll_offset
            if offset == 0:
                left_bar_y = 0
            else:
                y_factor = abs(offset)/(content_height_left-self.rect().height())
                y_factor = min(1.0, y_factor)
                left_bar_y = (self.rect().height()-left_bar_height)*y_factor
                left_bar_y = int(left_bar_y)

            left_bar_rect = QRect(CXP-(WIDTH+OFFSET_FROM_CENTER), left_bar_y, WIDTH, left_bar_height)

            path = QPainterPath()
            path.addRoundedRect(QRectF(left_bar_rect), 5, 5)
            painter.fillPath(path, Qt.white)

        if draw_right_scrollbar:
            factor = self.rect().height()/content_height_right
            right_bar_height = int(factor*right_scrollbar_rect.height())

            offset = cf.previews_scroll_offset
            if offset == 0:
                right_bar_y = 0
            else:
                y_factor = abs(offset)/(content_height_right-self.rect().height())
                y_factor = min(1.0, y_factor)
                right_bar_y = (self.rect().height()-right_bar_height)*y_factor
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

        elif self.movie:
            pass
        else:
            self.draw_center_label(painter, self.loading_text, large=True)

        # draw animation progressbar
        if self.movie:
            r = self.get_image_viewport_rect()
            movie = self.movie
            progress_width = r.width() * movie.currentFrameNumber()/movie.frameCount()
            progress_bar_rect = QRectF(r.left(), r.bottom(), int(progress_width), 10)
            painter.setBrush(QBrush(Qt.green))
            painter.setPen(Qt.NoPen)
            painter.drawRect(progress_bar_rect)

        self.draw_comments_viewer(painter)

        self.draw_view_history_row(painter)

        self.draw_image_metadata(painter)

        self.draw_tags_sidebar_overlay(painter)
        self.draw_tags_background(painter)

    def draw_center_label_main(self, painter):
        movie = self.movie
        if self.image_center_position:
            if self.center_label_info_type == self.label_type.SCALE:
                value = math.floor(self.image_scale*100)
                if value < 1.0:
                    value = 1
                # "{:.03f}"
                text = f"{value:,}%".replace(',', ' ')
            elif self.center_label_info_type == self.label_type.PLAYSPEED and self.animated:
                speed = movie.speed()
                text = f"speed {speed}%"
            elif self.center_label_info_type == self.label_type.FRAME_NUMBER and self.animated:
                frame_num = movie.currentFrameNumber()+1
                frame_count = movie.frameCount()
                text = f"frame {frame_num}/{frame_count}"
            else:
                text = self.center_label_info_type
            self.draw_center_label(painter, text)

    def draw_image_metadata(self, painter):
        if self.Globals.lite_mode:
            return

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
        if not self.isActiveWindow():
            return
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
            painter.save()
            painter.setPen(QPen(Qt.white))
            painter.drawText(rect, Qt.AlignCenter | Qt.AlignBottom, "история просмотра")
            painter.restore()

    def draw_center_point(self, painter, pos):
        painter.setPen(QPen(Qt.green, 5, Qt.SolidLine))
        painter.drawPoint(pos)

        painter.drawPoint(self.get_center_position())

    def closeEvent(self, event):
        event.accept()

    def close(self):
        super().close()

    def animated_or_not_animated_close(self, callback_on_finish):
        if self.isAnimationEffectsAllowed() and not self.is_library_page_active():
            if self.handling_input:
                # callback_on_finish()
                # closeAllWindows(), в отличие от callback_on_finish(), закрывает приложение сразу,
                # что полезно, когда функции animated_or_not_animated_close переходит управление
                # по причине предварительного вызова processAppEvents(update_only=False)
                QApplication.closeAllWindows()
            else:
                self.animate_properties(
                    [
                        (self, "image_scale", self.image_scale, 0.01, self.update),
                        (self, "image_center_position", self.image_center_position, self.get_center_position(), self.update)
                    ],
                    callback_on_finish=callback_on_finish
                )
        else:
            super().close()

    def require_window_closing(self):
        if Globals.lite_mode:
            self.animated_or_not_animated_close(QApplication.instance().quit)
        elif Globals.FORCE_FULL_DEBUG and Globals.DEBUG:
            QApplication.instance().quit()
        elif SettingsWindow.get_setting_value('hide_to_tray_on_close'):
            self.hide()
        else:
            self.animated_or_not_animated_close(QApplication.instance().quit)

    def show_center_label(self, info_type, error=False):
        self.center_label_error = error
        self.center_label_info_type = info_type
        if info_type not in self.label_type.all():
            # текстовые сообщения показываем дольше
            self.CENTER_LABEL_TIME_LIMIT = 5.0
        else:
            self.CENTER_LABEL_TIME_LIMIT = 2.0
        # show center label on screen
        self.center_label_time = time.time()

    def hide(self):
        # Этот метод вызывается, если закрывать окно через меню панели задач
        # или через кнопку "закрыть" у миниатюры окна во всё той же панели задач Windows.
        # По идее, если мы в упрощённом режиме, то здесь надо сразу закрывать и приложение тоже,
        # иначе приложение останется висеть в памяти и в диспетчере задач.
        if Globals.lite_mode:
            QApplication.instance().quit()
        else:
            super().hide()

    def hide_center_label(self):
        self.CENTER_LABEL_TIME_LIMIT = 2.0
        self.center_label_time = time.time() - self.CENTER_LABEL_TIME_LIMIT*5

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

    def check_thumbnails_fullscreen(self):
        CP = Globals.control_panel
        if CP is not None and CP.fullscreen_flag:
            return True
        return False

    def cancel_thumbnails_fullscreen(self):
        CP = Globals.control_panel
        if CP is not None and CP.fullscreen_flag:
            CP.do_toggle_fullscreen()

    def toggle_animation_playback(self):
        if self.animated:
            im_data = self.image_data
            im_data.anim_paused = not im_data.anim_paused
        self.update()

    def start_lite_process(self, path):
        start_lite_process(path)

    def toggle_BW_filter(self):
        self.BW_filter_state = BWFilterState.cycle_toggle(self.BW_filter_state)
        self.update()

    def keyReleaseEvent(self, event):
        key = event.key()

        if self.is_board_text_input_event:
            if not event.isAutoRepeat():
                self.is_board_text_input_event = False
            return

        self.boards_key_release_callback(event)

        if self.check_thumbnails_fullscreen():
            return

        # isAutoRepeat даёт отфильтровать ненужные срабатывания
        # иначе при зажатой клавише keyReleaseEvent будет генерироваться без конца
        if not event.isAutoRepeat():
            self._key_pressed = False
            self._key_unreleased = False

        if key == Qt.Key_F11 and not event.isAutoRepeat():
            if self.frameless_mode:
                self.fullscreen_mode = not self.fullscreen_mode
                self.showMaximized()

        if key == Qt.Key_F10 and not event.isAutoRepeat():
            self.toggle_BW_filter()

        if not event.isAutoRepeat():
            if key == Qt.Key_F5:
                self.SPT_update()
            elif key == Qt.Key_F6:
                self.SPT_toggle_tool_state()
            elif key == Qt.Key_F7:
                self.SPT_set_plots_position()
            elif key == Qt.Key_F8:
                self.SPT_toggle_plots_window()

        if key == Qt.Key_Tab:
            self.cycle_change_page()

        if self.is_start_page_active():
            return

        elif self.is_library_page_active():
            if key == Qt.Key_Up:
                LibraryData().choose_previous_folder()
            elif key == Qt.Key_Down:
                LibraryData().choose_next_folder()

        elif self.is_board_page_active():

            default = True
            if key == Qt.Key_Right:
                if event.modifiers() & Qt.ControlModifier:
                    if self.frameless_mode:
                        self.toggle_monitor('right')
                        default = False
            elif key == Qt.Key_Left:
                if event.modifiers() & Qt.ControlModifier:
                    if self.frameless_mode:
                        self.toggle_monitor('left')
                        default = False
            if default:
                self.board_keyReleaseEvent(event)

        elif self.is_viewer_page_active():

            if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:

                if self.check_scroll_lock():

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

                else:

                    if key == Qt.Key_Up:
                        self.do_scale_image(0.05, cursor_pivot=False, slow=True)

                    elif key == Qt.Key_Down:
                        self.do_scale_image(-0.05, cursor_pivot=False, slow=True)

                    elif key == Qt.Key_Right:
                        if event.modifiers() & Qt.AltModifier:
                            LibraryData().show_viewed_image_next()
                        elif event.modifiers() & Qt.ControlModifier:
                            if self.frameless_mode:
                                self.toggle_monitor('right')
                        elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                            LibraryData().show_next_image()
                    elif key == Qt.Key_Left:
                        if event.modifiers() & Qt.AltModifier:
                            LibraryData().show_viewed_image_prev()
                        elif event.modifiers() & Qt.ControlModifier:
                            if self.frameless_mode:
                                self.toggle_monitor('left')
                        elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                            LibraryData().show_previous_image()

        self.update()

    def keyPressEvent(self, event):
        key = event.key()

        ctrl_mod = event.modifiers() & Qt.ControlModifier
        self.is_board_text_input_event = False

        self.boards_key_press_callback(event)

        if self.check_thumbnails_fullscreen():
            if key == Qt.Key_Escape:
                self.cancel_thumbnails_fullscreen()
                self.update()
            return

        if not key in [Qt.Key_Control, Qt.Key_Shift]:
            if self._key_pressed:
                self._key_unreleased = True # зажата
            self._key_pressed = True # нажата


        if key == Qt.Key_Escape:
            if self.board_TextElementTextSelectionDragNDropOngoing():
                self.board_TextElementCancelTextSelectionDragNDrop()
            elif self.start_translation_pos or self.translation_ongoing:
                self.board_CANCEL_selected_items_TRANSLATION()
            elif self.rotation_ongoing:
                self.board_CANCEL_selected_items_ROTATION()
            elif self.scaling_ongoing:
                self.board_CANCEL_selected_items_SCALING()
            elif self.contextMenuActivated:
                self.contextMenuActivated = False
            elif self.input_rect:
                self.region_zoom_in_cancel()
            elif self.board_magnifier_input_rect:
                self.board_region_zoom_do_cancel()
            elif self.is_board_page_active() and self.board_TextElementDeactivateEditMode():
                return
            elif SettingsWindow.isWindowVisible:
                SettingsWindow.instance.hide()
            elif HookConsoleOutput.check_messages():
                HookConsoleOutput.clear_messages_list()
            else:
                self.require_window_closing()
        elif key == Qt.Key_F1:
            self.toggle_infopanel()
        elif event.nativeScanCode() == 0x29:
            self.open_settings_window()




        if check_scancode_for(event, "Y") and not self.active_element:
            if self.frameless_mode:
                self.toggle_to_frame_mode()
            else:
                self.toggle_to_frameless_mode()

        elif check_scancode_for(event, "G") and not self.active_element:

            board_status = f'translation ongoing: {self.translation_ongoing}, rotation ongoing: {self.rotation_ongoing}, scale ongoing: {self.scaling_ongoing}, start_translation_pos: {self.start_translation_pos}'
            print(board_status)
            # self.show_center_label("DEBUG")
            # self.toggle_test_animation()
            # self.hide_center_label()
            # import time
            # time = time.time()
            # LibraryData().create_folder_data(f"{time}", [], virtual=True)

        elif check_scancode_for(event, "Q") and not self.active_element:
            LibraryData().show_finder_window()

        elif check_scancode_for(event, "P") and not self.active_element:
            self.toggle_stay_on_top()
            self.update()

        elif key == Qt.Key_1 and not self.active_element:
            self.change_page(self.pages.START_PAGE)

        elif key == Qt.Key_2 and not self.active_element:
            self.change_page(self.pages.VIEWER_PAGE)

        elif key == Qt.Key_3 and not self.active_element:
            self.change_page(self.pages.BOARD_PAGE)

        elif key == Qt.Key_4 and not self.active_element:
            self.change_page(self.pages.LIBRARY_PAGE)

        elif check_scancode_for(event, ("W", "S", "A", "D")) and not ctrl_mod and not self.board_TextElementIsActiveElement():
            length = 1.0
            if event.modifiers() & Qt.ShiftModifier:
                length *= 20.0
                if event.modifiers() & Qt.AltModifier:
                    length *= 5.0
            if check_scancode_for(event, "W"):
                delta =  QPoint(0, 1) * length
            elif check_scancode_for(event, "S"):
                delta =  QPoint(0, -1) * length
            elif check_scancode_for(event, "A"):
                delta =  QPoint(1, 0) * length
            elif check_scancode_for(event, "D"):
                delta =  QPoint(-1, 0) * length
            if self.is_viewer_page_active():
                self.image_center_position += delta
            elif self.is_board_page_active():
                self.canvas_origin += delta
                self.update_selection_bouding_box()


        if self.is_start_page_active():
            return

        elif self.is_library_page_active():

            if key == Qt.Key_Backtab:
                LibraryData().choose_doom_scroll()
            elif key == Qt.Key_Delete:
                LibraryData().delete_current_folder()
            elif check_scancode_for(event, "U"):
                LibraryData().update_current_folder()

        elif self.is_viewer_page_active():

            if check_scancode_for(event, "U"):
                LibraryData().update_current_folder()

            elif key == Qt.Key_Backtab:
                LibraryData().choose_doom_scroll()
            elif key == Qt.Key_Delete:
                LibraryData().delete_current_image()
            elif key == Qt.Key_Home:
                LibraryData().jump_to_first()
            elif key == Qt.Key_End:
                LibraryData().jump_to_last()
            elif key == Qt.Key_Space:
                self.toggle_animation_playback()
            elif check_scancode_for(event, "F"):
                Globals.control_panel.manage_favorite_list()
            elif check_scancode_for(event, "C"):
                self.STNG_show_image_center = not self.STNG_show_image_center
            elif check_scancode_for(event, "D"):
                self.STNG_show_thirds = not self.STNG_show_thirds
            elif check_scancode_for(event, "T"):
                self.toggle_tags_overlay()
            elif check_scancode_for(event, "I"):
                self.invert_image = not self.invert_image
            elif check_scancode_for(event, "R"):
                self.start_inframed_image_saving(event)
            elif check_scancode_for(event, "M"):
                self.mirror_current_image(ctrl_mod)


        elif self.is_board_page_active():

            self.board_keyPressEvent(event)

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
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
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
            else:
                self.show_center_label('Путь не задан или его не существует', error=True)
        new_path = os.path.abspath(os.path.join(rootpath, f"{formated_datetime}{ext}"))
        if not use_screen_scale:
            factor = 1/self.image_scale
            save_pixmap = save_pixmap.transformed(QTransform().scale(factor, factor), Qt.SmoothTransformation)

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

    def recreate_control_panel(self, requested_page=None):
        MW = Globals.main_window
        CP = Globals.control_panel
        if CP is not None:
            CP.close()
            CP.setParent(None)
            Globals.control_panel = None

        CP = Globals.control_panel = ControlPanel(self, requested_page=requested_page)
        CP.show()
        return CP

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
            if not new_pixmap.isNull():
                self.copied_from_clipboard = True
                self.pixmap = new_pixmap
                self.get_rotated_pixmap(force_update=True)
                self.restore_image_transformations()
                self.show_center_label("вставлено")
        self.update()

    def get_selected_comment(self, pos):
        image_comments = LibraryData().get_comments_for_image()
        selected_comment = None
        if image_comments and hasattr(image_comments[0], "screen_rect"):
            for comment in image_comments:
                if comment.screen_rect.contains(pos):
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

        if not self.context_menu_allowed:
            return

        contextMenu = QMenu()
        contextMenu.setStyleSheet(self.context_menu_stylesheet)

        self.contextMenuActivated = True

        self.context_menu_exec_point = self.mapped_cursor_pos()

        minimize_window = contextMenu.addAction("Свернуть")
        minimize_window.triggered.connect(Globals.main_window.showMinimized)
        contextMenu.addSeparator()

        def toggle_boolean_var_generic(obj, attr_name):
            setattr(obj, attr_name, not getattr(obj, attr_name))
            self.update()

        self.toggle_boolean_var_generic = toggle_boolean_var_generic

        checkboxes = [
            ("DEBUG", Globals.DEBUG, partial(toggle_boolean_var_generic, Globals, 'DEBUG')),
            ("Антиальясинг и сглаживание пиксмапов", Globals.ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM, partial(toggle_boolean_var_generic, Globals, 'ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM')),
            ("Pixmap-прокси для пометок типа «Текст»", Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS, partial(toggle_boolean_var_generic, Globals, 'USE_PIXMAP_PROXY_FOR_TEXT_ITEMS')),
        ]

        if Globals.CRASH_SIMULATOR:
            crash_simulator = contextMenu.addAction("Крашнуть приложение (для дебага)...")
            crash_simulator.triggered.connect(lambda: 1/0)

        open_settings = contextMenu.addAction("Настройки...")
        open_settings.triggered.connect(self.open_settings_window)
        contextMenu.addSeparator()

        if self.frameless_mode:
            text = "Переключиться в оконный режим"
        else:
            text = "Переключиться в полноэкранный режим"
        toggle_frame_mode = contextMenu.addAction(text)
        toggle_frame_mode.triggered.connect(self.toggle_window_frame)
        if self.frameless_mode:
            if self.two_monitors_wide:
                text = "Вернуть окно в монитор"
            else:
                text = "Развернуть окно на два монитора"
            toggle_two_monitors_wide = contextMenu.addAction(text)

        if Globals.lite_mode:
            contextMenu.addSeparator()
            rerun_in_extended_mode = contextMenu.addAction("Перезапустить в обычном режиме")
            rerun_in_extended_mode.triggered.connect(partial(do_rerun_in_default_mode, False))
        else:
            contextMenu.addSeparator()
            rerun_extended_mode = contextMenu.addAction("Перезапуск (для сброса лишней памяти)")
            rerun_extended_mode.triggered.connect(partial(do_rerun_in_default_mode, self.is_library_page_active()))


        open_in_sep_app = contextMenu.addAction("Открыть в отдельной копии")
        open_in_sep_app.triggered.connect(partial(open_in_separated_app_copy, LibraryData().current_folder()))

        if self.is_library_page_active():
            folder_data = None
            if self.folders_list:
                for item_rect, item_data in self.folders_list:
                    if item_rect.contains(event.pos()):
                        folder_data = item_data
            if folder_data and not folder_data.virtual:
                action_title = f"Открыть папку \"{folder_data.folder_path}\" в копии"
                open_separated = contextMenu.addAction(action_title)
                open_separated.triggered.connect(partial(open_in_separated_app_copy, folder_data))
                toggle_two_monitors_wide = None
                if self.frameless_mode:
                    if self.two_monitors_wide:
                        text = "Вернуть окно в монитор"
                    else:
                        text = "Развернуть окно на два монитора"
                    toggle_two_monitors_wide = contextMenu.addAction(text)
                    toggle_two_monitors_wide.triggered.connect(self.do_toggle_two_monitors_wide)

        elif self.is_board_page_active():

            self.board_contextMenu(event, contextMenu, checkboxes)

        elif self.is_viewer_page_active():

            if self.image_data and not self.image_data.is_supported_filetype:
                run_unsupported_file = contextMenu.addAction("Открыть неподдерживаемый файл...")
                run_unsupported_file.triggered.connect(self.run_unsupported_file)

            contextMenu.addSeparator()

            if not Globals.lite_mode:
                sel_comment = self.get_selected_comment(event.pos())
                if sel_comment:
                    action_text = f'Редактировать текст комента "{sel_comment.get_title()}"'
                    change_comment_text = contextMenu.addAction(action_text)
                    change_comment_text.triggered.connect(partial(self.change_comment_text_menuitem, sel_comment))

                    action_text = f'Переопределить границы комента "{sel_comment.get_title()}"'
                    change_comment_borders = contextMenu.addAction(action_text)
                    change_comment_borders.triggered.connect(partial(self.change_comment_borders_menuitem, sel_comment))

                    action_text = f'Удалить комент "{sel_comment.get_title()}"'
                    delete_comment = contextMenu.addAction(action_text)
                    delete_comment.triggered.connect(partial(self.delete_comment_menuitem, sel_comment))

                    contextMenu.addSeparator()

                ci = LibraryData().current_folder().current_image()
                if ci.image_metadata:
                    copy_image_metadata = contextMenu.addAction("Скопировать метаданные в буферобмена")
                    copy_image_metadata.triggered.connect(partial(QApplication.clipboard().setText, ci.image_metadata_info))


            contextMenu.addSeparator()

            if not self.error:
                show_in_explorer = contextMenu.addAction("Найти на диске")
                show_in_explorer.triggered.connect(Globals.control_panel.show_in_folder)
                show_in_gchrome = contextMenu.addAction("Открыть в Google Chrome")
                show_in_gchrome.triggered.connect(self.show_in_gchrome_menuitem)
                place_at_center = contextMenu.addAction("Вернуть картинку в центр окна")
                place_at_center.triggered.connect(self.place_at_center_menuitem)

            contextMenu.addSeparator()

            if self.svg_rendered:
                text = "Изменить разрешение растеризации SVG-файла..."
                change_svg_scale = contextMenu.addAction(text)
                change_svg_scale.triggered.connect(self.contextMenuChangeSVGScale)
                contextMenu.addSeparator()

            if not self.error:
                save_as_png = contextMenu.addAction("Сохранить в .png...")
                save_as_png.triggered.connect(partial(self.save_image_as, 'png'))

                save_as_jpg = contextMenu.addAction("Сохранить в .jpg...")
                save_as_jpg.triggered.connect(partial(self.save_image_as, 'jpg'))

                copy_to_cp = contextMenu.addAction("Копировать в буфер обмена")
                copy_to_cp.triggered.connect(self.copy_to_clipboard)

                copy_from_cp = contextMenu.addAction("Вставить из буфера обмена")
                copy_from_cp.triggered.connect(self.paste_from_clipboard)

                if LibraryData().current_folder().is_fav_folder():
                    contextMenu.addSeparator()
                    action_title = "Перейти из избранного в папку с этим изображением"
                    go_to_folder = contextMenu.addAction(action_title)
                    go_to_folder.triggered.connect(LibraryData().go_to_folder_of_current_image)

        for title, value, callback in checkboxes:
            wa = QWidgetAction(contextMenu)
            chb = QCheckBox(title)
            chb.setStyleSheet(self.context_menu_stylesheet)
            chb.setChecked(value)
            chb.stateChanged.connect(callback)
            wa.setDefaultWidget(chb)
            contextMenu.addAction(wa)

        if self.SPT_is_context_menu_allowed():
            self.SPT_context_menu(event)
        else:
            action = contextMenu.exec_(self.mapToGlobal(event.pos()))

        self.contextMenuActivated = False

    def show_in_gchrome_menuitem(self):
        main_window = Globals.main_window
        if main_window.image_filepath:
            open_in_google_chrome(main_window.image_filepath)

    def place_at_center_menuitem(self):
        self.restore_image_transformations()
        self.update()

    def toggle_window_frame(self):
        if self.frameless_mode:
            self.toggle_to_frame_mode()
        else:
            self.toggle_to_frameless_mode()

    def delete_comment_menuitem(self, sel_comment):
        if sel_comment:
            LibraryData().delete_comment(sel_comment)
            self.update()

    def change_comment_text_menuitem(self, sel_comment):
        if sel_comment:
            self.show_comment_form(sel_comment)

    def change_comment_borders_menuitem(self, sel_comment):
        if sel_comment:
            self.comment_data_candidate = sel_comment
            self.show_center_label("Теперь переопределите границы комментария через Ctrl+Shift+LMB")

    def run_unsupported_file(self):
        import win32api
        win32api.ShellExecute(0, "open", self.image_data.filepath, None, ".", 1)

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

    def get_boards_user_data_filepath(self, filename):
        return os.path.join(self.LibraryData().get_boards_data_root(), filename)

    def get_boards_user_data_folder(self):
        return self.LibraryData().get_boards_data_root()

    def get_user_data_filepath(self, filename):
        return os.path.join(os.path.dirname(__file__), "user_data", filename)

    def get_user_data_folder(self):
        return os.path.join(os.path.dirname(__file__), "user_data")


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
        print("------ RERUN FROM 'CHOOSE_START_OPTION_CALLBACK' ------")
        restart_process_in_lite_mode(path)
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
    app = QApplication.instance()
    stray_icon = app.property("stray_icon")
    if stray_icon:
        stray_icon.hide()
    if not Globals.DEBUG:
        _restart_app(aftercrash=True)
    sys.exit()

def _restart_app(aftercrash=False):
    args = [sys.executable, sys.argv[0]]
    filepath = None
    if aftercrash:
        try:
            filepath = LibraryData().current_folder().current_image().filepath
        except:
            pass
        if filepath is not None:
            args.append(filepath)
        if not Globals.lite_mode:
            args.append('-full')
        args.append('-aftercrash')
    else:
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
            if os.path.exists(filepath):
                args.append(filepath)
        if '-full' in sys.argv:
            args.append('-full')
    subprocess.Popen(args)

def exit_threads():
    # принудительно глушим все потоки, что ещё работают
    for thread in ThumbnailsThread.threads_pool:
        thread.terminate()
        # нужно вызывать terminate вместо exit

def restart_process_in_lite_mode(path=None):
    app_path = sys.argv[0]
    if path is not None:
        args = [path]
    else:
        args = retrieve_cmd_args()
    args.insert(0, app_path)
    args.insert(0, sys.executable)
    args.append('-lite')
    subprocess.Popen(args)

def start_lite_process(path):
    if Globals.DEBUG:
        app_path = __file__
    else:
        app_path = sys.argv[0]
    args = [sys.executable, app_path, path, "-lite"]
    subprocess.Popen(args)

def do_rerun_in_default_mode(is_on_library_page):
    path = LibraryData.get_content_path(LibraryData().current_folder())
    if Globals.DEBUG:
        app_path = __file__
    else:
        app_path = sys.argv[0]
    args = [sys.executable, app_path, path, "-full"]
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
    path = ""
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
                        print(f"\tdefault path is set to {path}")
    else:
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
    def check_messages(cls):
        return bool(list(cls.get_messages()))

    @classmethod
    def clear_messages_list(cls):
        cls.messages.clear()

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
    print(f'Proccess ID: {pid} Command Arguments: {arguments}')

    if not Globals.DEBUG:
        RERUN_ARG = '-rerun'
        # Этот перезапуск с аргументом -rerun нужен для борьбы с идиотским проводником Windows,
        # который зачем-то запускает два процесса, и затем они держатся запущенными только для того,
        # чтобы работал один единственный процесс. У меня же всё традиционно, поэтому обязательный перезапуск.
        if (RERUN_ARG not in sys.argv) and ("-aftercrash" not in sys.argv):
            subprocess.Popen([sys.executable, *sys.argv, RERUN_ARG])
            sys.exit()

    _was_DEBUG = Globals.DEBUG
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
    parser.add_argument('-board', help='', action='store_true')
    args = parser.parse_args(sys.argv[1:])
    # print(args)
    Globals.args = args
    if args.path:
        path = args.path
    if args.frame:
        frameless_mode = False
    if args.aftercrash:
        Globals.aftercrash = True
    Globals.lite_mode = args.lite
    Globals.force_full_mode = args.full

    if _was_DEBUG and Globals.FORCE_FULL_DEBUG:
        Globals.lite_mode = False
        Globals.force_full_mode = True
        path = get_predefined_path_if_started_from_sublimeText()

    if Globals.lite_mode:
        app_icon = QIcon()
        path_icon = os.path.join(os.path.dirname(__file__), "image_viewer_lite.ico")
        app_icon.addFile(path_icon)
        app.setWindowIcon(app_icon)
        app.setQuitOnLastWindowClosed(True)

    if Globals.aftercrash:
        filepath = get_crashlog_filepath()
        msg0 = f"Информация о краше сохранена в файл\n\t{filepath}"
        msg = f"Программа аварийно завершила работу! Application crash! \n{msg0}\n\nПерезапустить? Restart app?"
        ret = QMessageBox.question(None, 'Fatal Error!', msg, QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            _restart_app()
        sys.exit(0)

    ServerOrClient.globals = Globals

    if not Globals.lite_mode:
        path = ServerOrClient.server_or_client_via_sockets(path, open_request,
                                                                    choose_start_option_callback)
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
    processAppEvents()
    # создание панели управления
    ControlPanel.globals = Globals
    ControlPanel.LibraryData = LibraryData
    ControlPanel.SettingsWindow = SettingsWindow
    # CP = MW.recreate_control_panel()
    # обработка входящих данных
    default_branch = True
    if args.board:
        LibraryData().create_empty_virtual_folder()
        MW.change_page(MW.pages.BOARD_PAGE)
        processAppEvents()
        if path.lower().endswith('.board'):
            MW.board_loadBoard(path)
        elif path.lower().endswith('.py'):
            MW.board_loadPluginBoard(path)
        else:
            raise Exception(f'Unable to handle board argument {path}')
        default_branch = False

    if default_branch:
        if path:
            LibraryData().handle_input_data(path)
        else:
            # без запроса
            LibraryData().create_empty_virtual_folder()
        if args.forcelibrarypage:
            MW.change_page(MW.pages.LIBRARY_PAGE)

    # вход в петлю обработки сообщений
    exit_code = app.exec()
    if sti:
        sti.hide()
    sys.exit(exit_code)

def retrieve_cmd_args():
    bin_args = []
    iterable = vars(Globals.args).items()
    for arg_name, arg_value in iterable:
        if isinstance(arg_value, bool):
            if arg_value:
                bin_args.append(f'-{arg_name}')
        elif isinstance(arg_value, str):
            bin_args.append(arg_value)
        elif isinstance(arg_value, type(None)):
            pass
        else:
            raise Exception(f'Not supported argument "{arg_name}" with value "{arg_value}"')
    return bin_args

def main():
    try:
        _main()
    except Exception as e:
        excepthook(type(e), e, traceback.format_exc())

if __name__ == '__main__':
    main()
