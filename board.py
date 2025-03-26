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

from _utils import *
import hidapi_adapter
from board_note_item import BoardTextEditItemMixin

from hidapi_adapter import draw_gamepad_monitor, draw_gamepad_easing_monitor

import cbor2

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

COPY_SELECTED_BOARD_ITEMS_STR = '~#~KRUMASSAN:IMAGE:VIEWER:COPY:SELECTED:BOARD:ITEMS~#~'


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

class BoardItem():

    FRAME_PADDING = 40.0

    class types():
        ITEM_UNDEFINED = 0
        ITEM_IMAGE = 1
        ITEM_FOLDER = 2
        ITEM_GROUP = 3
        ITEM_FRAME = 4
        ITEM_NOTE = 5

    def __init__(self, item_type):
        super().__init__()
        self.type = item_type

        self.pixmap = None
        self.animated = False

        self.scale_x = 1.0
        self.scale_y = 1.0
        self.position = QPointF()
        self.rotation = 0

        self.__scale_x = None
        self.__scale_y = None
        self.__position = None
        self.__rotation = None

        self.__scale_x_init = None
        self.__scale_y_init = None
        self.__position_init = None

        self.board_index = 0
        self.board_group_index = None

        self.width = 1000
        self.height = 1000

        self.image_source_url = None

        self.label = ""
        self.status = ''

        self._tags = []
        self._comments = []

        self._selected = False
        self._touched = False
        self._show_file_info_overlay = False

        self.__label_ui_rect = None

    def set_tags(self, tags):
        self._tags = tags

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

    def retrieve_image_data(self):
        if self.type == BoardItem.types.ITEM_IMAGE:
            image_data = self.image_data
        elif self.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            image_data = self.item_folder_data.current_image()
        return image_data

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
        if self.type == self.types.ITEM_IMAGE:
            image_data = self.image_data
            text = f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
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

    def calculate_absolute_position(self, canvas=None, rel_pos=None):
        _scale_x = canvas.canvas_scale_x
        _scale_y = canvas.canvas_scale_y
        if rel_pos is None:
            rel_pos = self.position
        return QPointF(canvas.canvas_origin) + QPointF(rel_pos.x()*_scale_x, rel_pos.y()*_scale_y)

    def aspect_ratio(self):
        rect = self.get_size_rect(scaled=False)
        return rect.width()/rect.height()

    def get_size_rect(self, scaled=False):
        if scaled:
            if self.type == self.types.ITEM_IMAGE:
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
        else:
            scale_x = 1.0
            scale_y = 1.0
        if self.type == self.types.ITEM_IMAGE:
            return QRectF(0, 0, self.image_data.source_width*scale_x, self.image_data.source_height*scale_y)
        elif self.type == self.types.ITEM_FOLDER:
            return QRectF(0, 0, self.width*scale_x, self.height*scale_y)
        elif self.type == self.types.ITEM_GROUP:
            return QRectF(0, 0, self.width*scale_x, self.height*scale_y)
        elif self.type == self.types.ITEM_FRAME:
            return QRectF(0, 0, self.width*scale_x, self.height*scale_y)
        elif self.type == self.types.ITEM_NOTE:
            return QRectF(0, 0, self.width*scale_x, self.height*scale_y)

    def get_selection_area(self, canvas=None, place_center_at_origin=True, apply_global_scale=True, apply_translation=True):
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
        transform = self.get_transform_obj(canvas=canvas, apply_global_scale=apply_global_scale, apply_translation=apply_translation)
        return transform.map(polygon)

    def get_transform_obj(self, canvas=None, apply_local_scale=True, apply_translation=True, apply_global_scale=True):
        local_scaling = QTransform()
        rotation = QTransform()
        global_scaling = QTransform()
        translation = QTransform()
        if apply_local_scale:
            local_scaling.scale(self.scale_x, self.scale_y)
        rotation.rotate(self.rotation)
        if apply_translation:
            if apply_global_scale:
                pos = self.calculate_absolute_position(canvas=canvas)
                translation.translate(pos.x(), pos.y())
            else:
                translation.translate(self.position.x(), self.position.y())
        if apply_global_scale:
            global_scaling.scale(canvas.canvas_scale_x, canvas.canvas_scale_y)
        transform = local_scaling * rotation * global_scaling * translation
        return transform

    def update_corner_info(self):
        if self.type == BoardItem.types.ITEM_IMAGE:
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

    def board_viewport_reset(self, scale=True, position=True, scale_inplace=False):
        if scale:
            self.canvas_scale_x = 1.0
            self.canvas_scale_y = 1.0
        if scale_inplace:
            self.set_default_boardviewport_scale(keep_position=True, center_as_pivot=True)
        if position:
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
        self.selection_bounding_box = None

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
        self.board_PluginsInit()

        self.debug_file_io_filepath = _("[variable self.debug_file_io_filepath is not set!]")

        self.long_process_label_text =  _("request processing")

        self.board_SetCallbacks()

        self.show_longtime_process_ongoing = show_longtime_process_ongoing
        self.board_frame_items_text_rects = []

        self.board_PTWS_init()

        self.show_easeInExpo_monitor = False

        self.expo_values = []

        self._expo_save_timer = None

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

        if self.STNG_show_gamepad_monitor:
            draw_gamepad_monitor(self, painter, event)

        if self.show_easeInExpo_monitor:
            draw_gamepad_easing_monitor(self, painter, event)

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

    def board_PluginsInit(self):
        plugins_folder = os.path.join(os.path.dirname(__file__), 'board_plugins')
        if not os.path.exists(plugins_folder):
            return
        # print(f'init plugins in {plugins_folder}...')
        for cur_dir, dirs, filenames in os.walk(plugins_folder):
            for filename in filenames:
                plugin_filepath = os.path.join(cur_dir, filename)
                if plugin_filepath.lower().endswith('.py'):
                    self.board_PluginInit(plugin_filepath)
        # print('end init plugins')

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

    def board_PluginInit(self, filepath):
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
        cf = self.LibraryData().current_folder()
        for board_item in cf.board.items_list:
            item_selection_area = board_item.get_selection_area(canvas=self)
            is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
            if is_under_mouse:
                if board_item.type == BoardItem.types.ITEM_NOTE:
                    self.board_TextElementActivateEditMode(board_item)
                    break
                elif board_item.type == BoardItem.types.ITEM_IMAGE and (event.modifiers() & Qt.ShiftModifier):
                    self.LibraryData().show_that_imd_on_viewer_page(board_item.image_data)
                    self.show_center_label(_('You\'re on viewer page now'))
                else:
                    self.board_fit_content_on_screen(None, board_item=board_item)
                    break

    def board_keyPressEventDefault(self, event):
        key = event.key()

        ctrl_mod = bool(event.modifiers() & Qt.ControlModifier)
        only_ctrl_mode = bool(event.modifiers() == Qt.ControlModifier)

        if self.board_TextElementKeyPressEventHandler(event):
            return

        if key == Qt.Key_Space:
            self.board_fly_over(user_call=True)

        elif check_scancode_for(event, "O") and only_ctrl_mode:
            self.board_loadBoard()

        elif check_scancode_for(event, "S") and only_ctrl_mode:
            self.board_saveBoard()

        elif check_scancode_for(event, "M"):
            self.board_toggle_minimap()

        elif check_scancode_for(event, "I"):
            self.board_toggle_item_info_overlay()

        elif check_scancode_for(event, "A") and ctrl_mod:
            self.board_select_all_items()

        elif check_scancode_for(event, "C") and ctrl_mod:
            self.board_control_c()

        elif check_scancode_for(event, "V") and ctrl_mod:
            self.board_control_v()

        elif check_scancode_for(event, "B") and ctrl_mod:
            self.grab().save('grab.png')

        elif key == Qt.Key_Home:
            self.board_viewport_show_first_item()

        elif key == Qt.Key_End:
            self.board_viewport_show_last_item()

        elif key == Qt.Key_PageDown:
            self.board_move_viewport(_previous=True)

        elif key == Qt.Key_PageUp:
            self.board_move_viewport(_next=True)

        elif key in [Qt.Key_Return, Qt.Key_Enter]:
            self.board_navigate_camera_via_minimap()

        elif key in [Qt.Key_Plus]:
            self.board_fit_selected_items_on_screen()

    def board_keyReleaseEventDefault(self, event):
        key = event.key()

        if key == Qt.Key_Control:
            # for not item selection drag&drop
            self.board_cursor_setter()

        if key in [Qt.Key_Return, Qt.Key_Enter]:
            self.board_dive_inside_board_item()
        elif key in [Qt.Key_Backspace]:
            self.board_dive_inside_board_item(back_to_referer=True)
        elif key in [Qt.Key_Delete]:
            self.board_delete_selected_board_items()
        elif key in [Qt.Key_F12]:
            if not event.isAutoRepeat():
                self.board_activate_gamepad()
        elif key in [Qt.Key_Asterisk, Qt.Key_Slash, Qt.Key_Minus]:
            self.board_SCALE_selected_items(
                up=key==Qt.Key_Asterisk,
                down=key==Qt.Key_Slash,
                toggle_monitor=key==Qt.Key_Minus)

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
            image = QImage(event.mimeData().imageData())
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

    def board_ContextMenuPluginsDefault(self, event, contextMenu):
        pis = []
        for pi in self.board_plugins:
            if pi.add_to_menu:
                pis.append(pi)

        if pis:
            submenu = contextMenu.addMenu(_('Plugin Boards'))
            for pi in pis:
                create_board_for_plugin = submenu.addAction(pi.name)
                create_board_for_plugin.triggered.connect(pi.menu_callback)

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
        checkboxes.append(
            (_("Show debug graphics for transformation widget"),
            self.board_debug_transform_widget,
                partial(self.toggle_boolean_var_generic, self, 'board_debug_transform_widget')
            ),
        )
        contextMenu.addSeparator()

        self.board_ContextMenuPluginsDefault(event, contextMenu)

        if plugin_implant is not None:
            plugin_implant(self, contextMenu)

        board_load_multifolder = contextMenu.addAction(_('Multifolder board...'))
        board_load_multifolder.triggered.connect(self.board_prepare_multifolder_board)

        board_go_to_note = contextMenu.addAction(_("Go to the link in the note (Explorer or Browser)"))
        board_go_to_note.triggered.connect(partial(self.board_go_to_note, event))

        board_add_item_folder = contextMenu.addAction(_("Folder..."))
        board_add_item_folder.triggered.connect(self.board_add_item_folder)

        command_label = _("Group")
        sel_count = self.board_selected_items_count()
        if sel_count > 0:
            command_label = _("{0} (add selected items to it: {1})").format(command_label, sel_count)
        board_add_item_group = contextMenu.addAction(command_label)
        board_add_item_group.triggered.connect(self.board_add_item_group_noargs)

        board_add_item_frame = contextMenu.addAction(_("Frame"))
        board_add_item_frame.triggered.connect(self.board_add_item_frame)

        board_add_item_note = contextMenu.addAction(_("Note"))
        board_add_item_note.triggered.connect(self.board_add_item_note)

        board_load_highres = contextMenu.addAction(_("Force highres loading of all items right now (may take some time)"))
        board_load_highres.triggered.connect(self.board_load_highres)

        board_place_items_in_column = contextMenu.addAction(_('Place items in column'))
        board_place_items_in_column.triggered.connect(self.board_place_items_in_column)

        frame_item = self.board_menuActivatedOverFrameItem()
        if frame_item:
            board_change_frame_item_label = contextMenu.addAction(_('Change frame title \'{0}\'').format(frame_item.label))
            board_change_frame_item_label.triggered.connect(partial(self.board_change_frame_item_label, frame_item))

        if bool(self.is_context_menu_executed_over_group_item()):
            board_retrieve_current_from_group_item = contextMenu.addAction(_('Take current image from group and place nearby'))
            board_retrieve_current_from_group_item.triggered.connect(self.board_retrieve_current_from_group_item)

        contextMenu.addSeparator()

        board_open_in_app_copy = contextMenu.addAction(_("Open in viewer in separated app copy running in lite mode"))
        board_open_in_app_copy.triggered.connect(self.board_open_in_app_copy)

        board_open_in_google_chrome = contextMenu.addAction(_("Open in Google Chrome"))
        board_open_in_google_chrome.triggered.connect(self.board_open_in_google_chrome)

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
        folder_path = self.SettingsWindow.get_setting_value("inframed_folderpath")
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
            board_item = self.BoardItem(self.BoardItem.types.ITEM_UNDEFINED)
            self.board_serial_to_object_attributes(board_item, board_item_attributes, fd=fd)
            fd.board.items_list.append(board_item)

        fd.board.nonAutoSerialized = self.board_loadNonAutoSerialized(board_nonAutoSerialized)

        self.LibraryData().make_viewer_thumbnails_and_library_previews(fd, None)
        fd.board.ready = True
        self.LibraryData().load_board_data() #callbacks are set here
        found_pi = self.board_FindPlugin(fd.board.plugin_filename)
        if fd.board.prepareBoardOnFileLoad:
            if found_pi.preparePluginBoard:
                found_pi.preparePluginBoard(self, found_pi, file_loading=True)
        self.init_selection_bounding_box_widget(fd)
        self.build_board_bounding_rect(fd)

        return fd

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

            elif attr_type == 'ImageData':
                filepath, source_width, source_height = attr_data
                image_data = self.LibraryData().create_image_data(filepath, fd)
                fd.images_list.append(image_data)
                obj.image_data = image_data
                image_data.board_item = obj
                image_data.source_width = source_width
                image_data.source_height = source_height
                continue # не нужна дальнейшая обработка

            elif attr_type == 'FolderData':
                if isinstance(obj, self.BoardItem):
                    if obj.type == self.BoardItem.types.ITEM_FOLDER:
                        folder_path = attr_data
                        files = self.LibraryData().list_interest_files(folder_path, deep_scan=False, all_allowed=False)
                        item_folder_data = self.LibraryData().create_folder_data(folder_path, files, image_filepath=None, make_current=False)
                        self.LibraryData().make_viewer_thumbnails_and_library_previews(item_folder_data, None)
                        obj.item_folder_data = item_folder_data
                    elif obj.type == self.BoardItem.types.ITEM_GROUP:
                        board_dict = attr_data
                        _folder_data = self.board_recreate_board_from_serial(board_dict)
                        obj.item_folder_data = _folder_data
                        _folder_data.board.root_folder = fd
                        _folder_data.board.root_item = obj
                        self.LibraryData().make_viewer_thumbnails_and_library_previews(_folder_data, None)
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

            if attr_name.startswith("__"):
                continue

            elif exclude is not None and attr_name in exclude:
                continue

            elif attr_name in ['referer_board_folder', 'root_folder', 'root_item', 'nonAutoSerialized']:
                attr_data = None
                attr_type = 'NoneType'

            elif attr_type in ['_tags', '_comments']:
                attr_data = []
                attr_type = 'list'

            elif isinstance(attr_value, self.ImageData):
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
        board_folder_data = dict()

        # СОХРАНЕНИЕ ДАННЫХ
        board_folder_data.update({'is_virtual':  fd.virtual})
        board_folder_data.update({'folder_name': fd.folder_name})
        # сохранение атрибутов доски
        self.board_object_attributes_to_serial(board, board_attributes, exclude=('items_list', 'user_points'))

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

        board_nonAutoSerialized = self.board_dumpNonAutoSerialized(board.nonAutoSerialized)

        board_base.update({
            'board_items': board_items,
            'board_attributes': board_attributes,
            'board_folder_data': board_folder_data,
            'board_nonAutoSerialized': board_nonAutoSerialized,
        })
        return board_base

    def board_BuildBoardFilename(self, folder_path, filename):
        if self.STNG_use_cbor2_instead_of_json:
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

            folder_path = self.SettingsWindow.get_setting_value("inframed_folderpath")
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
        if self.STNG_use_cbor2_instead_of_json:
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
        __folder_data = None
        if back_to_referer:
            referer = cf.board.referer_board_folder
            if referer is not None:
                __folder_data = referer
        else:
            item = None
            for bi in cf.board.items_list:
                item_selection_area = bi.get_selection_area(canvas=self)
                is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                if is_under_mouse:
                    item = bi
                    break

            case1 = bi.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]
            case2 = bi.type == BoardItem.types.ITEM_IMAGE and bi.animated
            if not (case1 or case2):
                msg = _("You can dive inside groups, folders and animated items only!")
                self.show_center_label(msg, error=True)
                return
            if item is not None and hasattr(item, 'item_folder_data'):
                __folder_data = item.item_folder_data
            elif case2:
                __folder_data = fd = self.LibraryData().create_folder_data(_("ANIMATED FILE Virtual Folder"), [], image_filepath=None, make_current=False, virtual=True)
                bi.item_folder_data = fd

                movie = item.movie
                offset = QPointF(0, 0)
                create_image_data = self.LibraryData().create_image_data
                for i in range(movie.frameCount()):
                    movie.jumpToFrame(i)
                    pixmap = item.movie.currentPixmap()
                    fd_bi = BoardItem(BoardItem.types.ITEM_IMAGE)
                    fd_bi.pixmap = pixmap

                    fd_bi.image_data = create_image_data("", fd_bi)
                    fd_bi.image_data.board_item = fd_bi
                    fd.images_list.append(fd_bi.image_data)

                    fd.board.items_list.append(fd_bi)
                    fd_bi.board_index = i
                    fd_bi.scale_x = 1.0
                    fd_bi.scale_y = 1.0

                    fd_bi.position = offset + QPointF(pixmap.width(), pixmap.height())/2
                    offset += QPointF(pixmap.width(), 0)
                self.LibraryData().make_viewer_thumbnails_and_library_previews(fd, None, from_board_items=True)


                self.build_board_bounding_rect(fd)

                fd.previews_done = True
                fd.board.ready = True
                fd.board.root_folder = cf
                fd.board.root_item = bi

            else:
                self.show_center_label(_("Place cursor above a group item!"), error=True)
                return
        if __folder_data is not None:
            self.board_make_board_current(__folder_data)
            if not back_to_referer:
                self.LibraryData().current_folder().board.referer_board_folder = cf
            self.init_selection_bounding_box_widget(__folder_data)
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

    def prepare_board(self, folder_data):
        if self.Globals.DEBUG:
            offset = QPointF(0, 0) - QPointF(500, 0)
        else:
            offset = QPointF(0, 0)

        items_list = folder_data.board.items_list = []

        for image_data in folder_data.images_list:
            if not image_data.preview_error:
                board_item = BoardItem(BoardItem.types.ITEM_IMAGE)
                board_item.image_data = image_data
                image_data.board_item = board_item
                folder_data.board.items_list.append(board_item)
                board_item.board_index = self.retrieve_new_board_item_index()
                board_item.position = offset + QPointF(image_data.source_width, image_data.source_height)/2
                offset += QPointF(image_data.source_width, 0)
                if not self.Globals.lite_mode:
                    board_item._tags = self.LibraryData().get_tags_for_image_data(image_data)
                    board_item._comments = self.LibraryData().get_comments_for_image(image_data)

        self.build_board_bounding_rect(folder_data)

        folder_data.board.ready = True
        if self.STNG_board_move_to_current_on_first_open:
            if folder_data.current_image().board_item is not None:
                self.board_fit_content_on_screen(folder_data.current_image())
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

        if not self.is_board_ready():
            self.prepare_board(folder_data)
        else:

            painter.setPen(QPen(Qt.white, 1))
            font = painter.font()
            font.setWeight(300)
            font.setPixelSize(12)
            painter.setFont(font)

            self.images_drawn = 0
            self.board_item_under_mouse = None
            for board_item in folder_data.board.items_list:
                self.board_draw_item(painter, board_item)

            self.draw_selection(painter, folder_data)

            painter.drawText(self.rect().bottomLeft() + QPoint(50, -150), _("perfomance status: {0} images drawn").format(self.images_drawn))

    def draw_selection(self, painter, folder_data):
        painter.save()
        pen = QPen(self.selection_color, 1)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for board_item in folder_data.board.items_list:
            if board_item._selected:
                painter.drawPolygon(board_item.get_selection_area(canvas=self))
        painter.restore()

    def get_monitor_area(self):
        r = self.rect()
        points = [
            QPointF(r.topLeft()),
            QPointF(r.topRight()),
            QPointF(r.bottomRight()),
            QPointF(r.bottomLeft()),
        ]
        return QPolygonF(points)

    def board_draw_item(self, painter, board_item):
        if board_item.type in [BoardItem.types.ITEM_FRAME]:
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
            board_item.__label_ui_rect = None
            show_text = True
            if rect.width() > area.boundingRect().width():
                show_text = False
                if area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill):
                    show_text = True
            else:
                show_text = True

            if show_text:
                board_item.__label_ui_rect = rect
                painter.drawText(rect, alignment, text)
                self.board_frame_items_text_rects.append((board_item, rect, area.boundingRect()))

            painter.setFont(before_font)

        elif board_item.type in [BoardItem.types.ITEM_NOTE]:

            if self.Globals.DISABLE_ITEM_DISTORTION_FIXER:
                self.board_TextElementDrawOnCanvas(painter, board_item, False)
            else:
                board_item.enable_distortion_fixer()
                self.board_TextElementDrawOnCanvas(painter, board_item, False)
                board_item.disable_distortion_fixer()

        else:

            image_data = board_item.retrieve_image_data()

            selection_area = board_item.get_selection_area(canvas=self)

            if selection_area.intersected(self.get_monitor_area()).boundingRect().isNull():
                if self.STNG_board_unloading:
                    self.trigger_board_item_pixmap_unloading(board_item)

            else:
                self.images_drawn += 1
                transform = board_item.get_transform_obj(canvas=self)

                painter.setTransform(transform)
                item_rect = board_item.get_size_rect()

                if board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
                    item_rect = fit_rect_into_rect(QRectF(0, 0, image_data.source_width, image_data.source_height), item_rect, float_mode=True)

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

                image_to_draw = None
                selection_area_rect = selection_area.boundingRect()
                if selection_area_rect.width() < 250 or selection_area_rect.height() < 250:
                    image_to_draw = image_data.preview
                else:
                    self.trigger_board_item_pixmap_loading(board_item)
                    image_to_draw = board_item.pixmap

                if image_to_draw:
                    painter.drawPixmap(item_rect, image_to_draw, QRectF(QPointF(0, 0), QSizeF(image_to_draw.size())))

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

                case4 = selection_area.containsPoint(QPointF(self.mapped_cursor_pos()), Qt.WindingFill)

                if show_tag_data and case4:
                    self.draw_board_item_tags(painter, selection_area_rect, board_item._tags)


                if case4:
                    self.board_item_under_mouse = board_item

                selection_area_bounding_rect = selection_area.boundingRect()

                if board_item._show_file_info_overlay:
                    text = board_item.info_text()
                    alignment = Qt.AlignCenter

                    painter.save()
                    text_rect = painter.boundingRect(selection_area_bounding_rect, alignment, text)
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
                        text_rect = painter.boundingRect(selection_area_bounding_rect, alignment, board_item.status)
                        text_rect.adjust(-5, -5, 5, 5)
                        text_rect.moveTopLeft(selection_area[0])

                        if text_rect.width() < selection_area_bounding_rect.width():
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

        dist = QVector2D(self.get_center_position() - board_item.calculate_absolute_position(canvas=self)).length()

        if dist > 10000.0:
            board_item.pixmap = None
            board_item.movie = None

            image_data = board_item.retrieve_image_data()
            filepath = image_data.filepath
            msg = f'unloaded from board: {filepath}'
            print(msg)

    def trigger_board_item_pixmap_loading(self, board_item):
        if board_item.pixmap is not None:
            return

        def show_msg(filepath):
            msg = f'loaded to board: {filepath}'
            print(msg)

        def __load_animated(filepath):
            if self.LibraryData().last_apng_check_result:
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
            board_item.animated = False
            show_msg(filepath)

        def __load_static(filepath):
            board_item.pixmap = load_image_respect_orientation(filepath)
            board_item.animated = False
            show_msg(filepath)

        if board_item.type == BoardItem.types.ITEM_IMAGE:
            filepath = board_item.image_data.filepath
        elif board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            filepath = board_item.item_folder_data.current_image().filepath

        if filepath == "":
            # для пустых групп (item_GROUP)
            board_item.pixmap = board_item.item_folder_data.current_image().preview
        else:
            try:
                board_item.pixmap = QPixmap()
                self.LibraryData().reset_apng_check_result()
                animated = self.LibraryData().is_gif_file(filepath) or self.LibraryData().is_webp_file_animated(filepath) or self.LibraryData().is_apng_file_animated(filepath)
                if animated:
                    __load_animated(filepath)
                elif self.LibraryData().is_svg_file(filepath):
                    __load_svg(filepath)
                else:
                    __load_static(filepath)
            except Exception as e:
                board_item.pixmap = QPixmap()

    def boards_generate_expo_values(self):
        exp = self.STNG_gamepad_move_stick_ease_in_expo_param
        SAMPLES = 50
        values = []
        for n in range(SAMPLES+1):
            x = n/SAMPLES
            y = math.pow(x, exp)
            values.append((x, y))
        self.expo_values = values

    def boards_save_expo_to_app_settings(self):
        def callback():
            self.SettingsWindow.store_to_disk()
            self.show_center_label('easeInExpo saved to settings file!')

        if self._expo_save_timer is not None:
            self._expo_save_timer.stop()

        millisecs_delay = 2000
        self._expo_save_timer = timer = QTimer(self)
        timer.setInterval(millisecs_delay)
        timer.timeout.connect(callback)
        timer.setSingleShot(True)
        timer.start()

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

    def board_draw_main_default(self, painter, event):
        cf = self.LibraryData().current_folder()
        if cf.previews_done:
            if self.Globals.DEBUG or self.STNG_board_draw_grid:
                self.board_draw_grid(painter)
            self.board_draw_content(painter, cf)
        else:
            self.board_draw_wait_label(painter)


        if self.Globals.DEBUG or self.STNG_board_draw_canvas_origin:
            self.board_draw_canvas_origin(painter)

        self.board_draw_user_points(painter, cf)

        self.board_draw_selection_mouse_rect(painter)
        self.board_draw_selection_transform_box(painter)
        self.board_region_zoom_in_draw(painter)

        if self.Globals.DEBUG or self.STNG_board_draw_origin_compass:
            self.board_draw_origin_compass(painter)

        self.board_draw_cursor_text(painter)

        self.board_draw_diving_notification(painter, cf)

        self.board_draw_board_info(painter, cf)

        self.board_draw_minimap(painter)

        self.board_draw_long_process_label(painter)

    def board_draw_board_info(self, painter, current_folder):
        before_font = painter.font()
        before_pen = painter.pen()

        lines = []
        board = current_folder.board
        if current_folder.virtual:
            lines.append(_('Virtual folder board: {}').format(current_folder.folder_path))
        else:
            lines.append(_('Board folder: {}').format(current_folder.folder_path))
        if board.plugin_filename:
            lines.append(_('File-plugin name: {}').format(board.plugin_filename))
        else:
            lines.append(_('This board has no plugin attached'))
        lines.append(_('Current item index: {}').format(board.current_item_index))
        lines.append(_('Current item-group index: {}').format(board.current_item_group_index))
        lines.append(_('Board bounding rect: {}').format(board.bounding_rect))

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
        pos = self.canvas_origin + QPoint(100, -100)
        alignment = Qt.AlignLeft
        rect = painter.boundingRect(self.rect(), alignment, text)
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
            _text_rect = text_rect.adjusted(-4, -4, 4, 4)
            painter.setBrush(QBrush(QColor(220, 50, 50)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(_text_rect)
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
        if self.selection_bounding_box is not None:

            painter.setOpacity(self.board_selection_transform_box_opacity)
            pen = QPen(self.selection_color, 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(self.selection_bounding_box)

            default_pen = painter.pen()

            # roration activation areas
            painter.setPen(QPen(Qt.red))
            for index, point in enumerate(self.selection_bounding_box):
                points_count = self.selection_bounding_box.size()
                prev_point_index = (index-1) % points_count
                next_point_index = (index+1) % points_count
                prev_point = self.selection_bounding_box[prev_point_index]
                next_point = self.selection_bounding_box[next_point_index]

                a = QVector2D(point - prev_point).normalized().toPointF()
                b = QVector2D(point - next_point).normalized().toPointF()
                a *= self.STNG_transform_widget_activation_area_size*2
                b *= self.STNG_transform_widget_activation_area_size*2
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
            default_pen.setWidthF(self.STNG_transform_widget_activation_area_size)
            default_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(default_pen)

            for index, point in enumerate(self.selection_bounding_box):
                painter.drawPoint(point)

            if self.board_debug_transform_widget and self.scaling_ongoing and self.scaling_pivot_point is not None:
                pivot = self.scaling_pivot_point
                x_axis = self.scaling_pivot_point_x_axis
                y_axis = self.scaling_pivot_point_y_axis

                painter.setPen(QPen(Qt.red, 4))
                painter.drawLine(pivot, pivot+x_axis)
                painter.setPen(QPen(Qt.green, 4))
                painter.drawLine(pivot, pivot+y_axis)
                if self.scaling_vector is not None:
                    painter.setPen(QPen(Qt.yellow, 4))
                    painter.drawLine(pivot, pivot + self.scaling_vector)

                if self.proportional_scaling_vector is not None:
                    painter.setPen(QPen(Qt.darkGray, 4))
                    painter.drawLine(pivot, pivot + self.proportional_scaling_vector)

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

    def corner_buttons_cursor_glitch_fixer(self):
        cb1 = self.over_corner_button()
        cb2 = self.over_corner_button(corner_attr="topLeft")
        cb3 = self.over_corner_menu(corner_attr="topLeft")
        return any((cb1, cb2, cb3))

    def board_cursor_setter(self):
        # защита от глитча курсора в угловых кнопках и угловом меню
        if self.corner_buttons_cursor_glitch_fixer():
            return

        if self.scaling_ongoing:
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
        elif self.selection_bounding_box is not None:
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
                # image_data = board_item.retrieve_image_data()

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
        self.init_selection_bounding_box_widget(current_folder)

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
            folder_data = cf
        else:
            folder_data = cf.board.root_folder

        gi = self.get_removed_items_group(folder_data)

        # здесь решаем что удалить безвозвратно
        for bi in self.selected_items:
            if bi.type is BoardItem.types.ITEM_FRAME:
                items_list.remove(bi)
            if bi.type is BoardItem.types.ITEM_IMAGE:
                pass
            if bi.type is BoardItem.types.ITEM_GROUP:
                if bi.board_group_index > 9:
                    self.move_items_to_group(
                        item_group=gi,
                        items=bi.item_folder_data.board.items_list,
                        items_folder=bi.item_folder_data
                    )
                    items_list.remove(bi)

        self.move_items_to_group(item_group=gi, items=self.selected_items)

        self.init_selection_bounding_box_widget(cf)
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
            bi = im_data.board_item
            item_folder_data.board.items_list.remove(bi)

            current_board.items_list.append(bi)
            bi.image_data.folder_data = current_folder
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
            gi.position = self.board_MapToBoard(self.context_menu_exec_point)
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
        ni.position = self.board_MapToBoard(self.context_menu_exec_point)
        self.board_TextElementAttributesInitOnCreation(ni)
        self.board_select_items([ni])
        self.update()

    def board_add_item_folder(self, folder_path=None):
        if folder_path is None:
            folder_path = str(QFileDialog.getExistingDirectory(None, _("Choose folder with images in it")))
        if folder_path:
            with self.show_longtime_process_ongoing(self, _("Loading folder to the board")):
                files = self.LibraryData().list_interest_files(folder_path, deep_scan=False, all_allowed=False)
                item_folder_data = self.LibraryData().create_folder_data(folder_path, files, image_filepath=None, make_current=False)
                self.LibraryData().make_viewer_thumbnails_and_library_previews(item_folder_data, None)
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
                items_folder.images_list.remove(bi.image_data)
                item_fd.images_list.append(bi.image_data)
                bi.image_data.folder_data = item_fd

            rect = bi.get_size_rect(scaled=True)
            width = rect.width()
            height = rect.height()
            bi.position = topLeftCorner + QPointF(width, height)/2
            topLeftCorner += QPointF(width, 0)

        group_item.update_corner_info()
        if update_selection:
            self.board_select_items([group_item])

    def board_add_item_frame(self):
        if self.selection_bounding_box is None:
            self.show_center_label(_("No items selected!"), error=True)
        else:
            folder_data = self.LibraryData().current_folder()
            bi = BoardItem(BoardItem.types.ITEM_FRAME)
            bi.board_index = self.retrieve_new_board_item_index()
            folder_data.board.items_list.append(bi)

            selection_bounding_rect = self.selection_bounding_box.boundingRect()
            bi.position = self.board_MapToBoard(selection_bounding_rect.center())
            bi.width = selection_bounding_rect.width() / self.canvas_scale_x
            bi.height = selection_bounding_rect.height() / self.canvas_scale_y
            bi.width += BoardItem.FRAME_PADDING
            bi.height += BoardItem.FRAME_PADDING
            bi.label = _("FRAME ITEM")
            self.board_select_items([bi])

        self.update()

    def isLeftClickAndNoModifiers(self, event):
        return event.buttons() == Qt.LeftButton and event.modifiers() == Qt.NoModifier

    def isLeftClickAndAlt(self, event):
        return (event.buttons() == Qt.LeftButton or event.button() == Qt.LeftButton) and event.modifiers() == Qt.AltModifier

    def is_pos_over_item_area(self, item, position):
        sa = item.get_selection_area(canvas=self)
        return sa.containsPoint(position, Qt.WindingFill) or \
                (item.type == BoardItem.types.ITEM_FRAME and item.__label_ui_rect is not None and item.__label_ui_rect.contains(position))

    def is_over_translation_activation_area(self, position):
        for item in self.selected_items:
            if self.is_pos_over_item_area(item, position):
                return True
        return False

    def board_START_selected_items_TRANSLATION(self, event_pos, viewport_zoom_changed=False):
        self.start_translation_pos = QPointF(self.board_MapToBoard(event_pos))
        current_folder = self.LibraryData().current_folder()
        items_list = current_folder.board.items_list
        if viewport_zoom_changed:
            for board_item in items_list:
                board_item.position = board_item.__position

        for board_item in items_list:
            board_item.__position = QPointF(board_item.position)
            if not viewport_zoom_changed:
                board_item.__position_init = QPointF(board_item.position)
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
            delta = QPointF(self.board_MapToBoard(event_pos)) - self.start_translation_pos
            if self.translation_ongoing:
                for board_item in current_folder.board.items_list:
                    if board_item._selected:
                        board_item.position = board_item.__position + delta
                        if board_item.type == BoardItem.types.ITEM_FRAME:
                            for ch_bi in board_item._children_items:
                                ch_bi.position = ch_bi.__position + delta
                self.init_selection_bounding_box_widget(current_folder)
                self.check_item_group_under_mouse()
        else:
            self.translation_ongoing = False

    def board_FINISH_selected_items_TRANSLATION(self, event, cancel=False):
        self.start_translation_pos = None
        current_folder = self.LibraryData().current_folder()
        for board_item in current_folder.board.items_list:
            if cancel:
                board_item.position = QPointF(board_item.__position_init)
            else:
                board_item.__position = None
            board_item._children_items = []
        self.translation_ongoing = False
        if cancel:
            pass
        else:
            self.build_board_bounding_rect(current_folder)
            self.move_items_to_group(items=self.selected_items)
            self.check_item_group_under_mouse(reset=True)

    def board_CANCEL_selected_items_TRANSLATION(self):
        if self.translation_ongoing:
            self.board_FINISH_selected_items_TRANSLATION(None, cancel=True)
            self.update_selection_bouding_box()
            self.transform_cancelled = True
            print('cancel translation')

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
        found_items = list(sorted(found_items, key=lambda x: x.calc_area))
        if found_items:
            return found_items[0]
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
        self.init_selection_bounding_box_widget(current_folder)

    def init_selection_bounding_box_widget(self, folder_data):
        self.selected_items = []
        for board_item in folder_data.board.items_list:
            if board_item._selected:
                self.selected_items.append(board_item)
        self.update_selection_bouding_box()

    def board_unselect_all_items(self):
        cf = self.LibraryData().current_folder()
        for board_item in cf.board.items_list:
            board_item._selected = False
        self.init_selection_bounding_box_widget(cf)

    def board_select_all_items(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.items_list:
            bi._selected = True
        self.update()

    def update_selection_bouding_box(self):
        self.selection_bounding_box = None
        if len(self.selected_items) == 1:
            self.selection_bounding_box = self.selected_items[0].get_selection_area(canvas=self)
        elif len(self.selected_items) > 1:
            bounding_box = QRectF()
            for board_item in self.selected_items:
                bounding_box = bounding_box.united(board_item.get_selection_area(canvas=self).boundingRect())
            self.selection_bounding_box = QPolygonF([
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

    def board_START_selected_items_ROTATION(self, event_pos, viewport_zoom_changed=False):
        self.rotation_ongoing = True
        if viewport_zoom_changed:
            for bi in self.selected_items:
                # лучше закоментить этот код, так адекватнее и правильнее, как мне кажется
                # if bi.__rotation is not None:
                #     bi.rotation = bi.__rotation
                if bi.type != BoardItem.types.ITEM_FRAME:
                    if bi.__position is not None:
                        bi.position = bi.__position

            self.update_selection_bouding_box()

        self.__selection_bounding_box = QPolygonF(self.selection_bounding_box)
        pivot = self.selection_bounding_box.boundingRect().center()
        radius_vector = QPointF(event_pos) - pivot
        self.rotation_start_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())

        points_count = self.selection_bounding_box.size()
        index = self.widget_active_point_index
        pivot_point_index = (index+2) % points_count
        self.rotation_pivot_corner_point = QPointF(self.selection_bounding_box[pivot_point_index])

        self.rotation_pivot_center_point = self.__selection_bounding_box.boundingRect().center()

        for bi in self.selected_items:
            bi.__rotation = bi.rotation
            bi.__position = QPointF(bi.position)

            if not viewport_zoom_changed:
                bi.__rotation_init = bi.rotation
                bi.__position_init = QPointF(bi.position)

    def step_rotation(self, rotation_value):
        interval = 45.0
        # формулу подбирал в графическом калькуляторе desmos.com/calculator
        # value = math.floor((rotation_value-interval/2.0)/interval)*interval+interval
        # ниже упрощённый вариант
        value = (math.floor(rotation_value/interval-0.5)+1.0)*interval
        return value

    def board_DO_selected_items_ROTATION(self, event_pos):
        self.start_translation_pos = None

        multi_item_mode = len(self.selected_items) > 1
        ctrl_mod = QApplication.queryKeyboardModifiers() & Qt.ControlModifier
        alt_mod = QApplication.queryKeyboardModifiers() & Qt.AltModifier
        use_corner_pivot = alt_mod
        if use_corner_pivot:
            pivot = self.rotation_pivot_corner_point
        else:
            pivot = self.rotation_pivot_center_point
        radius_vector = QPointF(event_pos) - pivot
        self.rotation_end_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())
        self.rotation_delta = self.rotation_end_angle_rad - self.rotation_start_angle_rad
        rotation_delta_degrees = math.degrees(self.rotation_delta)
        if multi_item_mode and ctrl_mod:
            rotation_delta_degrees = self.step_rotation(rotation_delta_degrees)
        rotation = QTransform()
        if ctrl_mod:
            rotation.rotate(self.step_rotation(rotation_delta_degrees))
        else:
            rotation.rotate(rotation_delta_degrees)
        for bi in self.selected_items:
            # rotation component
            if bi.type == BoardItem.types.ITEM_FRAME:
                continue
            bi.rotation = bi.__rotation + rotation_delta_degrees
            if not multi_item_mode and ctrl_mod:
                bi.rotation = self.step_rotation(bi.rotation)
            # position component
            pos = bi.calculate_absolute_position(canvas=self, rel_pos=bi.__position)
            pos_radius_vector = pos - pivot
            pos_radius_vector = rotation.map(pos_radius_vector)
            new_absolute_position = pivot + pos_radius_vector
            rel_pos_global_scaled = new_absolute_position - self.canvas_origin
            new_position = QPointF(rel_pos_global_scaled.x()/self.canvas_scale_x, rel_pos_global_scaled.y()/self.canvas_scale_y)
            bi.position = new_position
        # bounding box transformation
        translate_to_coord_origin = QTransform()
        translate_back_to_place = QTransform()
        if use_corner_pivot:
            offset = - self.rotation_pivot_corner_point
        else:
            offset = - self.__selection_bounding_box.boundingRect().center()
        translate_to_coord_origin.translate(offset.x(), offset.y())
        offset = - offset
        translate_back_to_place.translate(offset.x(), offset.y())
        transform = translate_to_coord_origin * rotation * translate_back_to_place
        self.selection_bounding_box = transform.map(self.__selection_bounding_box)

    def board_FINISH_selected_items_ROTATION(self, event, cancel=False):
        self.rotation_ongoing = False
        cf = self.LibraryData().current_folder()
        if cancel:
            for bi in self.selected_items:
                bi.rotation = bi.__rotation_init
                bi.position = QPointF(bi.__position_init)
        else:
            self.init_selection_bounding_box_widget(cf)
            self.build_board_bounding_rect(cf)

    def board_CANCEL_selected_items_ROTATION(self):
        if self.rotation_ongoing:
            self.board_FINISH_selected_items_ROTATION(None, cancel=True)
            self.update_selection_bouding_box()
            self.transform_cancelled = True
            print('cancel rotation')

    def is_over_scaling_activation_area(self, position):
        if self.selection_bounding_box is not None:
            enumerated = list(enumerate(self.selection_bounding_box))
            enumerated.insert(0, enumerated.pop(2))
            for index, point in enumerated:
                diff = point - QPointF(position)
                if QVector2D(diff).length() < self.STNG_transform_widget_activation_area_size:
                    self.scaling_active_point_index = index
                    self.widget_active_point_index = index
                    return True
        self.scaling_active_point_index = None
        self.widget_active_point_index = None
        return False

    def board_get_cursor_angle(self):
        points_count = self.selection_bounding_box.size()
        index = self.widget_active_point_index
        pivot_point_index = (index+2) % points_count
        prev_point_index = (pivot_point_index-1) % points_count
        next_point_index = (pivot_point_index+1) % points_count
        prev_point = self.selection_bounding_box[prev_point_index]
        next_point = self.selection_bounding_box[next_point_index]
        __scaling_pivot_corner_point = QPointF(self.selection_bounding_box[pivot_point_index])

        x_axis = QVector2D(next_point - __scaling_pivot_corner_point).normalized().toPointF()
        y_axis = QVector2D(prev_point - __scaling_pivot_corner_point).normalized().toPointF()

        __vector  = x_axis + y_axis
        return math.degrees(math.atan2(__vector.y(), __vector.x()))

    def board_START_selected_items_SCALING(self, event, viewport_zoom_changed=False):
        self.scaling_ongoing = True

        if viewport_zoom_changed:
            for bi in self.selected_items:
                if bi.__scale_x is not None:
                    bi.scale_x = bi.__scale_x
                if bi.__scale_y is not None:
                    bi.scale_y = bi.__scale_y
                if bi.__position is not None:
                    bi.position = bi.__position

            self.update_selection_bouding_box()

        self.__selection_bounding_box = QPolygonF(self.selection_bounding_box)

        bbw = self.selection_bounding_box.boundingRect().width()
        bbh = self.selection_bounding_box.boundingRect().height()
        self.selection_bounding_box_aspect_ratio = bbw/bbh
        self.selection_bounding_box_center = self.selection_bounding_box.boundingRect().center()

        points_count = self.selection_bounding_box.size()

        # заранее высчитываем пивот и оси для модификатора Alt;
        # для удобства вычислений оси заимствуем у нулевой точки и укорачиваем их в два раза
        index = 0
        pivot_point_index = (index+2) % points_count
        prev_point_index = (pivot_point_index-1) % points_count
        next_point_index = (pivot_point_index+1) % points_count
        prev_point = self.selection_bounding_box[prev_point_index]
        next_point = self.selection_bounding_box[next_point_index]
        spp = QPointF(self.selection_bounding_box[pivot_point_index])

        self.scaling_pivot_center_point = self.selection_bounding_box_center

        __x_axis = QVector2D(next_point - spp).toPointF()
        __y_axis = QVector2D(prev_point - spp).toPointF()

        self.scaling_from_center_x_axis = __x_axis/2.0
        self.scaling_from_center_y_axis = __y_axis/2.0

        # высчитываем пивот и оси для обычного скейла относительно угла
        index = self.scaling_active_point_index
        pivot_point_index = (index+2) % points_count
        prev_point_index = (pivot_point_index-1) % points_count
        next_point_index = (pivot_point_index+1) % points_count
        prev_point = self.selection_bounding_box[prev_point_index]
        next_point = self.selection_bounding_box[next_point_index]
        self.scaling_pivot_corner_point = QPointF(self.selection_bounding_box[pivot_point_index])

        x_axis = QVector2D(next_point - self.scaling_pivot_corner_point).toPointF()
        y_axis = QVector2D(prev_point - self.scaling_pivot_corner_point).toPointF()

        if self.scaling_active_point_index % 2 == 1:
            x_axis, y_axis = y_axis, x_axis

        self.scaling_x_axis = x_axis
        self.scaling_y_axis = y_axis

        for bi in self.selected_items:
            bi.__scale_x = bi.scale_x
            bi.__scale_y = bi.scale_y
            bi.__position = QPointF(bi.position)
            if not viewport_zoom_changed:
                bi.__scale_x_init = bi.scale_x
                bi.__scale_y_init = bi.scale_y
                bi.__position_init = QPointF(bi.position)
            position_vec = bi.calculate_absolute_position(canvas=self) - self.scaling_pivot_corner_point
            bi.normalized_pos_x, bi.normalized_pos_y = self.calculate_vector_projection_factors(x_axis, y_axis, position_vec)
            position_vec_center = bi.calculate_absolute_position(canvas=self) - self.scaling_pivot_center_point
            # умножение на 2 позволит коду board_DO_selected_items_SCALING отработать как нужно в случае масштабирования нескольких выделенных айтемов
            position_vec_center *= 2
            bi.normalized_pos_x_center, bi.normalized_pos_y_center = self.calculate_vector_projection_factors(x_axis, y_axis, position_vec_center)

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
            pivot = self.scaling_pivot_center_point
            scaling_x_axis = self.scaling_from_center_x_axis
            scaling_y_axis = self.scaling_from_center_y_axis
        else:
            pivot = self.scaling_pivot_corner_point
            scaling_x_axis = self.scaling_x_axis
            scaling_y_axis = self.scaling_y_axis

        # updating for draw functions
        self.scaling_pivot_point = pivot
        self.scaling_pivot_point_x_axis = scaling_x_axis
        self.scaling_pivot_point_y_axis = scaling_y_axis

        for bi in self.selected_items:
            __scaling_vector =  QVector2D(QPointF(event_pos) - pivot) # не вытаскивать вычисления вектора из цикла!
            # принудительно задаётся минимальный скейл, значение в экранных координатах
            # MIN_LENGTH = 100.0
            # if __scaling_vector.length() < MIN_LENGTH:
            #     __scaling_vector = __scaling_vector.normalized()*MIN_LENGTH
            self.scaling_vector = scaling_vector = __scaling_vector.toPointF()

            if proportional_scaling:
                x_axis = QVector2D(scaling_x_axis).normalized()
                y_axis = QVector2D(scaling_y_axis).normalized()
                x_sign = math.copysign(1.0, QVector2D.dotProduct(x_axis, QVector2D(self.scaling_vector).normalized()))
                y_sign = math.copysign(1.0, QVector2D.dotProduct(y_axis, QVector2D(self.scaling_vector).normalized()))
                if multi_item_mode:
                    aspect_ratio = self.selection_bounding_box_aspect_ratio
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

            if center_is_pivot and multi_item_mode:
                # это решение убирает флип скейла по обеим осям
                # но также лишает возможности отзеркаливать,
                # если курсор мыши завести с противоположной стороны относительно пивота
                x_factor = abs(x_factor)
                y_factor = abs(y_factor)

            bi.scale_x = bi.__scale_x * x_factor
            bi.scale_y = bi.__scale_y * y_factor
            if proportional_scaling and not multi_item_mode and not center_is_pivot:
                bi.scale_x = math.copysign(1.0, bi.scale_x)*abs(bi.scale_y)

            # position component
            if center_is_pivot and not multi_item_mode:
                bi.position = bi.__position

            elif center_is_pivot and multi_item_mode:
                scaling = QTransform()
                # эти нормализованные координаты актуальны для пропорционального и непропорционального масштабирования
                scaling.scale(bi.normalized_pos_x_center, bi.normalized_pos_y_center)
                mapped_scaling_vector = scaling.map(scaling_vector)
                new_viewport_position = pivot + mapped_scaling_vector
                rel_pos_global_scaled = new_viewport_position - self.canvas_origin
                new_rel_pos = QPointF(rel_pos_global_scaled.x()/self.canvas_scale_x, rel_pos_global_scaled.y()/self.canvas_scale_y)
                bi.position = new_rel_pos

            else:
                scaling = QTransform()
                # эти нормализованные координаты актуальны для пропорционального и непропорционального масштабирования
                scaling.scale(bi.normalized_pos_x, bi.normalized_pos_y)
                mapped_scaling_vector = scaling.map(scaling_vector)
                new_viewport_position = pivot + mapped_scaling_vector
                rel_pos_viewport_scaled = new_viewport_position - self.canvas_origin
                new_rel_pos = QPointF(rel_pos_viewport_scaled.x()/self.canvas_scale_x, rel_pos_viewport_scaled.y()/self.canvas_scale_y)
                bi.position = new_rel_pos

        # bounding box update
        self.update_selection_bouding_box()

    def board_FINISH_selected_items_SCALING(self, event, cancel=False):
        self.scaling_ongoing = False
        self.scaling_vector = None
        self.proportional_scaling_vector = None
        self.scaling_pivot_point = None
        cf = self.LibraryData().current_folder()
        if cancel:
            for bi in self.selected_items:
                bi.scale_x = bi.__scale_x_init
                bi.scale_y = bi.__scale_y_init
                bi.position = QPointF(bi.__position_init)
        else:
            self.init_selection_bounding_box_widget(cf)
            self.build_board_bounding_rect(cf)

    def board_CANCEL_selected_items_SCALING(self):
        if self.scaling_ongoing:
            self.board_FINISH_selected_items_SCALING(None, cancel=True)
            self.update_selection_bouding_box()
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
        if self.selection_bounding_box is None:
            return
        if self.PTWS_scaling_active_point_index is None:
            return

        cursor_pos = self.mapFromGlobal(QCursor().pos())
        index = self.PTWS_scaling_active_point_index
        if index == 4:
            pivot_pos = self.__selection_bounding_box_qpolygon_centroid()
        else:
            pivot_pos = self.selection_bounding_box[index]

        painter.save()
        painter.setPen(QPen(Qt.red, 2))
        painter.drawLine(cursor_pos, pivot_pos)
        painter.restore()

    def __selection_bounding_box_qpolygon_centroid(self):
        c = QPointF(0, 0)
        for p in self.selection_bounding_box:
            c += p
        c /= 4.0
        return c

    def board_SCALE_selected_items_choose_nearest_corner(self):
        position = self.mapFromGlobal(QCursor().pos())
        if self.selection_bounding_box is not None:
            enumerated = list(enumerate(self.selection_bounding_box))
            enumerated.append((4, self.__selection_bounding_box_qpolygon_centroid()))
            diffs = {}
            for index, point in enumerated:
                diffs[index] = QVector2D(point - QPointF(position)).length()
            diffs = sorted(diffs.items(), key=lambda x: x[1])
            index = diffs[0][0]
            self.PTWS_scaling_active_point_index = index
            if index == 4:
                # выбираем первую, но по идее, можно было бы выбрать любую другую
                self.PTWS_scaling_active_point_pos = self.selection_bounding_box[0]
            else:
                self.PTWS_scaling_active_point_pos = self.selection_bounding_box[index]

    def board_SCALE_selected_items(self, up=False, down=False, toggle_monitor=False):

        if (up or down):

            # in screen pixels
            VECTOR_LENGTH_FACTOR = self.STNG_one_key_selected_items_scaling_factor

            if up:
                pass

            elif down:
                VECTOR_LENGTH_FACTOR = -VECTOR_LENGTH_FACTOR

            self.PTWS = True
            self.board_SCALE_selected_items_choose_nearest_corner()

            direction = QVector2D(self.PTWS_scaling_active_point_pos -
                                    self.__selection_bounding_box_qpolygon_centroid()).normalized()
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
                item.scale_x = math.copysign(item.scale_x, item.__scale_x)
                item.scale_y = math.copysign(item.scale_y, item.__scale_y)

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
                    self.update_selection_bouding_box()

                else:
                    self.selection_start_point = QPointF(event.pos())
                    self.selection_rect = None
                    self.selection_ongoing = True

            elif alt:
                self.board_region_zoom_in_mousePressEvent(event)

        elif event.buttons() == Qt.MiddleButton:
            if self.transformations_allowed:
                self.board_camera_translation_ongoing = True
                self.start_cursor_pos = self.mapped_cursor_pos()
                self.start_origin_pos = self.canvas_origin
                self.update()

        self.update()

    def board_mouseMoveEventDefault(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        alt = event.modifiers() & Qt.AltModifier
        no_mod = event.modifiers() == Qt.NoModifier

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
                self.update_selection_bouding_box()

            elif self.board_region_zoom_in_input_started:
                self.board_region_zoom_in_mouseMoveEvent(event)

            elif self.selection_ongoing is not None:
                self.selection_end_point = QPointF(event.pos())
                if self.selection_start_point:
                    self.selection_rect = build_valid_rectF(self.selection_start_point, self.selection_end_point)
                    self.board_selection_callback(event.modifiers() == Qt.ShiftModifier)

        elif event.buttons() == Qt.MiddleButton:
            if self.transformations_allowed and self.board_camera_translation_ongoing:
                end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
                start_value = self.canvas_origin
                # delta = end_value-start_value
                self.canvas_origin = end_value
                self.update_selection_bouding_box()

        if self.PTWS_draw_monitor:
            self.board_SCALE_selected_items_choose_nearest_corner()

        self.board_cursor_setter()
        self.update()

    def board_is_items_transformation_ongoing(self):
        return self.translation_ongoing or self.rotation_ongoing or self.scaling_ongoing

    def board_mouseReleaseEventDefault(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier
        alt = event.modifiers() & Qt.AltModifier

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
                    self.update()
            elif alt:
                if self.transformations_allowed:
                    self.set_default_boardviewport_scale(keep_position=True)


        self.prevent_item_deselection = False

    def board_go_to_note(self, event):
        for sel_item in self.selected_items:
            if sel_item.type == BoardItem.types.ITEM_NOTE:
                if sel_item.get_selection_area(canvas=self).containsPoint(event.pos(), Qt.WindingFill):
                    note_content = sel_item.plain_text
                    execute_clickable_text(note_content)
                    break

    def board_MapToViewport(self, canvas_pos):
        scaled_rel_pos = QPointF(canvas_pos.x()*self.canvas_scale_x, canvas_pos.y()*self.canvas_scale_y)
        viewport_pos = self.canvas_origin + scaled_rel_pos
        return viewport_pos

    def board_MapToBoard(self, viewport_pos):
        delta = QPointF(viewport_pos - self.canvas_origin)
        board_pos = QPointF(delta.x()/self.canvas_scale_x, delta.y()/self.canvas_scale_y)
        return board_pos

    def board_paste_selected_items(self):
        selected_items = []
        selection_center = self.board_MapToBoard(self.selection_bounding_box.boundingRect().center())
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
            self.init_selection_bounding_box_widget(cf)

    def do_scale_board(self, scroll_value, ctrl, shift, no_mod,
                pivot=None, factor_x=None, factor_y=None, precalculate=False, canvas_origin=None, canvas_scale_x=None, canvas_scale_y=None, scale_speed=10.0):

        if not precalculate:
            self.board_region_zoom_do_cancel()

        if pivot is None:
            pivot = self.mapped_cursor_pos()

        if scroll_value > 0:
            factor = scale_speed/(scale_speed-1)
        else:
            factor = (scale_speed-1)/scale_speed

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
        self.update_selection_bouding_box()

        event_pos = self.mapped_cursor_pos()
        if self.scaling_ongoing:
            # пользователь вознамерился зумить посреди процесса скейла айтемов (нажал кнопку мыши и ещё не отпустил),
            # это значит, что инициализацию надо провести заново, но с нюансами
            self.board_START_selected_items_SCALING(None, viewport_zoom_changed=True)
            # вызываю, чтобы дебажная графика обновилась сразу, а не после того, как двинется курсор мыши
            self.board_DO_selected_items_SCALING(event_pos)

        if self.rotation_ongoing:
            # то же самое, что и для скейла
            self.board_START_selected_items_ROTATION(event_pos, viewport_zoom_changed=True)
            self.board_DO_selected_items_ROTATION(event_pos)

        self.update()

    def board_do_scale(self, scroll_value):
        self.do_scale_board(scroll_value, False, False, False, pivot=self.get_center_position())

    def board_item_scroll_animation_file(self, board_item, scroll_value):
        if board_item.movie is None:
            # такое случается, когда доска загружена из файла
            self.trigger_board_item_pixmap_loading(board_item)
        frames_list = list(range(0, board_item.movie.frameCount()))
        if scroll_value > 0:
            pass
        else:
            frames_list = list(reversed(frames_list))
        frames_list.append(0)
        i = frames_list.index(board_item.movie.currentFrameNumber()) + 1
        board_item.movie.jumpToFrame(frames_list[i])
        board_item.pixmap = board_item.movie.currentPixmap()
        board_item.update_corner_info()
        self.update()

    def board_item_scroll_folder(self, board_item, scroll_value):
        if scroll_value > 0:
            board_item.item_folder_data.next_image()
        else:
            board_item.item_folder_data.previous_image()
        # заставляем подгрузится
        board_item.pixmap = None
        board_item.update_corner_info()
        self.update()

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
        elif self.board_item_under_mouse is not None and event.buttons() == Qt.RightButton:
            board_item = self.board_item_under_mouse
            self.context_menu_allowed = False
            if board_item.type == board_item.types.ITEM_IMAGE:
                if board_item.animated:
                    self.board_item_scroll_animation_file(board_item, scroll_value)
            elif board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
                self.board_item_scroll_folder(board_item, scroll_value)
        elif no_mod:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif ctrl:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif shift:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)

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
            pixmap = QPixmap().fromImage(mdata.imageData())
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
            filepath = os.path.join(cf.folder_path, f'{time.time()}{ext}')
            urllib.request.urlretrieve(url, filepath)
            self.board_create_new_board_item_image(filepath, cf, source_url=url)

    def board_create_new_board_item_image(self, filepath, current_folder, source_url=None, make_previews=True, place_at_cursor=True):
        image_data = self.LibraryData().create_image_data(filepath, current_folder)
        board_item = BoardItem(BoardItem.types.ITEM_IMAGE)
        board_item.image_data = image_data
        board_item.image_source_url = source_url
        image_data.board_item = board_item
        current_folder.board.items_list.append(board_item)
        board_item.board_index = self.retrieve_new_board_item_index()
        if place_at_cursor:
            board_item.position = self.board_MapToBoard(self.mapped_cursor_pos())
        current_folder.images_list.append(image_data)
        if make_previews: # делаем превьюшку и миинатюрку для этой картинки
            self.LibraryData().make_viewer_thumbnails_and_library_previews(current_folder, None)
        return board_item

    def board_thumbnails_click_handler(self, image_data):
        self.board_fit_content_on_screen(image_data)

    def board_fit_content_on_screen(self, image_data, board_item=None, use_selection=False):

        if board_item is None and (image_data is not None) and image_data.board_item is None:
            self.show_center_label(_("This element is not presented on the board"), error=True)
        else:
            canvas_scale_x = self.canvas_scale_x
            canvas_scale_y = self.canvas_scale_y

            if (self.selection_bounding_box is None or not self.selected_items) and use_selection:
                self.show_center_label(_('No items selected!'))
                return

            if use_selection:
                content_pos = self.selection_bounding_box.boundingRect().center() - self.canvas_origin
            else:
                if board_item is not None:
                    pass
                else:
                    board_item = image_data.board_item
                content_pos = QPointF(board_item.position.x()*canvas_scale_x, board_item.position.y()*canvas_scale_y)
            viewport_center_pos = self.get_center_position()

            self.canvas_origin = - content_pos + viewport_center_pos

            if use_selection:
                content_rect = self.selection_bounding_box.boundingRect().toRect()
            else:
                content_rect = board_item.get_selection_area(canvas=self, place_center_at_origin=False).boundingRect().toRect()
            fitted_rect = fit_rect_into_rect(content_rect, self.rect())
            self.do_scale_board(0, False, False, False,
                pivot=viewport_center_pos,
                factor_x=fitted_rect.width()/content_rect.width(),
                factor_y=fitted_rect.height()/content_rect.height(),
            )

        self.update()

    def board_activate_gamepad(self):
        hidapi_adapter.activate_gamepad(self)

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

    def set_default_boardviewport_origin(self):
        self.canvas_origin = QPointF(600, 100)

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
                filepath = item.image_data.filepath
            elif item.type in [BoardItem.types.ITEM_GROUP, BoardItem.types.ITEM_FOLDER]:
                pass
                filepath = item.item_folder_data.current_image().filepath
            self.start_lite_process(filepath)

    def board_place_items_in_column(self):
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
            bi.position = offset + QPointF(bi_width/2, bi_height/2)
            offset += QPointF(0, bi_height)

        offset = QPointF(main_offset)
        for bi in reversed(neg_list):
            b_rect = bi.get_selection_area(canvas=self, apply_global_scale=False).boundingRect()
            bi_width = b_rect.width()
            bi_height = b_rect.height()
            bi.position = offset + QPointF(bi_width/2, -bi_height/2)
            offset -= QPointF(0, bi_height)

        self.build_board_bounding_rect(folder_data)
        self.init_selection_bounding_box_widget(folder_data)
        self.update()

    def board_open_in_google_chrome(self):
        item = self.retrieve_selected_item()
        if item is not None:
            if item.type == BoardItem.types.ITEM_IMAGE:
                pass
                filepath = item.image_data.filepath
            elif item.type in [BoardItem.types.ITEM_GROUP, BoardItem.types.ITEM_FOLDER]:
                pass
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
        min_distance = 9999999999999999
        min_distance_board_item = None
        if by_window_center:
            cursor_pos = self.get_center_position()
        else:
            cursor_pos = self.mapped_cursor_pos()
        for board_item in folder_data.board.items_list:

            pos = board_item.calculate_absolute_position(canvas=self)
            distance = QVector2D(pos - cursor_pos).length()
            if distance < min_distance:
                min_distance = distance
                min_distance_board_item = board_item

        return min_distance_board_item

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
            pos = first_item.calculate_absolute_position(canvas=self)
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

            new_canvas_scale_x, new_canvas_scale_y, new_canvas_origin = self.do_scale_board(1.0,
                False,
                False,
                True,
                factor_x=bx/self.canvas_scale_x,
                factor_y=by/self.canvas_scale_y,
                precalculate=True,
                canvas_scale_x=self.canvas_scale_x,
                canvas_scale_y=self.canvas_scale_y,
                canvas_origin=pos2,
                pivot = self.get_center_position()
            )

            self.animate_properties(
                [
                    (self, "canvas_origin", pos1, new_canvas_origin, self.update),
                    (self, "canvas_scale_x", self.canvas_scale_x, new_canvas_scale_x, self.update),
                    (self, "canvas_scale_y", self.canvas_scale_y, new_canvas_scale_y, self.update),
                ],
                anim_id="flying",
                duration=0.7,
            )

    def get_original_items_order(self, items_list):
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

        if not self.fly_pairs:
            _list = []

            if cf.board.user_points:
                for point, bx, by in cf.board.user_points:
                    _list.append([point, bx, by])
            else:
                nearest_item = self.board_get_nearest_item(cf)
                items_list = self.get_original_items_order(cf.board.items_list)
                if nearest_item:
                    sorted_list = shift_list_to_became_first(items_list, nearest_item)
                else:
                    sorted_list = items_list
                for board_item in sorted_list:
                    point = board_item.position
                    _list.append([point, None, board_item])

            self.fly_pairs = get_cycled_pairs(_list)
            pair = [
                [current_pos, self.canvas_scale_x, self.canvas_scale_y],
                [_list[0][0], _list[0][1], _list[0][2], ]
            ]

        if pair is None:
            pair = next(self.fly_pairs)

        def animate_scale():
            bx = pair[1][1]
            by = pair[1][2]

            if bx is None:
                board_item = by
                canvas_scale_x = self.canvas_scale_x
                canvas_scale_y = self.canvas_scale_y

                item_rect = board_item.get_selection_area(canvas=self, place_center_at_origin=False, apply_global_scale=False).boundingRect().toRect()
                fitted_rect = fit_rect_into_rect(item_rect, self.rect())
                bx = fitted_rect.width()/item_rect.width()
                by = fitted_rect.height()/item_rect.height()

            self.animate_properties(
                [
                    (self, "_canvas_scale_x", self.canvas_scale_x, bx, self.animate_scale_update),
                    (self, "_canvas_scale_y", self.canvas_scale_y, by, self.animate_scale_update),
                ],
                anim_id="flying",
                duration=1.5,
                easing=QEasingCurve.InOutSine,
                callback_on_finish=self.board_fly_over,
            )

        def update_viewport_position():
            self.canvas_origin = -self.pr_viewport + viewport_center_pos
            self.update()

        current_pos_ = self.board_MapToBoard(self.get_center_position())

        pair = [
            [current_pos_, self.canvas_scale_x, self.canvas_scale_y],
            pair[1],
        ]

        pos1 = QPointF(pair[0][0].x()*self.canvas_scale_x, pair[0][0].y()*self.canvas_scale_y)
        pos2 = QPointF(pair[1][0].x()*self.canvas_scale_x, pair[1][0].y()*self.canvas_scale_y)

        self.animate_properties(
            [
                (self, "pr_viewport", pos1, pos2, update_viewport_position),
            ],
            anim_id="flying",
            duration=2.0,
            # easing=QEasingCurve.InOutSine,
            callback_on_finish=animate_scale,
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
        if dialog.exec_() == QDialog.Accepted:
            selected_folders = dialog.selectedFiles()
        dialog.deleteLater()

        if not selected_folders:
            self.show_center_label(_('No folders selected!'), error=True)
            return

        cf = self.LibraryData().current_folder()

        cf.images_list.clear()
        cf.set_current_index(0)

        for folder_path in selected_folders:
            self.LibraryData().handle_input_data(folder_path, pre_load=True)

            # грузим из папок в стартовую папку
            cf.images_list.extend(self.LibraryData().current_folder().images_list)

        for image_data in cf.images_list:
            image_data.folder_data = cf

        # needed for board_place_items_in_column
        self.LibraryData().make_folder_current(cf, write_view_history=False)

        with self.show_longtime_process_ongoing(self, _("Loading images to the board")):

            self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)

            cf.board.ready = False

            self.prepare_board(cf)
            self.board_place_items_in_column()

        self.update()




# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
