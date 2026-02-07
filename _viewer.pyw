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

from collections import defaultdict

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

try:
    noise = __import__("noise")
except:
    noise = None

if platform.system() == "Windows":
    viewer_dll = __import__("viewer_dll") #viewer_dll is windows-only module
else:
    viewer_dll = None

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
    SUPER_LITE = True
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
    PREVIEW_CORNER_RADIUS = 20

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

    app_title = _("Krumassan Image Viewer v0.90 Alpha by Sergei Krumas")
    github_repo = _("https://github.com/sergkrumas/image_viewer")

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

    SCROLLBAR_WIDTH = 10
    SCROLL_THUMB_MIN_HEIGHT = 50

    hint_text = ""
    secret_hints_list = []

    START_HINT_AT_SCALE_VALUE = 40.0

    secret_pic = None
    secret_p = None

    class pages():
        START_PAGE = 1
        VIEWER_PAGE = 2
        BOARD_PAGE = 3
        LIBRARY_PAGE = 4
        WATERFALL_PAGE = 5

        @classmethod
        def all(cls):
            return [
                  cls.START_PAGE
                , cls.VIEWER_PAGE
                , cls.BOARD_PAGE
                , cls.LIBRARY_PAGE
                , cls.WATERFALL_PAGE
            ]

        @classmethod
        def name(cls, page_id):
            return {
                  cls.START_PAGE: _('START')
                , cls.VIEWER_PAGE: _('VIEWER')
                , cls.BOARD_PAGE: _('BOARD')
                , cls.LIBRARY_PAGE: _('LIBRARY')
                , cls.WATERFALL_PAGE: _('WATERFALL')
            }.get(page_id)

    pages.count = len(pages.all())

    class label_type():
        FRAME_NUMBER = 'FRAMENUMBER'
        PLAYSPEED = 'PLAYSPEED'
        SCALE = 'SCALE'

        @classmethod
        def all(cls):
            return [
                  cls.FRAME_NUMBER
                , cls.PLAYSPEED
                , cls.SCALE
            ]

    class vertical_scrollbars():
        NO_SCROLLBAR = -1
        LIBRARY_PAGE_FOLDERS_LIST = 0
        LIBRARY_PAGE_PREVIEWS_LIST = 1
        WATERFALL_PAGE_LEFT = 2
        WATERFALL_PAGE_RIGHT = 3

        scrollbar_data = type('scrollbar_data', (), {'visible': False})
        data = defaultdict(scrollbar_data)
        capture_index = NO_SCROLLBAR
        captured_thumb_rect_at_start = QRect()
        captured_curpos = QPointF()

        @classmethod
        def all(cls):
            return [
                    cls.LIBRARY_PAGE_FOLDERS_LIST
                  , cls.LIBRARY_PAGE_PREVIEWS_LIST
                  , cls.WATERFALL_PAGE_LEFT
                  , cls.WATERFALL_PAGE_RIGHT
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

    class InteractiveCorners():
        TOPLEFT = 0
        TOPRIGHT = 1

    def get_corner_pos(self, window_corner_id):
        if window_corner_id == self.InteractiveCorners.TOPLEFT:
            return self.rect().topLeft()
        elif window_corner_id == self.InteractiveCorners.TOPRIGHT:
            return self.rect().topRight()

    def get_corner_radius_factor(self, menu_mode):
        return 4 if menu_mode else 1

    def get_corner_button_rect(self, window_corner_id, menu_mode=False):
        corner_pos = self.get_corner_pos(window_corner_id)
        radius = self.CORNER_BUTTON_RADIUS*self.get_corner_radius_factor(menu_mode)
        btn_rect = QRectF(
            corner_pos.x() - radius,
            corner_pos.y() - radius,
            radius*2,
            radius*2,
        ).toRect()
        return btn_rect

    def over_corner_button(self, window_corner_id, menu_mode=False):
        btn_rect = self.get_corner_button_rect(window_corner_id, menu_mode=menu_mode)
        corner_pos = self.get_corner_pos(window_corner_id)
        diff = corner_pos - self.mapped_cursor_pos()
        distance = QVector2D(diff).length()
        client_area = self.rect().intersected(btn_rect)
        case1 = distance < self.CORNER_BUTTON_RADIUS*self.get_corner_radius_factor(menu_mode)
        case2 = client_area.contains(self.mapped_cursor_pos())
        return case2 and case1

    def handle_menu_item_click(self):
        curpos = self.mapFromGlobal(QCursor().pos())
        if not self.is_top_left_menu_visible():
            return False
        for page, rect in self.left_corner_menu_items:
            if rect.contains(curpos):
                self.change_page(page)

    def over_left_corner_menu_item(self):
        curpos = self.mapFromGlobal(QCursor().pos())
        if not self.is_top_left_menu_visible():
            return False
        for page, rect in self.left_corner_menu_items:
            if rect.contains(curpos):
                return True
        return False

    def over_corner_menu(self, window_corner_id):
        return self.over_corner_button(window_corner_id, menu_mode=True) and self.corner_menu_visibility[window_corner_id]

    def is_top_right_menu_visible(self):
        return self.corner_menu_visibility[self.InteractiveCorners.TOPRIGHT]

    def is_top_left_menu_visible(self):
        return self.corner_menu_visibility[self.InteractiveCorners.TOPLEFT]

    def draw_corner_button(self, painter, window_corner_id):
        btn_rect = self.get_corner_button_rect(window_corner_id)
        corner_pos = self.get_corner_pos(window_corner_id)

        if self.over_corner_button(window_corner_id):
            painter.setOpacity(.6)
        else:
            painter.setOpacity(.3)

        painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(btn_rect)

        # код для отрисовки креста правой кнопки
        _value = self.CORNER_BUTTON_RADIUS/2-5
        cross_pos = corner_pos + QPointF(-_value, _value).toPoint()

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
        corner_char = self.pages.name(self.current_page)[0]
        r = QRect(QPoint(0, 0), btn_rect.bottomRight()-QPoint(20, 20))
        painter.drawText(r, Qt.AlignBottom | Qt.AlignRight, corner_char)
        painter.setFont(oldfont)

    def draw_corner_menu(self, painter, window_corner_id):

        btn_rect = self.get_corner_button_rect(window_corner_id, menu_mode=True)

        # TODO: этот код управляет видимостью меню, а факт видимости записывается и используются вне этой функции. И если делать по-хорошему, то такого тут быть не должно.
        if self.over_corner_button(window_corner_id):
            self.corner_menu_visibility[window_corner_id] = True
        elif not self.over_corner_button(window_corner_id, menu_mode=True):
            self.corner_menu_visibility[window_corner_id] = False

        if not self.corner_menu_visibility[window_corner_id]:
            return

        painter.setOpacity(.5)

        if window_corner_id == self.InteractiveCorners.TOPLEFT:
            brush_color = Qt.red
        elif window_corner_id == self.InteractiveCorners.TOPRIGHT:
            brush_color = QColor(50, 50, 50)

        painter.setBrush(QBrush(brush_color, Qt.SolidPattern))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(btn_rect)

        painter.setOpacity(.8)

        if window_corner_id == self.InteractiveCorners.TOPRIGHT:
            rad_fac = self.get_corner_radius_factor(window_corner_id)-1.5
            rad = rad_fac*self.CORNER_BUTTON_RADIUS
            rad -= 10
            pixmap = Globals.MINIMIZE_ICON
            p = self.rect().topRight() + QPointF(-rad, rad) + QPointF(0, -pixmap.width())
            painter.drawPixmap(p, pixmap)

        if window_corner_id == self.InteractiveCorners.TOPLEFT:
            self.left_corner_menu_items = []
            r = self.CORNER_BUTTON_RADIUS*3
            points = []
            PAGES_COUNT_M_ONE = self.pages.count - 1
            deg90 = math.pi/2.0
            offset = deg90/9
            for i in range(PAGES_COUNT_M_ONE):
                angle = deg90*i/4 + offset
                x = r*math.cos(angle)
                y = r*math.sin(angle)
                point = QPointF(x, y).toPoint()
                points.append(point)

            painter.setPen(QPen(Qt.white, 5))
            painter.setBrush(Qt.NoBrush)

            oldfont = painter.font()
            font = QFont(painter.font())
            font.setPixelSize(20)
            font.setWeight(1900)
            painter.setFont(font)

            points = reversed(points)

            for page_id, point in zip(self.other_pages_list, points):
                # painter.drawPoint(point)
                # код для отрисовки угловой кнопки
                r = QRect(QPoint(0, 0), QPoint(50, 30))
                r.moveCenter(point)
                self.left_corner_menu_items.append((page_id, r))

                cursor_pos = self.mapFromGlobal(QCursor().pos())
                page_name = self.pages.name(page_id)
                text_align = Qt.AlignVCenter | Qt.AlignLeft
                if r.contains(cursor_pos):
                    painter.setOpacity(1.0)
                    text = page_name
                    label_rect = QRect(r.topLeft(), r.bottomRight())
                    br = painter.boundingRect(QRect(), text_align, text)
                    label_rect.setWidth(br.width())
                    text_rect = label_rect
                else:
                    painter.setOpacity(.8)
                    text = page_name[0]
                    text_rect = r
                painter.drawText(text_rect, text_align, text)

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
            return # raise Exception("no data")

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
            return #raise Exception("no data")

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

        self.start_page_lang_btns = []

        self.set_loading_text()

        self.prepare_secret_hints()

        self.set_window_title("")
        self.set_window_style()

        self.current_page = self.pages.START_PAGE
        self.current_page_draw_callback = self.startpage_draw_callback
        self.current_page_transparency_value = 0.9
        self.update_other_pages_list()

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

        self.library_previews_list_active_item = None
        self.library_previews_list = None

        self.waterfall_previews_list_active_item = None
        self.waterfall_previews_list = None

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

        self.corner_menu_visibility = [False, False]
        self.left_corner_menu_items = []

        self.fullscreen_mode = False
        self.firstCall_showMaximized = True

        self.BW_filter_state = BWFilterState.off

        class CornerUIButtons():
            NO_BUTTON = 0
            LEFT_CORNER = 1
            RIGHT_CORNER = 2
            LEFT_CORNER_MENU = 3
            RIGHT_CORNER_MENU = 4

        self.CornerUIButtons = CornerUIButtons
        self.corner_UI_button_pressed = self.CornerUIButtons.NO_BUTTON

        self.SPT_init()

        self.gamepad_thread_instance = None
        self.left_stick_vec = QPointF(0, 0)
        self.right_stick_vec = QPointF(0, 0)

        self.fps_iterator = None
        self.fps_counter = 0
        self.fps_indicator = 0
        self.show_fps_indicator = Globals.DEBUG
        self.fps_timestamp = 0.0

        self.viewer_modal = False

        self.autoscroll_init()

        self.rounded_previews = True

        self.board_CP_cursor_handled = False

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

    def is_waterfall_page_active(self):
        return self.current_page == self.pages.WATERFALL_PAGE

    def cycle_change_page(self):
        pages = self.pages.all()
        if self.current_page != self.pages.START_PAGE:
            # удаляем ненужную здесь стартовую страницу, но делать это нужно,
            # когда она не выбрана, иначе получим бесконечный цикл ниже и краш приложения
            pages.remove(self.pages.START_PAGE)
        pages_shifted = pages[:]
        pages_shifted.append(pages_shifted.pop(0))
        for page, next_page in itertools.cycle(zip(pages, pages_shifted)):
            if page == self.current_page:
                break
        self.change_page(next_page)

    def change_page_at_appstart(self, page_type):
        # для того, чтобы после старта программы во время загрузки
        # отобразилась надпись ЗАГРУЗКА, а не висела/мелькала стартовая страница;
        # вместо вызова MW.change_page(MW.pages.VIEWER_PAGE)
        # пришлось вытащить из неё же код сюда. Пока я не понял почему change_page не работает как надо
        # (29 янв 26) может дело в том, что мы принудительно обновляем окно панели управления,
        # и за это время главное окно успевает появится и отрисоваться со стартовой страницей?
        # self.change_page(page_type)
        # (30 янв 26) код change_page для задания страницы на старте приложения использовать нельзя,
        # поздей будет рефакторинг по этому поводу
        self.current_page = page_type
        self.update_other_pages_list()
        self.recreate_control_panel(requested_page=page_type)

        self.set_page_transparency_and_draw_callback(page_type)

        if page_type == self.pages.WATERFALL_PAGE:
            if Globals.control_panel is not None:
                Globals.control_panel.setVisible(False)
        if page_type == self.pages.VIEWER_PAGE:
            self.viewer_reset() # для показа сообщения о загрузке

    def change_page(self, requested_page, force=False, init_force=False):
        CP = Globals.control_panel

        def cancel_fullscreen_on_control_panel():
            if CP is not None:
                if CP.fullscreen_flag:
                    CP.do_toggle_fullscreen()


        if self.current_page == requested_page and not init_force:
            return

        if self.handling_input and not force:
            self.update_control_panel_label_text()
            return

        if self.current_page == self.pages.VIEWER_PAGE:
            self.region_zoom_in_cancel()
            LibraryData().before_current_image_changed()
            cancel_fullscreen_on_control_panel()

        elif self.current_page == self.pages.BOARD_PAGE:
            self.board_TextElementDeactivateEditMode()
            self.board_region_zoom_do_cancel()
            cancel_fullscreen_on_control_panel()
            LibraryData().save_board_data()

        elif self.current_page == self.pages.WATERFALL_PAGE:
            # отключать модальный режим презентации здесь
            pass

        self.cancel_all_anim_tasks()
        self.hide_center_label()

        self.set_page_transparency_and_draw_callback(requested_page)

        if requested_page == self.pages.LIBRARY_PAGE:
            LibraryData().update_current_folder_columns()
            self.library_page_scroll_autoset_or_reset()
            if Globals.control_panel is not None:
                Globals.control_panel.setVisible(False)
            self.library_previews_list_active_item = None
            for folder_data in LibraryData().folders:
                images_data = folder_data.images_list
                ThumbnailsThread(folder_data, Globals, run_from_library=True).start()
            self.transformations_allowed = False

        elif requested_page == self.pages.WATERFALL_PAGE:
            LibraryData().update_current_folder_columns()
            if Globals.control_panel is not None:
                Globals.control_panel.setVisible(False)
            self.waterfall_previews_list_active_item = None
            for folder_data in LibraryData().folders:
                images_data = folder_data.images_list
                ThumbnailsThread(folder_data, Globals, run_from_library=True).start()
            if self.viewer_modal:
                self.transformations_allowed = True
            else:
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


        if self.current_page == self.pages.START_PAGE:
            if requested_page == self.pages.VIEWER_PAGE:
                self.restore_image_transformations()

        self.update_control_panel_label_text()

        self.current_page = requested_page

        self.update_other_pages_list()
        self.update()

    def update_other_pages_list(self):
        pages = self.pages.all()
        pages.remove(self.current_page)
        self.other_pages_list = pages

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

    def region_zoom_in_init(self, full=True, cancel=False):
        self.input_rect = None
        self.projected_rect = None
        self.orig_scale = None
        self.orig_pos = None
        self.zoom_region_defined = False
        self.zoom_level = 1.0
        self.region_zoom_in_input_started = False
        if not cancel:
            self.region_zoom_ui_fx = False
            self.input_rect_animated = None
            self.zoom_region_stage_factor = 0.0
            self.is_out_animation_ongoing = False
        if full:
            self.region_zoom_break_activated = False

    def region_zoom_finish(self):
        self.region_zoom_ui_fx = False
        self.input_rect_animated = None

    def region_zoom_in_cancel(self):
        if self.input_rect:
            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "image_center_position", self.image_center_position, self.orig_pos, self.update),
                        (self, "image_scale", self.image_scale, self.orig_scale, self.update),
                        (self, "input_rect_animated", self.projected_rect, self.input_rect, self.update),
                        (self, "zoom_region_stage_factor", 1.0, 0.0, self.update),
                    ],
                    anim_id="region_zoom_out",
                    duration=0.4,
                    easing=QEasingCurve.InOutCubic,
                    callback_on_finish=self.region_zoom_finish,
                )
            else:
                self.image_scale = self.orig_scale
                self.image_center_position = self.orig_pos
                self.zoom_region_stage_factor = 0.0
                self.input_rect_animated = self.input_rect
                self.region_zoom_finish()
            self.region_zoom_in_init(cancel=True)
            self.update()
            self.show_center_label(self.label_type.SCALE)
            # self.setCursor(Qt.ArrowCursor)

    def region_zoom_build_input_rect(self):
        if self.region_zoom_in_input_started and self.INPUT_POINT1 and self.INPUT_POINT2:
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
            scale, center_pos = self.do_scale_image(1.0, override_factor=factor, clamping=False)

            self.region_zoom_ui_fx = True

            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "image_center_position", before_pos, center_pos, self.update),
                        (self, "image_scale", self.image_scale, scale, self.update),
                        (self, "input_rect_animated", self.input_rect_animated, self.projected_rect, self.update),
                        (self, "zoom_region_stage_factor", 0.0, 1.0, self.update),
                    ],
                    anim_id="region_zoom_in",
                    duration=0.8,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.zoom_region_stage_factor = 1.0
                self.image_center_position = center_pos
                self.image_scale = scale
                self.input_rect_animated = self.projected_rect
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
        painter.save()
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
                painter.drawRect(projected_rect)

        if self.input_rect_animated:
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.input_rect_animated)

        if self.region_zoom_ui_fx:
            painter.setOpacity(0.8*self.zoom_region_stage_factor)
            painter.setClipping(True)
            r = QPainterPath()
            r.addRect(QRectF(self.rect()))
            r.addRect(QRectF(self.input_rect_animated))
            painter.setClipPath(r)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(Qt.black))
            painter.drawRect(self.rect())
            painter.setClipping(False)
            painter.setOpacity(1.0)
        painter.restore()

    def update_for_center_label_fade_effect(self):
        delta = time.time() - self.center_label_time
        if delta < self.CENTER_LABEL_TIME_LIMIT:
            self.update()
        else:
            self.show_easeInExpo_monitor = False

    def correct_scale(self):
        # корректировка скейла для всех картинок таким образом
        # чтобы каждая занимала максимум экранного пространства
        # и при этом умещалась полностью независимо от размера
        size_rect = self.get_rotated_pixmap(force_update=True).rect()
        viewer_target_rect = self.rect()
        viewer_target_rect.adjust(0, 50, 0, -50)
        projected_rect = QRectF(fit_rect_into_rect(size_rect, viewer_target_rect))
        max_scale_to_fit = projected_rect.width()/size_rect.width()
        if (size_rect.width() < viewer_target_rect.width()) and (size_rect.height() < viewer_target_rect.height()):
            # мелкие картинки
            self.image_scale = fit(self.STNG_small_images_fit_factor, 0.0, 1.0, 1.0, max_scale_to_fit)
        else:
            # остальные; ранее этот код обрабатывал и мелкие и большие
            self.image_scale = max_scale_to_fit

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
            self.error_pixmap_and_reset(_("Unable\nto display"), _("The file is corrupted"))

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
            self.error_pixmap_and_reset(_("No images"), "", no_background=True)
        else:
            if not LibraryData().is_supported_file(filepath):
                filename = os.path.basename(filepath)
                _unsup_file_msg = _("The file is not supported")
                self.error_pixmap_and_reset(_("Unable\nto display"), f"{_unsup_file_msg}\n{filename}")
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
                    self.error_pixmap_and_reset(_("The file is corrupted"), traceback.format_exc())
        if not self.viewer_modal:
            if not self.error:
                self.read_image_metadata(image_data)
        self.restore_image_transformations()
        if not self.viewer_modal:
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
        self.loading_text = _('LOADING')

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
            _broken_file_msg = _("broken file")
            return f"{name} - {_broken_file_msg}"
        else:
            return _("Loading")

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
        self.center_comment_window()

        if self.is_library_page_active() or self.is_waterfall_page_active():
            LibraryData().update_current_folder_columns()
            self.render_waterfall_backplate()

        SettingsWindow.center_if_on_screen()

        # здесь по возможности ещё должен быть и скейл относительно центра.
        self.update()

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

    def cursor_corners_buttons_and_menus(self):
        if self.over_left_corner_menu_item():
            self.setCursor(Qt.PointingHandCursor)
            return True

        elif self.over_corner_button(self.InteractiveCorners.TOPRIGHT):
            self.setCursor(Qt.PointingHandCursor)
            return True

        elif self.over_corner_button(self.InteractiveCorners.TOPLEFT):
            self.setCursor(Qt.PointingHandCursor)
            return True

        elif self.over_corner_menu(self.InteractiveCorners.TOPLEFT):
            self.setCursor(Qt.ArrowCursor)
            return True

        elif self.over_corner_menu(self.InteractiveCorners.TOPRIGHT):
            # правого меню как такого нет, но эта менюшка работает как одна большая кнопка,
            # отсюда и причина выпендрёжа нижа
            if self.is_top_right_menu_visible():
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            return True
        else:
            return False

    def cursor_control_panel(self):
        CP = Globals.control_panel
        if CP and any(btn.underMouse() for btn in CP.buttons_list):
            self.setCursor(Qt.PointingHandCursor)
            return True

        elif CP and CP.thumbnails_click(define_cursor_shape=True):
            # TODO: (6 фев 26) тут ведь интересно отметить, 
            # что миниатюры всем своим массивом создают единый прямоугольник,
            # его-то и надо проверять, а не полностью каждую видимую миниатюру
            self.setCursor(Qt.PointingHandCursor)
            return True

        else:
            return False

    def cursor_setter(self):
        CP = Globals.control_panel
        self.board_CP_cursor_handled = False

        # код отсюда вызывается из mouseMove панели управления
        if self.isActiveWindow():

            if False:
                pass

            elif self.SPT_is_spt_tool_activated():
                self.SPT_set_cursor()

            elif self.cursor_corners_buttons_and_menus():
                pass

            elif self.is_library_page_active():
                if self.library_previews_list_active_item:
                    self.setCursor(Qt.PointingHandCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)

            elif self.is_waterfall_page_active():
                if self.viewer_modal:
                    if self.region_zoom_in_input_started:
                        self.setCursor(Qt.CrossCursor)
                    elif self.is_cursor_over_image():
                        self.setCursor(Qt.SizeAllCursor)
                    else:
                        self.setCursor(Qt.ArrowCursor)
                else:
                    if self.waterfall_previews_list_active_item:
                        self.setCursor(Qt.PointingHandCursor)
                    else:
                        self.setCursor(Qt.ArrowCursor)

            elif self.is_viewer_page_active():
                if self.region_zoom_in_input_started:
                    self.setCursor(Qt.CrossCursor)
                elif self.cursor_control_panel():
                    pass
                elif self.is_cursor_over_image() and not (CP and CP.underMouse()):
                    self.setCursor(Qt.SizeAllCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)

            elif self.is_start_page_active():
                nothing = True
                cursor_pos = self.mapFromGlobal(QCursor().pos())
                for lang, rect in self.start_page_lang_btns:
                    if rect.contains(cursor_pos):
                        self.setCursor(Qt.PointingHandCursor)
                        nothing = False
                        break
                if nothing:
                    self.setCursor(Qt.ArrowCursor)

            elif self.is_board_page_active():
                # cursor_control_panel надо прописать здесь явно,
                # потому что задание курсора вызывается из окна панели управления.
                # Если этого не сделать, то задание курсора над панелью работать не будет.
                if self.cursor_control_panel():
                    # ввожу эту переменную скорей для наглядного понимания того
                    # как система работает, а не для фикса бага или подобного
                    self.board_CP_cursor_handled = True
                else:
                    # тут ничего не пишем, потому что
                    # курсор определяется в методе board_cursor_setter
                    # миксина главного окна в файле boards.py
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

        elif self.is_waterfall_page_active():
            if self.viewer_modal:
                self.viewport_image_animation()

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

            lang_button_pressed = False
            for lang, rect in self.start_page_lang_btns:
                if rect.contains(event.pos()):
                    lang_button_pressed = True
                    SettingsWindow.set_new_lang_across_entire_app(lang)
                    self.show_center_label(lang.upper())
                    self.update()
                    break

            if not lang_button_pressed:
                path = input_path_dialog("", exit=False)
                if path:
                    LibraryData().handle_input_data(path)
                    self.update()
        elif event.button() == Qt.RightButton:
            self.open_settings_window()

    def ui_check_mouse_over_corners(self, event):
        if event.button() == Qt.LeftButton:
            if self.over_corner_button(self.InteractiveCorners.TOPRIGHT):
                return self.CornerUIButtons.RIGHT_CORNER
            elif self.over_corner_button(self.InteractiveCorners.TOPLEFT):
                return self.CornerUIButtons.LEFT_CORNER
            elif self.over_corner_menu(self.InteractiveCorners.TOPLEFT):
                return self.CornerUIButtons.LEFT_CORNER_MENU
            elif self.over_corner_menu(self.InteractiveCorners.TOPRIGHT):
                return self.CornerUIButtons.RIGHT_CORNER_MENU
        return self.CornerUIButtons.NO_BUTTON

    def ui_handle_corners_click(self, corner_button):
        if corner_button == self.CornerUIButtons.RIGHT_CORNER:
            self.require_window_closing()
        elif corner_button == self.CornerUIButtons.LEFT_CORNER:
            self.cycle_change_page()
        elif corner_button == self.CornerUIButtons.LEFT_CORNER_MENU:
            self.handle_menu_item_click()
        elif corner_button == self.CornerUIButtons.RIGHT_CORNER_MENU:
            if self.is_top_right_menu_visible():
                self.showMinimized()

    def previews_list_mousePressEvent(self, event):
        p_list = None
        if self.is_library_page_active():
            p_list = self.library_previews_list

        elif self.is_waterfall_page_active():
            p_list = self.waterfall_previews_list

        if p_list:
            for item_rect, item_data in p_list:
                if item_rect.contains(event.pos()):
                    if self.is_library_page_active():
                        LibraryData().show_that_imd_on_viewer_page(item_data)
                    elif self.is_waterfall_page_active():
                        self.enter_modal_viewer()
                    break

    def previews_list_mouseMoveEvent(self, event):
        p_list = None
        if self.is_library_page_active():
            p_list = self.library_previews_list
            ai = self.library_previews_list_active_item
        elif self.is_waterfall_page_active():
            p_list = self.waterfall_previews_list
            ai = self.waterfall_previews_list_active_item

        def set_active_item(data):
            if self.is_library_page_active():
                self.library_previews_list_active_item = data
            elif self.is_waterfall_page_active():
                self.waterfall_previews_list_active_item = data

        if p_list:
            over_active_item = False
            if ai:
                r = self.previews_active_item_rect(ai[0])
                over_active_item = r.contains(event.pos())
            if not over_active_item:
                set_active_item(None)
                for item_rect, item_data in p_list:
                    if item_rect.contains(event.pos()):
                        set_active_item((item_rect, item_data))

    def enter_modal_viewer(self):
        if self.is_waterfall_page_active():
            if self.waterfall_previews_list_active_item:

                self.render_waterfall_backplate()
                item_rect, item_data = self.waterfall_previews_list_active_item
                LibraryData().prepare_modal_viewer_mode(item_data)
                self.viewer_reset()
                LibraryData().after_current_image_changed()

                self.transformations_allowed = True

                self.viewer_modal = True

            else:
                self.show_center_label(_("No active item!"), error=True)
        else:
            self.show_center_label(_("Modal viewer is not configured for current page!"), error=True)


    def leave_modal_viewer(self):
        if self.is_waterfall_page_active():
            self.viewer_modal = False
            self.waterfall_backplate = None
        else:
            self.show_center_label(_("Modal viewer is not configured for current page!"), error=True)

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
            if event.button() == Qt.LeftButton:
                if not self.clickable_scrollbars_mousePressEvent(event):
                    self.previews_list_mousePressEvent(event)

                    if self.folders_list:
                        for item_rect, item_data in self.folders_list:
                            if item_rect.contains(event.pos()):
                                # здесь устанавливаем текующую папку
                                LibraryData().make_folder_current(item_data)
                                break

            if event.button() == Qt.MiddleButton:
                self.autoscroll_middleMousePressEvent(event)

        elif self.is_waterfall_page_active():
            if self.viewer_modal:

                if event.button() == Qt.LeftButton:
                    self.left_button_pressed = True

                if self.isLeftClickAndCtrl(event):
                    self.region_zoom_in_mousePressEvent(event)

                if event.button() == Qt.LeftButton:
                    self.viewer_LeftButton_mousePressEvent(event)
            else:
                if event.button() == Qt.LeftButton:
                    if not self.clickable_scrollbars_mousePressEvent(event):
                        self.previews_list_mousePressEvent(event)

                if event.button() == Qt.MiddleButton:
                    self.autoscroll_middleMousePressEvent(event)


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

            if event.button() == Qt.LeftButton:
                self.viewer_LeftButton_mousePressEvent(event)

            ready_to_view = self.is_viewer_page_active() and not self.handling_input
            cursor_not_over_image = not self.is_cursor_over_image()
            not_ctrl_pressed = not self.isLeftClickAndCtrl(event)

            conditions = (
                ready_to_view,
                cursor_not_over_image,
                self.frameless_mode,
                self.STNG_doubleclick_toggle,
                not self.isLeftClickAndCtrl(event),
            )
            if all(conditions):
                self.toggle_to_frame_mode()




        self.update()
        super().mousePressEvent(event)

    def viewer_LeftButton_mousePressEvent(self, event):
        if self.transformations_allowed:
            self.old_cursor_pos = self.mapped_cursor_pos()
            for anim_task in self.get_current_animation_tasks_id("zoom"):
                anim_task.translation_delta_when_animation = QPointF(0, 0)
            if self.is_cursor_over_image():
                self.image_translating = True
                self.old_image_center_position = self.image_center_position
                self.update()

    def viewer_LeftButton_mouseMoveEvent(self, event):
        if self.transformations_allowed and self.image_translating:
            new =  self.old_image_center_position - (self.old_cursor_pos - self.mapped_cursor_pos())
            old = self.image_center_position
            if not self.is_there_any_task_with_anim_id("zoom"):
                self.image_center_position = new
            for anim_task in self.get_current_animation_tasks_id("zoom"):
                anim_task.translation_delta_when_animation = self.mapped_cursor_pos() - self.old_cursor_pos

    def viewer_LeftButton_mouseReleaseEvent(self, event):
        if self.transformations_allowed:
            self.image_translating = False
            self.update()

            for anim_task in self.get_current_animation_tasks_id("zoom"):
                anim_task.translation_delta_when_animation_summary += anim_task.translation_delta_when_animation
                anim_task.translation_delta_when_animation = QPointF(0, 0)

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
                self.viewer_LeftButton_mouseMoveEvent(event)

        elif self.is_library_page_active():
            if event.buttons() == Qt.NoButton:
                self.previews_list_mouseMoveEvent(event)

            if event.buttons() == Qt.LeftButton:
                self.clickable_scrollbars_mouseMoveEvent(event)

            if event.buttons() == Qt.MiddleButton:
                self.autoscroll_middleMouseMoveEvent()


        elif self.is_waterfall_page_active():
            if self.viewer_modal:
                if self.isLeftClickAndCtrl(event) or self.region_zoom_in_input_started:
                    self.region_zoom_in_mouseMoveEvent(event)
                elif event.buttons() == Qt.LeftButton:
                    self.viewer_LeftButton_mouseMoveEvent(event)
            else:
                if event.buttons() == Qt.NoButton:
                    self.previews_list_mouseMoveEvent(event)

                if event.buttons() == Qt.LeftButton:
                    self.clickable_scrollbars_mouseMoveEvent(event)

                if event.buttons() == Qt.MiddleButton:
                    self.autoscroll_middleMouseMoveEvent()


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
                self.viewer_LeftButton_mouseReleaseEvent(event)


        elif self.is_library_page_active():
            if event.button() == Qt.LeftButton:
                self.clickable_scrollbars_mouseReleaseEvent(event)

            if event.button() == Qt.MiddleButton:
                self.autoscroll_middleMouseReleaseEvent()

        elif self.is_waterfall_page_active():
            if self.viewer_modal:
                if event.button() == Qt.LeftButton:
                    self.left_button_pressed = False

                if self.isLeftClickAndCtrl(event) or self.region_zoom_in_input_started:
                    self.region_zoom_in_mouseReleaseEvent(event)
                elif event.button() == Qt.LeftButton:
                    self.viewer_LeftButton_mouseReleaseEvent(event)
            else:
                if event.button() == Qt.LeftButton:
                    self.clickable_scrollbars_mouseReleaseEvent(event)

                if event.button() == Qt.MiddleButton:
                    self.autoscroll_middleMouseReleaseEvent()



        self.update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.is_library_page_active():
            pass
            # (29 янв 26) TODO: подзабыл, почему прописал обработку
            # для этой страницы ниже в eventFilter, а не тут;
            # может, там лучше срабатывает или нет? Надо будет проверить позже
        if self.is_waterfall_page_active():
            pass
            # (29 янв 26) TODO: то же самое, что и выше
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
        elif self.is_waterfall_page_active():
            if event.type() == QEvent.MouseButtonDblClick:
                if self.viewer_modal:
                    self.leave_modal_viewer()
                    return True
                else:
                    pass
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

    def clickable_scrollbars_mousePressEvent(self, event):
        vs = self.vertical_scrollbars
        scrollbar_captured = False
        for scrollbar_index in vs.all():
            sb_data = vs.data[scrollbar_index]
            if sb_data.visible and sb_data.thumb_rect.contains(event.pos()):
                vs.capture_index = scrollbar_index
                scrollbar_captured = True
                vs.captured_thumb_rect_at_start = QRectF(sb_data.thumb_rect)
                vs.captured_curpos = event.pos()
                break
        return scrollbar_captured

    def clickable_scrollbars_mouseMoveEvent(self, event):
        vs = self.vertical_scrollbars
        index = vs.capture_index
        if index != vs.NO_SCROLLBAR:
            sb_data = vs.data[index]

            cursor_y_delta = event.pos().y() - vs.captured_curpos.y()
            current_thumb_rect_top_pos = vs.captured_thumb_rect_at_start.top() + cursor_y_delta

            y_pos = current_thumb_rect_top_pos
            y_pos -= sb_data.track_rect.top()

            thumb_slide_length = sb_data.track_rect.height()-sb_data.thumb_rect.height()
            if thumb_slide_length == 0.0:
                factor = 0.0
            else:
                factor = y_pos/thumb_slide_length


            # в этой версии ограничители нормализованы,
            # поэтому и появились значения 0.0 и 1.0
            factor = max(0.0, factor)
            factor = min(1.0, factor)

            # кстати, сами скроллбары (sb_data.thumb_rect) мы тут не перемещаем и не обновляем,
            # ведь они обновятся сами после изменения переменных
            # типа `X_scroll_offset` и последующей отрисовки в paintEvent
            cf = LibraryData().current_folder()
            LIBRARY_VIEWFRAME_HEIGHT = self.library_page_viewframe_height()
            WATERFALL_VIEWFRAME_HEIGHT = self.waterfall_page_viewframe_height()
            if index == vs.LIBRARY_PAGE_FOLDERS_LIST:
                slide_content_height = self.library_page_folders_content_height()-LIBRARY_VIEWFRAME_HEIGHT
                offset = factor*slide_content_height
                LibraryData().folderslist_scroll_offset = -offset

            elif index == vs.LIBRARY_PAGE_PREVIEWS_LIST:
                slide_content_height = self.library_page_previews_columns_content_height(cf)-LIBRARY_VIEWFRAME_HEIGHT
                offset = factor*slide_content_height
                cf.library_previews_scroll_offset = -offset

            elif index in [vs.WATERFALL_PAGE_LEFT, vs.WATERFALL_PAGE_RIGHT]:
                slide_content_height = self.waterfall_page_previews_columns_content_height(cf)-WATERFALL_VIEWFRAME_HEIGHT
                offset = factor*slide_content_height
                cf.waterfall_previews_scroll_offset = -offset

            self.update()

    def clickable_scrollbars_mouseReleaseEvent(self, event):
        vs = self.vertical_scrollbars
        vs.capture_index = vs.NO_SCROLLBAR



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
            geometry = None
            for n, screen in enumerate(screens):
                screen_geometry = screen.geometry()
                if screen_geometry.contains(pos):
                    geometry = screen_geometry
                    break
            if geometry is None:
                # Если в настройках выбран автозапуск при старте Windows,
                # то приложение может начать работу до входа в систему ещё во время оторбажения экрана ввода пароля.
                # В таком случае, geometry будет None
                # эта проверка нужна, чтобы апликуха не крашилась при автозапуске при использовании переменной geometry
                geometry = screen_geometry
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

    def library_page_folders_content_height(self):
        height = self.LIBRARY_FOLDER_ITEM_HEIGHT*len(LibraryData().all_folders())
        # добавляем высоту одного айтема, чтобы оствалось пустое поле внизу списка
        height += self.LIBRARY_FOLDER_ITEM_HEIGHT
        return height

    def library_page_previews_columns_content_height(self, folder_data):
        height = max(col.height for col in folder_data.library_columns)
        # сюда тоже добавляем высоту айтема папки, хоть эта часть не про папки, а про превьюшки
        # в итоге получится пустое поле внизу списка
        height += self.LIBRARY_FOLDER_ITEM_HEIGHT
        return height

    def library_page_viewframe_height(self):
        return self.rect().height()

    def waterfall_page_previews_columns_content_height(self, folder_data):
        height = max(col.height for col in folder_data.waterfall_columns)
        # сюда тоже добавляем высоту айтема папки, хоть эта часть не про папки, а про превьюшки
        # в итоге получится пустое поле внизу списка
        height += self.LIBRARY_FOLDER_ITEM_HEIGHT
        return height

    def waterfall_page_viewframe_height(self):
        return self.rect().height()

    def library_page_scroll_autoset_or_reset(self):
        content_height = self.library_page_folders_content_height()
        VIEWFRAME_HEIGHT = self.library_page_viewframe_height()
        if content_height > VIEWFRAME_HEIGHT:
            # если контент не помещается в окне,
            # то надо установить сдвиг таким образом,
            # чтобы текущая папка была посередине
            viewport_capacity = VIEWFRAME_HEIGHT/self.LIBRARY_FOLDER_ITEM_HEIGHT
            offset_by_center = int(viewport_capacity/2)
            # вычисление сдвига в пикселях, чтобы папка была посередине
            current_folder_index = LibraryData()._index
            _offset = -self.LIBRARY_FOLDER_ITEM_HEIGHT*(current_folder_index-offset_by_center)
            # применение ограничителей сдвига:
            # если текущая папка в начале или в конце списка,
            # то нет смысла требовать её показа в середине
            max_offset = content_height - VIEWFRAME_HEIGHT
            _offset = max(-max_offset, _offset)
            _offset = min(0, _offset)
            LibraryData().folderslist_scroll_offset = _offset
        else:
            LibraryData().folderslist_scroll_offset = 0

    def library_page_is_inside_left_part(self):
        curpos = self.mapFromGlobal(QCursor().pos())
        left_column = QRect(self.rect())
        left_column.setRight(int(self.rect().width()/2))
        return left_column.contains(curpos)

    def apply_scroll_and_limits(self, offset, offset_delta, content_height, viewframe_height):
        offset += offset_delta
        max_offset = content_height-viewframe_height
        # ограничение при скроле в самом низу списка
        offset = max(-max_offset, offset)
        # ограничение при скроле в самому верху списка
        offset = min(0, offset)
        return offset

    def previews_list_folder_list_wheelEvent(self, scroll_value, event):
        offset_delta = int(scroll_value*200)

        if self.is_library_page_active():
            VIEWFRAME_HEIGHT = self.library_page_viewframe_height()

            if self.library_page_is_inside_left_part():
                content_height = self.library_page_folders_content_height()
                if content_height > VIEWFRAME_HEIGHT:
                    LibraryData().folderslist_scroll_offset = self.apply_scroll_and_limits(
                                                                LibraryData().folderslist_scroll_offset,
                                                                offset_delta,
                                                                content_height,
                                                                VIEWFRAME_HEIGHT,
                                                            )
            else:
                cf = LibraryData().current_folder()
                if cf.library_columns:
                    content_height = self.library_page_previews_columns_content_height(cf)
                    if content_height > VIEWFRAME_HEIGHT:
                        cf.library_previews_scroll_offset = self.apply_scroll_and_limits(
                                                                cf.library_previews_scroll_offset,
                                                                offset_delta,
                                                                content_height,
                                                                VIEWFRAME_HEIGHT,
                                                            )
                        self.reset_previews_active_item_on_scrolling(event)

        elif self.is_waterfall_page_active():
            VIEWFRAME_HEIGHT = self.waterfall_page_viewframe_height()
            cf = LibraryData().current_folder()
            if cf.waterfall_columns:
                content_height = self.waterfall_page_previews_columns_content_height(cf)
                if content_height > VIEWFRAME_HEIGHT:
                    cf.waterfall_previews_scroll_offset = self.apply_scroll_and_limits(
                                                            cf.waterfall_previews_scroll_offset,
                                                            offset_delta,
                                                            content_height,
                                                            VIEWFRAME_HEIGHT,
                                                        )
                    self.reset_previews_active_item_on_scrolling(event)

        self.update()

    def reset_previews_active_item_on_scrolling(self, event):
        current_item = None
        p_list = None
        if self.is_library_page_active():
            p_list = self.library_previews_list
            active_item = self.library_previews_list_active_item
        elif self.is_waterfall_page_active():
            p_list = self.waterfall_previews_list
            active_item = self.waterfall_previews_list_active_item

        def reset():
            if self.is_library_page_active():
                self.library_previews_list_active_item = None
            elif self.is_waterfall_page_active():
                self.waterfall_previews_list_active_item = None

        if p_list:
            for item_rect, item_data in p_list:
                if item_rect.contains(event.pos()):
                    current_item = (item_rect, item_data)
            if current_item != active_item or not any(self.corner_menu_visibility):
                # обнуляем выделенную мышкой превьюшку,
                # если под мышкой уже находится другая превьюшка
                reset()

    def is_control_panel_under_mouse(self):
        if Globals.control_panel is not None:
            if Globals.control_panel.isVisible():
                if Globals.control_panel.underMouse():
                    return True
        return False

    def viewer_wheelEvent(self, event, scroll_value, ctrl, shift, no_mod, control_panel_undermouse):

        if self.left_button_pressed and self.animated:
            self.do_scroll_playbar(scroll_value)
            self.show_center_label(self.label_type.FRAME_NUMBER)
            return True
        if shift and ctrl and self.animated:
            self.do_scroll_playspeed(scroll_value)
            self.show_center_label(self.label_type.PLAYSPEED)
            return True
        if no_mod and self.STNG_zoom_on_mousewheel and (not self.left_button_pressed) and (not control_panel_undermouse):
            self.do_scale_image(scroll_value)
            return True
        else:
            return False

    def waterfall_change_number_of_columns(self, event, scroll_value):
        min_value, max_value = SettingsWindow.get_setting_span('waterfall_columns_number')
        if scroll_value > 0:
            n = 1
        else:
            n = -1
        cf = LibraryData().current_folder()
        setting_value = self.STNG_waterfall_columns_number
        # пока закоментил, потому что не очень интуитивно получается
        # setting_value = self.STNG_waterfall_columns_number
        if setting_value > cf.waterfall_number_of_columns:
            value = setting_value
        else:
            if setting_value == 0:
                value = 0
            else:
                value = cf.waterfall_number_of_columns
        value = int(value)
        value += n
        value = max(min_value, min(max_value, value))
        # TODO: вообще тут лучше бы всё переписать, ибо я думал, что изменяя переменную настройки 
        # на главном окне, у меня должно изменяться и значение на матрице настроек,
        # а это оказалось не так. Я уже забыл, как в этом проекте работают настройки
        # Кстати, в одном месте boards.py вызывается store_to_disk, и именнно поэтому
        # там тоже надо будет всё переписать, ибо по факту настройка не сохраняется на диск 
        self.STNG_waterfall_columns_number = float(value)
        SettingsWindow.set_setting_value('waterfall_columns_number', float(value))
        value = int(value)
        if value == 0:
            msg = _(f"You've set 0 columns, so the number of columns depends only on the window width.")
        elif value == max_value:
            msg = _(f"You've set {value} columns. This is the maximum!")
        else:
            msg = _(f"You've set {value} columns")
        LibraryData().update_current_folder_columns()
        msg += f"\n\n{cf.waterfall_number_of_columns} columns are now displayed"
        self.show_center_label(msg)
        self.update()

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
            self.previews_list_folder_list_wheelEvent(scroll_value, event)

        elif self.is_waterfall_page_active():
            if self.viewer_modal:
                self.viewer_wheelEvent(event, scroll_value, ctrl, shift, no_mod, control_panel_undermouse)
            else:
                if ctrl and (not shift):
                    self.waterfall_change_number_of_columns(event, scroll_value)
                else:
                    self.previews_list_folder_list_wheelEvent(scroll_value, event)

        elif self.is_viewer_page_active():

            if self.show_tags_overlay:
                self.tagging_main_wheelEvent(self, event)
                return

            if ctrl and (not shift) and self.STNG_zoom_on_mousewheel:
                self.do_scroll_images_list(scroll_value)
            if self.viewer_wheelEvent(event, scroll_value, ctrl, shift, no_mod, control_panel_undermouse):
                pass #обработка внутри функции в условии
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

    def do_scale_image(self, scroll_value, cursor_pivot=True, override_factor=None, slow=False, clamping=True):

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
        if clamping:
            # claming scale to 100%
            if (before_scale < 1.0 and new_scale > 1.0) or (before_scale > 1.0 and new_scale < 1.0):
                factor = 1.0/scale

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

    def draw_rounded_frame_progress_label(self, event_painter, pos, text, bold=False,
                    color=Qt.red, normalized_progress=0.0, from_center_to_sides=False):

        font = event_painter.font()
        font.setFamily('consolas')
        if bold:
            font.setPixelSize(16)
            font.setWeight(1900)
            pen_size = 2
        else:
            font.setPixelSize(15)
            pen_size = 1

        style = Qt.AlignVCenter | Qt.AlignHCenter
        event_painter.setFont(font)
        text_rect = event_painter.boundingRect(QRect(), Qt.AlignLeft, text)

        h_offset = 5
        v_offset = 3
        main_rect = QRect(0, 0, text_rect.width()+h_offset*2, text_rect.height()+v_offset*2)

        pix = QPixmap(main_rect.width()+1, main_rect.height()+1)
        pix.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pix)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setFont(font)

        path = QPainterPath()
        path.addRoundedRect(QRectF(main_rect.adjusted(2, 2, -2, -2)), 3, 3)

        pen = QPen(color, pen_size)
        painter.setPen(pen)

        painter.setClipping(True)
        painter.setClipPath(path)

        if from_center_to_sides:
            rr = QRectF(QPointF(pix.width()/2*(1.0-normalized_progress), 0), QSizeF(pix.size()))
        else:
            rr = QRectF(QPointF(0, 0), QSizeF(pix.size()))
        rr.setWidth(rr.width()*normalized_progress)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawRect(rr)

        painter.setClipping(False)

        painter.setPen(pen)

        cm = painter.compositionMode()
        painter.setCompositionMode(QPainter.CompositionMode_SourceOut)
        painter.drawText(QRect(QPoint(0, 0), main_rect.size()), style, text)
        painter.setCompositionMode(cm)

        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        painter.end()

        show_pos_rect = QRect(QPoint(0,0), pix.size())
        show_pos_rect.moveCenter(pos)
        event_painter.drawPixmap(show_pos_rect, pix)

    def draw_rounded_frame_label(self, painter, pos, text, bold=False, color=Qt.red):
        painter.save()

        font = painter.font()
        font.setFamily('consolas')
        if bold:
            font.setPixelSize(16)
            font.setWeight(1900)
        else:
            font.setPixelSize(15)
        painter.setFont(font)

        style = Qt.AlignLeft
        r = painter.boundingRect(QRect(), style, text)
        r.moveCenter(pos)

        if bold:
            pen_size = 2
        else:
            pen_size = 1

        painter.setPen(QPen(color, pen_size))
        painter.setBrush(Qt.NoBrush)
        painter.drawText(r, style, text)

        path = QPainterPath()
        r.adjust(-3, 0, 3, 0)
        path.addRoundedRect(QRectF(r), 3, 3)
        painter.drawPath(path)

        painter.restore()

    def draw_center_label(self, painter, text, large=False):
        def set_font(pr):
            font = pr.font()
            if large:
                # font.setPixelSize(self.rect().height()//8)
                font.setPixelSize(150)
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

    def draw_FPS_indicator(self, painter):
        time_value = time.time()
        iterator_value = time_value % 1.0
        if self.fps_iterator is not None:
            if iterator_value < self.fps_iterator:
                self.fps_indicator = self.fps_counter
                self.fps_counter = 0
            else:
                self.fps_counter += 1
        self.fps_iterator = iterator_value
        fps_indicator_extrapolated = int(1.0/(time_value - self.fps_timestamp))
        self.fps_timestamp = time_value
        painter.save()
        text_to_show = f'FACTUAL FPS: {self.fps_indicator}, EXTRAPOLATED FPS: {fps_indicator_extrapolated} (BASED ON LAST FRAME CALCULATION TIME)' \
            f'\nTHE VALUE TO THE RIGHT CHANGES WHEN THE WINDOW DRAWING HAPPENS {time_value-math.trunc(time_value):.03}' \
            f'\nIf it is not updated in real time, it means new frames are not generated. Usually frames generation caused by the animation timer or mouse moving\\mouse buttons\\keyboard keys'
        r = self.rect()
        r.moveTopLeft(QPoint(210, 0))
        painter.drawText(r, Qt.AlignLeft, text_to_show)
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
        if self.show_fps_indicator:
            self.draw_FPS_indicator(painter)
        painter.end()

    def startpage_draw_callback(self, painter, event):
        self.draw_startpage(painter)

    def viewerpage_draw_callback(self, painter, event):
        self.draw_viewer_content(painter)
        self.region_zoom_in_draw(painter)

    def librarypage_draw_callback(self, painter, event):
        self.draw_library(painter)

    def boardpage_draw_callback(self, painter, event):
        self.board_draw(painter, event)

    def waterfallpage_draw_callback(self, painter, event):
        self.draw_waterfall(painter, event)

    def set_page_transparency_and_draw_callback(self, page_type):
        if page_type == self.pages.START_PAGE:
            self.current_page_transparency_value = self.STNG_start_page_transparency
            self.current_page_draw_callback = self.startpage_draw_callback

        elif page_type == self.pages.VIEWER_PAGE:
            self.current_page_transparency_value = self.STNG_viewer_page_transparency
            self.current_page_draw_callback = self.viewerpage_draw_callback

        elif page_type == self.pages.LIBRARY_PAGE:
            self.current_page_transparency_value = self.STNG_library_page_transparency
            self.current_page_draw_callback = self.librarypage_draw_callback

        elif page_type == self.pages.BOARD_PAGE:
            self.current_page_transparency_value = self.STNG_board_page_transparency
            self.current_page_draw_callback = self.boardpage_draw_callback

        elif page_type == self.pages.WATERFALL_PAGE:
            self.current_page_transparency_value = self.STNG_waterfall_page_transparency
            self.current_page_draw_callback = self.waterfallpage_draw_callback

    def _paintEvent(self, event, painter):
        if Globals.ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # draw darkened translucent background
        if self.frameless_mode:
            painter.setOpacity(self.current_page_transparency_value)

            painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
            painter.drawRect(self.rect())
            painter.setOpacity(1.0)
        else:
            painter.setBrush(QBrush(QColor(10, 10, 10), Qt.SolidPattern))
            painter.drawRect(self.rect())

        # draw current page
        self.current_page_draw_callback(painter, event)


        # autosroll animated activation zone
        self.autoscroll_draw(painter)


        # draw slice pipette tool
        self.SPT_draw_info(painter)


        # draw center label
        self.draw_center_label_main(painter)


        # draw minimize button holder as menu
        self.draw_corner_menu(painter, self.InteractiveCorners.TOPRIGHT)
        # draw page menu
        self.draw_corner_menu(painter, self.InteractiveCorners.TOPLEFT)
        # draw close button
        self.draw_corner_button(painter, self.InteractiveCorners.TOPRIGHT)
        # draw page button
        self.draw_corner_button(painter, self.InteractiveCorners.TOPLEFT)

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

    def draw_waterfall(self, painter, event):
        if self.viewer_modal:
            painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.drawPixmap(QPoint(0, 0), self.waterfall_backplate)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.setRenderHint(QPainter.Antialiasing, True)

            self.draw_viewer_modal(painter)
            self.region_zoom_in_draw(painter)
        else:
            painter.save()
            self.set_font_for_library_and_waterfall_pages(painter)
            self.draw_waterfall_content(painter)
            painter.restore()

    def draw_viewer_modal(self, painter):
        painter.save()
        painter.setPen(QPen(Qt.white))
        self.draw_viewer_content(painter)
        painter.restore()

    def render_waterfall_backplate(self):
        wb = self.waterfall_backplate = QPixmap(self.rect().size())
        wb.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(wb)
        painter.setOpacity(0.8)
        self.draw_waterfall_content(painter, render_as_blackplate=True)
        painter.fillRect(self.rect(), QBrush(QColor(0, 0, 0, 170)))
        painter.end()

    def draw_waterfall_content(self, painter, render_as_blackplate=False):

        cf = LibraryData().current_folder()

        interaction_list = self.waterfall_previews_list = []
        columns = cf.waterfall_columns
        active_item = self.waterfall_previews_list_active_item

        r = content_rect = self.rect()

        if columns:
            content_width = cf.waterfall_number_of_columns*cf.column_width

            left_offset = (self.rect().width()-content_width)/2
            content_rect = QRectF(left_offset, 0, content_width, r.height()).toRect()

        painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
        painter.setRenderHint(QPainter.Antialiasing, False)

        self.draw_previews_as_columns(painter,
                                        columns,
                                        interaction_list,
                                        active_item,
                                        content_rect,
                                        cf.column_width, cf.waterfall_previews_scroll_offset,
                                        bool(cf.images_list),
                                        render_as_blackplate,
                                    )

        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if columns and not render_as_blackplate:
            self.draw_waterfall_scrollbars(painter, content_rect)

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
        start_text = _("DRAG AND DROP A FILE OR A FOLDER")
        painter.drawText(rect1, Qt.TextWordWrap | Qt.AlignCenter, start_text)

        set_font_size(25, False)
        start_text = _("or left mouse click to open Explorer dialog.")
        start_text += _("\n\nRight mouse click to open settings window.")

        if Globals.lite_mode:
            start_text += _("\n\n[the program is running in lite mode]")
        else:
            start_text += _("\n\n\n\n[the program is running in standard mode]")

        painter.drawText(rect2, Qt.TextWordWrap | Qt.AlignHCenter | Qt.AlignTop, start_text)

        langs = ['en', 'ru', 'de', 'fr', 'it', 'es']
        SPAN_WIDTH = 30
        LANG_BTN_WIDTH = 100
        langs_count = len(langs)
        top_offset = self.rect().bottom() - LANG_BTN_WIDTH * 2.5
        left_offset = (self.rect().width() - (langs_count*LANG_BTN_WIDTH + SPAN_WIDTH*(langs_count-1)))/2
        self.start_page_lang_btns = []
        cursor_pos = self.mapFromGlobal(QCursor().pos())
        for n, lang in enumerate(langs):
            rect = QRectF(left_offset, top_offset, LANG_BTN_WIDTH, LANG_BTN_WIDTH)
            self.draw_startpage_langflag(painter, rect, cursor_pos, lang)
            self.start_page_lang_btns.append((lang, QRectF(rect)))
            left_offset += (LANG_BTN_WIDTH + SPAN_WIDTH)

    def draw_startpage_langflag(self, painter, rect, cursor_pos, lang):
        painter.save()

        cur_lang = SettingsWindow.matrix['ui_lang'][0]

        is_cursor_over = rect.contains(cursor_pos)
        is_cur_lang = cur_lang == lang


        if is_cur_lang or is_cursor_over:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)
            if is_cursor_over and not is_cur_lang:
                alpha = 10
            else:
                alpha = 20
            painter.setBrush(QColor(200, 200, 200, alpha))
            path = QPainterPath()
            path.addRoundedRect(rect, 20, 20)
            painter.drawPath(path)

            if is_cursor_over:
                if lang == '':
                    pass
                elif lang == 'ru':
                    lang_name = _("Russian")
                elif lang == 'en':
                    lang_name = _('English')
                elif lang == 'fr':
                    lang_name = _('French')
                elif lang == 'de':
                    lang_name = _('German')
                elif lang == 'es':
                    lang_name = _('Spanish')
                elif lang == 'it':
                    lang_name = _('Italian')

                painter.setPen(QPen(Qt.white, 1))
                lang_name_rect = QRectF(rect).adjusted(-50, -50, 50, 50)
                painter.drawText(lang_name_rect, Qt.AlignTop | Qt.AlignHCenter, lang_name)


        painter.setPen(QPen(Qt.gray, 1))
        lang_rect = rect.adjusted(20, 20, -20, -20)
        painter.drawRect(lang_rect)

        if lang == '':
            pass

        elif lang == 'en':

            red = QColor(201, 7, 42)
            white = QColor(255, 255, 255)
            blue = QColor(0, 27, 105)

            painter.fillRect(lang_rect, red)

            offset = 10
            lang_rect.adjust(offset, 0, 0, -offset)
            painter.fillRect(lang_rect, white)
            offset = 8
            lang_rect.adjust(offset, 0, 0, -offset)
            painter.fillRect(lang_rect, blue)

            p1 = lang_rect.bottomLeft()
            p2 = lang_rect.topRight() + QPointF(lang_rect.width()/2, 0)

            painter.setClipping(True)
            painter.setClipRect(lang_rect)
            painter.setPen(QPen(white, 15))

            painter.drawLine(p1 + QPoint(0, 6), p2 + QPoint(0, 6))
            painter.setPen(QPen(red, 5))

            p1 += QPoint(0, 3)
            p2 += QPoint(0, 3)
            painter.drawLine(p1, p2)

            painter.setClipping(False)

        elif lang == 'ru':

            white = QColor(255, 255, 255)
            blue = QColor(0, 54, 167)
            red = QColor(214, 39, 24)

            painter.fillRect(lang_rect, white)
            offset = lang_rect.height()/3
            lang_rect.adjust(0, offset, 0, 0)
            painter.fillRect(lang_rect, blue)
            lang_rect.adjust(0, offset, 0, 0)
            painter.fillRect(lang_rect, red)

        elif lang == 'de':

            schwarz = QColor(0, 0, 0)
            rot = QColor(222, 0, 0)
            gelb = QColor(255, 207, 0)

            painter.fillRect(lang_rect, schwarz)
            offset = lang_rect.height()/3
            lang_rect.adjust(0, offset, 0, 0)
            painter.fillRect(lang_rect, rot)
            lang_rect.adjust(0, offset, 0, 0)
            painter.fillRect(lang_rect, gelb)

        elif lang == 'fr':

            blue =  QColor(0, 0, 146)
            white = QColor(255, 255, 255)
            red =  QColor(226, 0, 6)

            painter.fillRect(lang_rect, blue)
            offset = lang_rect.width()/3
            lang_rect.adjust(offset, 0, 0, 0)
            painter.fillRect(lang_rect, white)
            lang_rect.adjust(offset, 0, 0, 0)
            painter.fillRect(lang_rect, red)

        elif lang == 'it':

            green = QColor(0, 147, 68)
            white = QColor(255, 255, 255)
            red = QColor(207, 39, 52)

            painter.fillRect(lang_rect, green)
            offset = lang_rect.width()/3
            lang_rect.adjust(offset, 0, 0, 0)
            painter.fillRect(lang_rect, white)
            lang_rect.adjust(offset, 0, 0, 0)
            painter.fillRect(lang_rect, red)

        elif lang == 'es':

            red = QColor(199, 3, 24)
            yellow = QColor(255, 197, 0)

            painter.fillRect(lang_rect, red)
            offset = lang_rect.height()/4
            lang_rect.adjust(0, offset, 0, 0)
            painter.fillRect(lang_rect, yellow)
            font = QFont()
            TEXT_HEIGHT = 18
            font.setPixelSize(TEXT_HEIGHT)
            font.setWeight(1500)
            painter.setFont(font)
            painter.setPen(Qt.black)
            painter.drawText(lang_rect.topLeft() + QPointF(0, offset + (offset*2 - TEXT_HEIGHT)/2), ' ES')
            lang_rect.adjust(0, offset*2, 0, 0)
            painter.fillRect(lang_rect, red)

        painter.restore()

    def draw_32bit_warning(self, painter):
        if Globals.is_32bit_exe:
            text = _(
                "The program is running under 32-bit Python interpreter,"
                "\nso the memory limit is 1.5GB which is not enough."
                "\nOnce the limit will be reached, the program deadly freezes."
                "\nUse 64-bit Python interpreter to avoid this kind of issues."
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

    def set_font_for_library_and_waterfall_pages(self, painter):
        font = painter.font()
        font.setPixelSize(20)
        font.setWeight(1900)
        font.setFamily("Consolas")
        painter.setFont(font)

    def draw_library(self, painter):
        painter.save()
        self.set_font_for_library_and_waterfall_pages(painter)

        H = self.LIBRARY_FOLDER_ITEM_HEIGHT
        CENTER_OFFSET = 50
        CENTER_X_POSITION = self.get_center_x_position()

        LEFT_COL_WIDTH = CENTER_X_POSITION-CENTER_OFFSET
        left_col_check_rect = QRect(0, 0, LEFT_COL_WIDTH, self.rect().height())

        RIGHT_COLUMN_LEFT = CENTER_X_POSITION+CENTER_OFFSET
        RIGHT_COLUMN_WIDTH = self.rect().width() - RIGHT_COLUMN_LEFT
        right_col_check_rect = QRect(RIGHT_COLUMN_LEFT, 0, RIGHT_COLUMN_WIDTH, self.rect().height())

        if Globals.DEBUG:
            painter.save()
            painter.setPen(QPen(Qt.white))
            for r in [left_col_check_rect, right_col_check_rect]:
                painter.drawLine(r.topLeft(), r.bottomRight())
                painter.drawLine(r.bottomLeft(), r.topRight())
            painter.restore()

        cf = LibraryData().current_folder()

        # left column
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
            if cf == folder_data:
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
        # left column end

        # right column
        painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
        painter.setRenderHint(QPainter.Antialiasing, False)

        interaction_list = self.library_previews_list = []
        columns = cf.library_columns
        active_item = self.library_previews_list_active_item

        self.draw_previews_as_columns(painter,
                                        columns,
                                        interaction_list,
                                        active_item,
                                        right_col_check_rect,
                                        cf.column_width, cf.library_previews_scroll_offset,
                                        bool(cf.images_list)
                                    )

        if columns and active_item:
            item_rect, item_data = active_item
            if not hasattr(item_data, "library_page_cached_version"):
                item_data.library_page_cached_version = load_image_respect_orientation(
                    item_data.filepath,
                    highres_svg=LibraryData().is_svg_file(item_data.filepath)
                )
            cached = item_data.library_page_cached_version
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
                    _error_msg = _("Error")
                    painter.drawText(main_rect, Qt.AlignCenter, f'{_error_msg}\n{item_data.filename}')
        # right column end

        self.draw_middle_line(painter)

        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.draw_library_scrollbars(painter)

        painter.restore()

    def draw_previews_as_columns(self, painter, columns, interaction_list, active_item, rect, column_width, scroll_offset, any_images, render_as_blackplate=False):

        PREVIEW_CORNER_RADIUS = Globals.PREVIEW_CORNER_RADIUS
        rounded_previews = self.rounded_previews

        if columns:
            if rounded_previews:
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setClipping(True)

            left = rect.left()
            painter.setPen(QPen(QColor(Qt.gray)))
            painter.setBrush(QBrush(Qt.black))
            painter.setPen(Qt.NoPen)
            main_offset_y = 20 + scroll_offset
            for n, col in enumerate(columns):
                offset_x = left + column_width*n
                offset_y = main_offset_y
                for im_data in col.images_data:
                    w = im_data.preview_size.width()
                    h = im_data.preview_size.height()
                    r = QRectF(offset_x, offset_y, w, h)
                    r.adjust(1, 1, -1, -1)
                    interaction_list.append((r, im_data))
                    pixmap = im_data.preview
                    if rounded_previews:
                        path = QPainterPath()
                        path.addRoundedRect(r, PREVIEW_CORNER_RADIUS, PREVIEW_CORNER_RADIUS)
                        painter.setClipPath(path)
                        # painter.drawRect(r) #for images with transparent layer
                        painter.drawPixmap(r.toRect(), pixmap)

                    else:
                        painter.drawPixmap(r.toRect(), pixmap)
                    offset_y += h

            if rounded_previews:
                painter.setClipping(False)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, False)
                painter.setRenderHint(QPainter.Antialiasing, False)

            if active_item and (not render_as_blackplate) and (not any(self.corner_menu_visibility)):
                item_rect, item_data = active_item
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

        else:
            painter.setPen(QPen(Qt.white))
            if any_images:
                self.draw_rounded_frame_progress_label(painter,
                                            rect.center(),
                                            _("Please wait"),
                                            normalized_progress=time.time() % 1.0,
                                            from_center_to_sides=True,
                )
            else:
                painter.drawText(rect, Qt.AlignCenter, _("No images"))

    def reset_scrollbars_visibility(self):
        vs = self.vertical_scrollbars
        for key, item in vs.data.items():
            item.visible = False

    def draw_waterfall_scrollbars(self, painter, content_rect):

        SCROLLBAR_WIDTH = self.SCROLLBAR_WIDTH
        VERTICAL_OFFSET = 50
        SCROLLBAR_HEIGHT = self.rect().height()-int(VERTICAL_OFFSET*1.1)

        curpos = self.mapped_cursor_pos()
        vs = self.vertical_scrollbars
        self.reset_scrollbars_visibility()

        cf = LibraryData().current_folder()
        viewframe_height = self.waterfall_page_viewframe_height()
        content_height = self.waterfall_page_previews_columns_content_height(cf)

        # скроллбар реагирует на мышку, если над ним показывается меню,
        # а так быть не должно, поэтому вырубаем этот эффект здесь
        ha = not any(self.corner_menu_visibility)

        offset_times = 4
        if cf.waterfall_columns:
            self.draw_vertical_scrollbar(painter,
                content_height=content_height,
                viewframe_height=viewframe_height,
                track_rect=QRect(
                    content_rect.left()-SCROLLBAR_WIDTH*offset_times,
                    VERTICAL_OFFSET,
                    SCROLLBAR_WIDTH,
                    SCROLLBAR_HEIGHT,
                ),
                content_offset=cf.waterfall_previews_scroll_offset,
                index=vs.WATERFALL_PAGE_LEFT,
                curpos=curpos,
                highlighting_allowed=ha,
            )

            self.draw_vertical_scrollbar(painter,
                content_height=content_height,
                viewframe_height=viewframe_height,
                track_rect=QRect(
                    content_rect.right()+SCROLLBAR_WIDTH*(offset_times-1),
                    VERTICAL_OFFSET,
                    SCROLLBAR_WIDTH,
                    SCROLLBAR_HEIGHT,
                ),
                content_offset=cf.waterfall_previews_scroll_offset,
                index=vs.WATERFALL_PAGE_RIGHT,
                curpos=curpos,
                highlighting_allowed=ha,
            )

    def draw_library_scrollbars(self, painter):

        CXP = self.get_center_x_position()
        OFFSET_FROM_CENTER = 5

        SCROLLBAR_WIDTH = self.SCROLLBAR_WIDTH
        VERTICAL_OFFSET = 40
        SCROLLBAR_HEIGHT = self.rect().height()-VERTICAL_OFFSET*2

        curpos = self.mapped_cursor_pos()
        vs = self.vertical_scrollbars
        self.reset_scrollbars_visibility()

        viewframe_height = self.library_page_viewframe_height()

        self.draw_vertical_scrollbar(painter,
            content_height=self.library_page_folders_content_height(),
            viewframe_height=viewframe_height,
            track_rect=QRect(
                CXP-(SCROLLBAR_WIDTH+OFFSET_FROM_CENTER),
                VERTICAL_OFFSET,
                SCROLLBAR_WIDTH,
                SCROLLBAR_HEIGHT,

            ),
            content_offset=LibraryData().folderslist_scroll_offset,
            index=vs.LIBRARY_PAGE_FOLDERS_LIST,
            curpos=curpos,
        )

        cf = LibraryData().current_folder()
        if cf.library_columns:
            self.draw_vertical_scrollbar(painter,
                content_height=self.library_page_previews_columns_content_height(cf),
                viewframe_height=viewframe_height,
                track_rect=QRect(
                    CXP+OFFSET_FROM_CENTER,
                    VERTICAL_OFFSET,
                    SCROLLBAR_WIDTH,
                    SCROLLBAR_HEIGHT,
                ),
                content_offset=cf.library_previews_scroll_offset,
                index=vs.LIBRARY_PAGE_PREVIEWS_LIST,
                curpos=curpos,
            )

    def draw_vertical_scrollbar(self, painter, content_height=1000,
                viewframe_height=100, track_rect=QRect(), content_offset=0.0, index=0, curpos=None,
                highlighting_allowed=True):

        vs = self.vertical_scrollbars
        data = vs.data[index]
        if content_height > viewframe_height:

            painter.save()
            painter.setOpacity(0.1)
            painter.fillRect(track_rect, Qt.white)

            highlighted = False
            if vs.capture_index == vs.NO_SCROLLBAR:
                if track_rect.contains(curpos):
                    highlighted = True
            elif vs.capture_index == index:
                highlighted = True

            if highlighted and highlighting_allowed:
                painter.setOpacity(0.8)
            else:
                painter.setOpacity(0.5)

            # вычисление высоты ползунка с учётом того, что она не должна быть меньше заданного минимума
            viewframe_fac = viewframe_height/content_height
            thumb_height = max(self.SCROLL_THUMB_MIN_HEIGHT, track_rect.height()*viewframe_fac)

            #abs здесь оттого, что content_offset задаётся отрицательным занчением
            thumb_y_factor = abs(content_offset)/(content_height-viewframe_height)
            thumb_y = thumb_y_factor*(track_rect.height()-thumb_height)

            thumb_rect = QRectF(track_rect.left(), track_rect.top() + thumb_y, track_rect.width(), thumb_height)

            path = QPainterPath()
            path.addRoundedRect(thumb_rect, 5, 5)
            painter.fillPath(path, Qt.white)

            painter.restore()

            data.visible = True
            data.thumb_rect = thumb_rect
            data.track_rect = track_rect
        else:
            data.visible = False

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
        new_h = (new_w/rect.width())*rect.height()
        r = QRectF(0, 0, new_w, new_h).toRect()
        r.moveCenter(rect.center().toPoint())
        return r

    def draw_viewer_content(self, painter):

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
            _p_ = QPainter()
            _p_.begin(pixmap)
            white_c = QColor(Qt.gray)
            black_c = QColor(Qt.black)

            if True:
                # making it darker for aesthetic
                white_c = white_c.darker(600)

            _p_.fillRect(QRect(0, 0, 40, 40), QBrush(white_c))
            _p_.setPen(Qt.NoPen)
            _p_.setBrush(QBrush(black_c))
            _p_.drawRect(QRect(0, 0, 20, 20))
            _p_.drawRect(QRect(20, 20, 20, 20))
            _p_.end()
            checkerboard_br.setTexture(pixmap)
            painter.setBrush(checkerboard_br)
            painter.save()
            painter.setOpacity(0.5)
            painter.drawRect(im_rect)
            painter.restore()
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

            if not self.viewer_modal:
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

        if not self.viewer_modal:
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
                _speed_msg = _("speed")
                text = f"{_speed_msg} {speed}%"
            elif self.center_label_info_type == self.label_type.FRAME_NUMBER and self.animated:
                frame_num = movie.currentFrameNumber()+1
                frame_count = movie.frameCount()
                _frame_msg = _("frame")
                text = f"{_frame_msg} {frame_num}/{frame_count}"
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
            painter.drawText(rect, Qt.AlignCenter | Qt.AlignBottom, _("viewing history"))
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
        self.show_easeInExpo_monitor = False
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

    def set_clipboard(self, text):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(text, mode=cb.Clipboard)

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

        done = False
        if key == Qt.Key_Right:
            if event.modifiers() & Qt.ControlModifier:
                if self.frameless_mode:
                    self.toggle_monitor('right')
                    done = True
        elif key == Qt.Key_Left:
            if event.modifiers() & Qt.ControlModifier:
                if self.frameless_mode:
                    self.toggle_monitor('left')
                    done = True
        if done:
            return

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
                self.SPT_copy_current_to_clipboard()
            elif check_scancode_for(event, 'C') and event.modifiers() == Qt.ControlModifier and self.spt_tool_activated:
                self.SPT_copy_current_to_clipboard()
            elif key == Qt.Key_F4:
                self.SPT_cycle_toggle_scale_factor_value()

        if key == Qt.Key_Tab:
            self.cycle_change_page()

        if self.is_start_page_active():
            return

        elif self.is_library_page_active():
            if key == Qt.Key_Up:
                LibraryData().choose_previous_folder()
            elif key == Qt.Key_Down:
                LibraryData().choose_next_folder()

        elif self.is_waterfall_page_active():

            if key in [Qt.Key_Enter, Qt.Key_Return] or check_scancode_for(event, 'F'):
                if self.viewer_modal:
                    self.leave_modal_viewer()
                else:
                    self.enter_modal_viewer()

            if self.viewer_modal:
                self.viewer_keyReleaseEvent(event)
            else:
                pass

        elif self.is_board_page_active():

            self.board_keyReleaseEvent(event)

        elif self.is_viewer_page_active():
            if self.viewer_keyReleaseEvent(event):
                pass
            elif key == Qt.Key_Right:
                if event.modifiers() & Qt.AltModifier:
                    LibraryData().show_viewed_image_next()
                elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                    LibraryData().show_next_image()
            elif key == Qt.Key_Left:
                if event.modifiers() & Qt.AltModifier:
                    LibraryData().show_viewed_image_prev()
                elif event.modifiers() in [Qt.NoModifier, Qt.KeypadModifier]:
                    LibraryData().show_previous_image()

        self.update()

    def viewer_keyReleaseEvent(self, event):
        res = True
        key = event.key()
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
                else:
                    res = False
        return res

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

        elif key == Qt.Key_5 and not self.active_element:
            self.change_page(self.pages.WATERFALL_PAGE)

        elif check_scancode_for(event, ("W", "S", "A", "D")) and not ctrl_mod and not self.board_TextElementIsActiveElement():
            length = 1.0
            if event.modifiers() & Qt.ShiftModifier:
                length *= 100.0
                if event.modifiers() & Qt.AltModifier:
                    length /= 5.0
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

        elif self.is_waterfall_page_active():
            if self.viewer_modal:
                if key == Qt.Key_Space:
                    self.toggle_animation_playback()
                elif check_scancode_for(event, "I"):
                    self.invert_image = not self.invert_image
                elif check_scancode_for(event, "R"):
                    self.start_inframed_image_saving(event)
                elif check_scancode_for(event, "M"):
                    self.mirror_current_image(ctrl_mod)
            else:
                if check_scancode_for(event, "U"):
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
            self.show_center_label(_("Abort!\nAnimation effects disabled in settings"), error=True)

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
            self.show_center_label(_("Unable to save: no source file or source file is not found"), error=True)
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
                self.show_center_label(_("The folder path is not set or the folder path doesn't exist"), error=True)
        new_path = os.path.abspath(os.path.join(rootpath, f"{formated_datetime}{ext}"))
        if not use_screen_scale:
            factor = 1/self.image_scale
            save_pixmap = save_pixmap.transformed(QTransform().scale(factor, factor), Qt.SmoothTransformation)

        save_pixmap.save(new_path)
        _new_path_msg = _("The image is saved in file")
        self.show_center_label(f"{_new_path_msg}\n{new_path}")

    def set_path_for_saved_pictures(self, init_path):
        msg = _("Choose folder to put images in")
        path = QFileDialog.getExistingDirectory(None, msg, init_path)
        if os.path.exists(path):
            rootpath = str(path)
            SettingsWindow.set_setting_value('inframed_folderpath', rootpath)
            return rootpath
        return None

    def save_image_as(self, format_ext):
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
        if self.animated:
            frame_num = self.movie.currentFrameNumber()+1
            frame_num = f'{frame_num:05}'
            content_filepath = f"{path}_{frame_num}.{format_ext}"
        else:
            content_filepath = f"{path}.{format_ext}"
        filepath = QFileDialog.getSaveFileName(
            None, _("Save file"),
            content_filepath, None
        )
        image.save(filepath[0], format_ext)

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
            label_msg = _("Abort! Feature is not implemented yet for animated images")
            self.show_center_label(label_msg, error=True)

    def paste_from_clipboard(self):
        if self.pixmap:
            new_pixmap = QPixmap.fromImage(QApplication.clipboard().image())
            if not new_pixmap.isNull():
                self.copied_from_clipboard = True
                self.pixmap = new_pixmap
                self.get_rotated_pixmap(force_update=True)
                self.restore_image_transformations()
                self.show_center_label(_("pasted!"))
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

    def debug_populate_data_to_test_library_page(self):
        cf = LibraryData().current_folder()

        paths = []
        app_root = os.path.dirname(__file__)
        test_folderpath = os.path.join(app_root, 'test')

        for cur_dir, dirs, files in os.walk(test_folderpath):
            for filename in files:
                filepath = os.path.join(cur_dir, filename)
                LibraryData().add_image_to_folderdata(filepath, cf)

        for n in range(3):
            cf.images_list.extend(cf.images_list)

        LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)

        for n in range(500):
            LibraryData().create_empty_virtual_folder()
            LibraryData().current_folder().folder_path = f'{n}'

    def contextMenuEvent(self, event):

        if not self.context_menu_allowed:
            return

        contextMenu = QMenu()
        contextMenu.setStyleSheet(self.context_menu_stylesheet)

        self.contextMenuActivated = True

        self.context_menu_exec_point = self.mapped_cursor_pos()

        minimize_window = contextMenu.addAction(_("Minimize"))
        minimize_window.triggered.connect(Globals.main_window.showMinimized)
        contextMenu.addSeparator()

        def toggle_boolean_var_generic(obj, attr_name):
            setattr(obj, attr_name, not getattr(obj, attr_name))
            self.update()

        self.toggle_boolean_var_generic = toggle_boolean_var_generic

        checkboxes = [
            (_("DEBUG"), Globals.DEBUG, partial(toggle_boolean_var_generic, Globals, 'DEBUG'))
            , (_("Show FPS"), self.show_fps_indicator, partial(toggle_boolean_var_generic, self, 'show_fps_indicator'))
            , (_("Antialiasing and pixmap smoothing"), Globals.ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM, partial(toggle_boolean_var_generic, Globals, 'ANTIALIASING_AND_SMOOTH_PIXMAP_TRANSFORM'))
            , (_("Use pixmap-proxy for text items"), Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS, partial(toggle_boolean_var_generic, Globals, 'USE_PIXMAP_PROXY_FOR_TEXT_ITEMS'))
        ]

        if self.is_waterfall_page_active():
            checkboxes.append(
                        (_("Rounded previews"), self.rounded_previews, partial(toggle_boolean_var_generic, self, 'rounded_previews'))
            )


        if Globals.CRASH_SIMULATOR:
            crash_simulator = contextMenu.addAction(_("Make program crash intentionally (for dev purposes only)..."))
            crash_simulator.triggered.connect(lambda: 1/0)

        if Globals.DEBUG or True:
            debug_populate_data_to_test_library_page = contextMenu.addAction('Create virtual folder list')
            debug_populate_data_to_test_library_page.triggered.connect(self.debug_populate_data_to_test_library_page)
            contextMenu.addSeparator()

        open_settings = contextMenu.addAction(_("Settings..."))
        open_settings.triggered.connect(self.open_settings_window)
        contextMenu.addSeparator()

        if self.frameless_mode:
            text = _("Enable window mode")
        else:
            text = _("Enable full-screen mode")
        toggle_frame_mode = contextMenu.addAction(text)
        toggle_frame_mode.triggered.connect(self.toggle_window_frame)
        if self.frameless_mode:
            if self.two_monitors_wide:
                text = _("Narrow window back to monitor frame")
            else:
                text = _("Expand window to two monitors frame")
            toggle_two_monitors_wide = contextMenu.addAction(text)

        if Globals.lite_mode:
            contextMenu.addSeparator()
            rerun_in_extended_mode = contextMenu.addAction(_("Restart app in standard mode"))
            rerun_in_extended_mode.triggered.connect(partial(do_rerun_in_default_mode, False))
        else:
            contextMenu.addSeparator()
            rerun_extended_mode = contextMenu.addAction(_("Restart app (to purge unused data in memory)"))
            rerun_extended_mode.triggered.connect(partial(do_rerun_in_default_mode, self.is_library_page_active()))

        open_in_sep_app = contextMenu.addAction(_("Open in separate app instance"))
        open_in_sep_app.triggered.connect(partial(open_in_separated_app_copy, LibraryData().current_folder()))

        if self.is_library_page_active():
            folder_data = None
            if self.folders_list:
                for item_rect, item_data in self.folders_list:
                    if item_rect.contains(event.pos()):
                        folder_data = item_data
            if folder_data and not folder_data.virtual:
                _action_title = _("Open the folder in separate app instance")
                action_title = f"{_action_title} \"{folder_data.folder_path}\""
                open_separated = contextMenu.addAction(action_title)
                open_separated.triggered.connect(partial(open_in_separated_app_copy, folder_data))
                toggle_two_monitors_wide = None
                if self.frameless_mode:
                    if self.two_monitors_wide:
                        text = _("Narrow window back to monitor frame")
                    else:
                        text = _("Expand window to two monitors frame")
                    toggle_two_monitors_wide = contextMenu.addAction(text)
                    toggle_two_monitors_wide.triggered.connect(self.do_toggle_two_monitors_wide)

        elif self.is_board_page_active():

            self.board_contextMenu(event, contextMenu, checkboxes)

        elif self.is_viewer_page_active():

            if self.image_data and not self.image_data.is_supported_filetype:
                open_unsupported_file = contextMenu.addAction(_("Open unsupported file..."))
                open_unsupported_file.triggered.connect(self.open_unsupported_file)

            contextMenu.addSeparator()

            if not Globals.lite_mode:
                sel_comment = self.get_selected_comment(event.pos())
                if sel_comment:
                    _action_text = _("Edit comment text")
                    action_text = f'{_action_text} "{sel_comment.get_title()}"'
                    change_comment_text = contextMenu.addAction(action_text)
                    change_comment_text.triggered.connect(partial(self.change_comment_text_menuitem, sel_comment))

                    _action_text = _("Redefine comment borders")
                    action_text = f'{_action_text} "{sel_comment.get_title()}"'
                    change_comment_borders = contextMenu.addAction(action_text)
                    change_comment_borders.triggered.connect(partial(self.change_comment_borders_menuitem, sel_comment))

                    _action_text = _("Delete comment")
                    action_text = f'{_action_text} "{sel_comment.get_title()}"'
                    delete_comment = contextMenu.addAction(action_text)
                    delete_comment.triggered.connect(partial(self.delete_comment_menuitem, sel_comment))

                    contextMenu.addSeparator()

                ci = LibraryData().current_folder().current_image()
                if ci.image_metadata:
                    copy_image_metadata = contextMenu.addAction(_("Copy metadata to clipboard"))
                    copy_image_metadata.triggered.connect(partial(QApplication.clipboard().setText, ci.image_metadata_info))


            contextMenu.addSeparator()

            if not self.error:
                show_in_explorer = contextMenu.addAction(_("Find on disk"))
                show_in_explorer.triggered.connect(Globals.control_panel.show_in_folder)
                show_in_gchrome = contextMenu.addAction(_("Open in Google Chrome"))
                show_in_gchrome.triggered.connect(self.show_in_gchrome_menuitem)
                place_at_center = contextMenu.addAction(_("Place image in window center"))
                place_at_center.triggered.connect(self.place_at_center_menuitem)

            contextMenu.addSeparator()

            if self.svg_rendered:
                text = _("Change SVG rasterization resolution...")
                change_svg_scale = contextMenu.addAction(text)
                change_svg_scale.triggered.connect(self.contextMenuChangeSVGScale)
                contextMenu.addSeparator()

            if not self.error:
                save_as_png = contextMenu.addAction(_("Save .png file..."))
                save_as_png.triggered.connect(partial(self.save_image_as, 'png'))

                save_as_jpg = contextMenu.addAction(_("Save .jpg file..."))
                save_as_jpg.triggered.connect(partial(self.save_image_as, 'jpg'))

                copy_to_cp = contextMenu.addAction(_("Copy to clipboard"))
                copy_to_cp.triggered.connect(self.copy_to_clipboard)

                copy_from_cp = contextMenu.addAction(_("Paste from clipboard"))
                copy_from_cp.triggered.connect(self.paste_from_clipboard)

                if LibraryData().current_folder().is_fav_folder():
                    contextMenu.addSeparator()
                    action_title = _("Switch from fovorites folder to actual image folder")
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
            _msg = _("Now redefine comment borders by pressing Ctrl+Shift+LMB")
            self.show_center_label(_msg)

    def open_unsupported_file(self):
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

    def autoscroll_init(self):
        self._autoscroll_timer = QTimer()
        self._autoscroll_timer.setInterval(10)
        self._autoscroll_timer.timeout.connect(self.autoscroll_timer)
        self._autoscroll_inside_activation_zone = False

        self._autoscroll_desactivation_pass = False

    def autoscroll_set_current_page_indicator(self):
        self._autoscroll_draw_vertical = False
        self._autoscroll_draw_horizontal = False
        if self.is_board_page_active():
            self._autoscroll_draw_vertical = True
            self._autoscroll_draw_horizontal = True
        elif self.is_library_page_active():
            self._autoscroll_draw_vertical = True
        elif self.is_waterfall_page_active():
            self._autoscroll_draw_vertical = True

    def autoscroll_is_scrollbar_available(self):
        vs = self.vertical_scrollbars
        if self.is_library_page_active():
            if self.library_page_is_inside_left_part():
                # если видно скроллбар, значит есть что прокручивать!
                if vs.data[vs.LIBRARY_PAGE_FOLDERS_LIST].visible:
                    return vs.LIBRARY_PAGE_FOLDERS_LIST
            else:
                if vs.data[vs.LIBRARY_PAGE_PREVIEWS_LIST].visible:
                    return vs.LIBRARY_PAGE_PREVIEWS_LIST
        elif self.is_waterfall_page_active():
            # по идее, не важно - левый или правый, но пусть будет левый
            if vs.data[vs.WATERFALL_PAGE_LEFT].visible:
                return vs.WATERFALL_PAGE_LEFT
        return vs.NO_SCROLLBAR

    def autoscroll_timer(self):
        OUTER_ZONE_ACTIVATION_RADIUS = 30.0
        cursor_offset = self.mapped_cursor_pos() - self._autoscroll_startpos
        diff_l = QVector2D(cursor_offset).length()
        self._autoscroll_inside_activation_zone = diff_l < OUTER_ZONE_ACTIVATION_RADIUS
        if not self._autoscroll_inside_activation_zone:
            # fixing velocity, because it should be 0.0 at the radius border, not greater than 0.0
            diff_l = max(0.0, diff_l - OUTER_ZONE_ACTIVATION_RADIUS)
            vec = QVector2D(cursor_offset).normalized()*diff_l
            velocity_vec = vec.toPointF()
            if self.is_board_page_active():
                self.canvas_origin -= velocity_vec/25.0
                self.update_selection_bouding_box()
            elif self.is_library_page_active() or self.is_waterfall_page_active():
                vs = self.vertical_scrollbars
                sb_index = self.autoscroll_is_scrollbar_available()
                if sb_index == vs.NO_SCROLLBAR:
                    self.autoscroll_finish()
                else:
                    self.autoscroll_do_for_LibraryWaterfall_pages(velocity_vec.y()/8.0)
        self.update()

    def autoscroll_intro_for_LibraryWaterfall_pages(self, scrollbar_index):
        vs = self.vertical_scrollbars
        sb_data = vs.data[scrollbar_index]
        vs.capture_index = scrollbar_index
        vs.captured_thumb_rect_at_start = QRectF(sb_data.thumb_rect)
        if scrollbar_index == vs.LIBRARY_PAGE_FOLDERS_LIST:
            vs.captured_scroll_offset = LibraryData().folderslist_scroll_offset
        elif scrollbar_index == vs.LIBRARY_PAGE_PREVIEWS_LIST:
            cf = LibraryData().current_folder()
            vs.captured_scroll_offset = cf.library_previews_scroll_offset

    def autoscroll_do_for_LibraryWaterfall_pages(self, velocity_y):
        vs = self.vertical_scrollbars
        index = vs.capture_index
        LIBRARY_VIEWFRAME_HEIGHT = self.library_page_viewframe_height()
        WATERFALL_VIEWFRAME_HEIGHT = self.waterfall_page_viewframe_height()
        if index != vs.NO_SCROLLBAR:
            sb_data = vs.data[index]

            if index == vs.LIBRARY_PAGE_FOLDERS_LIST:
                LibraryData().folderslist_scroll_offset -= velocity_y
                content_height = self.library_page_folders_content_height()
                LibraryData().folderslist_scroll_offset = self.apply_scroll_and_limits(
                                                            LibraryData().folderslist_scroll_offset,
                                                            0,
                                                            content_height,
                                                            LIBRARY_VIEWFRAME_HEIGHT,
                                                        )

            elif index == vs.LIBRARY_PAGE_PREVIEWS_LIST:
                cf = LibraryData().current_folder()
                cf.library_previews_scroll_offset -= velocity_y
                content_height = self.library_page_previews_columns_content_height(cf)
                cf.library_previews_scroll_offset = self.apply_scroll_and_limits(
                                                            cf.library_previews_scroll_offset,
                                                            0,
                                                            content_height,
                                                            LIBRARY_VIEWFRAME_HEIGHT,
                                                        )


            elif index in [vs.WATERFALL_PAGE_LEFT, vs.WATERFALL_PAGE_RIGHT]:
                cf = LibraryData().current_folder()
                cf.waterfall_previews_scroll_offset -= velocity_y
                content_height = self.waterfall_page_previews_columns_content_height(cf)
                cf.waterfall_previews_scroll_offset = self.apply_scroll_and_limits(
                                                            cf.waterfall_previews_scroll_offset,
                                                            0,
                                                            content_height,
                                                            WATERFALL_VIEWFRAME_HEIGHT,
                                                        )

            self.update()

    def autoscroll_outro_for_LibraryWaterfall_pages(self):
        vs = self.vertical_scrollbars
        vs.capture_index = vs.NO_SCROLLBAR

    def autoscroll_start(self):
        self._autoscroll_inside_activation_zone = False
        self.autoscroll_set_current_page_indicator()
        if self.is_library_page_active() or self.is_waterfall_page_active():
            sb_index = self.autoscroll_is_scrollbar_available()
            if sb_index != self.vertical_scrollbars.NO_SCROLLBAR:
                self.autoscroll_intro_for_LibraryWaterfall_pages(sb_index)
                self._autoscroll_timer.start()
        else:
            self._autoscroll_timer.start()

    def autoscroll_finish(self):
        if self.is_library_page_active() or self.is_waterfall_page_active():
            self.autoscroll_outro_for_LibraryWaterfall_pages()
        self._autoscroll_timer.stop()

    def autoscroll_middleMousePressEvent(self, event):
        self._autoscroll_is_moved_while_middle_button_pressed = False
        if self._autoscroll_timer.isActive():
            self._autoscroll_desactivation_pass = True
            self.autoscroll_finish()
        else:
            self._autoscroll_desactivation_pass = False
            self._autoscroll_startpos = event.pos()

    def autoscroll_middleMouseMoveEvent(self):
        self._autoscroll_is_moved_while_middle_button_pressed = True

    def autoscroll_middleMouseReleaseEvent(self):
        if self.is_board_page_active():
            if not self._autoscroll_desactivation_pass:
                if not self._autoscroll_is_moved_while_middle_button_pressed:
                    self.autoscroll_start()
        elif self.is_library_page_active() or self.is_waterfall_page_active():
            if not self._autoscroll_desactivation_pass:
                self.autoscroll_start()
        self._autoscroll_is_moved_while_middle_button_pressed = False

    def autoscroll_draw(self, painter):
        if self._autoscroll_timer.isActive():
            if self._autoscroll_inside_activation_zone:
                painter.save()

                painter.setOpacity(0.7)
                gray = QColor(100, 100, 100)
                painter.setPen(gray)
                painter.setBrush(QBrush(Qt.white))
                el_rect = QRectF(0, 0, 6, 6)
                el_rect.moveCenter(self._autoscroll_startpos)
                painter.drawEllipse(el_rect)

                o = self._autoscroll_startpos
                if int(time.time()*4) % 2 == 0:
                    f = 18
                else:
                    f = 32

                points = [
                    QPointF(0, f),
                    QPointF(-7, f-10),
                    QPointF(7, f-10),
                ]

                if self._autoscroll_draw_vertical:
                    painter.drawPolygon([p + o for p in points])
                    painter.drawPolygon([QPointF(p.x(), -p.y()) + o for p in points])
                if self._autoscroll_draw_horizontal:
                    painter.drawPolygon([QPointF(p.y(), p.x()) + o for p in points])
                    painter.drawPolygon([QPointF(-p.y(), p.x()) + o for p in points])

                painter.setBrush(Qt.NoBrush)

                painter.setPen(QPen(gray, 2))
                el_rect = QRectF(0, 0, 39, 39)
                el_rect.moveCenter(self._autoscroll_startpos)
                painter.drawEllipse(el_rect)

                painter.setPen(QPen(Qt.white, 1))
                el_rect = QRectF(0, 0, 38, 38)
                el_rect.moveCenter(self._autoscroll_startpos)
                painter.drawEllipse(el_rect)

                painter.restore()



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
                        _("Question"),
                        _("No running app instance at the moment.\nStart app in lite mode?"),
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
        path = str(QFileDialog.getExistingDirectory(None, _("Choose folder with pictures in it")))
        if not path and exit:
            QMessageBox.critical(None, _("Error-error"), _("Nothing to show, exit..."))
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
            msg = _("Memory allocated")
            memory_status = f'{msg} ~{mb_size:0.2f} MB'
            memory = menu.addAction(memory_status)
            menu.addSeparator()
            quit = menu.addAction('Quit')
            action = menu.exec_(QCursor().pos())
            if action == quit:
                app = QApplication.instance()
                app.quit()
            elif action == memory:
                msg = _("Purge unused objects")
                QMessageBox.critical(None, "Not implemented", msg)
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
        crash_log.write(sys.version)
        crash_log.write("\n\n")
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
        msg = _("Neither the image nor the folder it is in don't exist")
        QMessageBox.critical(None, "Отмена!", msg)

