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

import math
import time
import urllib.request
import functools
import importlib
import http
import datetime
from functools import partial
from contextlib import contextmanager
from collections import defaultdict
from _utils import *
import hidapi_adapter
from board_note_item import BoardTextEditItemMixin
from board_align_distribution_ui import (TOOLWINDOW_BUTTONSIDS, ToolActions, ToolWindow, AlignType)

import cbor2

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

COPY_SELECTED_BOARD_ITEMS_STR = '~#~KRUMASSAN:IMAGE:VIEWER:COPY:SELECTED:BOARD:ITEMS~#~'


"""
(6 мар 26) TODO: решение через декораторы,
        но хотелось бы решение через метаклассы,
        только нужно, чтобы метакласс влиял только на миксин,
        и не влиял на всё, во что он миксуется

    def _BOARD(func):
        def simple_wrapper(*args):
            return func(args[0].board, *args)
        return simple_wrapper

    class BoardMixin():

        def __init__(self):
            super().__init__()
            self.board = type('board_object', (), {})
            self.board.m = "[board_object_attr_value]"

        @_BOARD
        def method(BOARD, self, arg):
            print(self, BOARD.m, arg)

    nd = BoardMixin()
    nd.method('[function arg]')



- (10 мар 26) Решение через метаклассы
        Вживлять его пока не буду, потому что это
        добавляет вызов враппера при вызове метода
        и непонятно как это отразится на FPS

import types
from functools import partial

class MetaBase(type):
    def __new__(mcl, name, bases, namespace):

        if namespace.get('_meta_add_BOARD', False):
            for attr_name, attr_value in namespace.items():
                if callable(attr_value) and not attr_name.startswith("__"):
                    print('modification', attr_value, 'for', name)
                    def make_wrapper(func):
                        def wrapper(self, *args, **kwargs):
                            return func(self.BOARD, self, *args, **kwargs)
                        return wrapper
                    namespace[attr_name] = make_wrapper(attr_value)

        return super(MetaBase, mcl).__new__(mcl, name, bases, namespace)

class AnotherMixin(metaclass=MetaBase):

    _meta_add_BOARD = True

    def board_mixin_method(BOARD, self):
        print('board_mixin_method')

class TestMixin(
        AnotherMixin,
        metaclass=MetaBase
    ):

    _meta_add_BOARD = True

    def __init__(self):
        super().__init__()

        self.BOARD = type('BOARD', (), {})

    def board_method(BOARD, self, arg):
        print('board_method', BOARD, self, arg)
        self.board_method1(arg + ' !!!!!!!!')

    def board_method1(BOARD, self, arg):
        print('second method1', arg)
        self.viewer_method()

class MainClass(TestMixin):

    def app_main(self):
        print('app_main', self)


    def viewer_method(self):
        print('viewer_method')

main = MainClass()
main.app_main()

try:
    main.board_method('arg')
except:
    print('wanted fail')

try:
    main.board_method(None, 'arg')
except:
    print('unwanted fail')
# print(main)

main.board_mixin_method()


"""



@contextmanager
def show_longtime_process_ongoing(board_window, text):
    # inside __enter__
    # print("Enter")
    board_window.board_long_loading_begin(text)
    try:
        yield
    finally:
        # insdie __exit__
        # print("Exit")
        board_window.board_long_loading_end()

class BoardLibraryDataMixin():

    def get_boards_data_root(self):
        rootpath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.BOARDS_ROOT)
        create_pathsubfolders_if_not_exist(rootpath)
        return rootpath

    def load_boards(self):
        if os.path.exists(self.get_boards_data_root()):
            print("loading boards data")

    def load_paths_for_forced_board_vertical_layout(self):
        data_filepath = os.path.join(self.get_boards_data_root(), 'forced_vertical_layout_paths.data.txt')
        if os.path.exists(data_filepath):
            paths = []
            with open(data_filepath, 'r', encoding="utf8") as file:
                paths = file.read().split("\n")
            self.vertical_layout_paths = tuple(os.path.normpath(p) for p in paths if os.path.exists(p))

class BoardItem():

    FRAME_PADDING = 40.0
    NODE_SIZE = 40.0
    LINK_ACTIVATION_DIST = 20.0

    class types():
        ITEM_UNDEFINED = 0
        ITEM_IMAGE = 1
        ITEM_AV = 2
        ITEM_FOLDER = 3
        ITEM_GROUP = 4
        ITEM_NODE = 5
        ITEM_LINK = 6
        ITEM_FRAME = 7
        ITEM_NOTE = 8
        ITEM_EDITING_TABLE = 9

    def __init__(self, item_type, visible=True):
        super().__init__()
        self.type = item_type

        self.pixmap = None
        self.animated = False
        self.audiovideo_file = False
        self.audio = False
        self.video = False

        self.visible = visible

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.position = QPointF()
        self.rotation = 0

        self._scale_x = None
        self._scale_y = None
        self._position = None
        self._rotation = None

        self._scale_x_init = None
        self._scale_y_init = None
        self._position_init = None

        self.board_index = 0
        self.board_group_index = None

        self.width = 1000
        self.height = 1000

        self.from_item = None
        self.to_item = None
        self.link_width = 2
        self.is_directional = True
        self._node_ui_rect = None
        self._is_curved_link = False
        self._snapshot = None

        self.image_source_url = None

        self.label = ""
        self.status = ''

        self._tags = []
        self._comments = []

        self._selected = False
        self._touched = False
        self._show_file_info_overlay = False
        self._marked_item = False

        self._label_ui_rect = None

        self.force_full_quality = False
        self.scrubbed = False

        self.animated_file = False

        self.countdown_red_frame = 0

    def set_alert(self):
        self.countdown_red_frame = 10

    def set_tags(self, tags):
        self._tags = tags

    def visible_in_viewport(self, canvas, a, b):
        # TODO: это надо оптимизировать будет, это не ок
        viewport_rect = canvas.rect()
        sides = [
            QLineF(viewport_rect.topLeft(), viewport_rect.topRight()),
            QLineF(viewport_rect.topRight(), viewport_rect.bottomRight()),
            QLineF(viewport_rect.bottomRight(), viewport_rect.bottomLeft()),
            QLineF(viewport_rect.bottomLeft(), viewport_rect.topLeft())
        ]
        line = QLineF(a, b)
        for side in sides:
            result, point = line.intersects(side)
            if result == QLineF.BoundedIntersection:
                return True
        else:
            if viewport_rect.contains(a.toPoint()) or viewport_rect.contains(b.toPoint()):
                return True
            return False

    def is_near_link(self, canvas, pos):
        a = self.from_item.calculate_viewport_position(canvas=canvas)
        b = self.to_item.calculate_viewport_position(canvas=canvas)
        if not self.visible_in_viewport(canvas, a, b):
            return False
        if self._is_curved_link:
            poly = canvas.board_util_path_to_polygone(self._path)
            for a, b in zip(poly, poly[1:]):
                if self.segment_dist(a, b, pos, self.LINK_ACTIVATION_DIST):
                    return True
            return False

        else:
            return self.segment_dist(a, b,
                pos,
                self.LINK_ACTIVATION_DIST
            )

    @staticmethod
    def segment_dist(a, b, pos, dist_threshold):

        def dot(vec1, vec2):
            return vec1.x()*vec2.x() + vec1.y()*vec2.y()

        def get_projection(p, v1, v2):
            seg = v2-v1
            len_squared = dot(seg, seg)
            factor = dot(p-v1, v2-v1)/len_squared
            projection = v1 + factor * (v2 - v1)
            return projection, factor

        seg = b-a
        if dot(seg, seg) == 0.0:
            return False

        m, factor = get_projection(pos, a, b)
        dist = QVector2D(m-pos).length()

        if 0.0 < factor < 1.0 and dist < dist_threshold:
            return True
        else:
            return False

    def calc_local_data(self):
        if self.type in [self.types.ITEM_NOTE]:
            self.calc_local_data_default()
        else:
            raise Exception('calc_local_data', self.type)

    def calc_local_data_default(self):
        self.position = (self.start_point + self.end_point)/2.0
        self.local_start_point = self.start_point - self.position
        self.local_end_point = self.end_point - self.position
        diff = self.local_start_point - self.local_end_point
        self.width = abs(diff.x())
        self.height = abs(diff.y())

    @property
    def calc_area(self):
        r = self.get_size_rect(scaled=True)
        return abs(r.width() * r.height())

    def retrieve_file_data(self):
        if self.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_AV]:
            file_data = self.file_data
        elif self.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            file_data = self.item_folder_data.current_image()
        elif self.type == BoardItem.types.ITEM_NODE:
            file_data = self.label
        return file_data

    def make_copy(self, board, folder_data):
        copied_item = BoardItem(self.type)
        attributes = self.__dict__.items()
        for attr_name, attr_value in attributes:
            type_obj = type(attr_value)
            if type_obj is QPointF:
                attr_value = type_obj(attr_value)
            setattr(copied_item, attr_name, attr_value)
        copied_item.board_index = board.retrieve_new_board_item_index()
        folder_data.board.items_list.append(copied_item)
        return copied_item

    def info_text(self):
        if self.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_AV]:
            file_data = self.file_data
            text = f'{file_data.filename}\n{file_data.source_width} x {file_data.source_height}'
            if self.image_source_url is not None:
                text = f'{text}\n{self.image_source_url}'
            return text
        elif self.type == self.types.ITEM_FOLDER:
            path = self.item_folder_data.folder_path
            return _('FOLDER {0}').format(path)
        elif self.type == self.types.ITEM_GROUP:
            return _('GROUP {0} {1}').format(self.board_group_index, self.label)
        elif self.type == self.types.ITEM_FRAME:
            return _('FRAME')
        elif self.type == self.types.ITEM_NOTE:
            return _('TEXT NOTE')

    def calculate_viewport_position(self, canvas, pos=None):
        if pos is None:
            pos = self.position
        return canvas.board_MapToViewport(pos)

    def aspect_ratio(self):
        rect = self.get_size_rect(scaled=False)
        return rect.width()/rect.height()

    def get_size_rect(self, scaled=False):
        if scaled:
            if self.type in [self.types.ITEM_IMAGE, self.types.ITEM_AV]:
                scale_x = self.scale_x
                scale_y = self.scale_y
            elif self.type == self.types.ITEM_FOLDER:
                scale_x = self.scale_x
                scale_y = self.scale_y
            elif self.type == self.types.ITEM_GROUP:
                scale_x = self.scale_x
                scale_y = self.scale_y
            elif self.type == self.types.ITEM_FRAME:
                scale_x = self.scale_x
                scale_y = self.scale_y
            elif self.type == self.types.ITEM_NOTE:
                scale_x = self.scale_x
                scale_y = self.scale_y
            elif self.type == self.types.ITEM_NODE:
                scale_x = self.scale_x
                scale_y = self.scale_y
        else:
            scale_x = 1.0
            scale_y = 1.0
        if self.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_AV]:
            return QRectF(0, 0, self.file_data.source_width*scale_x, self.file_data.source_height*scale_y)
        elif self.type in [self.types.ITEM_FOLDER, self.types.ITEM_GROUP, self.types.ITEM_FRAME, self.types.ITEM_NOTE, self.types.ITEM_NODE]:
            return QRectF(0, 0, self.width*scale_x, self.height*scale_y)

    def get_selection_line(self, canvas=None):
        p1 = self.calculate_viewport_position(canvas=canvas, pos=self.to_item.position)
        p2 = self.calculate_viewport_position(canvas=canvas, pos=self.from_item.position)
        return QPolygonF([p1, p2, p1])

    def get_selection_area(self, canvas=None,
            place_center_at_origin=True,
            apply_global_scale=True,
            apply_translation=True,
            transformation_ongoing=False,
            debug_mw=None):

        size_rect = self.get_size_rect()
        if place_center_at_origin:
            size_rect.moveCenter(QPointF(0, 0))
        points = [
            size_rect.topLeft(),
            size_rect.topRight(),
            size_rect.bottomRight(),
            size_rect.bottomLeft(),
        ]
        polygon = QPolygonF(points)
        transform = self.get_transform_obj(canvas=canvas,
            apply_global_scale=apply_global_scale,
            apply_translation=apply_translation,
            transformation_ongoing=transformation_ongoing,
            debug_mw=debug_mw
        )
        return transform.map(polygon)

    def get_transform_obj(self, canvas=None,
                        apply_local_scale=True,
                        apply_translation=True,
                        apply_global_scale=True,
                        transformation_ongoing=False,
                        debug_mw=None):

        local_scaling = QTransform()
        rotation = QTransform()
        global_scaling = QTransform()
        translation = QTransform()
        if apply_local_scale:
            local_scaling.scale(self.scale_x, self.scale_y)
        if transformation_ongoing:
            rotation.rotate(self._rotation)
        else:
            rotation.rotate(self.rotation)
        if apply_translation:
            _pos = None
            if transformation_ongoing:
                _pos = self._position
                if debug_mw:
                    debug_mw.show_center_label(f'set_old_pos {transformation_ongoing} {_pos}')
            if transformation_ongoing and _pos is not None:
                pos = self.calculate_viewport_position(canvas, pos=_pos)
                translation.translate(pos.x(), pos.y())
            else:
                if apply_global_scale:
                    pos = self.calculate_viewport_position(canvas)
                    translation.translate(pos.x(), pos.y())
                else:
                    translation.translate(self.position.x(), self.position.y())
        if apply_global_scale:
            global_scaling.scale(canvas.canvas_scale_x, canvas.canvas_scale_y)
        transform = local_scaling * rotation * global_scaling * translation
        return transform

    def update_corner_info(self):
        if self.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_AV]:
            current_frame = self.movie.currentFrameNumber()
            frame_count = self.movie.frameCount()
            if frame_count > 0:
                current_frame += 1
            self.status = _('{0}/{1} ANIMATION').format(current_frame, frame_count)
        elif self.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            current_image_num = self.item_folder_data._index
            images_count = len(self.item_folder_data.images_list)
            if images_count > 0:
                current_image_num += 1
            if self.type == BoardItem.types.ITEM_FOLDER:
                item_type = _("FOLDER")
            elif self.type == BoardItem.types.ITEM_GROUP:
                item_type = _("GROUP")
            self.status = f'{current_image_num}/{images_count} {item_type}'

    def enable_distortion_fixer(self):
        if hasattr(self, 'local_end_point'):
            self._saved_data = (
                QPointF(self.local_end_point),
                QPointF(self.local_start_point),
                self.width,
                self.height,
                self.scale_x,
                self.scale_y
            )

            self.local_end_point.setX(self.local_end_point.x() * self.scale_x)
            self.local_end_point.setY(self.local_end_point.y() * self.scale_y)

            self.local_start_point.setX(self.local_start_point.x() * self.scale_x)
            self.local_start_point.setY(self.local_start_point.y() * self.scale_y)

            self.width *= self.scale_x
            self.height *= self.scale_y
            self.scale_x = self.scale_y = 1.0

    def disable_distortion_fixer(self):
        if hasattr(self, '_saved_data'):
            self.local_end_point, \
            self.local_start_point, \
            self.width, \
            self.height, \
            self.scale_x, \
            self.scale_y = self._saved_data

BoardCallbacksNames = [
    'mousePressEvent',
    'mouseMoveEvent',
    'mouseReleaseEvent',
    'mouseDoubleClickEvent',
    'wheelEvent',
    'contextMenu',
    'keyPressEvent',
    'keyReleaseEvent',
    'dragEnterEvent',
    'dragMoveEvent',
    'dropEvent',
    'getBoardFilepath',
    'dumpNonAutoSerialized',
    'loadNonAutoSerialized',
]

class PluginInfo():

    def __init__(self, module, board):
        super().__init__()
        self.name = 'undefined'
        self.filename = 'undefined'
        self.module = module
        self.board = board
        self.add_to_menu = True

        self.preparePluginBoard = None

        self.paintEvent = None

        for name in BoardCallbacksNames:
            setattr(self, name, None)

    def setDefaults(self, name):
        self.filename = name
        self.name = name

    def menu_callback(self):
        board = self.board
        board.board_SetPlugin(self)