def get_predefined_path_if_started_from_sublimeText():
    path = ""
    if not Globals.SUPER_LITE:
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

    if not Globals.SUPER_LITE:
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

    if viewer_dll is None:
        Globals.explorer_paths = []
    else:
        Globals.explorer_paths = viewer_dll.getFileListFromExplorerWindow(fullpaths=True)

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

    if Globals.SUPER_LITE:
        # нужно здесь для того, чтобы не тратить время на долгий вызов server_or_client_via_sockets
        # (ведь сокет секунду ждёт ответа, чтобы понять что делать дальше)
        Globals.lite_mode = True

    if Globals.lite_mode:
        app_icon = QIcon()
        path_icon = os.path.join(os.path.dirname(__file__), "image_viewer_lite.ico")
        app_icon.addFile(path_icon)
        app.setWindowIcon(app_icon)
        app.setQuitOnLastWindowClosed(True)

    if Globals.aftercrash:
        filepath = get_crashlog_filepath()
        crashfileinfo = _("Crash info save to file\n\t{0}").format(filepath)
        msg = _("Application crash!\n{0}\n\nRestart app?").format(crashfileinfo)
        ret = QMessageBox.question(None, _('Fatal Error!'), msg, QMessageBox.Yes | QMessageBox.No)
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

    # создание панели управления
    ControlPanel.globals = Globals
    ControlPanel.LibraryData = LibraryData
    ControlPanel.SettingsWindow = SettingsWindow
    # CP = MW.recreate_control_panel()

    legacy_viewer_page_branch = True
    # Нужно для того, чтобы иконка показалась в таскбаре.
    # И нужно это делать до того как будет показана панель управления.
    if not os.path.exists(path):
        # если путь не задан, то по дефолту
        # будет отображена стартовая страница

        if args.board:
            LibraryData().create_empty_virtual_folder()
            # тут хороший приём применён:
            # сначала выставляем колбэки, чтобы отрисовка была соответствующая,
            # а потом уже меняем полностью через change_page
            MW.change_page_at_appstart(MW.pages.BOARD_PAGE)
            # processAppEvents() # TODO: (6 фев 26) вызов этой темы вызывает мерцание, поэтому отключил пока
            MW.change_page(MW.pages.BOARD_PAGE, init_force=True)
            if path.lower().endswith('.board'):
                MW.board_loadBoard(path)
            elif path.lower().endswith('.py'):
                MW.board_loadPluginBoard(path)
            else:
                raise Exception(f'Unable to handle board argument {path}')
            legacy_viewer_page_branch = False

    else:
        waterfall_page_needed = SettingsWindow.get_setting_value("open_app_on_waterfall_page")
        if waterfall_page_needed:
            MW.change_page_at_appstart(MW.pages.WATERFALL_PAGE)

        else:
            MW.change_page_at_appstart(MW.pages.VIEWER_PAGE)

        MW.update()

    processAppEvents()

    # обработка входящих данных
    if legacy_viewer_page_branch:
        if path:
            LibraryData().handle_input_data(path, check_windows_explorer_window=True)
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