class BoardMixin(BoardTextEditItemMixin):

    # для поддержки миксинов
    BoardItem = BoardItem

    def set_default_boardviewport_origin(self):
        self.canvas_origin = QPointF(self.DEFAULT_CANVAS_ORIGIN)
        if self.DEFAULT_CANVAS_SCALE:
            self.canvas_scale_x, self.canvas_scale_y = self.DEFAULT_CANVAS_SCALE
            self.DEFAULT_CANVAS_SCALE = None

    def board_viewport_reset_position_to_item(self):
        cf = self.LibraryData().current_folder()
        items_list = self.get_original_items_order(cf.board.items_list)
        if len(items_list) > 0:
            min_index_item = items_list[0]
            content_pos = QPointF(min_index_item.position.x()*self.canvas_scale_x, min_index_item.position.y()*self.canvas_scale_y)
            viewport_center_pos = self.get_center_position()
            self.canvas_origin = - content_pos + viewport_center_pos
            # self.show_center_label('placed at first item!')
        else:
            self.canvas_origin = self.get_center_position()
            # self.show_center_label('placed at board origin')

    def board_viewport_reset(self, scale=True, position=True, scale_inplace=False, to_item=False):
        if scale:
            self.canvas_scale_x = 1.0
            self.canvas_scale_y = 1.0
        if scale_inplace:
            self.set_default_boardviewport_scale(keep_position=True, center_as_pivot=True)
        if position:
            if to_item:
                self.board_viewport_reset_position_to_item()
            else:
                self.canvas_origin = self.get_center_position()

    def board_init(self):
        self.board_viewport_reset()
        self.board_region_zoom_in_init()
        self.scale_rastr_source = None
        self.rotate_rastr_source = None
        self.load_cursors()
        self.selection_color = QColor(18, 118, 127)

        self.board_camera_translation_ongoing = False
        self.start_translation_pos = None
        self.translation_ongoing = False
        self.rotation_activation_areas = []
        self.rotation_ongoing = False
        self.scaling_ongoing = False
        self.scaling_vector = None
        self.proportional_scaling_vector = None
        self.scaling_pivot_point = None

        self.selection_rect = None
        self.selection_start_point = None
        self.selection_ongoing = False
        self.selected_items = []
        self.selection_box = None
        self.right_click_selection_init()

        self.board_show_minimap = False
        self.images_drawn = 0
        self.pr_viewport = QPointF(0, 0)
        self.fly_pairs = []
        self._canvas_scale_x = 1.0
        self._canvas_scale_y = 1.0
        self.board_selection_transform_box_opacity = 1.0
        self.board_debug_transform_widget = False
        self.context_menu_allowed = True
        self.long_loading = False

        self.DEFAULT_CANVAS_ORIGIN = QPointF(600, 100)
        self.DEFAULT_CANVAS_SCALE = None

        self.transform_cancelled = False

        self.board_item_under_mouse = None
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False

        self.board_bounding_rect = QRectF()

        self.is_board_text_input_event = False
        self._active_element = None

        self.board_TextElementInitModule()

        self.board_plugins = []

        self.active_plugin = None
        self.board_plugins_loaded = False
        if self.STNG.board_load_plugins_at_startup:
            self.board_LoadPlugins()

        self.debug_file_io_filepath = _("[variable self.debug_file_io_filepath is not set!]")

        self.long_process_label_text =  _("request processing")

        self.board_SetCallbacks()

        self.show_longtime_process_ongoing = show_longtime_process_ongoing
        self.board_frame_items_text_rects = []

        self.board_PTWS_init()

        self.show_easeInExpo_monitor = False

        self.expo_values = []

        self._expo_save_timer = None

        self.board_autoscroll_zoom_init()

        self.cursor_scrubbing_optimizer = False

        self.board_item_ctrl_z_data = defaultdict(list)

        self.scroll_items_timestamp = time.time()

        self.progressive_layout_ongoing = False

        ToolWindow.init_AD_toolbox_attrs(self)

        self.rotation_pivot_index = None

        self.board_snapping_init()

        self.item_magazin = []

        self.links_draw_before_items = True

    def board_FindPlugin(self, plugin_filename):
        found_pi = None
        for pi in self.board_plugins:
            if pi.filename == plugin_filename:
                found_pi = pi
                break
        return found_pi

    def board_loadPluginBoard(self, plugin_filename):
        found_pi = self.board_FindPlugin(plugin_filename)
        if found_pi:
            self.board_SetPlugin(found_pi)
        else:
            msg = _("plugin {0} is not found in \\boards_plugins folder!").format(plugin_filename)
            self.show_center_label(msg, error=True)

    def board_SetCallbacks(self, fd=None):
        if fd is None:
            fd = self.LibraryData().current_folder()
        found_pi = None
        if fd is not None:
            plugin_filename = fd.board.plugin_filename
            found_pi = self.board_FindPlugin(plugin_filename)

        for name in BoardCallbacksNames:
            if found_pi is None or getattr(found_pi, name) is None:
                # default callback
                callback = getattr(self.__class__, f'board_{name}Default')
            else:
                # plugin callback
                callback = getattr(found_pi, name)
            setattr(self, f'{name}BoardCallback', partial(callback, self))

        # paint callbacks
        if found_pi is None or found_pi.paintEvent is None:
            paint_callback = self.__class__.board_draw_main_default
        else:
            paint_callback = found_pi.paintEvent
        self.board_draw_mainBoardCallback = partial(paint_callback, self)

    def board_draw_main(self, painter, event):
        self.board_draw_mainBoardCallback(painter, event)

        if self.STNG.show_gamepad_monitor:
            hidapi_adapter.draw_gamepad_monitor(self, painter, event)

        if self.show_easeInExpo_monitor:
            hidapi_adapter.draw_gamepad_easing_monitor(self, painter, event)

    def board_mousePressEvent(self, event):
        self.mousePressEventBoardCallback(event)

    def board_mouseMoveEvent(self, event):
        self.mouseMoveEventBoardCallback(event)

    def board_mouseReleaseEvent(self, event):
        self.mouseReleaseEventBoardCallback(event)

    def board_wheelEvent(self, event):
        self.wheelEventBoardCallback(event)

    def board_contextMenu(self, event, contextMenu, checkboxes):
        self.contextMenuBoardCallback(event, contextMenu, checkboxes)

    def board_keyPressEvent(self, event):
        self.keyPressEventBoardCallback(event)

    def board_keyReleaseEvent(self, event):
        self.keyReleaseEventBoardCallback(event)

    def board_dragEnterEvent(self, event):
        self.dragEnterEventBoardCallback(event)

    def board_dragMoveEvent(self, event):
        self.dragMoveEventBoardCallback(event)

    def board_dropEvent(self, event):
        self.dropEventBoardCallback(event)

    def board_mouseDoubleClickEvent(self, event):
        self.mouseDoubleClickEventBoardCallback(event)

    def board_SetPlugin(self, pi):
        if pi.preparePluginBoard:
            pi.preparePluginBoard(self, pi)
        cf = self.LibraryData().current_folder()
        board = cf.board
        board.plugin_filename = pi.filename
        self.board_SetCallbacks()
        self.show_center_label(_("{0} activated").format(pi.name))
        self.update()

    def board_LoadPlugins(self, from_context_menu=False):
        plugins_folder = os.path.join(os.path.dirname(__file__), 'board_plugins')
        if not os.path.exists(plugins_folder):
            return
        # print(f'init plugins in {plugins_folder}...')
        for cur_dir, dirs, filenames in os.walk(plugins_folder):
            for filename in filenames:
                plugin_filepath = os.path.join(cur_dir, filename)
                if plugin_filepath.lower().endswith('.py'):
                    self.board_LoadPlugin(plugin_filepath)
        # print('end init plugins')
        self.board_plugins_loaded = True
        if from_context_menu:
            menu = self.board_PluginsMenu(None, loading_result=True)
            if menu:
                menu.exec_(QCursor().pos())

    def load_module_and_get_register_function(self, script_filename, full_path):
        spec = importlib.util.spec_from_file_location(script_filename, full_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_func = None
        try:
            plugin_func = getattr(module, "register")
        except AttributeError:
            pass
        return module, plugin_func

    def board_LoadPlugin(self, filepath):
        # print(f'\t{filepath}')
        filename = os.path.basename(filepath)
        module, plugin_reg_func = self.load_module_and_get_register_function(filename, filepath)
        pi = PluginInfo(module, self)
        pi.setDefaults(filename)
        if plugin_reg_func:
            ok = False
            try:
                plugin_reg_func(self, pi)
                ok = True
                # print(f'\tplugin {pi.name} registred!')
            except:
                print(f'\t! failed to load plugin {filename}')
            if ok:
                self.board_plugins.append(pi)

    def board_mouseDoubleClickEventDefault(self, event):
        if event.button() == Qt.LeftButton:
            if self.board_AD_toolbox_doubleClickEvent(event):
                return
            else:
                cf = self.LibraryData().current_folder()
                cursor_pos = self.mapped_cursor_pos()
                for bi in cf.board.items_list:
                    item_selection_area = bi.get_selection_area(canvas=self)
                    is_under_mouse = item_selection_area.containsPoint(cursor_pos, Qt.WindingFill)
                    is_over_text_ui_rect = bi._node_ui_rect and bi._node_ui_rect.contains(cursor_pos)
                    if is_over_text_ui_rect:
                        self.board_change_item_text(bi)
                        break
                    if is_under_mouse:
                        if bi.type == BoardItem.types.ITEM_NOTE:
                            self.board_TextElementActivateEditMode(bi)
                            break
                        elif bi.type == BoardItem.types.ITEM_IMAGE and (event.modifiers() & Qt.ShiftModifier):
                            self.LibraryData().show_that_imd_on_viewer_page(bi.file_data)
                            self.show_center_label(_('You\'re on viewer page now'))
                        elif bi.type == BoardItem.types.ITEM_AV:
                            execute_clickable_text(bi.file_data.filepath)
                        else:
                            self.board_fit_content_on_screen(None, board_item=bi)
                        break
                else:
                    # если цикл дошёл до конца, то есть break не был вызван
                    self.board_invoke_create_node_item(event.pos())

    def board_keyPressEventDefault(self, event):
        key = event.key()

        ctrl_mod = bool(event.modifiers() & Qt.ControlModifier)
        only_shift_mod = bool(event.modifiers() == Qt.ShiftModifier)
        only_ctrl_mode = bool(event.modifiers() == Qt.ControlModifier)

        if self.lineEdit.parent():
            event.setAccepted(True)
            return

        if self.board_TextElementKeyPressEventHandler(event):
            return

        if key == Qt.Key_Space:
            self.board_fly_over(user_call=True)

        elif check_scancode_for(event, Qt.Key_O):
            if only_ctrl_mode:
                self.board_loadBoard()
            elif only_shift_mod:
                self.board_marked_items_filepaths_to_clipboard()
            else:
                self.board_toggle_item_mark()

        elif check_scancode_for(event, Qt.Key_S) and only_ctrl_mode:
            self.board_saveBoard()

        elif check_scancode_for(event, Qt.Key_M):
            self.board_toggle_minimap()

        elif check_scancode_for(event, Qt.Key_I):
            self.board_toggle_item_info_overlay()

        elif check_scancode_for(event, Qt.Key_A) and ctrl_mod:
            self.board_select_all_items()

        elif check_scancode_for(event, Qt.Key_C) and ctrl_mod:
            self.board_control_c()

        elif check_scancode_for(event, Qt.Key_V) and ctrl_mod:
            self.board_control_v()

        elif check_scancode_for(event, Qt.Key_B) and ctrl_mod:
            self.grab().save('grab.png')

        elif key == Qt.Key_Home:
            self.board_viewport_show_first_item()

        elif key == Qt.Key_End:
            self.board_viewport_show_last_item()

        elif key == Qt.Key_PageDown:
            self.board_move_viewport(_next=True)

        elif key == Qt.Key_PageUp:
            self.board_move_viewport(_previous=True)

        elif key in [Qt.Key_Plus]:
            self.board_fit_selected_items_on_screen()

    def board_keyReleaseEventDefault(self, event):
        key = event.key()
        shift_only = event.modifiers() == Qt.ShiftModifier
        shift = event.modifiers() & Qt.ShiftModifier

        if self.lineEdit.parent():
            event.setAccepted(True)
            return

        if key == Qt.Key_Control:
            # for not item selection drag&drop
            self.board_cursor_setter()

        if key in [Qt.Key_Return, Qt.Key_Enter] and (not self.lineEditSkip):
            if self.board_show_minimap:
                self.board_navigate_camera_via_minimap()
            else:
                self.board_dive_inside_board_item()
        elif key in [Qt.Key_Backspace]:
            self.board_dive_inside_board_item(back_to_referer=True)
        elif key in [Qt.Key_Delete]:
            self.board_delete_selected_board_items()
        elif key in [Qt.Key_Asterisk, Qt.Key_Slash, Qt.Key_Minus]:
            self.board_SCALE_selected_items(
                up=key==Qt.Key_Asterisk,
                down=key==Qt.Key_Slash,
                toggle_monitor=key==Qt.Key_Minus)
        elif check_scancode_for(event, (Qt.Key_E, Qt.Key_R)):
            if check_scancode_for(event, Qt.Key_E):
                self.board_do_scale(-1)
            elif check_scancode_for(event, Qt.Key_R):
                self.board_do_scale(1)
        elif check_scancode_for(event, Qt.Key_F):
            self.board_toggle_full_forcing(reset=shift)
        elif check_scancode_for(event, Qt.Key_Z) and event.modifiers() & Qt.ControlModifier:
            self.board_ctrl_z()
        elif check_scancode_for(event, Qt.Key_N):
            self.board_invoke_create_node_item()
        elif check_scancode_for(event, Qt.Key_L):
            if shift_only:
                self.board_toggle_directional_notd_for_links()
            else:
                self.board_toggle_links_direction()
        elif key == Qt.Key_F8:
            self.board_change_links_draw_order()

        self.lineEditSkip = False

    def board_dragEnterEventDefault(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasImage():
            event.accept()
        else:
            event.ignore()

    def board_dragMoveEventDefault(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def board_dropEventDefault(self, event):
        mime_data = event.mimeData()
        if mime_data.hasImage():
            image = QImage(event.mimeData().FileData())
            image.save("data.png")
        elif event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    path = url.path()
                    if path:
                        path = path[1:]
                        if os.path.isdir(path):
                            self.board_add_item_folder(folder_path=path)
                        else:
                            self.show_center_label(_("No files, only folders supported"))
                else:
                    url = url.url()
                    if self.is_board_page_active():
                        self.board_download_file(url)
                        print(url)
            self.update()
        else:
            event.ignore()

    def board_PluginsMenu(self, menu, loading_result=False):
        pis = []
        for pi in self.board_plugins:
            if pi.add_to_menu:
                pis.append(pi)
        if pis:
            if menu is not None:
                plugin_items_menu = menu.addMenu(_('Plugin Boards'))
            else:
                plugin_items_menu = RoundedQMenu()
                plugin_items_menu.setStyleSheet(self.context_menu_stylesheet)
            for pi in pis:
                self.addItemToMenu(plugin_items_menu, pi.name, pi.menu_callback)
        elif loading_result:
            plugin_items_menu = RoundedQMenu()
            self.addItemToMenu(plugin_items_menu, _("No plugins found")).setEnabled(False)
        else:
            plugin_items_menu = None
        return plugin_items_menu

    def board_ContextMenuPluginsDefault(self, event, contextMenu):
        menu = self.board_PluginsMenu(contextMenu)
        if menu:
            pass
        elif not self.board_plugins_loaded:
            self.addItemToMenu(contextMenu, _("Load Plugins..."), partial(self.board_LoadPlugins, from_context_menu=True))
        else:
            self.addItemToMenu(contextMenu, _("No plugins found"), lambda: None).setEnabled(False)

        contextMenu.addSeparator()

    def board_menuActivatedOverFrameItem(self):
        point = self.context_menu_exec_point
        for board_item, label_rect, bounding_rect in self.board_frame_items_text_rects:
            if label_rect.contains(point) or bounding_rect.contains(point):
                return board_item
        return None

    def board_change_frame_item_label(self, frame_item, *args):
        dialog = QInputDialog(self)
        dialog.setInputMode(QInputDialog.TextInput)
        dialog.setTextValue(frame_item.label)
        dialog.setWindowTitle(_('Change frame item label'))
        dialog.setLabelText(_("Label Text:"))
        dialog.resize(500,100)
        ok = dialog.exec_()
        if ok:
            frame_item.label = dialog.textValue()
        self.update()

    def board_contextMenuDefault(self, event, contextMenu, checkboxes, plugin_implant=None):
        def addItem(*args):
            return self.addItemToMenu(contextMenu, *args)

        checkboxes.extend((
            (
                _("Show debug graphics for transformation widget"),
                self.board_debug_transform_widget,
                partial(self.toggle_boolean_var_generic, self, 'board_debug_transform_widget')
            ),
            (
                _("Use pixmap-proxy for text items"),
                self.Globals.USE_PIXMAP_PROXY_FOR_TEXT_ITEMS,
                partial(self.toggle_boolean_var_generic, self.Globals, 'USE_PIXMAP_PROXY_FOR_TEXT_ITEMS')
            ),
            (
                _("Cursor scrubbing optimizer"),
                self.cursor_scrubbing_optimizer,
                partial(self.toggle_boolean_var_generic, self, 'cursor_scrubbing_optimizer')
            ),
            (
                _("Сontrol with a gamepad"),
                hidapi_adapter.is_gamepad_input_ready(self),
                partial(hidapi_adapter.toggle_gamepad_inputs, self)
            ),
            (
                _('Items snapping'),
                self.STNG.board_items_snapping,
                partial(self.toggle_boolean_var_generic, self.STNG, 'board_items_snapping')
            ),
            (
                _('Show point snapping targets'),
                self.SNAPPING.show_point_targets,
                partial(self.toggle_boolean_var_generic, self.SNAPPING, 'show_point_targets')
            ),
        ))
        sep = contextMenu.addSeparator
        sep()

        self.board_ContextMenuPluginsDefault(event, contextMenu)

        if plugin_implant is not None:
            plugin_implant(self, contextMenu)

        submenu = contextMenu.addMenu(_('Actions'))
        self.board_contextSubMenu(submenu)

        sep()

        addItem(_("Go to the link in the note (Explorer or Browser)"), partial(self.board_go_to_note, event))

        addItem(_("Open in viewer in separated app copy running in lite mode"), self.board_open_in_app_copy)

        addItem(_("Open in Google Chrome"), self.board_open_in_google_chrome)

        sep()

    def board_contextSubMenu(self, menu):

        sep = menu.addSeparator
        menu.setStyleSheet(self.context_menu_stylesheet)
        menu.setAttribute(Qt.WA_TranslucentBackground, True)

        def addItem(*args):
            return self.addItemToMenu(menu, *args)

        addItem(_('Place items in column/row'), self.board_place_items_in_column_or_row)

        addItem(_('Align && Distribute...'), self.board_show_AD_toolbox)

        addItem(_('Multifolder board...'), self.board_prepare_multifolder_board)


        addItem(_("Folder..."), self.board_add_item_folder)

        text = _("Group")
        sel_count = self.board_selected_items_count()
        if sel_count > 0:
            text = _("{0} (add selected items to it: {1})").format(text, sel_count)
        addItem(text, self.board_add_item_group_noargs)

        addItem(_("Frame"), self.board_add_item_frame)

        addItem(_("Note"), self.board_add_item_note)


        addItem(_("Force highres loading of all items right now (may take some time)"), self.board_load_highres)

        addItem(_("Reset item(s) to layout position, scale, rotation"), self.board_reset_items_to_layout_transforms)

        frame_item = self.board_menuActivatedOverFrameItem()
        if frame_item:
            addItem(_('Change frame title \'{0}\'').format(frame_item.label), partial(self.board_change_frame_item_label, frame_item))

        if bool(self.is_context_menu_executed_over_group_item()):
            addItem(_('Take current image from group and place nearby'), self.board_retrieve_current_from_group_item)

    def board_CreatePluginVirtualFolder(self, plugin_name):
        fd = self.LibraryData().create_folder_data(
            _("{0} Virtual Folder").format(plugin_name),
            [], image_filepath=None, make_current=False, virtual=True)
        fd.board.ready = True
        return fd

    def board_loadBoard(self, path=None):
        with self.show_longtime_process_ongoing(self, _("Board loading")):
            self.board_loadBoardDefault(path)

    def board_saveBoard(self):
        with self.show_longtime_process_ongoing(self, _("Board saving")):
            self.board_saveBoardDefault()

    def dialog_open_boardfile(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.ExistingFile)
        title = ""
        filter_data = _("Board File (*.board)")
        folder_path = self.Settings.get("inframed_folderpath")
        if not os.path.exists(folder_path):
            folder_path = self.set_path_for_saved_pictures(folder_path)
        data = dialog.getOpenFileName(self, title, folder_path, filter_data)
        return data[0]

    def board_loadBoardDefault(self, path=None):
        if path is not None:
            board_filepath = path
        else:
            if self.Globals.DEBUG:
                board_filepath = self.debug_file_io_filepath

            if not os.path.exists(board_filepath):
                board_filepath = ""
                board_filepath = self.dialog_open_boardfile()

        is_file_exists = os.path.exists(board_filepath)
        is_file_extension_ok = board_filepath.lower().endswith(".board")
        is_file = os.path.isfile(board_filepath)
        if not (is_file_exists and is_file_extension_ok and is_file):
            msg = _("Error: either the file does not exist or the extension is wrong.\nAbort!\n{0}").format(board_filepath)
            self.show_center_label(msg, error=True)
            return

        project_format = ''
        try:
            # пытаемся читать как cbor2
            read_data = ""
            with open(board_filepath, "rb") as file:
                read_data = file.read()
            data = cbor2.loads(read_data)
            project_format = 'cbor2'
        except:
            try:
                # пытаемся читать как json
                read_data = ""
                with open(board_filepath, "r", encoding="utf8") as file:
                    read_data = file.read()
                data = json.loads(read_data)
                project_format = 'json'
            except:
                self.show_center_label(_("Reading error: neither cbor2 nor json could be read. Abort!"), error=True)
                return

        main_board_dict = data['main_board']
        self.board_recreate_board_from_serial(main_board_dict, main_board=True, board_load_filepath=board_filepath)

        msg = _("Board has been loaded from file {0} of format {1}").format(board_filepath, project_format)
        self.show_center_label(msg)

    def board_recreate_board_from_serial(self, board_dict, main_board=False, board_load_filepath=None):
        board_items = board_dict['board_items']
        board_link_items = board_dict['board_link_items']
        board_attributes = board_dict['board_attributes']
        board_folder_data = board_dict['board_folder_data']
        board_nonAutoSerialized = board_dict.get('board_nonAutoSerialized', {})

        is_virtual = board_folder_data['is_virtual']
        folder_name = board_folder_data['folder_name']

        if is_virtual:
            folder_data_path = folder_name
        else:
            folder_data_path = board_load_filepath

        # подготовка перед загрузкой данных
        fd = self.LibraryData().create_folder_data(folder_data_path, [], image_filepath=None, make_current=main_board, virtual=is_virtual)
        if is_virtual:
            fd.folder_name = folder_name

        # ЗАГРУЗКА ДАННЫХ
        # атрибуты доски
        # при загрузке доски могут использоваться колбэки и их нужно установить заранее
        self.board_serial_to_object_attributes(fd.board, board_attributes)
        self.board_SetCallbacks(fd)
        # айтемы доски
        for board_item_attributes in board_items:
            bi = self.BoardItem(self.BoardItem.types.ITEM_UNDEFINED)
            self.board_serial_to_object_attributes(bi, board_item_attributes, fd=fd)
            fd.board.items_list.append(bi)
        # линки доски
        for link_item_attributes in board_link_items:
            li = self.BoardItem(self.BoardItem.types.ITEM_UNDEFINED)
            self.board_serial_to_object_attributes(li, link_item_attributes, fd=fd)
            fd.board.link_items_list.append(li)
            self.board_add_link_to_slot(fd, li)

        fd.board.nonAutoSerialized = self.board_loadNonAutoSerialized(board_nonAutoSerialized)

        self.LibraryData().make_thumbnails_and_previews(fd, None)
        fd.board.ready = True
        self.LibraryData().load_board_data() #callbacks are set here
        found_pi = self.board_FindPlugin(fd.board.plugin_filename)
        if fd.board.prepareBoardOnFileLoad:
            if found_pi.preparePluginBoard:
                found_pi.preparePluginBoard(self, found_pi, file_loading=True)
        self.prepare_selection_box_widget(fd)
        self.build_board_bounding_rect(fd)

        return fd

    def board_find_board_item_with_board_index(self, fd, index):
        for bi in fd.board.items_list:
            if bi.board_index == index:
                return bi
        else:
            return None

    def board_serial_to_object_attributes(self, obj, obj_attrs_list, fd=None):
        for attr_name, attr_type, attr_data in obj_attrs_list:

            if attr_type in ['QPoint']:
                attr_value = QPoint(*attr_data)

            elif attr_type in ['QPointF']:
                attr_value = QPointF(*attr_data)

            elif attr_type in ['bool', 'int', 'float', 'str', 'tuple', 'list', 'dict']:
                attr_value = attr_data

            elif attr_type in ['QRect']:
                attr_value = QRect(*attr_data)

            elif attr_type in ['QRectF']:
                attr_value = QRectF(*attr_data)

            elif attr_type in ['QPainterPath']:
                continue
                # filepath = os.path.join(folder_path, attr_data)
                # file_handler = QFile(filepath)
                # file_handler.open(QIODevice.ReadOnly)
                # stream = QDataStream(file_handler)
                # path = QPainterPath()
                # stream >> path
                # attr_value = path

            elif attr_type in ['QPixmap']:
                continue
                # filepath = os.path.join(folder_path, attr_data)
                # attr_value = QPixmap(filepath)

            elif attr_type in ['QColor']:
                attr_value = QColor()
                attr_value.setRgbF(*attr_data)

            elif attr_type in ['NoneType'] or attr_name in ["text_doc"]:
                attr_value = None

            elif attr_type == 'FileData':
                filepath, source_width, source_height = attr_data
                file_data = self.LibraryData().create_file_data(filepath, fd)
                fd.images_list.append(file_data)
                obj.file_data = file_data
                file_data.board_items.append(obj)
                file_data.source_width = source_width
                file_data.source_height = source_height
                continue # не нужна дальнейшая обработка

            elif attr_type == 'FolderData':
                if isinstance(obj, self.BoardItem):
                    if obj.type == self.BoardItem.types.ITEM_FOLDER:
                        folder_path = attr_data
                        files = self.LibraryData().list_interest_files(folder_path, deep_scan=False, all_allowed=False)
                        item_folder_data = self.LibraryData().create_folder_data(folder_path, files, image_filepath=None, make_current=False)
                        self.LibraryData().make_thumbnails_and_previews(item_folder_data, None)
                        obj.item_folder_data = item_folder_data
                    elif obj.type == self.BoardItem.types.ITEM_GROUP:
                        board_dict = attr_data
                        _folder_data = self.board_recreate_board_from_serial(board_dict)
                        obj.item_folder_data = _folder_data
                        _folder_data.board.root_folder = fd
                        _folder_data.board.root_item = obj
                        self.LibraryData().make_thumbnails_and_previews(_folder_data, None)
                        _folder_data.board.ready = True
                continue

            elif attr_type == 'BoardUserPointsList':
                user_points = []
                for user_point in attr_data:
                    point_tuple = user_point[0]
                    scale_x = user_point[1]
                    scale_y = user_point[2]
                    user_points.append((QPointF(*point_tuple), scale_x, scale_y))
                obj.user_points = user_points
                continue

            else:
                status = f"name: '{attr_name}' type: '{attr_type}' value: '{attr_data}' obj: {obj}"
                raise Exception(f"Unable to handle attribute, {status}")

            if attr_name in ['from_item', 'to_item']:
                if attr_value is not None:
                    attr_value = self.board_find_board_item_with_board_index(fd, attr_value)

            setattr(obj, attr_name, attr_value)

        if isinstance(obj, self.BoardItem):
            if obj.type == self.BoardItem.types.ITEM_NOTE:
                self.board_TextElementInitAfterLoadFromFile(obj)

    def board_object_attributes_to_serial(self, obj, new_obj_base, exclude=None):
        attributes = list(obj.__dict__.items())

        if isinstance(obj, self.BoardItem):
            for attr_pair in attributes[:]:
                attr_name, attr_value = attr_pair
                if attr_name == 'type':
                    # переставляем этот атрибут в начало,
                    # чтобы при восстановлении он обрабатывался первым
                    # это важно при восстановлении, так как нужно знать какого типа айтем
                    # при восстановлении некоторых атрибутов айтема
                    attributes.remove(attr_pair)
                    attributes.insert(0, attr_pair)
                    break

        for attr_name, attr_value in attributes:

            attr_type = type(attr_value).__name__

            if attr_name.startswith("_"):
                continue

            elif exclude is not None and attr_name in exclude:
                continue

            elif attr_name in ['referer_board_folder', 'root_folder', 'root_item', 'nonAutoSerialized', 'progressive_board_preparation']:
                attr_data = None
                attr_type = 'NoneType'

            elif attr_type in ['_tags', '_comments']:
                attr_data = []
                attr_type = 'list'

            elif attr_name in ['from_item', 'to_item']:
                if attr_value is None:
                    attr_data = None
                    attr_type = 'NoneType'
                else:
                    attr_data = attr_value.board_index
                    attr_type = 'int'

            elif isinstance(attr_value, self.FileData):
                attr_data = (attr_value.filepath, attr_value.source_width, attr_value.source_height)

            elif isinstance(attr_value, self.FolderData):
                if isinstance(obj, self.BoardItem):
                    if obj.type == self.BoardItem.types.ITEM_IMAGE:
                        attr_data = None
                        attr_type = 'NoneType'
                    elif obj.type == self.BoardItem.types.ITEM_GROUP:
                        attr_data = self.board_data_to_dict(obj.item_folder_data)
                    elif obj.type == self.BoardItem.types.ITEM_FOLDER:
                        attr_data = attr_value.folder_path
                    else:
                        status = f"name: '{attr_name}' type: '{attr_type}' value: '{attr_value}'"
                        raise Exception('Error! Unable to handle folder data attribute: {status}')
                else:
                    attr_data = None
                    attr_type = 'NoneType'

            elif isinstance(attr_value, QPointF):
                attr_data = (attr_value.x(), attr_value.y())

            elif attr_name == '_saved_data' and isinstance(attr_value, tuple):
                continue

            elif isinstance(attr_value, (bool, int, float, str, tuple, list, dict)):
                attr_data = attr_value

            elif isinstance(attr_value, QPainterPath):
                attr_data = None
                attr_type = 'NoneType'
                # filename = f"path_{attr_name}_{element.unique_index:04}.data"
                # filepath = os.path.join(folder_path, filename)
                # file_handler = QFile(filepath)
                # file_handler.open(QIODevice.WriteOnly)
                # stream = QDataStream(file_handler)
                # stream << attr_value
                # attr_data = filename

            elif isinstance(attr_value, QPixmap):
                attr_data = None
                attr_type = 'NoneType'
                # filename = f"pixmap_{attr_name}_{element.unique_index:04}.png"
                # filepath = os.path.join(folder_path, filename)
                # attr_value.save(filepath)
                # attr_data = filename

            elif isinstance(attr_value, QColor):
                attr_data = attr_value.getRgbF()

            elif attr_value is None or attr_name in ["text_doc"]:
                attr_data = None

            elif isinstance(attr_value, (QTransform, )):
                attr_data = None
                attr_type = 'NoneType'

            elif isinstance(attr_value, (QMovie, APNGMovie)):
                attr_data = None
                attr_type = 'NoneType'

            elif isinstance(attr_value, (QRectF, QRect)):
                attr_data = (attr_value.left(), attr_value.top(), attr_value.width(), attr_value.height())

            else:
                status = f"name: '{attr_name}' type: '{attr_type}' value: '{attr_value}'"
                raise Exception(f"Unable to handle attribute, {status}")

            new_obj_base.append((attr_name, attr_type, attr_data))

    def board_data_to_dict(self, fd):
        board = fd.board

        board_base = dict()
        board_attributes = list()
        board_items = list()
        board_link_items = list()
        board_folder_data = dict()

        # СОХРАНЕНИЕ ДАННЫХ
        board_folder_data.update({'is_virtual':  fd.virtual})
        board_folder_data.update({'folder_name': fd.folder_name})
        # сохранение атрибутов доски
        self.board_object_attributes_to_serial(board, board_attributes,
                                    exclude=('items_list', 'user_points', 'link_items_list'))

        # сохранение юзер-поинтов отдельно,
        # т.к. QPoinF не сериализуется самостоятельно в tuple
        user_points_serialized = []
        for user_point in board.user_points:
            pos = user_point[0]
            scale_x = user_point[1]
            scale_y = user_point[2]
            user_points_serialized.append(((pos.x(), pos.y()), scale_x, scale_y))
        board_attributes.append(('user_points', 'BoardUserPointsList', user_points_serialized))

        # сохранение айтемов доски
        for item in board.items_list:
            new_item_base = list()
            board_items.append(new_item_base)
            self.board_object_attributes_to_serial(item, new_item_base)

        # сохранение линков доски
        for item in board.link_items_list:
            link_item_base = list()
            board_link_items.append(link_item_base)
            self.board_object_attributes_to_serial(item, link_item_base)

        board_nonAutoSerialized = self.board_dumpNonAutoSerialized(board.nonAutoSerialized)

        board_base.update({
            'board_items': board_items,
            'board_link_items': board_link_items,
            'board_attributes': board_attributes,
            'board_folder_data': board_folder_data,
            'board_nonAutoSerialized': board_nonAutoSerialized,
        })
        return board_base

    def board_BuildBoardFilename(self, folder_path, filename):
        if self.STNG.use_cbor2_instead_of_json:
            file_format = 'cbor2'
        else:
            file_format = 'json'
        board_filepath = os.path.normpath(os.path.join(folder_path, f"{filename}.{file_format}.board"))
        return board_filepath

    def board_dumpNonAutoSerialized(self, data):
        return self.dumpNonAutoSerializedBoardCallback(data)

    def board_loadNonAutoSerialized(self, data):
        return self.loadNonAutoSerializedBoardCallback(data)

    def board_dumpNonAutoSerializedDefault(self, data):
        return dict()

    def board_loadNonAutoSerializedDefault(self, data):
        return self.BoardNonAutoSerializedData()

    def board_getBoardFilepathDefault(self):
        cf = self.LibraryData().current_folder()

        if cf.virtual:
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            folder_path = self.Settings.get("inframed_folderpath")
            if not os.path.exists(folder_path):
                folder_path = self.set_path_for_saved_pictures(folder_path)
            save_folderpath = folder_path
        else:
            filename = 'board'

            save_folderpath = cf.folder_path

            if os.path.isfile(save_folderpath):
                # частенько тут оказывается путь на файл доски,
                # и тогда надо избавиться от имени файла доски в этом пути
                save_folderpath = os.path.dirname(save_folderpath)

        board_filepath = self.board_BuildBoardFilename(save_folderpath, filename)
        return board_filepath

    def board_getBoardFilepath(self):
        return self.getBoardFilepathBoardCallback()

    def board_saveBoardDefault(self):
        cf = self.LibraryData().current_folder()

        # если находимся в зависимой доске,
        # то сохраняем корневую доску, а зависимая запишется вместе с ней
        while cf.board.root_folder is not None:
            print(f'saving... {cf.folder_name}::{cf.folder_path} is not root folder...')
            cf = cf.board.root_folder

        board_filepath = self.board_getBoardFilepath()

        # сохранение текущих атрибутов доски в переменные, из которых будет вестись запись в файл
        self.LibraryData().save_board_data()

        data_base = dict()
        data_base['main_board'] = self.board_data_to_dict(cf)

        # ЗАПИСЬ В ФАЙЛ НА ДИСКЕ
        if self.STNG.use_cbor2_instead_of_json:
            data_to_write = cbor2.dumps(data_base)
            with open(board_filepath, "wb") as file:
                file.write(data_to_write)
        else:
            data_to_write = json.dumps(data_base, indent=True)
            with open(board_filepath, "w+", encoding="utf8") as file:
                file.write(data_to_write)

        # ВЫВОД СООБЩЕНИЯ О ЗАВЕРШЕНИИ
        text = _("Project is saved to {0}").format(board_filepath)
        self.show_center_label(text)

        if self.Globals.DEBUG:
            self.debug_file_io_filepath = board_filepath

    @property
    def active_element(self):
        return self._active_element

    @active_element.setter
    def active_element(self, el):
        self.board_TextElementDeactivateEditMode()
        self._active_element = el

    def board_dive_inside_board_item(self, back_to_referer=False):
        if self.translation_ongoing or self.rotation_ongoing or self.scaling_ongoing:
            msg = _("You cannot dive inside item when board operation is not finished!")
            self.show_center_label(msg, error=True)
            return
        self.board_TextElementDeactivateEditMode()
        cf = self.LibraryData().current_folder()
        BOARD_FOLDER_DATA = None
        if back_to_referer:
            board = cf.board
            referer = board.referer_board_folder
            if referer is not None:
                board.root_item._snapshot = self.grab()
                BOARD_FOLDER_DATA = referer
        else:
            item = None
            for bi in cf.board.items_list:
                item_selection_area = bi.get_selection_area(canvas=self)
                is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                if is_under_mouse:
                    item = bi
                    break
            if item is None:
                self.show_center_label(_("Place mouse cursor on item!"), error=True)
                return

            case1 = item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]
            case2 = item.type == BoardItem.types.ITEM_NODE
            case3 = item.type == BoardItem.types.ITEM_IMAGE and item.animated
            if not (case1 or case2 or case3):
                msg = _("You can dive inside groups, folders, nodes and animated items only!")
                self.show_center_label(msg, error=True)
                return

            item_folder_data = getattr(item, 'item_folder_data', None)
            if item_folder_data:
                BOARD_FOLDER_DATA = item.item_folder_data

            elif case2:
                BOARD_FOLDER_DATA = fd = self.LibraryData().create_folder_data(_("NODE BOARD Virtual Folder"), [], image_filepath=None, make_current=False, virtual=True)
                item.item_folder_data = fd
                self.build_board_bounding_rect(fd)
                fd.previews_done = True
                fd.board.ready = True
                fd.board.root_folder = cf
                fd.board.root_item = item

            elif case3:
                BOARD_FOLDER_DATA = fd = self.LibraryData().create_folder_data(_("ANIMATED FILE Virtual Folder"), [], image_filepath=None, make_current=False, virtual=True)
                item.item_folder_data = fd

                movie = item.movie
                offset = QPointF(0, 0)
                create_file_data = self.LibraryData().create_file_data
                for i in range(movie.frameCount()):
                    movie.jumpToFrame(i)
                    pixmap = item.movie.currentPixmap()
                    fd_bi = BoardItem(BoardItem.types.ITEM_IMAGE)
                    fd_bi.pixmap = pixmap

                    fd_bi.file_data = create_file_data("", fd_bi)
                    fd_bi.file_data.board_items.append(fd_bi)
                    fd.images_list.append(fd_bi.file_data)

                    fd.board.items_list.append(fd_bi)
                    fd_bi.board_index = i
                    fd_bi.scale_x = 1.0
                    fd_bi.scale_y = 1.0

                    fd_bi.position = offset + QPointF(pixmap.width(), pixmap.height())/2
                    offset += QPointF(pixmap.width(), 0)
                self.LibraryData().make_thumbnails_and_previews(fd, None, from_board_items=True)

                self.build_board_bounding_rect(fd)
                fd.previews_done = True
                fd.board.ready = True
                fd.board.root_folder = cf
                fd.board.root_item = item



        if BOARD_FOLDER_DATA is not None:
            self.board_make_board_current(BOARD_FOLDER_DATA)
            if not back_to_referer:
                self.LibraryData().current_folder().board.referer_board_folder = cf
            self.prepare_selection_box_widget(BOARD_FOLDER_DATA)
        else:
            self.show_center_label(_("No place to return"), error=True)
        self.update()

    def board_make_board_current(self, folder_data):
        self.LibraryData().save_board_data()
        self.LibraryData().make_folder_current(folder_data, write_view_history=False)
        self.LibraryData().load_board_data()

    def board_save_board_data(self, board_lib_obj, folder_data):
        board_lib_obj.bounding_rect = self.board_bounding_rect

        self.board_item_under_mouse = None
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False

    def board_load_board_data(self, board_lib_obj, folder_data):
        if board_lib_obj.bounding_rect is not None:
            self.board_bounding_rect = board_lib_obj.bounding_rect

    def load_cursors(self):
        cursors_folder_path = os.path.join(os.path.dirname(__file__), "cursors")
        filepath_scale_svg = os.path.join(cursors_folder_path, "scale.svg")
        filepath_rotate_svg = os.path.join(cursors_folder_path, "rotate.svg")
        filepath_translate_svg = os.path.join(cursors_folder_path, "translate.svg")

        scale_rastr_source = QPixmap(filepath_scale_svg)
        rotate_rastr_source = QPixmap(filepath_rotate_svg)
        translate_rastr_source = QPixmap(filepath_translate_svg)

        if not scale_rastr_source.isNull():
            self.scale_rastr_source = scale_rastr_source
        if not rotate_rastr_source.isNull():
            self.rotate_rastr_source = rotate_rastr_source
        if not translate_rastr_source.isNull():
            self.translate_rastr_source = translate_rastr_source

        self.board_TextElementLoadCursors(cursors_folder_path)

    def board_toggle_minimap(self):
        cf = self.LibraryData().current_folder()
        self.build_board_bounding_rect(cf)
        self.board_show_minimap = not self.board_show_minimap

    def board_draw_stub(self, painter):
        font.setPixelSize(250)
        font.setWeight(1900)
        painter.setFont(font)
        pen = QPen(QColor(180, 180, 180), 1)
        painter.setPen(pen)
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, _("WELCOME TO\nBOARDS"))

    def board_draw(self, painter, event):
        self.board_draw_main(painter, event)
        # board_draw_stub(self, painter)

    def board_draw_long_process_label(self, painter):
        if self.long_loading:
            self.board_draw_wait_label(painter,
                socondary_text=self.long_process_label_text
            )

    def board_draw_wait_label(self, painter, primary_text=_("WAITING"),
                                                        socondary_text=_("creating previews")):
        painter.save()
        font = painter.font()
        font.setPixelSize(100)
        font.setWeight(1900)
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter

        painter.setPen(QPen(QColor(240, 10, 50, 100), 1))
        text = "  ".join(primary_text)
        main_text_rect = painter.boundingRect(max_rect, alignment, text)
        pos = self.rect().center() + QPoint(0, -80)
        main_text_rect.moveCenter(pos)
        painter.fillRect(main_text_rect.adjusted(-100, -10, 100, 10), QColor(10, 10, 10, 150))
        painter.drawText(main_text_rect, alignment, text)

        font = painter.font()
        font.setPixelSize(15)
        # font.setWeight(900)
        painter.setFont(font)

        text = " ".join(socondary_text).upper()
        secondary_text_rect = painter.boundingRect(main_text_rect, alignment, text)
        brush = QBrush(Qt.black)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(secondary_text_rect.adjusted(-3, -3, 3, 3))
        painter.setPen(QPen(Qt.white))

        painter.drawText(secondary_text_rect, alignment, text)
        painter.setBrush(Qt.NoBrush)
        painter.restore()

    def retrieve_new_board_item_index(self):
        cf = self.LibraryData().current_folder()
        cf.board.current_item_index += 1
        return cf.board.current_item_index

    def retrieve_new_board_item_group_index(self):
        cf = self.LibraryData().current_folder()
        cf.board.current_item_group_index += 1
        return cf.board.current_item_group_index

    def board_get_selected_or_visible_items(self, visible=False):
        cf = self.LibraryData().current_folder()
        items_to_reset = []
        viewport_rect = self.rect()
        if self.selected_items and not visible:
            items_to_reset = self.selected_items[:]
        else:
            for bi in cf.board.items_list:
                item_selection_rect = bi.get_selection_area(canvas=self).boundingRect().toRect()
                if item_selection_rect.intersects(viewport_rect):
                    items_to_reset.append(bi)
        return items_to_reset

    def board_ctrl_z(self):
        for bi in self.board_get_selected_or_visible_items():
            self.board_retrieve_transform_back_from_history(bi)
        self.board_update_selection_box_widget()

    def board_reset_items_to_layout_transforms(self):
        for bi in self.board_get_selected_or_visible_items():
            self.board_stash_current_transform_to_history(bi)
            self.board_apply_layout_transforms(bi)
        self.board_update_selection_box_widget()

    def board_stash_current_transform_to_history(self, board_item):
        # item_key = board_item.board_index
        item_key = id(board_item)
        BoardItemTransform = namedtuple('BoardItemTransform', 'position rotation scale_x scale_y')
        self.board_item_ctrl_z_data[item_key].append(BoardItemTransform(
            QPointF(board_item.position),
            board_item.rotation,
            board_item.scale_x,
            board_item.scale_y,
        ))

    def board_retrieve_transform_back_from_history(self, board_item):
        # item_key = board_item.board_index
        item_key = id(board_item)
        transforms_list = self.board_item_ctrl_z_data.get(item_key, None)
        if transforms_list:
            transform = transforms_list.pop()
            board_item.position = QPointF(transform.position)
            board_item.rotation = transform.rotation
            board_item.scale_x = transform.scale_x
            board_item.scale_y = transform.scale_y
        else:
            board_item.set_alert()

    def board_apply_layout_transforms(self, board_item):
        board_item.position = QPointF(board_item.layout_position)
        board_item.rotation = board_item.layout_rotation
        board_item.scale_x = board_item.layout_scale_x
        board_item.scale_y = board_item.layout_scale_y

    def board_save_layout_transforms(self, board_item):
        board_item.layout_position = QPointF(board_item.position)
        board_item.layout_rotation = board_item.rotation
        board_item.layout_scale_x = board_item.scale_x
        board_item.layout_scale_y = board_item.scale_y

    def board_progressive_layout_start(self, folder_data):
        self.board_set_window_title(folder_data)

    def board_set_window_title(self, folder_data):
        self.set_window_title(folder_data.folder_path)

    def board_progressive_layout_finish(self, folder_data):
        if self.is_board_page_active():
            self.show_center_label(_("The board is prepared"), duration=1.0)
        self.progressive_layout_ongoing = False

    def board_progressive_fill_layout(self, folder_data, file_data):
        """
            Превьюшки могут генерится в совершенно произвольном порядке,
            но нам всё-таки надо сохранить порядок,
            поэтому здесь очень много кода, который это делает
        """

        board = folder_data.board
        if not hasattr(board, "progressive_board_preparation"):
            board.items_list = []
            pbp = board.progressive_board_preparation = type('PBPClass', (), {})()
            pbp.forward_offset = QPointF()
            pbp.backward_offset = QPointF()
            pbp.pivot_index = None
        else:
            pbp = board.progressive_board_preparation

        pbp.direction = 1
        if pbp.pivot_index is not None:
            if folder_data.images_list.index(file_data) < pbp.pivot_index:
                pbp.direction = -1
            else:
                pbp.direction = 1

        bi = self.board_prepare_board_item(board, file_data,
            pbp.forward_offset if pbp.direction == 1 else pbp.backward_offset,
            pbp.direction,
            folder_data.board.force_vertical_layout
        )
        if bi is not None:
            if pbp.pivot_index is None:
                self.progressive_layout_ongoing = True
                # пивот-индекс задаём именно тут, а не выше, где происходит инициализация pbp,
                # ибо board_prepare_board_item создаёт айтем не для каждого file_data
                pbp.pivot_index = folder_data.images_list.index(file_data)
                self.board_fit_content_on_screen(file_data)
                self.DEFAULT_CANVAS_ORIGIN = QPointF(self.canvas_origin)
                self.DEFAULT_CANVAS_SCALE = self.canvas_scale_x, self.canvas_scale_y
            self.build_board_bounding_rect(folder_data)
            bi.sort_index = folder_data.images_list.index(file_data) - pbp.pivot_index

        if self.is_board_page_active() and self.Globals.DEBUG:
            self.show_center_label(str(file_data.filepath))

    def board_prepare_board_item(self, board, file_data, offset, direction, force_vertical_layout):

        def _set_position(bi, imd, offset):
            bi.position = offset + QPointF(imd.source_width, imd.source_height)/2
            self.board_save_layout_transforms(bi)

        def _offset_anchor(imd):
            nonlocal offset
            if force_vertical_layout or self.STNG.board_vertical_items_layout:
                offset += QPointF(0, direction*imd.source_height)
            else:
                offset += QPointF(direction*imd.source_width, 0)

        if file_data.preview_error:
            return None
        else:
            if file_data.is_audio_video_filetype:
                item_type = BoardItem.types.ITEM_AV
            else:
                item_type = BoardItem.types.ITEM_IMAGE
            board_item = BoardItem(item_type, visible=False)
            # linking board and image data
            board_item.file_data = file_data
            file_data.board_items.append(board_item)
            board.items_list.append(board_item)
            # fill attributes and overlays
            board_item.animated_file = file_data.is_animated_file
            board_item.audiovideo_file = file_data.is_audio_video_filetype
            board_item.video = file_data.is_audio_video_filetype
            board_item.audio = file_data.is_audio_video_filetype and not file_data.is_video_filetype
            board_item.board_index = self.retrieve_new_board_item_index()
            if direction == 1:
                _set_position(board_item, file_data, offset)
                _offset_anchor(file_data)

            elif direction == -1:
                _offset_anchor(file_data)
                _set_position(board_item, file_data, offset)

            if not self.Globals.lite_mode:
                board_item._tags = self.LibraryData().get_tags_for_file_data(file_data)
                board_item._comments = self.LibraryData().get_comments_for_image(file_data)
            board_item.visible = True
            return board_item

    def board_prepare_items_layout_and_viewport(self, folder_data):

        # layout and items overlays
        if self.Globals.DEBUG:
            offset = QPointF(0, 0) - QPointF(500, 0)
        else:
            offset = QPointF(0, 0)
        board = folder_data.board
        board.items_list = []
        for file_data in folder_data.images_list:
            self.board_prepare_board_item(board, file_data, offset, 1, board.force_vertical_layout)

        # for board items map
        self.build_board_bounding_rect(folder_data)

        board.ready = True

        # UX: viewport positioning and scaling
        if self.STNG.board_move_to_current_on_first_open:
            if folder_data.current_image().board_items:
                self.board_fit_content_on_screen(folder_data.current_image())

        self.board_set_window_title(folder_data)
        self.update()

    def board_timer_handler(self):
        if self.isActiveWindow():
            self.board_selection_transform_box_opacity = 1.0
        else:
            if self.underMouse():
                # to 1.0
                value = 1.0
                if not self.is_there_any_task_with_anim_id("transforom_widget_fading") and self.board_selection_transform_box_opacity != value:
                    self.animate_properties(
                        [
                            (self, "board_selection_transform_box_opacity", self.board_selection_transform_box_opacity, value, self.update),
                        ],
                        anim_id="transforom_widget_fading",
                        duration=0.3,
                    )
            else:
                # to 0.0
                value = 0.0
                if not self.is_there_any_task_with_anim_id("transforom_widget_fading") and self.board_selection_transform_box_opacity != value:
                    self.animate_properties(
                        [
                            (self, "board_selection_transform_box_opacity", self.board_selection_transform_box_opacity, value, self.update),
                        ],
                        anim_id="transforom_widget_fading",
                        duration=0.3,
                    )

    def board_draw_content(self, painter, folder_data):
        self.board_TextElementResetColorsButtons()
        self.board_frame_items_text_rects = []

        painter.setPen(QPen(Qt.white, 1))
        font = painter.font()
        font.setWeight(300)
        font.setPixelSize(12)
        painter.setFont(font)

        self.board_draw_content_links(painter, folder_data, True, False)

        self.images_drawn = 0
        self.board_item_under_mouse = None
        for board_item in folder_data.board.items_list:
            if board_item.visible:
                self.board_draw_item(painter, board_item)
        self.draw_selection(painter, folder_data)

        self.board_draw_content_links(painter, folder_data, False, True)

        painter.drawText(self.rect().bottomLeft() + QPoint(50, -150), _("perfomance status: {0} images drawn").format(self.images_drawn))

    def board_util_path_to_polygone(self, path):
        def float_range(start, stop, step):
            while start < stop:
                yield start
                start += step
        points = [path.pointAtPercent(t) for t in float_range(0.0, 1.0, 0.05)]
        points.append(path.pointAtPercent(1.0))
        return QPolygonF(points)

    def board_draw_content_links(self, painter, folder_data, pre, post):
        if self.links_draw_before_items and post:
            return
        if not self.links_draw_before_items and pre:
            return

        selected_color = QColor(127, 18, 34)
        selected_color2 = QColor(selected_color)
        selected_color2.setAlpha(255-100)
        gray_color = QColor(255, 255, 255, 255-100)

        pos = self.mapped_cursor_pos()
        # ITEM_LINK
        for slot_id, slot in folder_data.board._link_slots_list.items():
            if not slot:
                continue

            links_count = len(slot)
            pivot_index = (links_count + 1)/2

            is_odd = bool(links_count % 2 == 1)

            check_to_item = slot[0].to_item

            for n, li in enumerate(slot):
                _to = li.to_item
                _from = li.from_item
                to_pos = _to.calculate_viewport_position(canvas=self)
                from_pos = _from.calculate_viewport_position(canvas=self)
                center_pos = (to_pos + from_pos)/2.0

                slot_index_offset = pivot_index - (n + 1)

                v = QVector2D(center_pos - from_pos).normalized()
                pd1 = QVector2D(-v.y(), v.x())
                pd2 = QVector2D(v.y(), -v.x())


                is_near = li.is_near_link(self, pos)
                if li._selected and not is_near:
                    color = selected_color2
                elif li._selected and is_near:
                    color = selected_color
                elif is_near:
                    color = self.selection_color
                else:
                    color = gray_color
                style = Qt.DashLine
                style = Qt.SolidLine
                painter.setPen(QPen(color, li.link_width*min(self.canvas_scale_x, self.canvas_scale_y), style))
                li._is_curved_link = not (pivot_index == slot_index_offset and is_odd)
                if li._is_curved_link:

                    if check_to_item is _to:
                        pd = pd1
                    else:
                        pd = pd2
                    center_pos = center_pos + (pd*slot_index_offset*50).toPointF()
                    if False:
                        painter.drawLine(to_pos, center_pos)
                        painter.drawLine(center_pos, from_pos)
                    else:
                        path = QPainterPath()
                        path.moveTo(to_pos)
                        a = QPointF(to_pos) + (pd*slot_index_offset*50).toPointF() + (-v*30).toPointF()
                        b = QPointF(from_pos) + (pd*slot_index_offset*50).toPointF() + (v*30).toPointF()
                        path.cubicTo(a, b, from_pos)
                        painter.setBrush(Qt.NoBrush)
                        painter.drawPath(path)
                        li._path = path
                        # lowpoly
                        # painter.drawPoint(a)
                        # painter.drawPoint(b)
                        # correction for arrow
                        center_pos = path.pointAtPercent(0.5)
                else:
                    painter.drawLine(to_pos, from_pos)


                # arrow
                if li.is_directional:
                    back_d = (-v*20).toPointF()
                    a1 = (pd1*20).toPointF() + back_d + center_pos
                    a2 = (pd2*20).toPointF() + back_d + center_pos
                    painter.drawLine(center_pos, a2)
                    painter.drawLine(center_pos, a1)

            links_count_str = f'{links_count}'

            count_rect = painter.boundingRect(QRectF(), Qt.AlignLeft, links_count_str)
            size = max(count_rect.width(), count_rect.height())
            count_rect.setWidth(size)
            count_rect.setHeight(size)
            count_rect.adjust(-4, -4, 4, 4)
            count_rect.moveCenter(center_pos + QPointF(0, -25))

            painter.setPen(Qt.NoPen)
            painter.drawEllipse(count_rect)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawText(count_rect, Qt.AlignVCenter | Qt.AlignHCenter, links_count_str)

    def draw_selection(self, painter, folder_data):
        painter.save()
        pen = QPen(self.selection_color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        ITEM_NODE = BoardItem.types.ITEM_NODE
        for board_item in folder_data.board.items_list:
            if board_item._selected and not board_item.type == ITEM_NODE:
                painter.drawPolygon(board_item.get_selection_area(canvas=self))
        painter.restore()

    # TODO: (10 фев 26) удалить перед релизом
    # def rectrect_intersect_asim_check_pass(self, r1, r2):
    #     return any(r1.contains(p) for p in [
    #         r2.topLeft(),
    #         r2.topRight(),
    #         r2.bottomRight(),
    #         r2.bottomLeft(),
    #         r2.center(),
    #     ])
    # def is_rect_insersects_rect(self, r1, r2):
    #     return any((
    #         self.rectrect_intersect_asim_check_pass(r1, r2),
    #         self.rectrect_intersect_asim_check_pass(r2, r1),
    #     ))

    def board_toggle_full_forcing(self, reset=False):
        cf = self.LibraryData().current_folder()
        toggle = not reset
        for board_item in cf.board.items_list:
            selection_area = board_item.get_selection_area(canvas=self)
            item_rect = selection_area.boundingRect().toRect()
            if self.boards_resolve_rects_intersection(self.rect(), item_rect):
                board_item.force_full_quality = (not board_item.force_full_quality) if toggle else False
        self.update()

    def boards_resolve_rects_intersection(self, rect1, rect2):
        # WARNING: (10 фев 26) пересечение прямоугольников надо проверять через пересечение проекций на обе оси,
        # а функция self.is_rect_insersects_rect даёт сбой, когда картинка, например, сильно вытянута по вертикали, и тогда
        # при просмотре её верхушки или низины она пропадает с экрана.
        # Я затупил тогда, и сейчас исправляю свой затуп. К счастью, реализовывать сравнение проекций не нужно, всё уже реализовано в Qt.
        return rect1.intersects(rect2)

    def board_draw_item(self, painter, board_item):

        if board_item.countdown_red_frame > 0:
            br = board_item.get_selection_area(canvas=self).boundingRect()
            painter.save()
            painter.setPen(QPen(Qt.red, board_item.countdown_red_frame))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(br)
            painter.restore()
            board_item.countdown_red_frame -= 1

        if board_item.type == BoardItem.types.ITEM_FRAME:
            FRAME_PADDING = BoardItem.FRAME_PADDING

            area = board_item.get_selection_area(canvas=self)
            pen = QPen(Qt.white, 2, Qt.DashLine)
            pen.setCosmetic(True) # не скейлить пен
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            path = QPainterPath()
            path.addRoundedRect(area.boundingRect(), FRAME_PADDING*self.canvas_scale_x, FRAME_PADDING*self.canvas_scale_y)
            painter.drawPath(path)
            pos = area.boundingRect().topLeft()
            zoom_delta = QPointF(FRAME_PADDING*self.canvas_scale_x, 0)
            font = painter.font()
            before_font = painter.font()
            font.setPixelSize(30)
            painter.setFont(font)

            text = board_item.label
            alignment = Qt.AlignLeft
            rect = painter.boundingRect(area.boundingRect(), alignment, text)
            rect.moveBottomLeft(pos+zoom_delta)
            board_item._label_ui_rect = None
            show_text = True
            if rect.width() > area.boundingRect().width():
                show_text = False
                if area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill):
                    show_text = True
            else:
                show_text = True

            if show_text:
                board_item._label_ui_rect = rect
                painter.drawText(rect, alignment, text)
                self.board_frame_items_text_rects.append((board_item, rect, area.boundingRect()))

            painter.setFont(before_font)

        elif board_item.type == BoardItem.types.ITEM_NOTE:

            if self.Globals.DISABLE_ITEM_DISTORTION_FIXER:
                self.board_TextElementDrawOnCanvas(painter, board_item, False)
            else:
                board_item.enable_distortion_fixer()
                self.board_TextElementDrawOnCanvas(painter, board_item, False)
                board_item.disable_distortion_fixer()

        elif board_item.type == BoardItem.types.ITEM_NODE:

            cursor_pos = self.mapped_cursor_pos()
            sa_br = board_item.get_selection_area(canvas=self).boundingRect()
            radius = min(sa_br.width(), sa_br.height())/2.0
            is_cursor_over = QVector2D(sa_br.center() - cursor_pos).length() < radius

            transform = board_item.get_transform_obj(canvas=self)
            painter.setTransform(transform)

            item_rect = board_item.get_size_rect()
            item_rect.moveCenter(QPointF(0, 0))
            pen = QPen()
            pen.setStyle(Qt.DashLine)
            if is_cursor_over or board_item._selected:
                pen.setColor(self.selection_color)
            else:
                pen.setColor(Qt.gray)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(50, 50, 50)))
            painter.drawEllipse(item_rect)

            painter.resetTransform()


            before_font = painter.font()
            font = QFont(before_font)
            font.setPixelSize(30)
            painter.setFont(font)

            item_folder_data = getattr(board_item, 'item_folder_data', None)
            if item_folder_data:
                item_folder_data = board_item.item_folder_data
                board = item_folder_data.board
                items_count = len(board.items_list)
                label_text = f'({items_count}) {board_item.label}'
            else:
                label_text = board_item.label
            label_rect = painter.boundingRect(QRectF(), Qt.AlignLeft, label_text)
            # для отрисовки внутри board_item.get_transform_obj
            # pos = (item_rect.topLeft() + item_rect.topRight())/2.0
            # pos -= QPointF(0, label_rect.height())
            # label_rect.moveCenter(pos)
            if label_rect.isNull():
                label_rect = QRectF(item_rect)
            label_rect.moveBottomLeft(sa_br.topLeft())
            board_item._node_ui_rect = label_rect

            alignment = Qt.AlignVCenter | Qt.AlignHCenter
            painter.drawText(label_rect, alignment, label_text)
            painter.setFont(before_font)


            snapshot = board_item._snapshot
            if is_cursor_over and snapshot:
                painter.setOpacity(0.5)
                place_rect = self.rect()
                place_rect.setTopLeft(place_rect.center())
                place_rect = fit_rect_into_rect(QRectF(snapshot.rect()), place_rect, float_mode=True)
                painter.drawPixmap(place_rect, snapshot, QRectF(QPointF(0, 0), QSizeF(snapshot.size())))
                painter.setOpacity(1.0)

        else:

            file_data = board_item.retrieve_file_data()

            selection_area = board_item.get_selection_area(canvas=self)

            sbr_ = selection_area.boundingRect()

            if not self.boards_resolve_rects_intersection(self.rect(), sbr_.toRect()):

                if self.STNG.board_unloading:
                    self.trigger_board_item_pixmap_unloading(board_item)

            else:

                self.images_drawn += 1
                transform = board_item.get_transform_obj(canvas=self)

                painter.setTransform(transform)
                item_rect = board_item.get_size_rect()

                if board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
                    item_rect = fit_rect_into_rect(QRectF(0, 0, file_data.source_width, file_data.source_height), item_rect, float_mode=True)

                item_rect.moveCenter(QPointF(0, 0))

                if_0 = self.item_group_under_mouse is not None
                if_1 = board_item is self.item_group_under_mouse
                if_x = all((if_0, if_1))
                if if_x:
                    pen = QPen(QColor(220, 50, 50), 1)
                    pen.setCosmetic(True) # не скейлить пен
                    pen.setWidthF(10.0)
                    painter.setPen(pen)
                else:
                    pen = QPen(Qt.white, 1)
                    pen.setCosmetic(True) # не скейлить пен
                    painter.setPen(pen)


                if if_0 and board_item in self.selected_items:
                    painter.setOpacity(0.5)

                painter.setBrush(Qt.NoBrush)
                painter.drawRect(item_rect)

                case4 = selection_area.boundingRect().toRect().contains(self.mapped_cursor_pos())

                image_to_draw = None
                selection_area_rect = selection_area.boundingRect()
                full_quality = selection_area_rect.width() > 250 or selection_area_rect.height() > 250
                full_quality = any((
                    full_quality,
                    board_item.force_full_quality,
                    board_item.types.ITEM_IMAGE and board_item.animated_file and (case4 or board_item.scrubbed)
                ))
                if full_quality:
                    self.trigger_board_item_pixmap_loading(board_item)
                    image_to_draw = board_item.pixmap
                else:
                    image_to_draw = file_data.preview

                before_item_rect = None
                if board_item.type == BoardItem.types.ITEM_AV:
                    before_item_rect = item_rect
                    item_rect = fit_rect_into_rect(QRectF(0, 0, image_to_draw.width(), image_to_draw.height()), item_rect, float_mode=True)
                    item_rect.moveCenter(QPointF(0, 0))


                if board_item._marked_item:
                    pass

                elif image_to_draw:
                    painter.drawPixmap(item_rect, image_to_draw, QRectF(QPointF(0, 0), QSizeF(image_to_draw.size())))
                    if board_item.type == BoardItem.types.ITEM_AV and full_quality and before_item_rect:
                        painter.drawText(before_item_rect, Qt.AlignLeft | Qt.TextWordWrap, board_item.file_data.filename)

                painter.setOpacity(1.0)
                case1 = board_item.type == BoardItem.types.ITEM_IMAGE
                case2 = not self.Globals.lite_mode
                case3 = selection_area_rect.intersected(QRectF(self.rect()))
                show_tag_data = all((case1, case2, case3))
                if show_tag_data:
                    ir = board_item.get_size_rect(scaled=True)
                    ir.moveCenter(QPointF(0, 0))
                    inverted_transform, status = transform.inverted()
                    if status:
                        cp = inverted_transform.map(QPointF(self.mapped_cursor_pos()))
                        self.draw_board_item_comments(painter, ir, board_item._comments, cp)
                painter.resetTransform()

                if all((any((
                            board_item.types.ITEM_IMAGE and board_item.animated_file,
                            BoardItem.types.ITEM_FOLDER,
                            BoardItem.types.ITEM_GROUP
                        )),
                        case4,
                        board_item.scrubbed
                    )):

                    inside_rect_x_offset = self.mapped_cursor_pos().x() - selection_area_rect.left()
                    offset = QPoint(int(inside_rect_x_offset), 0)
                    if self.globals.DEBUG:
                        vertical_offset = QPoint(0, 50)
                    else:
                        vertical_offset = QPoint(0, 0)
                    p1 = selection_area_rect.topLeft() + offset - vertical_offset
                    p2 = selection_area_rect.bottomLeft() + offset + vertical_offset
                    painter.drawLine(p1, p2)
                    board_item.scrubbed = False

                if show_tag_data and case4:
                    self.draw_board_item_tags(painter, selection_area_rect, board_item._tags)

                if board_item._marked_item:
                    self.draw_rounded_frame_label(painter, selection_area_rect.center().toPoint(), f'MARKED AS BETRUG/TRUFFA/ESTAFA/ESCROQUERIE\n{board_item.info_text()}')

                if case4:
                    self.board_item_under_mouse = board_item

                selection_area_rect = selection_area.boundingRect()

                if board_item._show_file_info_overlay:
                    text = board_item.info_text()
                    alignment = Qt.AlignCenter

                    painter.save()
                    text_rect = painter.boundingRect(selection_area_rect, alignment, text)
                    painter.setBrush(QBrush(Qt.white))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(text_rect)
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(text_rect, alignment, text)
                    painter.restore()

                if board_item == self.board_item_under_mouse:
                    if board_item.status:
                        alignment = Qt.AlignCenter | Qt.AlignVCenter
                        text_rect = painter.boundingRect(selection_area_rect, alignment, board_item.status)
                        text_rect.adjust(-5, -5, 5, 5)
                        text_rect.moveTopLeft(selection_area[0])

                        if text_rect.width() < selection_area_rect.width():
                            path = QPainterPath()
                            path.addRoundedRect(QRectF(text_rect), 5, 5)
                            painter.setPen(Qt.NoPen)
                            painter.setBrush(QBrush(QColor(50, 60, 90)))
                            painter.drawPath(path)

                            painter.setPen(QPen(Qt.white, 1))
                            painter.drawText(text_rect, alignment, board_item.status)
                            painter.setBrush(Qt.NoBrush)

    def trigger_board_item_pixmap_unloading(self, board_item):
        if board_item.pixmap is None:
            return

        dist = QVector2D(self.get_center_position() - self.board_MapToViewport(board_item)).length()

        if dist > 10000.0:
            board_item.pixmap = None
            board_item.movie = None

            file_data = board_item.retrieve_file_data()
            filepath = file_data.filepath
            msg = f'unloaded from board: {filepath}'
            print(msg)

    def trigger_board_item_pixmap_loading(self, board_item):
        if board_item.pixmap is not None:
            return

        def show_msg(filepath):
            msg = f'loaded to board: {filepath}'
            print(msg)

        def __load_animated(filepath):
            if board_item.file_data.is_animated_apng:
                board_item.movie = APNGMovie(filepath)
            else:
                board_item.movie = QMovie(filepath)
                board_item.movie.setCacheMode(QMovie.CacheAll)
            board_item.movie.jumpToFrame(0)
            board_item.pixmap = board_item.movie.currentPixmap()
            board_item.animated = True
            board_item.update_corner_info()
            if board_item.movie.frameRect().isNull():
                board_item.pixmap = None
            else:
                show_msg(filepath)

        def __load_svg(filepath):
            board_item.pixmap = load_svg(filepath)
            show_msg(filepath)

        def __load_static(filepath):
            board_item.pixmap = load_image_respect_orientation(filepath)
            show_msg(filepath)

        def __load_audio_video(filepath):
            if board_item.video:
                board_item.pixmap = FFMPEG.load_one_of_the_first_frames_from_video(self.STNG.ffmpeg_exe_filepath, filepath, self.Globals.FFMPEG_NOT_FOUND)
                # TODO: вообще тут превьюшки делать не надо, но не хочется тормозить начальную загрузку этим
                file_data = board_item.file_data
                pixmap = board_item.pixmap
                self.LibraryData().make_preview(self.Globals, file_data, pixmap, pixmap.size(), set_source_size=False)
                self.LibraryData().make_thumbnail(self.Globals, file_data, file_data.preview)
            elif board_item.audio:
                board_item.pixmap = QPixmap()
            show_msg(filepath)

        if board_item.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_AV]:
            filepath = board_item.file_data.filepath
        elif board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            filepath = board_item.item_folder_data.current_image().filepath

        if filepath == "":
            # для пустых групп (item_GROUP)
            board_item.pixmap = board_item.item_folder_data.current_image().preview
        else:
            try:
                board_item.pixmap = QPixmap()
                if board_item.animated_file:
                    __load_animated(filepath)
                elif self.LibraryData().is_svg_file(filepath):
                    __load_svg(filepath)
                elif board_item.audiovideo_file:
                    __load_audio_video(filepath)
                else:
                    __load_static(filepath)
            except Exception as e:
                board_item.pixmap = QPixmap()

    def boards_generate_expo_values(self):
        exp = self.STNG.gamepad_move_stick_ease_in_expo_param
        SAMPLES = 50
        values = []
        for n in range(SAMPLES+1):
            x = n/SAMPLES
            y = math.pow(x, exp)
            values.append((x, y))
        self.expo_values = values

    def boards_postponed_set_expo(self, setting_id, setting_value):
        self.Settings.postponed_set(setting_id, setting_value)

    def board_draw_grid(self, painter):
        LINES_INTERVAL_X = 300 * self.canvas_scale_x
        LINES_INTERVAL_Y = 300 * self.canvas_scale_y
        r = QRectF(self.rect()).adjusted(-LINES_INTERVAL_X*2, -LINES_INTERVAL_Y*2, LINES_INTERVAL_X*2, LINES_INTERVAL_Y*2)
        value_x = int(fit(self.canvas_scale_x, 0.08, 1.0, 0, 200))
        # value_x = 100
        pen = QPen(QColor(220, 220, 220, value_x), 1)
        painter.setPen(pen)
        icp = self.canvas_origin
        offset = QPointF(icp.x() % LINES_INTERVAL_X, icp.y() % LINES_INTERVAL_Y)

        i = r.left()
        while i < r.right():
            painter.drawLine(offset+QPointF(i, r.top()), offset+QPointF(i, r.bottom()))
            i += LINES_INTERVAL_X

        i = r.top()
        while i < r.bottom():
            painter.drawLine(offset+QPointF(r.left(), i), offset+QPointF(r.right(), i))
            i += LINES_INTERVAL_Y

    def board_draw_user_points(self, painter, cf):
        painter.setPen(QPen(Qt.red, 5))
        for point, canvas_scale_x, canvas_scale_y in cf.board.user_points:
            painter.drawPoint(self.board_MapToViewport(point))

    def draw_grid_wrapper(self, painter):
        if self.Globals.DEBUG or self.STNG.board_draw_grid:
            self.board_draw_grid(painter)

    def board_draw_main_default(self, painter, event):
        cf = self.LibraryData().current_folder()
        if self.Globals.ENABLE_PROGRESSIVE_BOARD_LAYOUT:
            self.draw_grid_wrapper(painter)
            self.board_draw_content(painter, cf)
        else:
            if cf.previews_done:
                self.draw_grid_wrapper(painter)
                if not self.is_board_ready():
                    self.board_prepare_items_layout_and_viewport(cf)
                else:
                    self.board_draw_content(painter, cf)
            else:
                self.board_draw_wait_label(painter)


        if self.Globals.DEBUG or self.STNG.board_draw_canvas_origin:
            self.board_draw_canvas_origin(painter)

        self.board_draw_user_points(painter, cf)

        self.board_draw_selection_mouse_rect(painter)
        self.board_draw_selection_transform_box(painter)
        self.right_click_selection_drawEvent(painter)
        self.board_region_zoom_in_draw(painter)

        if self.Globals.DEBUG or self.STNG.board_draw_origin_compass:
            self.board_draw_origin_compass(painter)

        self.board_draw_cursor_text(painter)

        self.board_draw_diving_notification(painter, cf)

        self.board_draw_board_info(painter, cf)

        self.board_draw_minimap(painter)

        self.board_draw_long_process_label(painter)

        self.draw_progressive_layout_animation(painter)

        self.board_draw_snapping_targets(painter)

        self.board_draw_AD_toolbox(painter)

        self.board_draw_debug_item_transform_autoscroll_activation_zones(painter)

    def board_draw_debug_item_transform_autoscroll_activation_zones(self, painter):
        if self.Globals.DEBUG:
            o, i = self.autoscroll_activation_zones_for_board_item_transform()
            painter.setBrush(Qt.NoBrush)
            pen = QPen(Qt.gray, 1)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(o)
            painter.drawRect(i)

    def draw_progressive_layout_animation(self, painter):
        if self.progressive_layout_ongoing:
            self.draw_rounded_frame_progress_label(painter,
                                        (RectHelper(self.rect()).top_center()+QPointF(0, 50)).toPoint(),
                                        _("Please wait").upper(),
                                        normalized_progress=time.time() % 1.0,
                                        from_center_to_sides=True,
            )


    def board_draw_board_info(self, painter, current_folder):
        before_font = painter.font()
        before_pen = painter.pen()

        lines = []
        board = current_folder.board
        if current_folder.virtual:
            lines.append(_('Virtual folder board: {}').format(current_folder.folder_path))
        else:
            lines.append(_('Board folder: {}').format(current_folder.folder_path))
        lines.append(_('Generation time: {}').format(datetime.datetime.fromtimestamp(board.generation_time).strftime("%d.%m.%Y %H:%M")))
        if board.plugin_filename:
            lines.append(_('File-plugin name: {}').format(board.plugin_filename))
        else:
            lines.append(_('This board has no plugin attached'))
        lines.append(_('Current item index: {}').format(board.current_item_index))
        lines.append(_('Current item-group index: {}').format(board.current_item_group_index))
        lines.append(_('Board bounding rect: {}').format(rect_to_string(board.bounding_rect)))

        lines.append('')

        if board.referer_board_folder is not None:
            lines.append(_("You've entered this board from the board of folder {}").format(board.referer_board_folder.folder_path))
        if board.root_folder is not None:
            lines.append(_("Parent folder of this board {}").format(board.root_folder.folder_path))
        if board.root_item is not None:
            lines.append(_("This board parent item title {}").format(board.root_item.label))

        text = "\n".join(lines)
        painter.setPen(QPen(Qt.white, 1))
        font = painter.font()
        font.setPixelSize(20)
        font.setWeight(300)
        painter.setFont(font)
        alignment = Qt.AlignLeft
        rect = painter.boundingRect(self.rect(), alignment, text)
        if self.STNG.board_vertical_items_layout or board.force_vertical_layout:
            pos = self.canvas_origin + QPointF(-100, -100)
            rect.moveBottomRight(pos.toPoint())
        else:
            pos = self.canvas_origin + QPointF(100, -100)
            rect.moveBottomLeft(pos.toPoint())
        painter.drawText(rect, alignment, text)

        painter.setFont(before_font)
        painter.setPen(before_pen)

    def board_draw_diving_notification(self, painter, folder_data):
        referer = folder_data.board.referer_board_folder
        if referer is not None:
            folder_name = referer.folder_path
            text = _("Pressing Backspace key returns to board of the folder {0}").format(folder_name)
            font = painter.font()
            font.setPixelSize(20)
            painter.setFont(font)
            text_rect = painter.boundingRect(QRect(0, 0, 500, 500), Qt.AlignLeft, text)
            text_rect.moveTopLeft(QPoint(150, 150))
            _text_rect = text_rect.adjusted(-10, -10, 10, 10)
            color = QColor(51, 47, 150)
            painter.setPen(QPen(color, 2))
            color.setAlpha(150)
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.addRoundedRect(QRectF(_text_rect), 10, 10)
            painter.drawPath(path)
            painter.setPen(QPen(Qt.white, 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawText(text_rect, Qt.AlignLeft, text)

    def board_draw_cursor_text(self, painter):
        if self.item_group_under_mouse:
            pos = self.mapped_cursor_pos()
            count = len(self.selected_items)
            text = _("Add to the group ({})").format(count)
            bounding_rect = painter.boundingRect(QRect(0, 0, 500, 500), Qt.AlignLeft, text)
            painter.setBrush(QBrush(Qt.black))
            painter.setPen(Qt.NoPen)
            bounding_rect.moveCenter(pos)
            painter.drawRect(bounding_rect.adjusted(-2, -2, 2, 2))
            painter.setPen(Qt.white)
            painter.drawText(bounding_rect, Qt.AlignLeft, text)
            painter.setBrush(Qt.NoBrush)

    def board_draw_selection_mouse_rect(self, painter):
        if self.selection_rect is not None:
            c = self.selection_color
            painter.setPen(QPen(c))
            c.setAlphaF(0.5)
            brush = QBrush(c)
            painter.setBrush(brush)
            painter.drawRect(self.selection_rect)

    def board_draw_selection_transform_box(self, painter):
        self.rotation_activation_areas = []
        if self.selection_box is not None:

            painter.setOpacity(self.board_selection_transform_box_opacity)
            pen = QPen(self.selection_color, 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(self.selection_box)

            default_pen = painter.pen()

            # rotation activation areas
            painter.setPen(QPen(Qt.red))
            for index, point in enumerate(self.selection_box):
                points_count = self.selection_box.size()
                prev_point_index = (index-1) % points_count
                next_point_index = (index+1) % points_count
                prev_point = self.selection_box[prev_point_index]
                next_point = self.selection_box[next_point_index]

                a = QVector2D(point - prev_point).normalized().toPointF()
                b = QVector2D(point - next_point).normalized().toPointF()
                a *= self.STNG.transform_widget_activation_area_size*2
                b *= self.STNG.transform_widget_activation_area_size*2
                points = [
                    point,
                    point + a,
                    point + a + b,
                    point + b,
                ]
                raa = QPolygonF(points)
                if self.board_debug_transform_widget:
                    painter.drawPolygon(raa)

                self.rotation_activation_areas.append((index, raa))

            # scale activation areas
            default_pen.setWidthF(self.STNG.transform_widget_activation_area_size)
            default_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(default_pen)

            for index, point in enumerate(self.selection_box):
                painter.drawPoint(point)

            if self.board_debug_transform_widget and self.scaling_ongoing and self.scaling_pivot_point is not None:
                pivot = self.scaling_pivot_point
                pivot_vm = self.board_MapToViewport(pivot)
                x_axis = self.scaling_pivot_point_x_axis
                y_axis = self.scaling_pivot_point_y_axis

                painter.setPen(QPen(Qt.red, 4))
                painter.drawLine(
                    pivot_vm,
                    self.board_MapToViewport(pivot+x_axis)
                )
                painter.setPen(QPen(Qt.green, 4))
                painter.drawLine(
                    pivot_vm,
                    self.board_MapToViewport(pivot+y_axis)
                )
                if self.scaling_vector is not None:
                    painter.setPen(QPen(Qt.yellow, 4))
                    painter.drawLine(
                        pivot_vm,
                        self.board_MapToViewport(pivot + self.scaling_vector)
                    )

                painter.setPen(QPen(Qt.blue, 4))
                painter.drawLine(
                    pivot_vm,
                    self.board_MapToViewport(pivot + self.mapped_scaling_vector)
                )

                if self.proportional_scaling_vector is not None:
                    painter.setPen(QPen(Qt.darkGray, 4))
                    painter.drawLine(
                        self.board_MapToViewport(pivot),
                        self.board_MapToViewport(pivot + self.proportional_scaling_vector)
                    )

            painter.setOpacity(1.0)

            self.board_SCALE_selected_items_draw_monitor(painter)


    def board_draw_origin_compass(self, painter):
        curpos = self.mapFromGlobal(QCursor().pos())

        pos = self.canvas_origin

        painter.save()

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        # painter.drawLine(QPointF(pos).toPoint(), curpos)

        radius = 40
        delta = curpos - QPointF(pos).toPoint()
        radians_angle = math.atan2(delta.y(), delta.x())
        # painter.translate(curpos)
        # painter.rotate(180/3.14*radians_angle-180)
        # painter.drawLine(QPoint(0, 0), QPoint(radius-40, 0))
        # painter.resetTransform()

        ellipse_rect = QRect(0, 0, radius*2, radius*2)
        ellipse_rect.moveCenter(curpos)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(ellipse_rect)

        dist = QVector2D(pos - curpos).length()
        radius += 10
        radians_angle += math.pi
        if dist < radius:
            point = pos
        else:
            point = QPointF(curpos) + QPointF(math.cos(radians_angle)*radius, math.sin(radians_angle)*radius)

        # painter.setPen(QPen(Qt.red, 5))
        # painter.drawPoint(point)

        # text_rect_center = QPointF(curpos).toPoint() + QPoint(0, -10)
        text_rect_center = point.toPoint()

        scale_percent_x = math.ceil(self.canvas_scale_x*100)
        scale_percent_y = math.ceil(self.canvas_scale_y*100)
        text = f'{dist:.2f}\n{scale_percent_x:,}% {scale_percent_y:,}%'.replace(',', ' ')
        font = painter.font()
        font.setPixelSize(10)
        font.setWeight(1900)
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter


        text_rect = painter.boundingRect(max_rect, alignment, text)

        text_rect.moveCenter(text_rect_center)
        painter.setBrush(QBrush(QColor(10, 10, 10)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(text_rect)
        painter.setPen(QPen(Qt.red))
        painter.drawText(text_rect, alignment, text)
        painter.setBrush(Qt.NoBrush)
        painter.restore()

    def board_draw_canvas_origin(self, painter):
        painter.save()
        pos = self.canvas_origin
        pen = QPen(QColor(220, 220, 220, 200), 5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        offset = QPoint(50, 50)
        center_rect = QRect(QPointF(pos).toPoint() - offset, QPointF(pos).toPoint() + offset)
        painter.drawEllipse(center_rect)

        # offset = QPoint(10, 10)
        # rect = QRect(QPointF(pos).toPoint() - offset, QPointF(pos).toPoint() + offset)
        # painter.drawRect(rect)

        painter.drawLine(QPointF(pos).toPoint() + QPoint(0, -20), QPointF(pos).toPoint() + QPoint(0, 20))
        painter.drawLine(QPointF(pos).toPoint() + QPoint(-20, 0), QPointF(pos).toPoint() + QPoint(20, 0))

        font = painter.font()
        font.setPixelSize(30)
        font.setWeight(1900)
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter

        text = _("AXES")
        text_rect = painter.boundingRect(max_rect, alignment, text)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, -80))
        painter.drawText(text_rect, alignment, text)

        text = _("ORIGIN")
        text_rect = painter.boundingRect(max_rect, alignment, text)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, 80))
        painter.drawText(text_rect, alignment, text)
        painter.restore()

    def _get_board_bounding_rect(self, folder_data, apply_global_scale=False):
        points = []
        # points.append(self.canvas_origin) #мешает при использовании board_navigate_camera_via_minimap, поэтому убрал нафег
        if folder_data.board.items_list:
            for board_item in folder_data.board.items_list:
                rf = board_item.get_selection_area(canvas=self, apply_global_scale=apply_global_scale).boundingRect()
                points.append(rf.topLeft())
                points.append(rf.bottomRight())
            p1, p2 = get_bounding_points(points)
            result = build_valid_rectF(p1, p2)
        else:
            result = QRectF(self.rect())
        folder_data.board.bounding_rect = result
        return result

    def build_board_bounding_rect(self, folder_data, apply_global_scale=False):
        self.board_bounding_rect = self._get_board_bounding_rect(folder_data, apply_global_scale=apply_global_scale)

    def get_widget_cursor(self, source_pixmap, angle):
        pixmap = QPixmap(source_pixmap.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        transform = QTransform()
        transform1 = QTransform()
        transform2 = QTransform()
        transform3 = QTransform()
        rect = QRectF(source_pixmap.rect())
        center = rect.center()
        transform1.translate(-center.x(), -center.y())
        transform2.rotate(angle)
        transform3.translate(center.x(), center.y())
        transform = transform1 * transform2 * transform3
        painter.setTransform(transform)
        painter.drawPixmap(rect, source_pixmap, rect)
        painter.end()
        pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QCursor(pixmap)

    @functools.cache
    def get_widget_translation_cursor(self):
        pixmap = self.translate_rastr_source.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QCursor(pixmap)

    def board_cursor_setter(self):

        if False:
            pass

        elif self.autoscroll_is_cursor_activated():
           self.autoscroll_set_cursor()

        elif self.cursor_corners_buttons_and_menus():
            pass

        elif self.board_CP_cursor_handled:
            pass

        elif self.scaling_ongoing:
            if self.scale_rastr_source is not None:
                cursor = self.get_widget_cursor(self.scale_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.PointingHandCursor)
        elif self.rotation_ongoing:
            if self.rotate_rastr_source is not None:
                cursor = self.get_widget_cursor(self.rotate_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.OpenHandCursor)
        elif self.board_TextElementCursorSetterNeeded():
            self.board_TextElementCursorSetter()
        elif self.selection_box is not None:
            if self.is_over_scaling_activation_area(self.mapped_cursor_pos()):
                cursor = self.get_widget_cursor(self.scale_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)

            elif self.is_over_rotation_activation_area(self.mapped_cursor_pos()):
                cursor = self.get_widget_cursor(self.rotate_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)

            elif self.is_over_translation_activation_area(self.mapped_cursor_pos()):
                cursor = self.get_widget_translation_cursor()
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def board_navigate_camera_via_minimap(self):
        if not self.board_show_minimap:
            return
        if self.minimap_rect.contains(self.mapped_cursor_pos()):
            minimap_local_cursor_pos = self.mapped_cursor_pos() - self.minimap_rect.topLeft()
            normalized_minimap_cursor_pos = QPointF(minimap_local_cursor_pos.x()/self.minimap_rect.width(),
                                                minimap_local_cursor_pos.y()/self.minimap_rect.height())
            cf = self.LibraryData().current_folder()
            # getting viewport-mapped bounding rect
            self.build_board_bounding_rect(cf, apply_global_scale=True)
            viewport_mapped_board_bounding_rect = self.board_bounding_rect
            x = viewport_mapped_board_bounding_rect.width()*normalized_minimap_cursor_pos.x()
            y = viewport_mapped_board_bounding_rect.height()*normalized_minimap_cursor_pos.y()
            viewport_mapped_bounding_rect_cursor_top_left = QPointF(x, y)
            viewport_mapped_bounding_rect_top_left = self.board_bounding_rect.topLeft()
            new_canvas_origin = self.canvas_origin - viewport_mapped_bounding_rect_cursor_top_left - viewport_mapped_bounding_rect_top_left + self.get_center_position()
            self.canvas_origin = new_canvas_origin
            # восстанавливаем прежний bounding rect
            self.build_board_bounding_rect(cf, apply_global_scale=False)
            self.show_center_label(_("The camera has been moved"))
        else:
            self.show_center_label(_("Out of the map frame!"), error=True)
        self.update()

    def board_draw_minimap(self, painter):
        if not self.board_show_minimap:
            return

        painter.resetTransform()

        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
            painter.fillRect(self.rect(), QBrush(QColor(20, 20, 20, 220)))

            minimap_rect = self.board_bounding_rect

            self_rect = self.rect()
            self_rect.setWidth(self_rect.width()-300)
            self_rect.setHeight(self_rect.height()-100)
            minimap_rect = fit_rect_into_rect(minimap_rect.toRect(), self_rect)

            minimap_rect.moveCenter(self.get_center_position().toPoint())
            map_width = minimap_rect.width()
            map_height = minimap_rect.height()
            self.minimap_rect = minimap_rect

            # backplate
            minimap_backplate = minimap_rect.adjusted(-10, -10, 10, 10)
            painter.fillRect(minimap_backplate, QBrush(QColor(0, 0, 0, 150)))
            # gray frame
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawRect(minimap_rect)

            for board_item in cf.board.items_list:

                # крашится на item_frame-ах, потому что у них изображений нет
                # file_data = board_item.retrieve_file_data()

                delta = board_item.position - self.board_bounding_rect.topLeft()
                delta = QPointF(
                    delta.x()/self.board_bounding_rect.width(),
                    delta.y()/self.board_bounding_rect.height()
                )
                point = minimap_rect.topLeft() + QPointF(delta.x()*map_width, delta.y()*map_height)
                painter.setPen(QPen(Qt.red, 4))
                painter.drawPoint(point)


                painter.setPen(QPen(Qt.green, 1))
                selection_area = board_item.get_selection_area(canvas=self, place_center_at_origin=False, apply_global_scale=False)
                transform = QTransform()
                scale_x = map_width/self.board_bounding_rect.width()
                scale_y = map_height/self.board_bounding_rect.height()
                transform.scale(scale_x, scale_y)

                selection_area_scaled = transform.map(selection_area)
                p = point - selection_area_scaled.boundingRect().center()
                selection_area_scaled.translate(p)

                painter.drawPolygon(selection_area_scaled)

                bounding_rect_selection_area_scaled = selection_area_scaled.boundingRect()
                if bounding_rect_selection_area_scaled.contains(self.mapped_cursor_pos()):
                    text = board_item.info_text()
                    alignment = Qt.AlignCenter

                    old_pen = painter.pen()
                    text_rect = painter.boundingRect(bounding_rect_selection_area_scaled, alignment, text)
                    painter.setBrush(QBrush(Qt.white))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(text_rect)
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(text_rect, alignment, text)
                    painter.setPen(old_pen)



            # origin point
            center_point_rel = -self.board_bounding_rect.topLeft()
            center_point = QPointF(
                map_width * center_point_rel.x()/self.board_bounding_rect.width(),
                map_height * center_point_rel.y()/self.board_bounding_rect.height()
            ) + minimap_rect.topLeft()
            painter.setPen(QPen(Qt.red, 2))
            painter.drawLine(center_point+QPointF(-10, -10), center_point+QPointF(10, 10))
            painter.drawLine(center_point+QPointF(-10, 10), center_point+QPointF(10, -10))

            # viewport rect
            viewport_rect = self.rect()
            viewport_pos = -self.canvas_origin + self.get_center_position()
            tp = self.board_bounding_rect.topLeft()

            # здесь board_scale необходим для правильной передачи смещения вьюпорта
            delta = viewport_pos - QPointF(tp.x()*self.canvas_scale_x, tp.y()*self.canvas_scale_y)
            delta = QPointF(
                delta.x()/self.board_bounding_rect.width()/self.canvas_scale_x,
                delta.y()/self.board_bounding_rect.height()/self.canvas_scale_y
            )

            point = minimap_rect.topLeft() + QPointF(delta.x()*map_width, delta.y()*map_height)
            painter.setPen(QPen(Qt.yellow, 4))
            painter.drawPoint(point)

            vw = viewport_rect.width()
            vh = viewport_rect.height()
            rel_size = QPointF(
                vw/self.board_bounding_rect.width(),
                vh/self.board_bounding_rect.height()
            )
            # здесь board scale нужен для передачи мастабирования вьюпорта
            w = map_width*rel_size.x()/self.canvas_scale_x
            h = map_height*rel_size.y()/self.canvas_scale_y
            miniviewport_rect = QRectF(0, 0, w, h)
            miniviewport_rect.moveCenter(point)
            painter.setPen(QPen(Qt.yellow, 1))
            painter.drawRect(miniviewport_rect)

    def board_select_items(self, items):
        current_folder = self.LibraryData().current_folder()
        for bi in current_folder.board.items_list:
            bi._selected = False
        for item in items:
            item._selected = True
        self.prepare_selection_box_widget(current_folder)

    def board_load_highres(self):
        with self.show_longtime_process_ongoing(self, _("Loading hires images")):
            items = self.LibraryData().current_folder().board.items_list
            for bi in items:
                self.trigger_board_item_pixmap_loading(bi)

    def board_delete_selected_board_items(self):
        cf = self.LibraryData().current_folder()
        items_list = cf.board.items_list

        root_item = cf.board.root_item
        if root_item and root_item.type == BoardItem.types.ITEM_IMAGE and root_item.animated:
            self.show_center_label(_("You cannot delete items from animated file board"), error=True)
            return

        if root_item is None:
            fd = cf
        else:
            fd = cf.board.root_folder

        if self.selected_items:
            gi = self.get_removed_items_group(fd)

            # здесь решаем что удалить безвозвратно
            for bi in self.selected_items:
                if bi.type == BoardItem.types.ITEM_FRAME:
                    items_list.remove(bi)
                if bi.type == BoardItem.types.ITEM_IMAGE:
                    pass
                if bi.type == BoardItem.types.ITEM_GROUP:
                    if bi.board_group_index > 9:
                        self.move_items_to_group(
                            item_group=gi,
                            items=bi.item_folder_data.board.items_list,
                            items_folder=bi.item_folder_data
                        )
                        items_list.remove(bi)
                if bi.type == BoardItem.types.ITEM_NODE:
                    self.board_delete_nonlink_item_info(bi, cf=cf)
                    items_list.remove(bi)

            self.move_items_to_group(item_group=gi, items=self.selected_items)



        for li in fd.board.link_items_list[:]:
            if li._selected:
                self.board_delete_link_item(li, cf=cf)

        self.prepare_selection_box_widget(cf)

        self.update()

    def get_removed_items_group(self, folder_data):
        for bi in folder_data.board.items_list:
            if bi.board_group_index == 0:
                return bi

        item_folder_data = self.LibraryData().create_folder_data(_("GROUP Virtual Folder"), [], image_filepath=None, make_current=False, virtual=True)
        gi = BoardItem(BoardItem.types.ITEM_GROUP)

        gi.item_folder_data = item_folder_data
        gi.board_index = self.retrieve_new_board_item_index()
        gi.board_group_index = 0 # index reserved for group of removed items
        folder_data.board.items_list.append(gi)
        item_folder_data.previews_done = True
        item_folder_data.board.ready = True
        item_folder_data.board.root_folder = folder_data
        item_folder_data.board.root_item = gi
        gi.position = - QPointF(gi.width, gi.height)/2.0

        gi.update_corner_info()

        return gi

    def board_retrieve_current_from_group_item(self):
        gi = self.is_context_menu_executed_over_group_item()
        current_folder = self.LibraryData().current_folder()
        current_board = current_folder.board
        if len(gi.item_folder_data.board.items_list) == 0:
            self.show_center_label(_("Nothing to delete, the group is empty"), error=True)
            return

        if gi is not None:
            item_folder_data = gi.item_folder_data
            im_data = self.LibraryData().delete_current_image(item_folder_data, force=True)
            bi = im_data.board_items[0]
            item_folder_data.board.items_list.remove(bi)

            current_board.items_list.append(bi)
            bi.file_data.folder_data = current_folder
            current_folder.images_list.append(im_data)

            pos = self.board_MapToBoard(gi.get_selection_area(canvas=self).boundingRect().topRight())
            size_rect = bi.get_size_rect(scaled=False)
            offset = QPointF(size_rect.width()/2, size_rect.height()/2)
            bi.position = (pos + offset)
            bi._selected = False

            gi.update_corner_info()
            gi.pixmap = None
        else:
            self.show_center_label(_("Group-item not found"), error=True)
        self.update()

    def board_add_item_group_noargs(self):
        # !!! если засунуть board_add_item_group в connect,
        # то значение move_selection_to_group будет равно позиционному аргументу, который будет передан при вызове,
        # и важно этого избежать, поэтому действуем через прокладку board_add_item_group_noargs
        self.board_add_item_group()

    def board_add_item_group(self, move_selection_to_group=True, virtual_allowed=False, item_position=None):
        current_folder_data = self.LibraryData().current_folder()
        if not virtual_allowed and current_folder_data.virtual:
            self.show_center_label(_("You cannot create group-item inside virtual folder board"), error=True)
            return
        item_folder_data = self.LibraryData().create_folder_data(_("GROUP Virtual Folder"), [], image_filepath=None, make_current=False, virtual=True)
        gi = BoardItem(BoardItem.types.ITEM_GROUP)
        gi.item_folder_data = item_folder_data
        gi.board_index = self.retrieve_new_board_item_index()
        gi.board_group_index = self.retrieve_new_board_item_group_index()
        current_folder_data.board.items_list.append(gi)
        item_folder_data.previews_done = True
        item_folder_data.board.ready = True
        item_folder_data.board.root_folder = current_folder_data
        item_folder_data.board.root_item = gi
        # располагаем центр в координате вызова контекстеного меню
        if item_position is None:
            gi.position = self.board_MapToBoard(self.rect().center())
        else:
            gi.position = item_position
        if move_selection_to_group and self.board_selected_items_count() > 0:
            self.move_items_to_group(item_group=gi, items=self.selected_items)
        gi.update_corner_info()
        self.board_select_items([gi])
        self.update()
        return gi

    def board_add_item_note(self):
        current_folder_data = self.LibraryData().current_folder()
        if current_folder_data.virtual:
            self.show_center_label(_("You cannot create note-item inside virtual folder board"), error=True)
            return
        ni = BoardItem(BoardItem.types.ITEM_NOTE)
        ni.board_index = self.retrieve_new_board_item_index()
        current_folder_data.board.items_list.append(ni)
        ni.position = self.board_MapToBoard(self.rect().center())
        self.board_TextElementAttributesInitOnCreation(ni)
        self.board_select_items([ni])
        self.update()

    def board_add_item_folder(self, folder_path=None):
        if folder_path is None:
            folder_path = QFileDialog.getExistingDirectory(None, _("Choose folder with images in it"), '.')
        if folder_path:
            with self.show_longtime_process_ongoing(self, _("Loading folder to the board")):
                files = self.LibraryData().list_interest_files(folder_path, deep_scan=False, all_allowed=False)
                item_folder_data = self.LibraryData().create_folder_data(folder_path, files, image_filepath=None, make_current=False)
                self.LibraryData().make_thumbnails_and_previews(item_folder_data, None, do_progressive_grid_layout=True, do_progressive_board_layout=True)
                fi = BoardItem(BoardItem.types.ITEM_FOLDER)
                fi.item_folder_data = item_folder_data
                fi.board_index = self.retrieve_new_board_item_index()
                _fd = self.LibraryData().current_folder()
                _fd.board.items_list.append(fi)
                # располагаем в центре экрана
                fi.position = self.board_MapToBoard(self.rect().center())
                fi.update_corner_info()
                self.board_select_items([fi])
                self.update()

    def move_items_to_group(self, item_group=None, items=None, items_folder=None):
        if items_folder is None:
            items_folder = self.LibraryData().current_folder()
            default = True
        else:
            default = False
        if self.item_group_under_mouse is not None:
            group_item = self.item_group_under_mouse
            update_selection = True
        elif item_group is not None:
            group_item = item_group
            update_selection = False
        else:
            return

        item_fd = group_item.item_folder_data
        group_board_item_list = item_fd.board.items_list

        board_item_list = items_folder.board.items_list

        if group_board_item_list:
            item_board_bb = self._get_board_bounding_rect(item_fd)
        else:
            item_board_bb = QRectF()

        topLeftCorner = item_board_bb.topRight()

        for bi in items[:]:

            if bi.type is bi.types.ITEM_GROUP:
                continue
            if bi.type is bi.types.ITEM_FRAME:
                continue
            if bi in board_item_list:
                board_item_list.remove(bi)
            else:
                # значит элемент был перемещён или удалён ранее и нам не надо его обрабатывать здесь
                continue
            group_board_item_list.append(bi)
            if bi.type is bi.types.ITEM_IMAGE:
                # items_folder.images_list.remove(bi.file_data)
                item_fd.images_list.append(bi.file_data)
                bi.file_data.folder_data = item_fd

            rect = bi.get_size_rect(scaled=True)
            width = rect.width()
            height = rect.height()
            bi.position = topLeftCorner + QPointF(width, height)/2
            topLeftCorner += QPointF(width, 0)

        group_item.update_corner_info()
        if update_selection:
            self.board_select_items([group_item])

    def board_add_item_frame(self):
        if self.selection_box is None:
            self.show_center_label(_("No items selected!"), error=True)
        else:
            folder_data = self.LibraryData().current_folder()
            bi = BoardItem(BoardItem.types.ITEM_FRAME)
            bi.board_index = self.retrieve_new_board_item_index()
            folder_data.board.items_list.append(bi)

            selection_bounding_rect = self.selection_box.boundingRect()
            bi.position = self.board_MapToBoard(selection_bounding_rect.center())
            bi.width = selection_bounding_rect.width() / self.canvas_scale_x
            bi.height = selection_bounding_rect.height() / self.canvas_scale_y
            bi.width += BoardItem.FRAME_PADDING
            bi.height += BoardItem.FRAME_PADDING
            bi.label = _("FRAME ITEM")
            self.board_select_items([bi])

        self.update()

    def board_invoke_create_node_item(self, viewport_pos=None):
        self.modal_input_field_show(self.board_create_node_item, _('Node label'))
        self.board_invoke_pos = viewport_pos

    def board_delete_link_item(self, item, cf=None):
        cf = cf or self.LibraryData().current_folder()
        links = cf.board.link_items_list
        if item in links:
            links.remove(item)
        item._slot.remove(item)
        item.from_item = None
        item.to_item = None

    def board_delete_nonlink_item_info(self, item, cf=None):
        cf = cf or self.LibraryData().current_folder()
        links = cf.board.link_items_list
        for link in links[:]:
            if (link.from_item is item) or (link.to_item is item):
                self.board_delete_link_item(link)

    def board_invoke_create_link_item(self):
        cf = self.LibraryData().current_folder()
        item = self.find_min_area_item(cf, self.mapped_cursor_pos())
        if item:
            if item in self.item_magazin:
                self.item_magazin.remove(item)
                self.show_center_label(_('This item was removed to stack'))
            else:
                self.item_magazin.append(item)
                self.show_center_label(_('This item was added to stack'))
            if len(self.item_magazin) == 2:
                self.board_create_link_item(*self.item_magazin)
                self.item_magazin.clear()

    def board_toggle_directional_notd_for_links(self):
        fd = self.LibraryData().current_folder()
        for bli in fd.board.link_items_list:
            if bli._selected:
                bli.is_directional = not bli.is_directional

    def board_toggle_links_direction(self):
        fd = self.LibraryData().current_folder()
        for bli in fd.board.link_items_list:
            if bli._selected:
                bli.to_item, bli.from_item = bli.from_item, bli.to_item

    def board_change_links_draw_order(self):
        self.links_draw_before_items = not self.links_draw_before_items

    def board_create_node_item(self):
        cf = self.LibraryData().current_folder()
        bi = BoardItem(BoardItem.types.ITEM_NODE)
        bi.board_index = self.retrieve_new_board_item_index()
        cf.board.items_list.append(bi)
        bi.label = self.modal_input_field_text()
        bi.width = BoardItem.NODE_SIZE
        bi.height = BoardItem.NODE_SIZE
        if self.board_invoke_pos:
            pos = self.board_MapToBoard(self.board_invoke_pos)
            self.board_invoke_pos = None
        else:
            pos = self.board_MapToBoard(self.rect().center())
        bi.position = pos
        self.build_board_bounding_rect(cf)
        # self.board_select_items([bi])

    def board_add_link_to_slot(self, folder_data, li):
        indexes = (li.from_item.board_index, li.to_item.board_index)
        ordered_indexes_key = (min(indexes), max(indexes))
        link_slot = folder_data.board._link_slots_list[ordered_indexes_key]
        link_slot.append(li)
        li._slot = link_slot

    def board_create_link_item(self, from_item, to_item):
        cf = self.LibraryData().current_folder()
        # creating link
        li = BoardItem(BoardItem.types.ITEM_LINK)
        li.from_item = from_item
        li.to_item = to_item
        cf.board.link_items_list.append(li)
        # add to slot
        self.board_add_link_to_slot(cf, li)
        self.update()

    def board_change_node_radius(self, event, scroll_value):
        cf = self.LibraryData().current_folder()
        cursor_pos = event.pos()
        items = self.find_all_items_under_this_pos(cf, cursor_pos)
        for bli in items:
            if bli.type == BoardItem.types.ITEM_NODE:
                break
        else:
            return False
        if scroll_value > 0:
            bli.scale_x *= 1.1
        else:
            bli.scale_x /= 1.1
        bli.scale_y = bli.scale_x = max(1.0, bli.scale_x)
        self.update()
        self.board_update_selection_box_widget()
        return True

    def board_change_link_width(self, event, scroll_value):
        cf = self.LibraryData().current_folder()
        cursor_pos = event.pos()
        for bli in cf.board.link_items_list:
            if bli.is_near_link(self, cursor_pos):
                break
        else:
            return False
        if scroll_value > 0:
            bli.link_width += 1.0
        else:
            bli.link_width -= 1.0
        bli.link_width = max(1.0, bli.link_width)
        self.update()
        return True

    def isLeftClickAndNoModifiers(self, event):
        return event.buttons() == Qt.LeftButton and event.modifiers() == Qt.NoModifier

    def isLeftClickAndAlt(self, event):
        return (event.buttons() == Qt.LeftButton or event.button() == Qt.LeftButton) and event.modifiers() == Qt.AltModifier

    def is_pos_over_item_area(self, item, position):
        sa = item.get_selection_area(canvas=self)
        return sa.containsPoint(position, Qt.WindingFill) or \
                (item.type == BoardItem.types.ITEM_FRAME and item._label_ui_rect is not None and item._label_ui_rect.contains(position))

    def is_over_translation_activation_area(self, position):
        for item in self.selected_items:
            if self.is_pos_over_item_area(item, position):
                return True
        return False

    def board_START_selected_items_TRANSLATION(self, event_pos):
        self.start_translation_pos = QPointF(self.board_MapToBoard(event_pos))
        current_folder = self.LibraryData().current_folder()
        items_list = current_folder.board.items_list

        for board_item in items_list:
            board_item._position = QPointF(board_item.position)
            self.board_stash_current_transform_to_history(board_item)
            board_item._position_init = QPointF(board_item.position)
            board_item._children_items = []
            if board_item.type == BoardItem.types.ITEM_FRAME:
                this_frame_area = board_item.calc_area
                item_frame_area = board_item.get_selection_area(canvas=self)
                for bi in current_folder.board.items_list[:]:
                    bi_area = bi.get_selection_area(canvas=self)
                    center_point = bi_area.boundingRect().center()
                    if item_frame_area.containsPoint(QPointF(center_point), Qt.WindingFill):
                        if bi.type != BoardItem.types.ITEM_FRAME or (bi.type == BoardItem.types.ITEM_FRAME and bi.calc_area < this_frame_area):
                            board_item._children_items.append(bi)

    def board_ALLOW_selected_items_TRANSLATION(self, event_pos):
        if self.start_translation_pos:
            delta = QPointF(self.board_MapToBoard(event_pos)) - self.start_translation_pos
            if not self.translation_ongoing:
                if abs(delta.x()) > 0 or abs(delta.y()) > 0:
                    self.translation_ongoing = True

    def board_DO_selected_items_TRANSLATION(self, event_pos):
        if self.start_translation_pos:
            current_folder = self.LibraryData().current_folder()
            cursor_pos = self.board_items_snapping(QPointF(self.board_MapToBoard(event_pos)))
            delta = cursor_pos - self.start_translation_pos
            if self.translation_ongoing:
                for board_item in current_folder.board.items_list:
                    if board_item._selected:
                        board_item.position = board_item._position + delta
                        if board_item.type == BoardItem.types.ITEM_FRAME:
                            for ch_bi in board_item._children_items:
                                ch_bi.position = ch_bi._position + delta
                self.prepare_selection_box_widget(current_folder)
                self.check_item_group_under_mouse()
                self.autoscroll_activate_board_item_transform_autoscroll()
        else:
            self.translation_ongoing = False

    def board_FINISH_selected_items_TRANSLATION(self, event, cancel=False):
        self.start_translation_pos = None
        current_folder = self.LibraryData().current_folder()
        for board_item in current_folder.board.items_list:
            if cancel:
                board_item.position = QPointF(board_item._position_init)
            else:
                board_item._position = None
            board_item._children_items = []
        self.translation_ongoing = False
        if cancel:
            pass
        else:
            self.build_board_bounding_rect(current_folder)
            self.move_items_to_group(items=self.selected_items)
            self.check_item_group_under_mouse(reset=True)
        self.autoscroll_desactivate_board_item_transform_autoscroll()
        self.board_items_snapping_finish()

    def board_CANCEL_selected_items_TRANSLATION(self):
        if self.translation_ongoing:
            self.board_FINISH_selected_items_TRANSLATION(None, cancel=True)
            self.board_update_selection_box_widget()
            self.transform_cancelled = True
            print('cancel translation')

    def board_draw_snapping_targets(self, painter):
        if self.STNG.board_items_snapping:
            painter.save()
            for target in self.SNAPPING.targets:
                if target.type == target.types.POINT and not self.SNAPPING.show_point_targets:
                    continue
                target.draw(self, painter)

            for anchor in self.SNAPPING.anchors:
                anchor.draw(self, painter)
            painter.restore()

    def board_snapping_init(self):
        self.SNAPPING = SNAPPING = type('SnappingData', (), {})()
        SNAPPING.targets = list()
        SNAPPING.anchors = list()
        SNAPPING.show_point_targets = False

    def board_items_snapping_finish(self):
        if self.STNG.board_items_snapping:
            self.show_center_label('snapping finished')
            self.SNAPPING.targets.clear()
            self.SNAPPING.anchors.clear()

    def board_items_snapping(self, board_mapped_cursor_pos):
        cursor_pos = board_mapped_cursor_pos

        if not self.STNG.board_items_snapping:
            return board_mapped_cursor_pos

        if not self.selected_items:
            self.show_center_label('skipping', error=True)
            # ситуация возникает, если начинаешь тащить айтем, который не был выделен перед этим
            # на самом деле это плохо, надо исправлять эти баги, но пока тут побудет костыль
            # (24 мар 26) TODO: избавиться от этого костыля
            return cursor_pos

        class SnapAnchor():
            def __init__(self, item, offset, place):
                self.offset = offset
                self.snapped = False
                self.cursor_pos = None
                self.place = place
                self.item = item

            def draw(self, canvas, painter):
                point = self.place + self.offset
                point = canvas.board_MapToViewport(point)
                painter.setPen(QPen(Qt.white, 20))
                # painter.drawPoint(point)
                painter.drawText(point, 'A')

        self.board_snapping_set_targets()

        item = self.selected_items[0]
        if (not self.SNAPPING.anchors) or (self.SNAPPING.anchors[0].item is not item):
            sa = item.get_selection_area(canvas=self, apply_global_scale=False)
            sa_br = sa.boundingRect()
            center = sa_br.center()
            self.SNAPPING.anchors = [
                SnapAnchor(item, sa_br.bottomLeft() - center, center),
                SnapAnchor(item, sa_br.topLeft() - center, center),
                SnapAnchor(item, QPointF(0, 0), center), # позиция этого якоря влияет на срабатывание его самого и других якорей
                SnapAnchor(item, sa_br.bottomRight() - center, center),
                SnapAnchor(item, sa_br.topRight() - center, center),
                SnapAnchor(item, sa[0] - center, center),
                SnapAnchor(item, sa[1] - center, center),
                SnapAnchor(item, sa[2] - center, center),
                SnapAnchor(item, sa[3] - center, center),
            ]
            # self.show_center_label(f'updating anchors for {item}')

        ACTIVATION_RADIUS = 100.0

        for st in self.SNAPPING.targets:
            for snap_anchor in self.SNAPPING.anchors:
                snap_offset = snap_anchor.offset
                dist = QVector2D(st.point(snap_offset + item.position) - (snap_offset + item.position))
                snap_dist = self.board_snapping_map_dist_to_viewport(dist).length()
                if snap_dist < ACTIVATION_RADIUS:
                    if snap_anchor.snapped and st.get_deactivation_length(snap_anchor.cursor_pos, cursor_pos) > (ACTIVATION_RADIUS+20):
                        snap_anchor.snapped = False
                        snap_anchor.cursor_pos = None
                        return cursor_pos
                    offset = QPointF(item._position) + snap_offset
                    result = self.start_translation_pos - offset + st.point(cursor_pos)
                    if snap_anchor.cursor_pos is None:
                        snap_anchor.snapped = True
                        snap_anchor.cursor_pos = QPointF(cursor_pos)
                        snap_anchor.st = st
                    return result
        return cursor_pos

    def board_snapping_map_dist_to_viewport(self, dist_vector):
        return dist_vector * QVector2D(self.canvas_scale_x, self.canvas_scale_y)

    def board_snapping_set_targets(self):
        # self.SNAPPING.targets.clear()

        canvas_self = self

        class SnappingTarget():
            class types():
                UNDEFINED = 0
                POINT = 1
                LINE = 2

            def __init__(self, x_snapping, y_snapping):
                self.x_snapping = x_snapping
                self.y_snapping = y_snapping
                self.type = -1

                nones = [self.x_snapping, self.y_snapping].count(None)
                if nones == 2:
                    self.type = SnappingTarget.types.UNDEFINED
                elif nones == 1:
                    self.type = SnappingTarget.types.LINE
                elif nones == 0:
                    self.type = SnappingTarget.types.POINT

            def point(self, cp):
                if self.type == SnappingTarget.types.POINT:
                    return QPointF(self.x_snapping, self.y_snapping)
                elif self.type == SnappingTarget.types.LINE:
                    if self.x_snapping is None:
                        return QPointF(cp.x(), self.y_snapping)
                    elif self.y_snapping is None:
                        return QPointF(self.x_snapping, cp.y())

            def draw(self, canvas, painter):
                if self.type == SnappingTarget.types.UNDEFINED:
                    pass

                elif self.type == SnappingTarget.types.POINT:
                    painter.setPen(QPen(Qt.red, 1, Qt.DashLine))
                    pos = canvas.board_MapToViewport(QPointF(self.x_snapping, self.y_snapping))
                    vertical = QPointF(0, 100)
                    horizontal = QPointF(100, 0)
                    painter.drawLine(pos - vertical, pos + vertical)
                    painter.drawLine(pos - horizontal, pos + horizontal)
                    rect = QRectF(0, 0, 25, 25)
                    rect.moveCenter(pos)
                    painter.drawRect(rect)

                elif self.type == SnappingTarget.types.LINE:
                    painter.setPen(QPen(QColor(220, 100, 100, 50), 1, Qt.DashLine))
                    if self.x_snapping is None:
                        x = 0
                        y = self.y_snapping
                    elif self.y_snapping is None:
                        x = self.x_snapping
                        y = 0
                    pos = canvas.board_MapToViewport(QPointF(x, y))
                    canvas_rect = canvas.rect()
                    if self.x_snapping is None:
                        pos_y = pos.y()
                        painter.drawLine(QPointF(0, pos_y), QPointF(canvas_rect.width(), pos_y))
                    elif self.y_snapping is None:
                        pos_x = pos.x()
                        painter.drawLine(QPointF(pos_x, 0), QPointF(pos_x, canvas_rect.height()))

            def get_deactivation_length(self, snap_pos, cursor_pos):
                dist = QVector2D()
                if self.type == SnappingTarget.types.POINT:
                    dist = QVector2D(snap_pos - cursor_pos)
                elif self.type == SnappingTarget.types.LINE:
                    if self.x_snapping is None:
                        dist = QVector2D(QPointF(0, snap_pos.y()) - QPointF(0, cursor_pos.y()))
                    elif self.y_snapping is None:
                        dist = QVector2D(QPointF(snap_pos.x(), 0) - QPointF(cursor_pos.x(), 0))
                return canvas_self.board_snapping_map_dist_to_viewport(dist).length()

        if not self.SNAPPING.targets:
            if False:
                self.SNAPPING.targets = [
                    # SnappingTarget(0.0, 0.0),
                    SnappingTarget(0.0, 500.0),
                    # SnappingTarget(100.0, 0.0),
                    SnappingTarget(100.0, None),
                    SnappingTarget(None, 500.0),
                ]
            else:
                cf = self.LibraryData().current_folder()
                viewport_rect = self.rect()
                board_mapped_viewport_rect = self.board_MapRectToBoard(viewport_rect).toRect()
                def append(*args):
                    self.SNAPPING.targets.append(SnappingTarget(*args))
                self.SNAPPING.targets = []
                for bi in cf.board.items_list:
                    if bi not in self.selected_items:
                        sa = bi.get_selection_area(canvas=self, apply_global_scale=False)
                        sa_br = sa.boundingRect().toRect()
                        if sa_br.intersects(board_mapped_viewport_rect):
                            # TODO: (24 мар 26) лейаут создаётся так,
                            # что айтемы прилегают вплотную друг к другу,
                            # поэтому для одной и той же позициии может быть два таргета,
                            # и значит, надо как-то удалять дубликаты,
                            # Можно было бы воспользоваться свойстом лэйаута и брать только левые две точки
                            # у каждого айтема, и не брать превые две точки, но у них у всех разный размер,
                            # да и их могут переместить и это свойство уже не будет работать.
                            append(None, sa_br.top())
                            append(None, sa_br.bottom())
                            append(sa_br.left(), None)
                            append(sa_br.right(), None)

                            append(sa_br.left(), sa_br.top())
                            append(sa_br.left(), sa_br.bottom())
                            append(sa_br.right(), sa_br.top())
                            append(sa_br.right(), sa_br.bottom())

    def is_context_menu_executed_over_group_item(self):
        self.check_item_group_under_mouse(use_context_menu_exec_point=True)
        group_item = self.item_group_under_mouse
        self.check_item_group_under_mouse(reset=True)
        return group_item

    def check_item_group_under_mouse(self, reset=False, use_context_menu_exec_point=False):
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False
        if reset:
            return
        self.group_inside_selection_items = any(bi.type == BoardItem.types.ITEM_GROUP for bi in self.selected_items)

        if use_context_menu_exec_point:
            pos = self.context_menu_exec_point
        else:
            pos = self.mapped_cursor_pos()
        if not self.group_inside_selection_items or use_context_menu_exec_point:
            cf = self.LibraryData().current_folder()
            for bi in cf.board.items_list:
                if bi.type is BoardItem.types.ITEM_GROUP:
                    item_selection_area = bi.get_selection_area(canvas=self)
                    is_under_mouse = item_selection_area.containsPoint(pos, Qt.WindingFill)
                    if is_under_mouse:
                        self.item_group_under_mouse = bi
                        break

    def any_item_area_under_mouse(self, add_selection):
        self.prevent_item_deselection = False
        current_folder = self.LibraryData().current_folder()
        if self.is_flyover_ongoing():
            return False
        min_item = self.find_min_area_item(current_folder, self.mapped_cursor_pos())
        # reversed для того, чтобы картинки на переднем плане чекались первыми
        pos = self.mapped_cursor_pos()
        for board_item in reversed(current_folder.board.items_list):
            item_selection_area = board_item.get_selection_area(canvas=self)
            # is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
            is_under_mouse = self.is_pos_over_item_area(board_item, pos)

            if is_under_mouse and not board_item._selected:
                if board_item.type == BoardItem.types.ITEM_FRAME:
                    if min_item is not board_item:
                        continue

                if not add_selection:
                    for bi in current_folder.board.items_list:
                        bi._selected = False

                board_item._selected = True
                self.active_element = board_item
                # вытаскиваем айтем на передний план при отрисовке
                current_folder.board.items_list.remove(board_item)
                current_folder.board.items_list.append(board_item)
                self.prevent_item_deselection = True
                return True
            if is_under_mouse and board_item._selected:
                self.active_element = board_item
                return True
        return False

    def find_min_area_item(self, folder_data, pos):
        found_items = self.find_all_items_under_this_pos(folder_data, pos)
        if found_items:
            return min(found_items, key=lambda x: x.calc_area)
        else:
            return None

    def find_all_items_under_this_pos(self, folder_data, pos):
        undermouse_items = []
        for board_item in folder_data.board.items_list:
            item_selection_area = board_item.get_selection_area(canvas=self)
            # is_under_mouse = item_selection_area.containsPoint(pos, Qt.WindingFill)
            is_under_mouse = self.is_pos_over_item_area(board_item, pos)
            if is_under_mouse:
                undermouse_items.append(board_item)
        return undermouse_items

    def board_selection_callback(self, add_to_selection):
        # (27 мар 26) выделениями также занимается функция any_item_area_under_mouse
        if self.is_flyover_ongoing():
            return
        current_folder = self.LibraryData().current_folder()
        if self.selection_rect is not None:
            selection_rect_area = QPolygonF(self.selection_rect)
            for board_item in current_folder.board.items_list:
                item_selection_area = board_item.get_selection_area(canvas=self)
                if item_selection_area.intersects(selection_rect_area):
                    board_item._selected = True
                else:
                    if add_to_selection and board_item._selected:
                        pass
                    else:
                        board_item._selected = False
        else:
            min_item = self.find_min_area_item(current_folder, self.mapped_cursor_pos())
            # reversed для того, чтобы картинки на переднем плане чекались первыми
            pos = self.mapped_cursor_pos()
            for board_item in reversed(current_folder.board.items_list):
                item_selection_area = board_item.get_selection_area(canvas=self)
                # is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                is_under_mouse = self.is_pos_over_item_area(board_item, pos)
                if add_to_selection and board_item._selected:
                    # subtract item from selection!
                    if is_under_mouse and not self.prevent_item_deselection:
                        board_item._selected = False
                else:
                    if min_item is not board_item:
                        board_item._selected = False
                    else:
                        board_item._selected = is_under_mouse
        self.prepare_selection_box_widget(current_folder)

    def prepare_selection_box_widget(self, folder_data):
        self.selected_items = []
        for board_item in folder_data.board.items_list:
            if board_item._selected:
                self.selected_items.append(board_item)
        self.board_update_selection_box_widget()

    def board_unselect_all_items(self):
        cf = self.LibraryData().current_folder()
        for board_item in cf.board.items_list:
            board_item._selected = False
        self.prepare_selection_box_widget(cf)

    def board_select_all_items(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.items_list:
            bi._selected = True
        self.update()

    def board_update_selection_box_widget(self, transformation_ongoing=False, debug_mw=None):
        self.selection_box = None
        if len(self.selected_items) == 1:
            if self.selected_items[0].type != BoardItem.types.ITEM_NODE:
                self.selection_box = self.selected_items[0].get_selection_area(canvas=self, transformation_ongoing=transformation_ongoing, debug_mw=debug_mw)
        elif len(self.selected_items) > 1:
            bounding_box = QRectF()
            for board_item in self.selected_items:
                bounding_box = bounding_box.united(
                    board_item.get_selection_area(canvas=self,
                        transformation_ongoing=transformation_ongoing,
                        debug_mw=debug_mw).boundingRect()
                )
            self.selection_box = QPolygonF([
                bounding_box.topLeft(),
                bounding_box.topRight(),
                bounding_box.bottomRight(),
                bounding_box.bottomLeft(),
            ])

    def is_over_rotation_activation_area(self, position):
        for index, raa in self.rotation_activation_areas:
            if raa.containsPoint(position, Qt.WindingFill):
                self.widget_active_point_index = index
                return True
        self.widget_active_point_index = None
        return False

    def board_START_selected_items_ROTATION(self, event_pos):
        self.rotation_ongoing = True
        mtb = self.board_MapToBoard

        self.__selection_box = QPolygonF(self.selection_box)
        pivot = mtb(self.selection_box.boundingRect().center())
        radius_vector = mtb(QPointF(event_pos)) - pivot
        self.rotation_start_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())

        points_count = self.selection_box.size()
        index = self.widget_active_point_index
        pivot_point_index = (index+2) % points_count
        self.rotation_pivot_index = pivot_point_index

        self.rotation_pivot_corner_pos = mtb(QPointF(self.__selection_box[self.rotation_pivot_index]))
        self.rotation_pivot_center_pos = mtb(self.__selection_box.boundingRect().center())

        for bi in self.selected_items:
            bi._rotation = bi.rotation
            bi._position = QPointF(bi.position)
            self.board_stash_current_transform_to_history(bi)

            bi._rotation_init = bi.rotation
            bi._position_init = QPointF(bi.position)

    def step_rotation(self, rotation_value):
        interval = 45.0
        # формулу подбирал в графическом калькуляторе desmos.com/calculator
        # value = math.floor((rotation_value-interval/2.0)/interval)*interval+interval
        # ниже упрощённый вариант
        value = (math.floor(rotation_value/interval-0.5)+1.0)*interval
        return value

    def board_DO_selected_items_ROTATION(self, event_pos):
        self.start_translation_pos = None
        mtb = self.board_MapToBoard

        multi_item_mode = len(self.selected_items) > 1
        ctrl_mod = QApplication.queryKeyboardModifiers() & Qt.ControlModifier
        alt_mod = QApplication.queryKeyboardModifiers() & Qt.AltModifier
        use_corner_pivot = alt_mod
        if use_corner_pivot:
            pivot = self.rotation_pivot_corner_pos
        else:
            pivot = self.rotation_pivot_center_pos
        radius_vector = mtb(QPointF(event_pos)) - pivot

        # self.show_center_label(f'{radius_vector}')

        self.rotation_end_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())
        self.rotation_delta = self.rotation_end_angle_rad - self.rotation_start_angle_rad
        rotation_delta_degrees = math.degrees(self.rotation_delta)
        rotation = QTransform()
        if ctrl_mod:
            rotation_delta_degrees = self.step_rotation(rotation_delta_degrees)
        rotation.rotate(rotation_delta_degrees)

        for bi in self.selected_items:
            # rotation component
            if bi.type == BoardItem.types.ITEM_FRAME:
                continue
            bi.rotation = bi._rotation + rotation_delta_degrees
            if not multi_item_mode and ctrl_mod:
                bi.rotation = self.step_rotation(bi.rotation)
            # position component
            pos_radius_vector = bi._position - pivot
            pos_radius_vector = rotation.map(pos_radius_vector)
            bi.position = pivot + pos_radius_vector

        # bounding box transformation
        self.mtb_rotation_pivot = pivot
        self.rotation_transform = rotation
        self.board_DO_selection_box_ROTATION()
        self.autoscroll_activate_board_item_transform_autoscroll()

    def board_DO_selection_box_ROTATION(self):
        debug_mw = self
        debug_mw = None
        if len(self.selected_items) == 1:
            self.board_update_selection_box_widget(transformation_ongoing=True, debug_mw=debug_mw)
        else:
            self.board_update_selection_box_widget(transformation_ongoing=True, debug_mw=debug_mw)
        translate_to_coord_origin = QTransform()
        translate_back_to_place = QTransform()

        offset = self.board_MapToViewport(self.mtb_rotation_pivot)
        translate_to_coord_origin.translate(-offset.x(), -offset.y())
        translate_back_to_place.translate(offset.x(), offset.y())
        transform = translate_to_coord_origin * self.rotation_transform * translate_back_to_place
        self.selection_box = transform.map(self.selection_box)

    def board_FINISH_selected_items_ROTATION(self, event, cancel=False):
        self.rotation_ongoing = False
        cf = self.LibraryData().current_folder()
        if cancel:
            for bi in self.selected_items:
                bi.rotation = bi._rotation_init
                bi.position = QPointF(bi._position_init)
        else:
            self.prepare_selection_box_widget(cf)
            self.build_board_bounding_rect(cf)
        self.autoscroll_desactivate_board_item_transform_autoscroll()

    def board_CANCEL_selected_items_ROTATION(self):
        if self.rotation_ongoing:
            self.board_FINISH_selected_items_ROTATION(None, cancel=True)
            self.board_update_selection_box_widget()
            self.transform_cancelled = True
            print('cancel rotation')

    def is_over_scaling_activation_area(self, position):
        if self.selection_box is not None:
            enumerated = list(enumerate(self.selection_box))
            enumerated.insert(0, enumerated.pop(2))
            for index, point in enumerated:
                diff = point - QPointF(position)
                if QVector2D(diff).length() < self.STNG.transform_widget_activation_area_size:
                    self.scaling_active_point_index = index
                    self.widget_active_point_index = index
                    return True
        self.scaling_active_point_index = None
        self.widget_active_point_index = None
        return False

    def board_get_cursor_angle(self):
        x_axis, y_axis, pivot_point = self.board_SCALING_pivot_data(self.widget_active_point_index)

        x_axis = QVector2D(x_axis).normalized().toPointF()
        y_axis = QVector2D(y_axis).normalized().toPointF()

        __vector  = x_axis + y_axis
        return math.degrees(math.atan2(__vector.y(), __vector.x()))

    def board_SCALING_pivot_data(self, index, map_to_board=False):
        points_count = self.selection_box.size()

        pivot_point_index = (index+2) % points_count
        prev_point_index = (pivot_point_index-1) % points_count
        next_point_index = (pivot_point_index+1) % points_count
        prev_point = QPointF(self.selection_box[prev_point_index])
        next_point = QPointF(self.selection_box[next_point_index])
        pivot_point = QPointF(self.selection_box[pivot_point_index])

        if map_to_board:
            prev_point = self.board_MapToBoard(prev_point)
            next_point = self.board_MapToBoard(next_point)
            pivot_point = self.board_MapToBoard(pivot_point)

        x_axis = next_point - pivot_point
        y_axis = prev_point - pivot_point

        return x_axis, y_axis, pivot_point

    def board_START_selected_items_SCALING(self, event):
        self.scaling_ongoing = True

        bbw = self.selection_box.boundingRect().width()
        bbh = self.selection_box.boundingRect().height()
        self.selection_box_aspect_ratio = bbw/bbh

        points_count = self.selection_box.size()

        if True:
            # заранее высчитываем пивот и оси для скейла относительно центра выделения (включается модификатором Alt);
            # для удобства вычислений заимствуем оси у нулевой точки и укорачиваем их в два раза
            index = 0
            __x_axis, __y_axis, pivot_point = self.board_SCALING_pivot_data(index, map_to_board=True)
            self.scaling_pivot_CENTER_point = self.board_MapToBoard(self.selection_box.boundingRect().center())

            self.scaling_from_center_x_axis = __x_axis/2.0
            self.scaling_from_center_y_axis = __y_axis/2.0

        if True:
            # высчитываем пивот и оси для обычного скейла относительно угла
            x_axis, y_axis, self.scaling_pivot_CORNER_point = self.board_SCALING_pivot_data(self.scaling_active_point_index, map_to_board=True)

            if self.scaling_active_point_index % 2 == 1:
                x_axis, y_axis = y_axis, x_axis

            self.scaling_x_axis = x_axis
            self.scaling_y_axis = y_axis

        for bi in self.selected_items:
            bi._scale_x = bi.scale_x
            bi._scale_y = bi.scale_y
            bi._position = QPointF(bi.position)
            self.board_stash_current_transform_to_history(bi)
            bi._scale_x_init = bi.scale_x
            bi._scale_y_init = bi.scale_y
            bi._position_init = QPointF(bi.position)
            # corner
            position_vec = bi.position - self.scaling_pivot_CORNER_point
            bi.factor_item_pos_x_corner, bi.factor_item_pos_y_corner = self.calculate_vector_projection_factors(x_axis, y_axis, position_vec)
            # center
            position_vec_center = bi.position - self.scaling_pivot_CENTER_point
            # умножение на 2 позволит коду board_DO_selected_items_SCALING отработать как нужно в случае масштабирования нескольких выделенных айтемов
            position_vec_center *= 2
            bi.factor_item_pos_x_center, bi.factor_item_pos_y_center = self.calculate_vector_projection_factors(x_axis, y_axis, position_vec_center)

            # self.show_center_label(f'{position_vec} {position_vec_center}')

    def calculate_vector_projection_factors(self, x_axis, y_axis, vector):
        x_axis = QVector2D(x_axis)
        y_axis = QVector2D(y_axis)
        x_axis_normalized = x_axis.normalized().toPointF()
        y_axis_normalized = y_axis.normalized().toPointF()
        x_axis_length = x_axis.length()
        y_axis_length = y_axis.length()
        x_factor = QPointF.dotProduct(x_axis_normalized, vector)/x_axis_length
        y_factor = QPointF.dotProduct(y_axis_normalized, vector)/y_axis_length
        return x_factor, y_factor

    def board_DO_selected_items_SCALING(self, event_pos):
        self.start_translation_pos = None

        multi_item_mode = len(self.selected_items) > 1
        alt_mod = QApplication.queryKeyboardModifiers() & Qt.AltModifier
        shift_mod = QApplication.queryKeyboardModifiers() & Qt.ShiftModifier
        center_is_pivot = alt_mod
        proportional_scaling = multi_item_mode or shift_mod

        if self.PTWS:
            proportional_scaling = True
            if self.PTWS_scaling_active_point_index == 4:
                center_is_pivot = True

        # отключаем модификатор alt для группы выделенных айтемов
        # center_is_pivot = center_is_pivot and not multi_item_mode

        if center_is_pivot:
            pivot = self.scaling_pivot_CENTER_point
            scaling_x_axis = self.scaling_from_center_x_axis
            scaling_y_axis = self.scaling_from_center_y_axis
        else:
            pivot = self.scaling_pivot_CORNER_point
            scaling_x_axis = self.scaling_x_axis
            scaling_y_axis = self.scaling_y_axis

        # updating for draw functions
        self.scaling_pivot_point = pivot
        self.scaling_pivot_point_x_axis = scaling_x_axis
        self.scaling_pivot_point_y_axis = scaling_y_axis

        for bi in self.selected_items:
            cursor_scaling_vector =  self.board_MapToBoard(QPointF(event_pos)) - pivot # не вытаскивать вычисления вектора из цикла!

            # принудительно задаётся минимальный скейл, значение в экранных координатах
            # MIN_LENGTH = 100.0
            # cursor_scaling_vector = QVector2D(cursor_scaling_vector)
            # if cursor_scaling_vector.length() < MIN_LENGTH:
            #     cursor_scaling_vector = cursor_scaling_vector.normalized().toPointF()*MIN_LENGTH
            # else:
            #     cursor_scaling_vector = cursor_scaling_vector.toPointF()

            self.scaling_vector = scaling_vector = cursor_scaling_vector

            if proportional_scaling:
                x_axis = QVector2D(scaling_x_axis).normalized()
                y_axis = QVector2D(scaling_y_axis).normalized()
                x_sign = math.copysign(1.0, QVector2D.dotProduct(x_axis, QVector2D(self.scaling_vector).normalized()))
                y_sign = math.copysign(1.0, QVector2D.dotProduct(y_axis, QVector2D(self.scaling_vector).normalized()))
                if multi_item_mode:
                    aspect_ratio = self.selection_box_aspect_ratio
                else:
                    aspect_ratio = bi.aspect_ratio()
                psv = x_sign*aspect_ratio*x_axis.toPointF() + y_sign*y_axis.toPointF()
                self.proportional_scaling_vector = QVector2D(psv).normalized().toPointF()
                factor = QPointF.dotProduct(self.proportional_scaling_vector, self.scaling_vector)
                self.proportional_scaling_vector *= factor

                self.scaling_vector = scaling_vector = self.proportional_scaling_vector

            if center_is_pivot:
                scaling_x_axis = - scaling_x_axis
                scaling_y_axis = - scaling_y_axis

            # scaling component
            x_factor, y_factor = self.calculate_vector_projection_factors(scaling_x_axis, scaling_y_axis, scaling_vector)
            # self.show_center_label(f'{x_factor} {y_factor}')

            if center_is_pivot and multi_item_mode:
                # это решение убирает флип скейла по обеим осям
                # но также лишает возможности отзеркаливать,
                # если курсор мыши завести с противоположной стороны относительно пивота
                x_factor = abs(x_factor)
                y_factor = abs(y_factor)

            bi.scale_x = bi._scale_x * x_factor
            bi.scale_y = bi._scale_y * y_factor
            if proportional_scaling and not multi_item_mode and not center_is_pivot:
                bi.scale_x = math.copysign(1.0, bi.scale_x)*abs(bi.scale_y)

            # position component
            if center_is_pivot and not multi_item_mode:
                bi.position = bi._position

            elif center_is_pivot and multi_item_mode:
                scaling = QTransform()
                scaling.scale(bi.factor_item_pos_x_center, bi.factor_item_pos_y_center)
                mapped_scaling_vector = scaling.map(scaling_vector)
                bi.position = pivot + mapped_scaling_vector
                self.mapped_scaling_vector = mapped_scaling_vector

            else:
                scaling = QTransform()
                scaling.scale(bi.factor_item_pos_x_corner, bi.factor_item_pos_y_corner)
                mapped_scaling_vector = scaling.map(scaling_vector)
                bi.position = pivot + mapped_scaling_vector
                self.mapped_scaling_vector = mapped_scaling_vector

        # bounding box update
        self.board_update_selection_box_widget()
        self.autoscroll_activate_board_item_transform_autoscroll()

    def board_FINISH_selected_items_SCALING(self, event, cancel=False):
        self.scaling_ongoing = False
        self.scaling_vector = None
        self.proportional_scaling_vector = None
        self.scaling_pivot_point = None
        cf = self.LibraryData().current_folder()
        if cancel:
            for bi in self.selected_items:
                bi.scale_x = bi._scale_x_init
                bi.scale_y = bi._scale_y_init
                bi.position = QPointF(bi._position_init)
        else:
            self.prepare_selection_box_widget(cf)
            self.build_board_bounding_rect(cf)
        self.autoscroll_desactivate_board_item_transform_autoscroll()

    def board_CANCEL_selected_items_SCALING(self):
        if self.scaling_ongoing:
            self.board_FINISH_selected_items_SCALING(None, cancel=True)
            self.board_update_selection_box_widget()
            self.transform_cancelled = True
            print('cancel scaling')

    def board_PTWS_init(self):
        # parameterized transform widget scaling
        self.PTWS = False
        self.PTWS_draw_monitor = False
        self.PTWS_scaling_active_point_index = None

    def board_SCALE_selected_items_draw_monitor(self, painter):
        if not self.PTWS_draw_monitor:
            return
        if self.selection_box is None:
            return
        if self.PTWS_scaling_active_point_index is None:
            return

        cursor_pos = self.mapFromGlobal(QCursor().pos())
        index = self.PTWS_scaling_active_point_index
        if index == 4:
            pivot_pos = self.__selection_box_qpolygon_centroid()
        else:
            pivot_pos = self.selection_box[index]

        painter.save()
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(cursor_pos, pivot_pos)
        painter.restore()

    def __selection_box_qpolygon_centroid(self):
        c = QPointF(0, 0)
        for p in self.selection_box:
            c += p
        c /= 4.0
        return c

    def board_SCALE_selected_items_choose_nearest_corner(self):
        position = self.mapFromGlobal(QCursor().pos())
        if self.selection_box is not None:
            enumerated = list(enumerate(self.selection_box))
            enumerated.append((4, self.__selection_box_qpolygon_centroid()))
            diffs = {}
            for index, point in enumerated:
                diffs[index] = QVector2D(point - QPointF(position)).length()
            diffs = sorted(diffs.items(), key=lambda x: x[1])
            index = diffs[0][0]
            self.PTWS_scaling_active_point_index = index
            if index == 4:
                # выбираем первую, но по идее, можно было бы выбрать любую другую
                self.PTWS_scaling_active_point_pos = self.selection_box[0]
            else:
                self.PTWS_scaling_active_point_pos = self.selection_box[index]

    def board_SCALE_selected_items(self, up=False, down=False, toggle_monitor=False):

        if (up or down):

            # in screen pixels
            VECTOR_LENGTH_FACTOR = self.STNG.one_key_selected_items_scaling_factor

            if up:
                pass

            elif down:
                VECTOR_LENGTH_FACTOR = -VECTOR_LENGTH_FACTOR

            self.PTWS = True
            self.board_SCALE_selected_items_choose_nearest_corner()

            direction = QVector2D(self.PTWS_scaling_active_point_pos -
                                    self.__selection_box_qpolygon_centroid()).normalized()
            direction *= VECTOR_LENGTH_FACTOR
            pos = self.PTWS_scaling_active_point_pos
            parameter_pos = pos + direction.toPointF()

            self.scaling_active_point_index = self.PTWS_scaling_active_point_index

            self.board_START_selected_items_SCALING(None)
            self.board_DO_selected_items_SCALING(parameter_pos)
            self.board_FINISH_selected_items_SCALING(None)

            self.board_SCALE_selected_items_choose_nearest_corner()
            self.PTWS = False

            # restore scale values signs, they may be corrupted by scaling one item with pivot in the center
            for item in self.selected_items:
                item.scale_x = math.copysign(item.scale_x, item._scale_x)
                item.scale_y = math.copysign(item.scale_y, item._scale_y)

        elif toggle_monitor:
            self.PTWS_draw_monitor = not self.PTWS_draw_monitor
            if self.PTWS_draw_monitor:
                self.board_SCALE_selected_items_choose_nearest_corner()

    def boards_do_scaling_key_callback(self):
        if self.scaling_ongoing:
            self.board_DO_selected_items_SCALING(self.mapped_cursor_pos())

    def boards_key_release_callback(self, event):
        self.boards_do_scaling_key_callback()

    def boards_key_press_callback(self, event):
        self.boards_do_scaling_key_callback()

    def board_mousePressEventDefault(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        alt = event.modifiers() & Qt.AltModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if self.AD_TOOLBOX.visible and self.board_AD_toolbox_pressEvent(event):
            return

        if self.board_TextElementMousePressEvent(event):
            return

        self.active_element = None

        if event.buttons() == Qt.LeftButton:

            if not alt:

                if self.is_over_scaling_activation_area(event.pos()):
                    self.board_START_selected_items_SCALING(event)

                elif self.is_over_rotation_activation_area(event.pos()):
                    self.board_START_selected_items_ROTATION(event.pos())

                elif self.any_item_area_under_mouse(event.modifiers() & Qt.ShiftModifier):
                    self.board_START_selected_items_TRANSLATION(event.pos())
                    self.board_update_selection_box_widget()

                else:
                    self.selection_start_point = QPointF(event.pos())
                    self.selection_rect = None
                    self.selection_ongoing = True

            elif alt:
                self.board_region_zoom_in_mousePressEvent(event)

        elif event.buttons() == Qt.MiddleButton:
            self.autoscroll_middleMousePressEvent(event)

            if self.transformations_allowed:
                self.board_camera_translation_ongoing = True
                self.start_cursor_pos = self.mapped_cursor_pos()
                self.start_origin_pos = self.canvas_origin
                self.update()

        elif event.buttons() == Qt.RightButton:
            self.right_click_selection_pressEvent(event, shift)

        self.update()

    def update(self, *args):
        super().update(*args)

    def board_mouseMoveEventDefault(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        alt = event.modifiers() & Qt.AltModifier
        no_mod = event.modifiers() == Qt.NoModifier

        special_update = False
        self.board_scrubbed_item_rect = None

        if self.AD_TOOLBOX.visible and self.board_AD_toolbox_moveEvent(event):
            return

        if self.board_TextElementMouseMoveEvent(event):
            return

        if event.buttons() == Qt.LeftButton:

            self.board_ALLOW_selected_items_TRANSLATION(event.pos())

            if any((self.translation_ongoing, self.scaling_ongoing, self.rotation_ongoing)):
                self.board_TextElementDeactivateEditMode()

                # для создания модификаций
                pass

            if self.transform_cancelled:
                pass

            elif self.scaling_ongoing:
                self.board_DO_selected_items_SCALING(event.pos())

            elif self.rotation_ongoing:
                self.board_DO_selected_items_ROTATION(event.pos())

            elif self.translation_ongoing:
                self.board_DO_selected_items_TRANSLATION(event.pos())
                self.board_update_selection_box_widget()

            elif self.board_region_zoom_in_input_started:
                self.board_region_zoom_in_mouseMoveEvent(event)

            elif self.selection_ongoing is not None:
                self.selection_end_point = QPointF(event.pos())
                if self.selection_start_point:
                    self.selection_rect = build_valid_rectF(self.selection_start_point, self.selection_end_point)
                    self.board_selection_callback(event.modifiers() == Qt.ShiftModifier)

        elif event.buttons() == Qt.MiddleButton:
            self.autoscroll_middleMouseMoveEvent()
            if self.transformations_allowed and self.board_camera_translation_ongoing:
                end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
                start_value = self.canvas_origin
                # delta = end_value-start_value
                self.canvas_origin = end_value
                self.board_update_selection_box_widget()

        elif event.buttons() == Qt.NoButton:
            bi = self.board_item_under_mouse
            if bi:
                special_update = self.board_item_cursor_scrubbing(bi, event)

        elif event.buttons() == Qt.RightButton:
            self.right_click_selection_moveEvent(event)

        if self.PTWS_draw_monitor:
            self.board_SCALE_selected_items_choose_nearest_corner()

        self.board_cursor_setter()
        if self.cursor_scrubbing_optimizer and self.board_scrubbed_item_rect:
            self.update(self.board_scrubbed_item_rect)
        else:
            self.update()

    def board_item_cursor_scrubbing(self, board_item, event):
        bi = board_item
        need = False
        if bi.type == bi.types.ITEM_IMAGE and bi.animated:
            if bi.movie is None:
                # такое случается, когда доска загружена из файла
                self.trigger_board_item_pixmap_loading(bi)
            item_rect = bi.get_selection_area(canvas=self).boundingRect()
            inside_rect_x_offset = event.pos().x() - item_rect.left()
            frame_index = self.map_cursor_pos_inside_rect_to_frame_number(
                inside_rect_x_offset,
                item_rect,
                bi.movie.frameCount(),
            )
            # TODO: по идее need показывает, надо ли перерерисовывать окно, но
            # если опираться на её значение, то линия скраба будет запинаться,
            # поэтому я пока воздержусь от её применения
            need = self.board_item_animation_file_set_frame(bi, frame_index)
            # заставляем скраб-линию отрисоваться, после её отрисовки это флаг сбросится,
            # чтобы скраб-линия не отрисовывалась во время работы, например,
            # той же board_fly_over, когда курсор мыши находится поверх айтема
            bi.scrubbed = True
            self.board_scrubbed_item_rect = item_rect.toRect()
        if bi.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            item_rect = bi.get_selection_area(canvas=self).boundingRect()
            inside_rect_x_offset = event.pos().x() - item_rect.left()
            image_index = self.map_cursor_pos_inside_rect_to_frame_number(
                inside_rect_x_offset,
                item_rect,
                len(board_item.item_folder_data.images_list),
            )
            need = image_index != board_item.item_folder_data._index
            if need:
                board_item.item_folder_data.set_current_index(image_index)
                # заставляем подгрузится
                board_item.pixmap = None
                board_item.update_corner_info()
            bi.scrubbed = True
            self.board_scrubbed_item_rect = item_rect.toRect()
        return need

    def board_is_items_transformation_ongoing(self):
        return self.translation_ongoing or self.rotation_ongoing or self.scaling_ongoing

    def board_mouseReleaseEventDefault(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier
        alt = event.modifiers() & Qt.AltModifier

        if self.AD_TOOLBOX.visible and self.board_AD_toolbox_releaseEvent(event):
            return

        if self.board_TextElementMouseReleaseEvent(event):
            return

        if self.transform_cancelled:
            self.transform_cancelled = False
            return

        if event.button() == Qt.LeftButton:
            self.start_translation_pos = None

            if not alt and not self.translation_ongoing and not self.rotation_ongoing and not self.scaling_ongoing:
                self.board_selection_callback(event.modifiers() == Qt.ShiftModifier)
                # if self.selection_rect is not None:
                self.selection_start_point = None
                self.selection_end_point = None
                self.selection_rect = None
                self.selection_ongoing = False

            if self.rotation_ongoing:
                self.board_FINISH_selected_items_ROTATION(event)

            if self.scaling_ongoing:
                self.board_FINISH_selected_items_SCALING(event)

            if self.translation_ongoing:
                self.board_FINISH_selected_items_TRANSLATION(event)
                self.selection_start_point = None
                self.selection_end_point = None
                self.selection_rect = None
                self.selection_ongoing = False

            if alt or self.board_region_zoom_in_input_started:
                self.board_region_zoom_in_mouseReleaseEvent(event)

            elif ctrl and not shift:
                cf = self.LibraryData().current_folder()
                canvas_pos = self.board_MapToBoard(event.pos())
                cf.board.user_points.append([canvas_pos, self.canvas_scale_x, self.canvas_scale_y])

        elif event.button() == Qt.MiddleButton:
            if no_mod:
                if self.transformations_allowed:
                    self.board_camera_translation_ongoing = False
                    self.autoscroll_middleMouseReleaseEvent()
                    self.update()

            elif alt:
                if self.transformations_allowed:
                    self.set_default_boardviewport_scale(keep_position=True)

        elif event.button() == Qt.RightButton:
            self.right_click_selection_releaseEvent(event)

        self.prevent_item_deselection = False

    def board_clear_selection(self):
        self.board_unselect_all_items()

    def board_clear_links_selection(self):
        cf = self.LibraryData().current_folder()
        for link in cf.board.link_items_list:
            link._selected = False

    def right_click_selection_init(self):
        self.RCS = RCS = type('RightClickSelectionData', (), {})()
        RCS.selection_points = QPolygonF()
        RCS.ongoing = False
        RCS.clear_magazin = True

    def right_click_selection_input_callback(self):
        RCS = self.RCS
        cf = self.LibraryData().current_folder()
        items = cf.board.items_list
        im = self.item_magazin

        def check_polygon_point_inside_selection_area(bi):
            area = bi.get_selection_area(canvas=self).boundingRect()
            for po in RCS.selection_points:
                if area.contains(po):
                    im.append(bi)

        for bi in items:
            if bi not in im:
                check_polygon_point_inside_selection_area(bi)

        def check_near_link(li):
            # TODO: это конечно полный провал,
            # надо рефакторить RCS.selection_points,
            # потому что там слишком много точек
            for po in RCS.selection_points:
                if li.is_near_link(self, po):
                    li._selected = True
                    # раньше тут стоял break, но он, кажется,
                    # выходит и из внешнего цикла тоже
                    return

        for li in cf.board.link_items_list:
            check_near_link(li)

    def right_click_selection_pressEvent(self, event, shift_pressed):
        RCS = self.RCS
        RCS.ongoing = True
        RCS.selection_points.clear()
        self.board_clear_selection()
        RCS.selection_points.append(event.pos())
        RCS.clear_selection = not shift_pressed

    def right_click_selection_moveEvent(self, event):
        RCS = self.RCS
        RCS.ongoing = True
        RCS.selection_points.append(event.pos())
        self.right_click_selection_input_callback()
        self.update()

    def right_click_selection_releaseEvent(self, event):
        RCS = self.RCS
        RCS.ongoing = False
        RCS.selection_points.append(event.pos())
        spbb = RCS.selection_points.boundingRect()
        if all(i.type != i.types.ITEM_LINK for i in self.item_magazin):
            item_magazin = list(self.item_magazin)
            # включаем очистку принудительно,
            # если будут создаваться линки, ибо уже надоело
            if item_magazin:
                RCS.clear_selection = True
            for first, second in zip(item_magazin, item_magazin[1:]):
                self.board_create_link_item(first, second)
        self.item_magazin.clear()
        if RCS.clear_selection:
            self.board_clear_links_selection()
        if spbb.width() > 30 or spbb.height() > 30:
            self.context_menu_allowed = False
        self.update()

    def right_click_selection_drawEvent(self, painter):
        RCS = self.RCS
        if RCS.ongoing:
            painter.save()
            pen = QPen(self.selection_color, 4)
            painter.setPen(pen)
            painter.drawPolyline(RCS.selection_points)
            pen.setColor(Qt.black)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.drawPolyline(RCS.selection_points)
            painter.restore()

    def board_go_to_note(self, event):
        for sel_item in self.selected_items:
            if sel_item.type == BoardItem.types.ITEM_NOTE:
                if (event and sel_item.get_selection_area(canvas=self).containsPoint(event.pos(), Qt.WindingFill)) or not event:
                    note_content = sel_item.plain_text
                    execute_clickable_text(note_content)
                    break

    def board_MapRectToViewport(self, rect):
        return QRectF(
            self.board_MapToViewport(rect.topLeft()),
            self.board_MapToViewport(rect.bottomRight())
        )

    def board_MapRectToBoard(self, rect):
        return QRectF(
            self.board_MapToBoard(rect.topLeft()),
            self.board_MapToBoard(rect.bottomRight())
        )

    def board_MapToViewport(self, canvas_pos):
        scaled_board_pos = QPointF(canvas_pos.x()*self.canvas_scale_x, canvas_pos.y()*self.canvas_scale_y)
        viewport_pos = self.canvas_origin + scaled_board_pos
        return viewport_pos

    def board_MapToBoard(self, viewport_pos):
        delta = QPointF(viewport_pos - self.canvas_origin)
        board_pos = QPointF(delta.x()/self.canvas_scale_x, delta.y()/self.canvas_scale_y)
        return board_pos

    def board_paste_selected_items(self):
        selected_items = []
        selection_center = self.board_MapToBoard(self.selection_box.boundingRect().center())
        rel_cursor_pos = self.board_MapToBoard(self.mapped_cursor_pos())
        for bi in self.LibraryData().current_folder().board.items_list:
            if bi._selected:
                selected_items.append(bi)
                bi._selected = False
        if selected_items:
            cf = self.LibraryData().current_folder()
            for sel_item in selected_items:
                new_item = sel_item.make_copy(self, cf)
                # new_item.position += QPointF(100, 100)
                delta = new_item.position - selection_center
                new_item.position = rel_cursor_pos + delta
                new_item._selected = True
            self.prepare_selection_box_widget(cf)

    def do_scale_board(self, scroll_value, ctrl, shift, no_mod,
                pivot=None, factor_x=None, factor_y=None, precalculate=False, canvas_origin=None, canvas_scale_x=None, canvas_scale_y=None, scale_speed=0.1):

        if not precalculate:
            self.board_region_zoom_do_cancel()

        if pivot is None:
            pivot = self.mapped_cursor_pos()

        inv_speed_fac = 1.0/scale_speed
        if scroll_value > 0:
            factor = inv_speed_fac/(inv_speed_fac-1)
        else:
            factor = (inv_speed_fac-1)/inv_speed_fac

        if factor_x is None:
            factor_x = factor

        if factor_y is None:
            factor_y = factor

        if ctrl:
            factor_x = factor
            factor_y = 1.0
        elif shift:
            factor_x = 1.0
            factor_y = factor

        _canvas_origin = canvas_origin if canvas_origin is not None else self.canvas_origin
        _canvas_scale_x = canvas_scale_x if canvas_scale_x is not None else self.canvas_scale_x
        _canvas_scale_y = canvas_scale_y if canvas_scale_y is not None else self.canvas_scale_y

        _canvas_scale_x *= factor_x
        _canvas_scale_y *= factor_y

        _canvas_origin -= pivot
        _canvas_origin = QPointF(_canvas_origin.x()*factor_x, _canvas_origin.y()*factor_y)
        _canvas_origin += pivot

        if precalculate:
            return _canvas_scale_x, _canvas_scale_y, _canvas_origin

        self.canvas_origin  = _canvas_origin
        self.canvas_scale_x = _canvas_scale_x
        self.canvas_scale_y = _canvas_scale_y

        if self.selection_rect:
            self.board_selection_callback(QApplication.queryKeyboardModifiers() == Qt.ShiftModifier)

        if self.rotation_ongoing:
            self.board_DO_selection_box_ROTATION()
        elif self.scaling_ongoing:
            self.board_update_selection_box_widget()
        else:
            self.board_update_selection_box_widget()

        self.update()

    def board_do_scale(self, scroll_value):
        self.do_scale_board(scroll_value, False, False, False, pivot=self.get_center_position())

    def board_item_scroll_animation_file(self, board_item, scroll_value, set_first_frame=None):
        if board_item.movie is None:
            # такое случается, когда доска загружена из файла
            self.trigger_board_item_pixmap_loading(board_item)
        if scroll_value > 0:
            inc = 1
        else:
            inc = -1
        if set_first_frame is None:
            current_frame = board_item.movie.currentFrameNumber()
            current_frame += inc
            current_frame %= board_item.movie.frameCount()
        elif set_first_frame:
            current_frame = 0
        else:
            current_frame = board_item.movie.frameCount()-1
        self.board_item_animation_file_set_frame(board_item, current_frame)
        self.update()

    def board_item_animation_file_set_frame(self, board_item, frame_index):
        movie = board_item.movie
        need = movie.currentFrameNumber() != frame_index
        if need:
            movie.jumpToFrame(frame_index)
            board_item.pixmap = movie.currentPixmap()
            board_item.update_corner_info()
        return need

    def board_item_scroll_folder(self, board_item, scroll_value):
        if scroll_value > 0:
            board_item.item_folder_data.next_image()
        else:
            board_item.item_folder_data.previous_image()
        # заставляем подгрузится
        board_item.pixmap = None
        board_item.update_corner_info()
        self.update()

    def board_autoscroll_zoom_init(self):
        self.autoscroll_zoom_timer = QTimer()
        self.autoscroll_zoom_timer.setInterval(10)
        self.autoscroll_zoom_timer.timeout.connect(self.board_autoscroll_zoom_timer_handler)
        self.autoscroll_zoom_timer_dir = 1.0
        self.az_ticks = 0

    def board_autoscroll_zoom_timer_handler(self):
        self.do_scale_board(self.autoscroll_zoom_timer_dir, False, False, None, scale_speed=0.025)
        self.az_ticks += 1
        if self.az_ticks > 10:
            self.autoscroll_zoom_timer.stop()
            self.az_ticks = 0

    def board_autoscroll_wheelEventHandler(self, scroll_value):
        if not self.autoscroll_zoom_timer.isActive():
            self.autoscroll_zoom_timer_dir = scroll_value
            self.autoscroll_zoom_timer.start()

    def board_scroll_board_item(self, scroll_value, board_item):
        if board_item.type == board_item.types.ITEM_IMAGE:
            if board_item.animated:
                self.board_item_scroll_animation_file(board_item, scroll_value)
        elif board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            self.board_item_scroll_folder(board_item, scroll_value)
        self.update()

    def board_set_start_or_end_for_animation_board_items(self, set_first_frame):
        current_time = time.time()
        if current_time - self.scroll_items_timestamp > 0.2:
            self.scroll_items_timestamp = current_time
            for bi in self.board_get_selected_or_visible_items(visible=True):
                if bi.type == bi.types.ITEM_IMAGE and bi.animated:
                    self.board_item_scroll_animation_file(bi, 0, set_first_frame=set_first_frame)

    def board_scroll_visible_board_items(self, scroll_value):
        current_time = time.time()
        if current_time - self.scroll_items_timestamp > 0.2:
            self.scroll_items_timestamp = current_time
            for bi in self.board_get_selected_or_visible_items(visible=True):
                self.board_scroll_board_item(scroll_value, bi)

    def board_wheelEventDefault(self, event):
        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        control_panel_undermouse = self.is_control_panel_under_mouse()
        if control_panel_undermouse:
            return
        elif self.board_camera_translation_ongoing:
            return
        elif self.board_change_node_radius(event, scroll_value):
            return
        elif self.board_change_link_width(event, scroll_value):
            return
        elif self.AUTOSCROLL.timer.isActive():
            self.board_autoscroll_wheelEventHandler(scroll_value)
            return
        elif self.board_item_under_mouse is not None and event.buttons() == Qt.RightButton:
            board_item = self.board_item_under_mouse
            self.context_menu_allowed = False
            self.board_scroll_board_item(scroll_value, board_item)
        elif no_mod:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif ctrl:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif shift:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)

    def board_toggle_item_mark(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.items_list:
            item_selection_area = bi.get_selection_area(canvas=self)
            is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
            if is_under_mouse:
                bi._marked_item = not bi._marked_item

    def board_marked_items_filepaths_to_clipboard(self):
        cf = self.LibraryData().current_folder()
        filepaths = [bi.file_data.filepath for bi in cf.board.items_list if bi._marked_item]
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText("\n".join(filepaths), mode=cb.Clipboard)
        l = len(filepaths)
        if l > 0:
            if not hasattr(self, '_marked_items_deleted_from_disk'):
                self._marked_items_deleted_from_disk = True
                for fp in filepaths:
                    delete_to_recyclebin(fp)
            self.show_center_label(f'The files are moved to recycle bin!\n{l} filepaths has been copied to clipboard!')
        else:
            self.show_center_label('Nothing marked!', error=True)

    def board_toggle_item_info_overlay(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.items_list:
            item_selection_area = bi.get_selection_area(canvas=self)
            is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
            if is_under_mouse or bi._selected:
                bi._show_file_info_overlay = not bi._show_file_info_overlay
        self.update()

    def board_control_c(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(COPY_SELECTED_BOARD_ITEMS_STR, mode=cb.Clipboard)

    def board_control_v(self):
        app = QApplication.instance()
        cb = app.clipboard()
        text = cb.text()
        mdata = cb.mimeData()
        cf = self.LibraryData().current_folder()

        pixmap = None
        if text and text == COPY_SELECTED_BOARD_ITEMS_STR:
            self.board_paste_selected_items()

        elif mdata and mdata.hasText():
            path = mdata.text()
            qt_supported_exts = (
                ".jpg", ".jpeg", ".jfif",
                ".bmp",
                ".gif",
                ".png",
                ".tif", ".tiff",
                ".webp",
            )
            svg_exts = (
                ".svg",
                ".svgz"
            )
            PREFIX = "file:///"
            if path.startswith(PREFIX):
                filepath = path[len(PREFIX):]
                _gif_file = self.LibraryData().is_gif_file(filepath)
                _webp_animated_file = self.LibraryData().is_webp_file(filepath) and self.LibraryData().is_webp_file_animated(filepath)
                if _gif_file or _webp_animated_file:
                    return filepath
                # supported exts
                elif path.lower().endswith(qt_supported_exts):
                    pixmap = QPixmap(filepath)
                # svg-files
                elif path.lower().endswith(svg_exts):
                    pixmap = load_svg(filepath, scale_factor=20)

        elif mdata and mdata.hasImage():
            pixmap = QPixmap().fromImage(mdata.FileData())
            filepath = os.path.join(cf.folder_path, f'{time.time()}.jpg')

            pixmap.save(filepath)

        if pixmap is not None:
            self.board_create_new_board_item_image(filepath, cf)

    def board_long_loading_begin(self, text):
        text = text.strip()
        if text:
            self.long_process_label_text = text
        self.long_loading = True
        self.update()
        processAppEvents()

    def board_long_loading_end(self):
        self.long_loading = False
        self.update()

    def board_download_file(self, url):
        with self.show_longtime_process_ongoing(self, _("Loading image to the board")):
            cf = self.LibraryData().current_folder()
            try:
                response = urllib.request.urlopen(url)
            except http.client.InvalidURL:
                try:
                    url = url.replace(" ", "%20")
                    response = urllib.request.urlopen(url)
                except http.client.InvalidURL:
                    self.show_center_label(f'http.client.InvalidURL: {url}', error=True)
                    return

            filename = os.path.basename(response.url)
            name, ext = os.path.splitext(filename)
            if "?" in ext:
                ext = ext[:ext.index("?")]
            if not self.LibraryData().is_supported_file(ext):
                mime_type = response.headers.get('content-type', '')
                if mime_type == '':
                    ext = 'unknown'
                else:
                    if ';' in mime_type:
                        mime_type = mime_type.split(";")[0]
                    ext = mime_type.split("/")[1]
            if not ext.startswith("."):
                ext = f'.{ext}'
            filepath = os.path.join(cf.folder_path, f'{time.time()}{ext}')
            urllib.request.urlretrieve(url, filepath)
            self.board_create_new_board_item_image(filepath, cf, source_url=url)

    def board_create_new_board_item_image(self, filepath, current_folder, source_url=None, make_previews=True, place_at_cursor=True):
        file_data = self.LibraryData().create_file_data(filepath, current_folder)
        board_item = BoardItem(BoardItem.types.ITEM_IMAGE)
        board_item.file_data = file_data
        board_item.image_source_url = source_url
        file_data.board_items.append(board_item)
        current_folder.board.items_list.append(board_item)
        board_item.board_index = self.retrieve_new_board_item_index()
        if place_at_cursor:
            board_item.position = self.board_MapToBoard(self.mapped_cursor_pos())
        current_folder.images_list.append(file_data)
        if make_previews: # делаем превьюшку и миинатюрку для этой картинки
            self.LibraryData().make_thumbnails_and_previews(current_folder, None)
        return board_item

    def board_thumbnails_click_handler(self, file_data):
        self.board_fit_content_on_screen(file_data)

    def board_fit_content_on_screen(self, file_data, board_item=None, use_selection=False):

        if board_item is None and (file_data is not None) and not file_data.board_items:
            self.show_center_label(_("This element is not presented on the board"), error=True)
        else:
            canvas_scale_x = self.canvas_scale_x
            canvas_scale_y = self.canvas_scale_y

            if (self.selection_box is None or not self.selected_items) and use_selection:
                self.show_center_label(_('No items selected!'))
                return

            if use_selection:
                content_pos = self.selection_box.boundingRect().center() - self.canvas_origin
            else:
                if board_item is not None:
                    pass
                else:
                    board_item = file_data.board_items[0]
                content_pos = QPointF(board_item.position.x()*canvas_scale_x, board_item.position.y()*canvas_scale_y)
            viewport_center_pos = self.get_center_position()

            self.canvas_origin = - content_pos + viewport_center_pos

            if use_selection:
                content_rect = self.selection_box.boundingRect().toRect()
            else:
                content_rect = board_item.get_selection_area(canvas=self, place_center_at_origin=False).boundingRect().toRect()
            fitted_rect = fit_rect_into_rect(content_rect, self.rect())
            self.do_scale_board(0, False, False, False,
                pivot=viewport_center_pos,
                factor_x=fitted_rect.width()/content_rect.width(),
                factor_y=fitted_rect.height()/content_rect.height(),
            )

        self.update()

    def board_fit_selected_items_on_screen(self):
        self.board_fit_content_on_screen(None, use_selection=True)

    def set_default_boardviewport_scale(self, keep_position=False, center_as_pivot=False):
        if center_as_pivot:
            pivot = self.get_center_position()
        else:
            pivot = self.mapped_cursor_pos()
        if keep_position:
            self.do_scale_board(0, False, False, False,
                pivot=pivot,
                factor_x=1/self.canvas_scale_x,
                factor_y=1/self.canvas_scale_y,
            )
        else:
            self.canvas_scale_x = 1.0
            self.canvas_scale_y = 1.0

    def retrieve_selected_item(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.items_list:
            if bi.type in [BoardItem.types.ITEM_IMAGE, BoardItem.types.ITEM_GROUP, BoardItem.types.ITEM_FOLDER]:
                if bi._selected:
                    return bi
        return None

    def board_open_in_app_copy(self):
        item = self.retrieve_selected_item()
        if item is not None:
            if item.type == BoardItem.types.ITEM_IMAGE:
                pass
                filepath = item.file_data.filepath
            elif item.type in [BoardItem.types.ITEM_GROUP, BoardItem.types.ITEM_FOLDER]:
                pass
                filepath = item.item_folder_data.current_image().filepath
            # TODO: когда сделаю задание стартовой страницы,
            # тут надо ещё будет задавать и принудительное включение вьювера
            self.APP_start_lite_process(filepath)

    def board_place_items_in_column_or_row(self):
        subMenu = RoundedQMenu()
        subMenu.setStyleSheet(self.context_menu_stylesheet)
        horizontal = subMenu.addAction(_("Horizontally"))
        vertical = subMenu.addAction(_("Vertically"))
        item = subMenu.exec_(QCursor().pos())
        if item is None:
            pass
        elif item == horizontal:
            self.board_do_place_items_in_column_or_row(column=False)
        elif item == vertical:
            self.board_do_place_items_in_column_or_row(column=True)

    def board_do_place_items_in_column_or_row(self, column=True):
        folder_data = self.LibraryData().current_folder()

        items_list = folder_data.board.items_list

        if not items_list:
            self.show_center_label(_("No items on the board! Abort!"), error=True)

        all_items = self.get_original_items_order(items_list)
        item = self.board_get_nearest_item(folder_data, by_window_center=True)

        item_index = all_items.index(item)

        pos_list = all_items[item_index:]
        neg_list = all_items[:item_index]

        main_offset = item.get_selection_area(canvas=self, apply_global_scale=False).boundingRect().topLeft()

        offset = QPointF(main_offset)
        for bi in pos_list:
            b_rect = bi.get_selection_area(canvas=self, apply_global_scale=False).boundingRect()
            bi_width = b_rect.width()
            bi_height = b_rect.height()
            if column == True:
                bi.position = offset + QPointF(bi_width/2, bi_height/2)
                offset += QPointF(0, bi_height)
            else:
                bi.position = offset + QPointF(bi_width/2, bi_height/2)
                offset += QPointF(bi_width, 0)

        offset = QPointF(main_offset)
        for bi in reversed(neg_list):
            b_rect = bi.get_selection_area(canvas=self, apply_global_scale=False).boundingRect()
            bi_width = b_rect.width()
            bi_height = b_rect.height()
            if column == True:
                bi.position = offset + QPointF(bi_width/2, -bi_height/2)
                offset -= QPointF(0, bi_height)
            else:
                bi.position = offset + QPointF(-bi_width/2, bi_height/2)
                offset -= QPointF(bi_width, 0)

        self.build_board_bounding_rect(folder_data)
        self.prepare_selection_box_widget(folder_data)
        self.update()

    def board_open_in_google_chrome(self):
        item = self.retrieve_selected_item()
        if item is not None:
            if item.type == BoardItem.types.ITEM_IMAGE:
                filepath = item.file_data.filepath
            elif item.type in [BoardItem.types.ITEM_GROUP, BoardItem.types.ITEM_FOLDER]:
                filepath = item.item_folder_data.current_image().filepath
            open_in_google_chrome(filepath)

    def animate_scale_update(self):
        # надо менять и значение self.canvas_origin для того,
        # чтобы увеличивать относительно центра картинки и центра экрана,
        # а они совпадают в данном случае
        factor_x = self._canvas_scale_x/self.canvas_scale_x
        factor_y = self._canvas_scale_y/self.canvas_scale_y

        pivot = self.get_center_position()

        _canvas_origin = self.canvas_origin

        self.canvas_scale_x *= factor_x
        self.canvas_scale_y *= factor_y

        _canvas_origin -= pivot
        _canvas_origin = QPointF(_canvas_origin.x()*factor_x, _canvas_origin.y()*factor_y)
        _canvas_origin += pivot

        self.canvas_origin  = _canvas_origin

        self.update()

    def board_get_nearest_item(self, folder_data, by_window_center=False):
        cursor_pos = self.get_center_position() if by_window_center else self.mapped_cursor_pos()
        items = folder_data.board.items_list
        def min_key_function(board_item):
            item_pos = self.board_MapToViewport(board_item.position)
            distance = QVector2D(item_pos - cursor_pos).length()
            return distance
        if items:
            return min(items, key=min_key_function)
        else:
            return None

    def board_move_viewport(self, _previous=False, _next=False):
        self.board_unselect_all_items()

        cf = self.LibraryData().current_folder()
        nearest_item = self.board_get_nearest_item(cf, by_window_center=True)

        if nearest_item is not None and len(cf.board.items_list) > 1:
            if _previous:
                reverse = True
            elif _next:
                reverse = False

            items_list = self.get_original_items_order(cf.board.items_list)
            _list = shift_list_to_became_first(items_list, nearest_item, reverse=reverse)

            first_item = _list[0]
            second_item = _list[1]
            pos = self.board_MapToViewport(first_item.position)
            distance = QVector2D(pos - self.get_center_position()).length()
            if distance < 5.0:
                # если цент картинки практически совпадает с центром вьюпорта, то выбираем следующую картинку
                item_to_center_viewport = second_item
            else:
                item_to_center_viewport = first_item

            current_pos = self.board_MapToBoard(self.get_center_position())

            item_point = item_to_center_viewport.position

            pos1 = QPointF(current_pos.x()*self.canvas_scale_x, current_pos.y()*self.canvas_scale_y)
            pos2 = QPointF(item_point.x()*self.canvas_scale_x, item_point.y()*self.canvas_scale_y)

            viewport_center_pos = self.get_center_position()

            pos1 = -pos1 + viewport_center_pos
            pos2 = -pos2 + viewport_center_pos


            board_item = item_to_center_viewport

            canvas_scale_x = self.canvas_scale_x
            canvas_scale_y = self.canvas_scale_y

            item_rect = board_item.get_selection_area(canvas=self, place_center_at_origin=False, apply_global_scale=False).boundingRect().toRect()

            fitted_rect = fit_rect_into_rect(item_rect, self.rect())
            bx = fitted_rect.width()/item_rect.width()
            by = fitted_rect.height()/item_rect.height()

            if self.check_scroll_lock():
                # если включён scroll lock, то при переходе
                # от картинки к картинке не изменяем масштаб вьюпорта
                factor_x = 1.0
                factor_y = 1.0
            else:
                factor_x = bx/self.canvas_scale_x
                factor_y = by/self.canvas_scale_y

            new_canvas_scale_x, new_canvas_scale_y, new_canvas_origin = self.do_scale_board(1.0,
                False,
                False,
                True,
                factor_x=factor_x,
                factor_y=factor_y,
                precalculate=True,
                canvas_scale_x=self.canvas_scale_x,
                canvas_scale_y=self.canvas_scale_y,
                canvas_origin=pos2,
                pivot = self.get_center_position()
            )

            anim_data = [
                (self, "canvas_origin", pos1, new_canvas_origin, self.update),
                (self, "canvas_scale_x", self.canvas_scale_x, new_canvas_scale_x, self.update),
                (self, "canvas_scale_y", self.canvas_scale_y, new_canvas_scale_y, self.update),
            ]

            self.animate_properties(
                anim_data,
                anim_id="flying",
                duration=0.7,
            )

    def get_original_items_order(self, items_list):
        if all((hasattr(bi, 'sort_index') for bi in items_list)):
            return list(sorted(items_list, key=lambda x: x.sort_index))
        else:
            return list(sorted(items_list, key=lambda x: x.board_index))

    def is_flyover_ongoing(self):
        return bool(self.fly_pairs)

    def board_fly_over(self, user_call=False):
        if self.board_is_items_transformation_ongoing():
            return

        self.board_unselect_all_items()

        if user_call and self.fly_pairs:
            self.cancel_all_anim_tasks()
            self.fly_pairs = []
            return

        viewport_center_pos = self.get_center_position()
        cf = self.LibraryData().current_folder()
        pair = None

        current_pos = self.board_MapToBoard(self.get_center_position())

        LocData = namedtuple("LocationData", "pos scale_x scale_y board_item")


        if not self.fly_pairs:
            locations_data_list = []

            if cf.board.user_points:
                for point, bx, by in cf.board.user_points:
                    locations_data_list.append(LocData(point, bx, by, None))
            else:
                nearest_item = self.board_get_nearest_item(cf)
                items_list = self.get_original_items_order(cf.board.items_list)
                if nearest_item:
                    sorted_list = shift_list_to_became_first(items_list, nearest_item)
                else:
                    sorted_list = items_list
                for board_item in sorted_list:
                    point = board_item.position
                    locations_data_list.append(LocData(point, None, None, board_item))

            self.fly_pairs = get_cycled_pairs(locations_data_list)
            pair = [
                LocData(current_pos, self.canvas_scale_x, self.canvas_scale_y, None),
                locations_data_list[0]
            ]

        # pair будет None только когда анимация уже пошла
        if pair is None:
            pair = next(self.fly_pairs)


        def get_bx_by(loc_data):
            if loc_data.board_item:
                item_rect = loc_data.board_item.get_selection_area(canvas=self, place_center_at_origin=False, apply_global_scale=False).boundingRect().toRect()
                fitted_rect = fit_rect_into_rect(item_rect, self.rect())
                bx = fitted_rect.width()/item_rect.width()
                by = fitted_rect.height()/item_rect.height()
            else:
                bx = loc_data.scale_x
                by = loc_data.scale_y
            return (bx, by)

        def animate_scale_or_not_animate_that_is_the_question():

            loc_data = pair[1]
            bx, by = get_bx_by(loc_data)

            skip_scale_animation = False

            if not loc_data.board_item:
                skip_scale_animation = False
            else:
                current_canvas_scale_x = self.canvas_scale_x
                current_canvas_scale_y = self.canvas_scale_y

                __, __, new_origin = self.do_scale_board(
                    1.0, False, False, False,
                    pivot=self.get_center_position(),
                    factor_x=bx/current_canvas_scale_x,
                    factor_y=by/current_canvas_scale_y,
                    precalculate=True,
                    canvas_origin=QPointF(self.canvas_origin),
                    canvas_scale_x=current_canvas_scale_x,
                    canvas_scale_y=current_canvas_scale_y,
                )

                if QVector2D(new_origin - self.canvas_origin).length() < 2.0:
                    # Если точка ориджина не сместилась на заметную величину,
                    # то анимация не нужна по сути, а 2.0 измеряется в пикселях
                    if self.Globals.DEBUG:
                        self.show_center_label('skipping the scale animation')
                    skip_scale_animation = True
                else:
                    if self.Globals.DEBUG:
                        self.show_center_label('doing the scale animation')
                    skip_scale_animation = False

            if skip_scale_animation:
                callback_on_finish = animate_pause
            else:
                callback_on_finish = animate_scale

            self.animate_properties(
                [
                    (self, "_anim_tech", 0.0, 1.0, lambda: None),
                ],
                anim_id="flying",
                duration=0.01,
                callback_on_finish=callback_on_finish,
            )

        def animate_scale():

            loc_data = pair[1]
            bx, by = get_bx_by(loc_data)

            self.animate_properties(
                [
                    (self, "_canvas_scale_x", self.canvas_scale_x, bx, self.animate_scale_update),
                    (self, "_canvas_scale_y", self.canvas_scale_y, by, self.animate_scale_update),
                ],
                anim_id="flying",
                duration=1.5,
                easing=QEasingCurve.InOutSine,
                callback_on_finish=animate_pause
            )

        def animate_pause():

            self.animate_properties(
                [
                    (self, "_anim_pause", 0.0, 1.0, lambda: None),
                ],
                anim_id="flying",
                duration=0.5,
                callback_on_finish=self.board_fly_over,
            )

        def update_viewport_position():
            self.canvas_origin = -self.pr_viewport + viewport_center_pos
            self.update()

        current_pos_ = self.board_MapToBoard(self.get_center_position())

        # подменяем первую позицию на текущие данные, чтобы избежать перескоков и прочего неприятного,
        # мало ли, нет блокировки, и из-за этого позиция или масштаб были изменены пользователем
        pair = [
            LocData(current_pos_, self.canvas_scale_x, self.canvas_scale_y, None),
            pair[1],
        ]

        pos_from = QPointF(pair[0].pos.x()*self.canvas_scale_x, pair[0].pos.y()*self.canvas_scale_y)
        pos_to = QPointF(pair[1].pos.x()*self.canvas_scale_x, pair[1].pos.y()*self.canvas_scale_y)

        self.animate_properties(
            [
                (self, "pr_viewport", pos_from, pos_to, update_viewport_position),
            ],
            anim_id="flying",
            duration=2.0,
            easing=QEasingCurve.InOutSine,
            callback_on_finish=animate_scale_or_not_animate_that_is_the_question,
            # callback_on_finish=self.board_fly_over
        )

    def is_board_ready(self):
        return self.LibraryData().current_folder().board.ready

    def board_selected_items_count(self):
        return len(self.selected_items)

    def board_viewport_show_first_item(self):
        self.board_unselect_all_items()
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
            if cf.board.items_list:
                items_list = self.get_original_items_order(cf.board.items_list)
                item = items_list[0]
                self.board_fit_content_on_screen(None, item)

    def board_viewport_show_last_item(self):
        self.board_unselect_all_items()
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
           if cf.board.items_list:
                items_list = self.get_original_items_order(cf.board.items_list)
                item = items_list[-1]
                self.board_fit_content_on_screen(None, item)

    def board_region_zoom_in_init(self):
        self.board_magnifier_input_rect = None
        self.board_magnifier_projected_rect = None
        self.board_orig_scale_x = None
        self.board_orig_scale_y = None
        self.board_orig_origin = None
        self.board_zoom_region_defined = False
        self.board_magnifier_zoom_level = 1.0
        self.board_region_zoom_in_input_started = False
        self.board_magnifier_input_rect_animated = None
        self.board_INPUT_POINT1 = None
        self.board_INPUT_POINT2 = None

    def board_region_zoom_do_cancel(self):
        if self.board_magnifier_input_rect:
            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "canvas_origin", self.canvas_origin, self.board_orig_origin, self.update),
                        (self, "canvas_scale_x", self.canvas_scale_x, self.board_orig_scale_x, self.update),
                        (self, "canvas_scale_y", self.canvas_scale_y, self.board_orig_scale_y, self.update),
                    ],
                    anim_id="board_region_zoom_out",
                    duration=0.4,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.canvas_scale_x = self.board_orig_scale_x
                self.canvas_scale_y = self.board_orig_scale_y
                self.canvas_origin = self.board_orig_origin
            self.board_region_zoom_in_init()
            self.update()
            self.board_unselect_all_items()

    def board_region_zoom_build_magnifier_input_rect(self):
        if self.board_INPUT_POINT1 is not None and self.board_INPUT_POINT2 is not None:
            self.board_magnifier_input_rect = build_valid_rect(self.board_INPUT_POINT1, self.board_INPUT_POINT2)
            self.board_magnifier_projected_rect = fit_rect_into_rect(self.board_magnifier_input_rect, self.rect())
            w = self.board_magnifier_input_rect.width() or self.board_magnifier_projected_rect.width()
            self.board_magnifier_zoom_level = self.board_magnifier_projected_rect.width()/w
            self.board_magnifier_input_rect_animated = self.board_magnifier_input_rect

    def board_region_zoom_do_zooming(self):
        if self.board_magnifier_input_rect.width() != 0:

            # 0. подготовка
            input_center = self.board_magnifier_input_rect.center()
            self.board_magnifier_input_rect_animated = QRect(self.board_magnifier_input_rect)
            before_pos = QPointF(self.canvas_origin)

            # 1. сдвинуть изображение так, чтобы позиция input_center оказалась в центре окна
            diff = self.rect().center() - input_center
            pos = self.canvas_origin + diff
            self.canvas_origin = pos

            # 2. увеличить относительно центра окна на factor с помощью функции
            # которая умеет увеличивать масштаб
            factor_x = self.board_magnifier_projected_rect.width()/self.board_magnifier_input_rect.width()
            factor_y = self.board_magnifier_projected_rect.height()/self.board_magnifier_input_rect.height()
            scale_x, scale_y, origin = self.do_scale_board(1.0, False, False, True,
                                                    factor_x=factor_x, factor_y=factor_y, precalculate=True,
                                                    pivot=self.get_center_position())

            if self.isAnimationEffectsAllowed():
                self.animate_properties(
                    [
                        (self, "canvas_origin", before_pos, origin, self.update),
                        (self, "canvas_scale_x", self.canvas_scale_x, scale_x, self.update),
                        (self, "canvas_scale_y", self.canvas_scale_y, scale_y, self.update),
                        (self, "board_magnifier_input_rect_animated", self.board_magnifier_input_rect_animated, self.board_magnifier_projected_rect, self.update)
                    ],
                    anim_id="board_region_zoom_in",
                    duration=0.8,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.canvas_origin = origin
                self.canvas_scale_x = scale_x
                self.canvas_scale_y = scale_y

    def board_region_zoom_in_mousePressEvent(self, event):
        if not self.board_zoom_region_defined:
            self.board_region_zoom_in_input_started = True
            self.board_INPUT_POINT1 = event.pos()
            self.board_magnifier_input_rect = None
            self.board_orig_scale_x = self.canvas_scale_x
            self.board_orig_scale_y = self.canvas_scale_y
            self.board_orig_origin = self.canvas_origin
            # self.setCursor(Qt.CrossCursor)
            self.board_unselect_all_items()

    def board_region_zoom_in_mouseMoveEvent(self, event):
        if not self.board_zoom_region_defined:
            self.board_INPUT_POINT2 = event.pos()
            self.board_region_zoom_build_magnifier_input_rect()

    def board_region_zoom_in_mouseReleaseEvent(self, event):
        if not self.board_zoom_region_defined:
            self.board_INPUT_POINT2 = event.pos()
            self.board_region_zoom_build_magnifier_input_rect()
            if self.board_INPUT_POINT1 and self.board_INPUT_POINT2:
                self.board_zoom_region_defined = True
                self.board_region_zoom_do_zooming()
            else:
                self.board_region_zoom_do_cancel()
            self.board_region_zoom_in_input_started = False

    def board_region_zoom_in_draw(self, painter):
        if self.board_magnifier_input_rect:
            painter.setBrush(Qt.NoBrush)
            board_magnifier_input_rect = self.board_magnifier_input_rect
            board_magnifier_projected_rect = self.board_magnifier_projected_rect
            # if not self.board_zoom_region_defined:
            #     painter.setPen(QPen(Qt.white, 1, Qt.DashLine))
            #     painter.drawRect(board_magnifier_input_rect)
            painter.setPen(QPen(Qt.white, 1))
            if not self.board_zoom_region_defined or self.board_magnifier_input_rect_animated:
                if True:
                    painter.drawLine(self.board_magnifier_input_rect_animated.topLeft(),
                                                                        board_magnifier_projected_rect.topLeft())
                    painter.drawLine(self.board_magnifier_input_rect_animated.topRight(),
                                                                        board_magnifier_projected_rect.topRight())
                    painter.drawLine(self.board_magnifier_input_rect_animated.bottomLeft(),
                                                                    board_magnifier_projected_rect.bottomLeft())
                    painter.drawLine(self.board_magnifier_input_rect_animated.bottomRight(),
                                                                    board_magnifier_projected_rect.bottomRight())
                else:
                    painter.drawLine(board_magnifier_projected_rect.topLeft(), board_magnifier_projected_rect.bottomRight())
                    painter.drawLine(board_magnifier_projected_rect.bottomLeft(), board_magnifier_projected_rect.topRight())
            if not self.board_zoom_region_defined:
                value = math.ceil(self.board_magnifier_zoom_level*100)
                text = f"{value:,}%".replace(',', ' ')
                font = painter.font()
                font.setPixelSize(14)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignCenter, text)
            if self.board_magnifier_input_rect_animated:
                painter.drawRect(self.board_magnifier_input_rect_animated)
                painter.drawRect(board_magnifier_projected_rect)
            if self.board_zoom_region_defined:
                painter.setOpacity(0.8)
                painter.setClipping(True)
                r = QPainterPath()
                r.addRect(QRectF(self.rect()))
                r.addRect(QRectF(board_magnifier_projected_rect))
                painter.setClipPath(r)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(Qt.black))
                painter.drawRect(self.rect())
                painter.setClipping(False)
                painter.setOpacity(1.0)

    def board_retrieve_default_path_for_multifolder(self):
        filepath = self.get_user_data_filepath("default_miltifolder_path.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding="utf8") as file:
                lines = file.readlines()
                if lines:
                    default_path = lines[0].strip()
                    return default_path
        return "."

    def board_prepare_multifolder_board(self):
        default_path = self.board_retrieve_default_path_for_multifolder()

        selected_folders = []
        dialog = QFileDialog(self)
        dialog.setWindowTitle(_('Choose Directories'))
        dialog.setDirectory(default_path)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        for view in dialog.findChildren((QListView, QTreeView)):
            if isinstance(view.model(), QFileSystemModel):
                view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        combo = dialog.findChild(QComboBox, "lookInCombo", Qt.FindDirectChildrenOnly)
        combo.setEditable(True)
        edit = combo.lineEdit()
        def returnPressed():
            newPath = edit.text().strip()
            # check if the newPath is valid path
            if os.path.exists(newPath) and os.path.isdir(newPath):
                dialog.setDirectory(newPath)
            return False
        # edit.returnPressed.connect(returnPressed) # при нажатии Return одновременно срабатывает и кнопка диалога, пока не знаю как это исправить, поэтому поставил обработчик на любое изменение текста, а вставка пути к папке и есть изменение
        edit.textChanged.connect(returnPressed)
        button_box = dialog.findChild(QDialogButtonBox, "buttonBox", Qt.FindDirectChildrenOnly)
        # for ch in button_box.children():
        #     if isinstance(ch, QPushButton):
        #         ch.setDefault(False)
        #         ch.setAutoDefault(False)
        #     print(ch.objectName(), type(ch))

        if dialog.exec_() == QDialog.Accepted:
            selected_folders = dialog.selectedFiles()
        dialog.deleteLater()

        if not selected_folders:
            self.show_center_label(_('No folders selected!'), error=True)
            return

        cf = self.LibraryData().current_folder() #startapp virtual folder

        cf.images_list.clear()
        cf.set_current_index(0)

        for folder_path in selected_folders:
            self.LibraryData().handle_input_data(folder_path, pre_load=True)

            # переносим из всё в стартовую папку
            cf.images_list.extend(self.LibraryData().current_folder().images_list)

            # почему-то он иногда сообщает, что виртуальную доску удалить нельзя,
            # но по идее такого сообщения быть не должно
            # Пока просто буду делать проверку
            if cf is not self.LibraryData().current_folder():
                # удаляем информацию о загруженной папке
                self.LibraryData().delete_current_folder()

        for file_data in cf.images_list:
            file_data.folder_data = cf

        if not cf.images_list:
            self.show_center_label(_("No images found in selected folders!"), error=True)
            return

        self.LibraryData().make_folder_current(cf, write_view_history=False)

        if self.Globals.ENABLE_PROGRESSIVE_BOARD_LAYOUT:
            cf.board.force_vertical_layout = True # будет сброшен после окончания прогрессивной раскладки
            cf.previews_done = False
            self.Globals.ThumbnailsPreviewsThread(cf, self.Globals).start()
        else:
            # старая версия, когда прогрессивного расположения айтемов ещё не было реализовано
            with self.show_longtime_process_ongoing(self, _("Loading images to the board")):
                self.LibraryData().make_thumbnails_and_previews(cf, None)
                cf.board.ready = False
                self.board_prepare_items_layout_and_viewport(cf)
                self.board_do_place_items_in_column_or_row()

        self.update()

    def board_show_AD_toolbox(self, viewport_center=False):
        if self.AD_TOOLBOX.visible:
            self.board_hide_AD_toolbox()
        self.AD_TOOLBOX.visible = True
        if not self.AD_TOOLBOX.pos:
            # задаём положение только в первый раз,
            # чтобы далее положение сохранялось между следующими вызовами
            if viewport_center:
                pos = self.rect().center()
            else:
                pos = self.mapped_cursor_pos()
            self.AD_TOOLBOX.pos = pos
            self.AD_TOOLBOX.buttons_handler = self.board_AD_do_align_and_distribute

        self.update()

    def board_draw_AD_toolbox(self, painter):
        if self.AD_TOOLBOX.visible:

            rh = painter.renderHints()
            aa = rh & QPainter.Antialiasing
            spt = rh & QPainter.SmoothPixmapTransform
            haa = rh & QPainter.HighQualityAntialiasing
            ta = rh & QPainter.TextAntialiasing

            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

            painter.save()
            pen_width = 3
            bbr = self.board_bounding_rect.adjusted(-pen_width, -pen_width, pen_width, pen_width)

            atr = self.AD_TOOLBOX.rel_to_radiobutton
            if all((
                    bbr,
                    atr is not None and atr.get_active_id() == AlignType.ALIGN_TO_WHOLE_BOARD
                )):
                painter.setPen(QPen(QColor(200, 50, 50, 100), pen_width))
                painter.setBrush(Qt.NoBrush)
                bbr_viewport_mapped = self.board_MapRectToViewport(bbr)
                painter.drawRect(bbr_viewport_mapped)
                text = _("Whole board")
                font = painter.font()
                font.setPixelSize(30)
                painter.setFont(font)
                text_rect = painter.boundingRect(QRectF(), Qt.AlignLeft, text)
                text_rect.moveTopLeft(bbr_viewport_mapped.bottomLeft())
                painter.drawText(text_rect, Qt.AlignLeft, text)

            painter.setPen(QPen(ToolWindow.BORDER, 1))
            painter.setBrush(QBrush(ToolWindow.BCKG))
            font = painter.font()
            font.setBold(True)
            font.setFamily('Consolas')
            font.setPixelSize(15)
            painter.setFont(font)
            ToolWindow.layout(self, painter, 0)
            painter.setPen(QPen(Qt.red, 10))
            # painter.drawPoint(self.AD_TOOLBOX.pos)
            painter.restore()

            painter.setRenderHint(QPainter.Antialiasing, aa)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, spt)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, haa)
            painter.setRenderHint(QPainter.TextAntialiasing, ta)

    def board_hide_AD_toolbox(self):
        self.AD_TOOLBOX.visible = False
        self.AD_TOOLBOX.layout_ready = False
        self.AD_TOOLBOX.rows = []
        self.AD_TOOLBOX.current_row = None

    def board_AD_toolbox_pressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.AD_TOOLBOX.mouse_captured = False
            if ToolWindow.is_toolbox_inactive_area_click(self, event):
                self.AD_TOOLBOX.drag = True
                self.AD_TOOLBOX.drag_startpos = event.pos()
                self.AD_TOOLBOX.drag_toolbox_pos = QPoint(self.AD_TOOLBOX.pos)
                self.update()
                self.AD_TOOLBOX.mouse_captured = True
                return True
            if ToolWindow.toolbox_layout_mouse(self, event):
                self.update()
                self.AD_TOOLBOX.mouse_captured = True
                return True
        return False

    def board_AD_toolbox_moveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.AD_TOOLBOX.mouse_captured:
            if self.AD_TOOLBOX.drag:
                self.AD_TOOLBOX.pos = self.AD_TOOLBOX.drag_toolbox_pos + (event.pos() - self.AD_TOOLBOX.drag_startpos)
                self.update()
                return True
            if ToolWindow.toolbox_layout_mouse(self, event) or ToolWindow.is_toolbox_inactive_area_click(self, event):
                self.update()
                return True
            self.update()
            return False
        return False

    def board_AD_toolbox_releaseEvent(self, event):
        if event.button() == Qt.LeftButton or self.AD_TOOLBOX.mouse_captured:
            self.AD_TOOLBOX.mouse_captured = False
            if self.AD_TOOLBOX.drag:
                self.AD_TOOLBOX.drag = False
                self.update()
                return True
            else:
                btn_clicked = ToolWindow.toolbox_layout_mouse(self, event, call_handler=True)
                toolbox_clicked = ToolWindow.is_toolbox_inactive_area_click(self, event)
                self.update()
                return btn_clicked or toolbox_clicked
        return False

    def board_AD_toolbox_doubleClickEvent(self, event):
        check = ToolWindow.is_toolbox_inactive_area_click(self, event)
        if check:
            self.board_hide_AD_toolbox()
        return check

    def board_AD_do_align_and_distribute(self, btn_id, action_id, align_type):

        button_identifier = TOOLWINDOW_BUTTONSIDS.names()[btn_id]
        action_identifier = ToolActions.names()[action_id]
        align_identifier = AlignType.get_consts_and_their_names()[align_type]
        self.show_center_label(f'{button_identifier}, {action_identifier}, {align_identifier}')

        B_IDs = TOOLWINDOW_BUTTONSIDS

        class BoardItemHelper():
            def __init__(self, board_item):
                self.board_item = board_item
                self.bounding_rect = self.board_item.get_selection_area(canvas=None,
                    place_center_at_origin=False,
                    apply_global_scale=False,
                    apply_translation=True
                ).boundingRect()

            def move(self, dx, dy):
                self.board_item.position += QPointF(dx, dy)

            def width(self):
                return self.bounding_rect.width()

            def height(self):
                return self.bounding_rect.height()

            def left(self):
                return self.bounding_rect.left()

            def top(self):
                return self.bounding_rect.top()

            def right(self):
                return self.bounding_rect.right()

            def bottom(self):
                return self.bounding_rect.bottom()

            def hcenter(self):
                return self.bounding_rect.center().x()

            def vcenter(self):
                return self.bounding_rect.center().y()



        board_items = self.selected_items
        if not board_items:
            self.show_center_label(_('Nothing selected!'), error=True)
            return

        if action_id == ToolActions.DISTRIBUTE and len(board_items) < 3:
            self.show_center_label(_('Select at least 3 items!'), error=True)
            return

        items = [BoardItemHelper(bi) for bi in board_items]

        def get_target(get_func, result_func):

            if align_type == AlignType.ALIGN_TO_VIEWPORT:
                vr = self.board_MapToBoard(self.rect())
                return get_func(vr)

            elif align_type == AlignType.ALIGN_TO_SELECTION:
                return result_func(get_func(item) for item in items)

            elif align_type == AlignType.ALIGN_TO_WHOLE_BOARD:
                return get_func(self.board_bounding_rect)

            else:
                raise Exception("")

        def boundingBox(bihs):

            if align_type == AlignType.ALIGN_TO_VIEWPORT:
                return self.board_MapRectToBoard(self.rect())

            elif align_type == AlignType.ALIGN_TO_SELECTION:
                left = min(i.left() for i in bihs)
                right = max(i.right() for i in bihs)
                top = min(i.top() for i in bihs)
                bottom = max(i.bottom() for i in bihs)
                return QRectF(QPointF(left, top), QPointF(right, bottom))

            elif align_type == AlignType.ALIGN_TO_WHOLE_BOARD:
                return self.board_bounding_rect

            else:
                raise Exception("")

        def get_distribute_inputs(input_items, get_func, get_min_func, get_max_func):

            if align_type == AlignType.ALIGN_TO_VIEWPORT:
                br = self.board_MapRectToBoard(self.rect())
                return (
                    sum(get_func(item) for item in input_items),
                    get_min_func(br),
                    get_max_func(br),
                    True
                )

            elif align_type == AlignType.ALIGN_TO_SELECTION:
                return (
                    sum(get_func(item) for item in input_items),
                    get_min_func(items[0]),
                    get_max_func(items[-1]),
                    False
                )

            elif align_type == AlignType.ALIGN_TO_WHOLE_BOARD:
                bbr = self.board_bounding_rect
                return (
                    sum(get_func(item) for item in input_items),
                    get_min_func(bbr),
                    get_max_func(bbr),
                    True
                )

            else:
                raise Exception("")



        for item in items:
            self.board_stash_current_transform_to_history(item.board_item)


        if action_id == ToolActions.ALIGN:

            if btn_id == B_IDs.ALIGN_LEFT_EDGE:
                target = get_target(lambda i: i.left(), min)

                for item in items:
                    dx = target - item.left()
                    item.move(dx, 0)

            elif btn_id == B_IDs.ALIGN_TOP_EDGE:
                target = get_target(lambda i: i.top(), min)

                for item in items:
                    dy = target - item.top()
                    item.move(0, dy)

            elif btn_id == B_IDs.ALIGN_RIGHT_EDGE:
                target = get_target(lambda i: i.right(), max)

                for item in items:
                    dx = target - item.right()
                    item.move(dx, 0)

            elif btn_id == B_IDs.ALIGN_BOTTOM_EDGE:
                target = get_target(lambda i: i.bottom(), max)

                for item in items:
                    dy = target - item.bottom()
                    item.move(0, dy)

            elif btn_id == B_IDs.ALIGN_CENTER:
                bb = boundingBox(items)
                center = bb.left() + bb.width() / 2.0

                for item in items:
                    dx = center - item.hcenter()
                    item.move(dx, 0)

            elif btn_id == B_IDs.ALIGN_MIDDLE:
                bb = boundingBox(items)
                center = bb.top() + bb.height() / 2.0

                for item in items:
                    dy = center - item.vcenter()
                    item.move(0, dy)



        elif action_id == ToolActions.DISTRIBUTE:

            # проверять, что есть больше 3х объектов
            if btn_id == B_IDs.ALIGN_LEFT_EDGE:

                items = sorted(items, key=lambda i: i.left())

                first = items[0].left()
                last  = items[-1].left()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dx = target - items[i].left()
                    items[i].move(dx, 0)

            elif btn_id == B_IDs.ALIGN_TOP_EDGE:

                items = sorted(items, key=lambda i: i.top())

                first = items[0].top()
                last  = items[-1].top()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dy = target - items[i].top()
                    items[i].move(0, dy)

            elif btn_id == B_IDs.ALIGN_RIGHT_EDGE:

                items = sorted(items, key=lambda i: i.right())

                first = items[0].right()
                last  = items[-1].right()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dx = target - items[i].right()
                    items[i].move(dx, 0)

            elif btn_id == B_IDs.ALIGN_BOTTOM_EDGE:

                items = sorted(items, key=lambda i: i.bottom())

                first = items[0].bottom()
                last  = items[-1].bottom()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dy = target - items[i].bottom()
                    items[i].move(0, dy)

            elif btn_id == B_IDs.ALIGN_CENTER:

                items = sorted(items, key=lambda i: i.hcenter())

                first = items[0].hcenter()
                last  = items[-1].hcenter()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dx = target - items[i].hcenter()
                    items[i].move(dx, 0)

            elif btn_id == B_IDs.ALIGN_MIDDLE:

                items = sorted(items, key=lambda i: i.vcenter())

                first = items[0].vcenter()
                last  = items[-1].vcenter()

                step = (last - first) / (len(items) - 1)

                for i in range(len(items)):
                    target = first + i * step
                    dy = target - items[i].vcenter()
                    items[i].move(0, dy)

            elif btn_id == B_IDs.DISTRIBUTE_H:

                items = sorted(items, key=lambda i: i.left())

                # totalWidth = sum(item.width() for item in items)
                totalWidth, left, right, do_fix = get_distribute_inputs(items,
                    lambda i: i.width(),
                    lambda i: i.left(),
                    lambda i: i.right()
                )

                if do_fix:
                    left += items[0].width()/2.0
                    right += items[-1].width()/2.0

                totalSpace = (right - left) - totalWidth
                gap = totalSpace / (len(items) - 1)

                currentX = left

                for item in items:
                    dx = currentX - item.left()
                    item.move(dx, 0)
                    currentX += item.width() + gap


            elif btn_id == B_IDs.DISTRIBUTE_V:

                items = sorted(items, key=lambda i: i.top())

                # totalHeight = sum(item.height() for item in items)
                totalHeight, top, bottom, do_fix = get_distribute_inputs(items,
                    lambda i: i.height(),
                    lambda i: i.top(),
                    lambda i: i.bottom()
                )

                if do_fix:
                    top += items[0].height()/2.0
                    bottom += items[-1].height()/2.0

                totalSpace = (bottom - top) - totalHeight
                gap = totalSpace / (len(items) - 1)

                currentY = top

                for item in items:
                    dy = currentY - item.top()
                    item.move(0, dy)
                    currentY += item.height() + gap

        cf = self.LibraryData().current_folder()
        self.build_board_bounding_rect(cf)
        self.prepare_selection_box_widget(cf)
        self.update()

    def board_do_change_item_text(self, board_item):
        board_item.label = self.modal_input_field_text()

    def board_change_item_text(self, board_item):
        if board_item.type == BoardItem.types.ITEM_NODE:
            self.modal_input_field_show(
                partial(self.board_do_change_item_text, board_item),
                board_item.label,
            )
        else:
            self.show_center_label(_('This item not supported!'), error=True)



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
