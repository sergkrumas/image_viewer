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
import math
import time

COPY_SELECTED_BOARD_ITEMS_STR = '~#~KRUMASSAN:IMAGE:VIEWER:COPY:SELECTED:BOARD:ITEMS~#~'

class BoardLibraryDataMixin():

    def get_boards_root(self):
        rootpath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.BOARDS_ROOT)
        create_pathsubfolders_if_not_exist(rootpath)
        return rootpath

    def load_boards(self):
        if os.path.exists(self.get_boards_root()):
            print("loading boards data")

class BoardItem():

    FRAME_PADDING = 40.0

    class types():
        ITEM_IMAGE = 1
        ITEM_FOLDER = 2
        ITEM_GROUP = 3
        ITEM_FRAME = 4

    def __init__(self, item_type):
        super().__init__()
        self.type = item_type

        self.pixmap = None
        self.animated = False

        self.item_scale_x = 1.0
        self.item_scale_y = 1.0
        self.item_position = QPointF()
        self.item_rotation = 0

        self.__item_scale_x = None
        self.__item_scale_y = None
        self.__item_position = None
        self.__item_rotation = None

        self.board_index = 0
        self.board_group_index = None

        self.item_width = 300
        self.item_height = 300

        self.item_name = ""

        self._selected = False
        self._touched = False
        self._show_file_info_overlay = False

    def board_retrieve_image_data(self):
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
        folder_data.board.board_items_list.append(copied_item)
        return copied_item

    def info_text(self):
        if self.type == self.types.ITEM_IMAGE:
            image_data = self.image_data
            return f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
        elif self.type == self.types.ITEM_FOLDER:
            path = self.item_folder_data.folder_path
            return f'FOLDER {path}'
        elif self.type == self.types.ITEM_GROUP:
            return f'GROUP {self.board_group_index} {self.item_name}'
        elif self.type == self.types.ITEM_FRAME:
            return f'FRAME'

    def calculate_absolute_position(self, board=None, rel_pos=None):
        _scale_x = board.board_scale_x
        _scale_y = board.board_scale_y
        if rel_pos is None:
            rel_pos = self.item_position
        return QPointF(board.board_origin) + QPointF(rel_pos.x()*_scale_x, rel_pos.y()*_scale_y)

    def aspect_ratio(self):
        rect = self.get_size_rect(scaled=False)
        return rect.width()/rect.height()

    def get_size_rect(self, scaled=False):
        if scaled:
            if self.type == self.types.ITEM_IMAGE:
                scale_x = self.item_scale_x
                scale_y = self.item_scale_y
            elif self.type == self.types.ITEM_FOLDER:
                scale_x = self.item_scale_x
                scale_y = self.item_scale_y
            elif self.type == self.types.ITEM_GROUP:
                scale_x = self.item_scale_x
                scale_y = self.item_scale_y
            elif self.type == self.types.ITEM_FRAME:
                scale_x = self.item_scale_x
                scale_y = self.item_scale_y
        else:
            scale_x = 1.0
            scale_y = 1.0
        if self.type == self.types.ITEM_IMAGE:
            return QRectF(0, 0, self.image_data.source_width*scale_x, self.image_data.source_height*scale_y)
        elif self.type == self.types.ITEM_FOLDER:
            return QRectF(0, 0, self.item_width*scale_x, self.item_height*scale_y)
        elif self.type == self.types.ITEM_GROUP:
            return QRectF(0, 0, self.item_width*scale_x, self.item_height*scale_y)
        elif self.type == self.types.ITEM_FRAME:
            return QRectF(0, 0, self.item_width*scale_x, self.item_height*scale_y)

    def get_selection_area(self, board=None, place_center_at_origin=True, apply_global_scale=True, apply_translation=True):
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
        transform = self.get_transform_obj(board=board, apply_global_scale=apply_global_scale, apply_translation=apply_translation)
        return transform.map(polygon)

    def get_transform_obj(self, board=None, apply_local_scale=True, apply_translation=True, apply_global_scale=True):
        local_scaling = QTransform()
        rotation = QTransform()
        global_scaling = QTransform()
        translation = QTransform()
        if apply_local_scale:
            local_scaling.scale(self.item_scale_x, self.item_scale_y)
        rotation.rotate(self.item_rotation)
        if apply_translation:
            if apply_global_scale:
                pos = self.calculate_absolute_position(board=board)
                translation.translate(pos.x(), pos.y())
            else:
                translation.translate(self.item_position.x(), self.item_position.y())
        if apply_global_scale:
            global_scaling.scale(board.board_scale_x, board.board_scale_y)
        transform = local_scaling * rotation * global_scaling * translation
        return transform

    def update_corner_info(self):
        if self.type == BoardItem.types.ITEM_IMAGE:
            current_frame = self.movie.currentFrameNumber()
            frame_count = self.movie.frameCount()
            if frame_count > 0:
                current_frame += 1
            self.status = f'{current_frame}/{frame_count} ANIMATION'
        elif self.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
            current_image_num = self.item_folder_data._index
            images_count = len(self.item_folder_data.images_list)
            if images_count > 0:
                current_image_num += 1
            if self.type == BoardItem.types.ITEM_FOLDER:
                item_type = "FOLDER"
            elif self.type == BoardItem.types.ITEM_GROUP:
                item_type = "GROUP"
            self.status = f'{current_image_num}/{images_count} {item_type}'

class BoardMixin():

    def board_init(self):

        self.board_origin = self.get_center_position()
        self.board_scale_x = 1.0
        self.board_scale_y = 1.0
        self.board_region_zoom_in_init()
        self.scale_rastr_source = None
        self.rotate_rastr_source = None
        self.load_svg_cursors()
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
        self._board_scale_x = 1.0
        self._board_scale_y = 1.0
        self.board_selection_transform_box_opacity = 1.0
        self.board_debug_transform_widget = False
        self.context_menu_allowed = True
        self.long_loading = False

        self.board_item_under_mouse = None
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False

        self.board_bounding_rect = QRectF()
        self.current_board_item_index = 0
        self.current_board_item_group_index = 0

    def board_dive_inside_board_item(self, back_to_referer=False):
        if self.translation_ongoing or self.rotation_ongoing or self.scaling_ongoing:
            self.show_center_label("Нельзя погружаться во время незавершённых операций с доской", error=True)
            return
        cf = self.LibraryData().current_folder()
        __folder_data = None
        if back_to_referer:
            referer = cf.board.referer_board_folder
            if referer is not None:
                __folder_data = referer
        else:
            item = None
            for bi in cf.board.board_items_list:
                item_selection_area = bi.get_selection_area(board=self)
                is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                if is_under_mouse:
                    item = bi
                    break
            if bi.type not in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP]:
                self.show_center_label("Нырять можно только в группы и папки!", error=True)
                return
            if item is not None:
                __folder_data = item.item_folder_data
            else:
                self.show_center_label("Наведи курсор на группу!", error=True)
                return
        if __folder_data is not None:
            self.LibraryData().save_board_data()
            self.LibraryData().make_folder_current(__folder_data, write_view_history=False)
            self.LibraryData().load_board_data()
            if not back_to_referer:
                self.LibraryData().current_folder().board.referer_board_folder = cf
            self.init_selection_bounding_box_widget(__folder_data)
        else:
            self.show_center_label("Некуда возвращаться!", error=True)
        self.update()

    def board_save_board_data(self, board_lib_obj, folder_data):
        board_lib_obj.board_bounding_rect = self.board_bounding_rect
        board_lib_obj.current_board_item_index = self.current_board_item_index
        board_lib_obj.current_board_item_group_index = self.current_board_item_group_index

        self.board_item_under_mouse = None
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False

    def board_load_board_data(self, board_lib_obj, folder_data):
        if board_lib_obj.board_bounding_rect is not None:
            self.board_bounding_rect = board_lib_obj.board_bounding_rect
        self.current_board_item_index = board_lib_obj.current_board_item_index
        self.current_board_item_group_index = board_lib_obj.current_board_item_group_index

    def load_svg_cursors(self):
        folder_path = os.path.dirname(__file__)
        filepath_scale_svg = os.path.join(folder_path, "cursors", "scale.svg")
        filepath_rotate_svg = os.path.join(folder_path, "cursors", "rotate.svg")

        scale_rastr_source = QPixmap(filepath_scale_svg)
        rotate_rastr_source = QPixmap(filepath_rotate_svg)

        if not scale_rastr_source.isNull():
            self.scale_rastr_source = scale_rastr_source
        if not rotate_rastr_source.isNull():
            self.rotate_rastr_source = rotate_rastr_source

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
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, "WELCOME TO \n BOARDS")

    def board_draw(self, painter):
        old_font = painter.font()
        font = QFont(old_font)

        self.board_draw_main(painter)
        # board_draw_stub(self, painter)

        painter.setFont(old_font)

    def board_draw_wait_long_loading_label(self, painter):
        if self.long_loading:
            self.board_draw_wait_label(painter, socondary_text="загрузка данных")

    def board_draw_wait_label(self, painter, primary_text="ПОДОЖДИ",
                    socondary_text="создаются превьюшки"):
        font = painter.font()
        font.setPixelSize(100)
        font.setWeight(1900)
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter

        painter.setPen(QPen(QColor(240, 10, 50, 100), 1))
        text = "  ".join(primary_text)
        text_rect = painter.boundingRect(max_rect, alignment, text)
        pos = self.rect().center() + QPoint(0, -80)
        text_rect.moveCenter(pos)
        painter.drawText(text_rect, alignment, text)

        font = painter.font()
        font.setPixelSize(15)
        # font.setWeight(900)
        painter.setFont(font)

        text = " ".join(socondary_text).upper()
        text_rect = painter.boundingRect(text_rect, alignment, text)
        brush = QBrush(Qt.black)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(text_rect.adjusted(-3, -3, 3, 3))
        painter.setPen(QPen(Qt.white))

        painter.drawText(text_rect, alignment, text)
        painter.setBrush(Qt.NoBrush)

    def retrieve_new_board_item_index(self):
        self.current_board_item_index += 1
        return self.current_board_item_index

    def retrieve_new_board_item_group_index(self):
        self.current_board_item_group_index += 1
        return self.current_board_item_group_index

    def prepare_board(self, folder_data):

        if self.Globals.DEBUG:
            offset = QPointF(0, 0) - QPointF(500, 0)
        else:
            offset = QPointF(0, 0)

        items_list = folder_data.board.board_items_list = []

        for image_data in folder_data.images_list:
            if not image_data.preview_error:
                board_item = BoardItem(BoardItem.types.ITEM_IMAGE)
                board_item.image_data = image_data
                image_data.board_item = board_item
                folder_data.board.board_items_list.append(board_item)
                board_item.board_index = self.retrieve_new_board_item_index()
                board_item.item_position = offset + QPointF(image_data.source_width, image_data.source_height)/2
                offset += QPointF(image_data.source_width, 0)

        self.build_board_bounding_rect(folder_data)

        folder_data.board.board_ready = True
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
            for board_item in folder_data.board.board_items_list:
                self.board_draw_item(painter, board_item)

            self.draw_selection(painter, folder_data)

            painter.drawText(self.rect().bottomLeft() + QPoint(50, -150), f'perfomance status: {self.images_drawn} images drawn')

    def draw_selection(self, painter, folder_data):
        old_pen = painter.pen()
        pen = QPen(self.selection_color, 1)
        painter.setPen(pen)

        for board_item in folder_data.board.board_items_list:
            if board_item._selected:
                painter.drawPolygon(board_item.get_selection_area(board=self))

        painter.setPen(old_pen)

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

            area = board_item.get_selection_area(board=self)
            pen = QPen(Qt.white, 2, Qt.DashLine)
            pen.setCosmetic(True) # не скейлить пен
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            path = QPainterPath()
            path.addRoundedRect(area.boundingRect(), FRAME_PADDING*self.board_scale_x, FRAME_PADDING*self.board_scale_y)
            painter.drawPath(path)
            pos = area.boundingRect().topLeft()
            zoom_delta = QPointF(FRAME_PADDING*self.board_scale_x, 0)
            font = painter.font()
            before_font = painter.font()
            font.setPixelSize(30)
            painter.setFont(font)

            text = board_item.item_name
            alignment = Qt.AlignLeft
            rect = painter.boundingRect(area.boundingRect(), alignment, text)
            rect.moveBottomLeft(pos+zoom_delta)
            show_text = True
            if rect.width() > area.boundingRect().width():
                show_text = False
                if area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill):
                    show_text = True
            else:
                show_text = True

            if show_text:
                painter.drawText(rect, alignment, text)

            painter.setFont(before_font)

        else:

            image_data = board_item.board_retrieve_image_data()

            selection_area = board_item.get_selection_area(board=self)

            if selection_area.intersected(self.get_monitor_area()).boundingRect().isNull():
                self.trigger_board_item_pixmap_unloading(board_item)

            else:
                self.images_drawn += 1
                transform = board_item.get_transform_obj(board=self)

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

                painter.setTransform(transform)
                image_to_draw = None
                selection_area_rect = selection_area.boundingRect()
                if selection_area_rect.width() < 250 or selection_area_rect.height() < 250:
                    image_to_draw = image_data.preview
                else:
                    self.trigger_board_item_pixmap_loading(board_item)
                    image_to_draw = board_item.pixmap

                if selection_area.containsPoint(QPointF(self.mapped_cursor_pos()), Qt.WindingFill):
                    self.board_item_under_mouse = board_item

                if image_to_draw:
                    painter.drawPixmap(item_rect, image_to_draw, QRectF(QPointF(0, 0), QSizeF(image_to_draw.size())))

                painter.setOpacity(1.0)
                painter.resetTransform()

                selection_area_bounding_rect = selection_area.boundingRect()

                if board_item._show_file_info_overlay:
                    text = board_item.info_text()
                    alignment = Qt.AlignCenter

                    old_pen = painter.pen()
                    text_rect = painter.boundingRect(selection_area_bounding_rect, alignment, text)
                    painter.setBrush(QBrush(Qt.white))
                    painter.setPen(Qt.NoPen)
                    painter.drawRect(text_rect)
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawText(text_rect, alignment, text)
                    painter.setPen(old_pen)


                if board_item == self.board_item_under_mouse:
                    is_animation_file = board_item.type == BoardItem.types.ITEM_IMAGE and board_item.animated

                    if board_item.type in [BoardItem.types.ITEM_FOLDER, BoardItem.types.ITEM_GROUP] or is_animation_file:

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

        dist = QVector2D(self.get_center_position() - board_item.calculate_absolute_position(board=self)).length()

        if dist > 10000.0:
            board_item.pixmap = None
            board_item.movie = None

            image_data = board_item.board_retrieve_image_data()
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
                if self.LibraryData().is_gif_file(filepath) or self.LibraryData().is_webp_file_animated(filepath):
                    __load_animated(filepath)
                elif self.LibraryData().is_svg_file(filepath):
                    __load_svg(filepath)
                else:
                    __load_static(filepath)
            except Exception as e:
                board_item.pixmap = QPixmap()

    def board_draw_grid(self, painter):
        LINES_INTERVAL_X = 300 * self.board_scale_x
        LINES_INTERVAL_Y = 300 * self.board_scale_y
        r = QRectF(self.rect()).adjusted(-LINES_INTERVAL_X*2, -LINES_INTERVAL_Y*2, LINES_INTERVAL_X*2, LINES_INTERVAL_Y*2)
        value_x = int(fit(self.board_scale_x, 0.08, 1.0, 0, 200))
        # value_x = 100
        pen = QPen(QColor(220, 220, 220, value_x), 1)
        painter.setPen(pen)
        icp = self.board_origin
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
        for point, board_scale_x, board_scale_y in cf.board.board_user_points:
            p = self.board_origin + QPointF(point.x()*self.board_scale_x, point.y()*self.board_scale_y)
            painter.drawPoint(p)

    def board_draw_main(self, painter):

        cf = self.LibraryData().current_folder()
        if cf.previews_done:
            if self.Globals.DEBUG or self.STNG_board_draw_grid:
                self.board_draw_grid(painter)
            self.board_draw_content(painter, cf)
        else:
            self.board_draw_wait_label(painter)


        if self.Globals.DEBUG or self.STNG_board_draw_board_origin:
            self.board_draw_board_origin(painter)

        self.board_draw_user_points(painter, cf)

        self.board_draw_selection_frames(painter)
        self.board_draw_selection_transform_box(painter)
        self.board_region_zoom_in_draw(painter)

        if self.Globals.DEBUG or self.STNG_board_draw_origin_compass:
            self.board_draw_origin_compass(painter)

        self.board_draw_cursor_text(painter)

        self.board_draw_diving_notification(painter, cf)

        self.board_draw_minimap(painter)

        self.board_draw_wait_long_loading_label(painter)

    def board_draw_diving_notification(self, painter, folder_data):
        referer = folder_data.board.referer_board_folder
        if referer is not None:
            folder_name = referer.folder_path
            text = f"клавиша Backspace ➜ вернуться на доску папки {folder_name}"
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
            text = f'Добавить в группу ({count})'
            bounding_rect = painter.boundingRect(QRect(0, 0, 500, 500), Qt.AlignLeft, text)
            painter.setBrush(QBrush(Qt.black))
            painter.setPen(Qt.NoPen)
            bounding_rect.moveCenter(pos)
            painter.drawRect(bounding_rect.adjusted(-2, -2, 2, 2))
            painter.setPen(Qt.white)
            painter.drawText(bounding_rect, Qt.AlignLeft, text)
            painter.setBrush(Qt.NoBrush)

    def board_draw_selection_frames(self, painter):
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

    def board_draw_origin_compass(self, painter):

        curpos = self.mapFromGlobal(QCursor().pos())

        pos = self.board_origin

        # self.board_origin
        old_pen = painter.pen()

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

        scale_percent_x = math.ceil(self.board_scale_x*100)
        scale_percent_y = math.ceil(self.board_scale_y*100)
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
        painter.setPen(old_pen)

    def board_draw_board_origin(self, painter):
        pos = self.board_origin
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

        text = "НАЧАЛО"
        text_rect = painter.boundingRect(max_rect, alignment, text)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, -80))
        painter.drawText(text_rect, alignment, text)

        text = "КООРДИНАТ"
        text_rect = painter.boundingRect(max_rect, alignment, text)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, 80))
        painter.drawText(text_rect, alignment, text)

    def build_board_bounding_rect(self, folder_data, apply_global_scale=False):
        points = []
        # points.append(self.board_origin) #мешает при использовании board_navigate_camera_via_minimap, поэтому убрал нафег
        if folder_data.board.board_items_list:
            for board_item in folder_data.board.board_items_list:
                rf = board_item.get_selection_area(board=self, apply_global_scale=apply_global_scale).boundingRect()
                points.append(rf.topLeft())
                points.append(rf.bottomRight())
            p1, p2 = get_bounding_points(points)
            result = build_valid_rectF(p1, p2)
        else:
            result = self.rect()
        self.board_bounding_rect = result

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

    def board_cursor_setter(self):
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
        elif self.selection_bounding_box is not None:
            if self.is_over_scaling_activation_area(self.mapped_cursor_pos()):
                cursor = self.get_widget_cursor(self.scale_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)

            elif self.is_over_rotation_activation_area(self.mapped_cursor_pos()):
                cursor = self.get_widget_cursor(self.rotate_rastr_source, self.board_get_cursor_angle())
                self.setCursor(cursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def board_navigate_camera_via_minimap(self):
        if not self.board_show_minimap:
            return
        if self.minimap_rect.contains(self.mapped_cursor_pos()):
            rel_pos = self.mapped_cursor_pos() - self.minimap_rect.topLeft()
            norm_rel_pos = QPointF(rel_pos.x()/self.minimap_rect.width(), rel_pos.y()/self.minimap_rect.height())
            cf = self.LibraryData().current_folder()
            self.build_board_bounding_rect(cf, apply_global_scale=True)
            board_origin = QPointF(self.board_bounding_rect.width()*norm_rel_pos.x(), self.board_bounding_rect.height()*norm_rel_pos.y())
            board_origin = - board_origin + QPointF(self.rect().width()/2.0, self.rect().height()/2.0)
            board_origin = board_origin + (self.board_origin - self.board_bounding_rect.topLeft())
            self.board_origin = board_origin
            # восстанавливаем прежний bounding rect
            self.build_board_bounding_rect(cf, apply_global_scale=False)
            self.show_center_label("Камера перемещена!")
        else:
            self.show_center_label("Вне прямоугольника! Отмена", error=True)
        self.update()

    def board_draw_minimap(self, painter):
        if not self.board_show_minimap:
            return

        painter.resetTransform()

        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
            painter.fillRect(self.rect(), QBrush(QColor(20, 20, 20, 220)))

            minimap_rect = self.board_bounding_rect
            map_width = max(400, self.rect().width() - 300)
            factor = map_width / self.board_bounding_rect.width()
            map_height = self.board_bounding_rect.height()*factor
            minimap_rect = QRectF(0, 0, map_width, map_height)
            minimap_rect.moveCenter(self.get_center_position())
            self.minimap_rect = minimap_rect

            # backplate
            minimap_backplate = minimap_rect.adjusted(-10, -10, 10, 10)
            painter.fillRect(minimap_backplate, QBrush(QColor(0, 0, 0, 150)))
            # gray frame
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawRect(minimap_rect)

            for board_item in cf.board.board_items_list:

                image_data = board_item.board_retrieve_image_data()

                delta = board_item.item_position - self.board_bounding_rect.topLeft()
                delta = QPointF(
                    delta.x()/self.board_bounding_rect.width(),
                    delta.y()/self.board_bounding_rect.height()
                )
                point = minimap_rect.topLeft() + QPointF(delta.x()*map_width, delta.y()*map_height)
                painter.setPen(QPen(Qt.red, 4))
                painter.drawPoint(point)


                painter.setPen(QPen(Qt.green, 1))
                selection_area = board_item.get_selection_area(board=self, place_center_at_origin=False, apply_global_scale=False)
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
            viewport_pos = -self.board_origin + self.get_center_position()
            tp = self.board_bounding_rect.topLeft()

            # здесь board_scale необходим для правильной передачи смещения вьюпорта
            delta = viewport_pos - QPointF(tp.x()*self.board_scale_x, tp.y()*self.board_scale_y)
            delta = QPointF(
                delta.x()/self.board_bounding_rect.width()/self.board_scale_x,
                delta.y()/self.board_bounding_rect.height()/self.board_scale_y
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
            w = map_width*rel_size.x()/self.board_scale_x
            h = map_height*rel_size.y()/self.board_scale_y
            miniviewport_rect = QRectF(0, 0, w, h)
            miniviewport_rect.moveCenter(point)
            painter.setPen(QPen(Qt.yellow, 1))
            painter.drawRect(miniviewport_rect)

    def board_select_items(self, items):
        current_folder = self.LibraryData().current_folder()
        for bi in current_folder.board.board_items_list:
            bi._selected = False
        for item in items:
            item._selected = True
        self.init_selection_bounding_box_widget(current_folder)

    def board_add_item_group(self):
        folder_data = self.LibraryData().current_folder()
        item_folder_data = self.LibraryData().create_folder_data("GROUP Virtual Folder", [], image_filepath=None, make_current=False, virtual=True)
        bi = BoardItem(BoardItem.types.ITEM_GROUP)
        bi.item_folder_data = item_folder_data
        bi.board_index = self.retrieve_new_board_item_index()
        bi.board_group_index = self.retrieve_new_board_item_group_index()
        folder_data.board.board_items_list.append(bi)
        item_folder_data.previews_done = True
        item_folder_data.board.board_ready = True
        item_folder_data.board.board_root_folder = folder_data
        item_folder_data.board.board_root_item = bi
        # располагаем в центре экрана
        bi.item_position = self.get_relative_position(self.context_menu_exec_point)
        bi.update_corner_info()
        self.board_select_items([bi])
        self.update()

    def board_add_item_folder(self):
        folder_path = str(QFileDialog.getExistingDirectory(None, "Выбери папку с пикчами"))
        folder_data = self.LibraryData().current_folder()

        if folder_path:
            self.long_loading = True
            self.update()
            processAppEvents()
            files = self.LibraryData().list_interest_files(folder_path, deep_scan=False, all_allowed=False)
            item_folder_data = self.LibraryData().create_folder_data(folder_path, files, image_filepath=None, make_current=False)
            self.LibraryData().make_viewer_thumbnails_and_library_previews(item_folder_data, None)
            bi = BoardItem(BoardItem.types.ITEM_FOLDER)
            bi.item_folder_data = item_folder_data
            bi.board_index = self.retrieve_new_board_item_index()
            folder_data.board.board_items_list.append(bi)
            # располагаем в центре экрана
            bi.item_position = self.get_relative_position(self.rect().center())
            bi.update_corner_info()
            self.board_select_items([bi])
            self.long_loading = False
            self.update()

    def board_add_item_frame(self):

        if self.selection_bounding_box is None:
            self.show_center_label('Не выделено ни одного айтема!', error=True)
        else:
            folder_data = self.LibraryData().current_folder()
            bi = BoardItem(BoardItem.types.ITEM_FRAME)
            bi.board_index = self.retrieve_new_board_item_index()
            folder_data.board.board_items_list.append(bi)

            selection_bounding_rect = self.selection_bounding_box.boundingRect()
            bi.item_position = self.get_relative_position(selection_bounding_rect.center())
            bi.item_width = selection_bounding_rect.width() / self.board_scale_x
            bi.item_height = selection_bounding_rect.height() / self.board_scale_y
            bi.item_width += BoardItem.FRAME_PADDING
            bi.item_height += BoardItem.FRAME_PADDING
            bi.item_name = "FRAME ITEM"
            self.board_select_items([bi])

        self.update()

    def isLeftClickAndNoModifiers(self, event):
        return event.buttons() == Qt.LeftButton and event.modifiers() == Qt.NoModifier

    def isLeftClickAndAlt(self, event):
        return (event.buttons() == Qt.LeftButton or event.button() == Qt.LeftButton) and event.modifiers() == Qt.AltModifier

    def board_START_selected_items_TRANSLATION(self, event):
        self.start_translation_pos = event.pos()
        current_folder = self.LibraryData().current_folder()
        items_list = current_folder.board.board_items_list
        for board_item in items_list:
            board_item.start_translation_pos = QPointF(board_item.item_position)
            board_item._children_items = []
            if board_item.type == BoardItem.types.ITEM_FRAME:
                item_frame_area = board_item.get_selection_area(board=self)
                for bi in current_folder.board.board_items_list[:]:
                    bi_area = bi.get_selection_area(board=self)
                    center_point = bi_area.boundingRect().center()
                    if item_frame_area.containsPoint(QPointF(center_point), Qt.WindingFill):
                        board_item._children_items.append(bi)

    def board_DO_selected_items_TRANSLATION(self, event):
        if self.start_translation_pos:
            self.translation_ongoing = True
            current_folder = self.LibraryData().current_folder()
            delta = event.pos() - self.start_translation_pos
            delta = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)
            for board_item in current_folder.board.board_items_list:
                if board_item._selected:
                    board_item.item_position = board_item.start_translation_pos + delta
                    if board_item.type == BoardItem.types.ITEM_FRAME:
                        for ch_bi in board_item._children_items:
                            ch_bi.item_position = ch_bi.start_translation_pos + delta
            self.init_selection_bounding_box_widget(current_folder)
            self.check_item_group_under_mouse()
        else:
            self.translation_ongoing = False

    def board_FINISH_selected_items_TRANSLATION(self, event):
        self.start_translation_pos = None
        current_folder = self.LibraryData().current_folder()
        for board_item in current_folder.board.board_items_list:
            board_item.start_translation_pos = None
            board_item._children_items = []
        self.translation_ongoing = False
        self.build_board_bounding_rect(current_folder)
        self.move_selected_items_to_item_group()
        self.check_item_group_under_mouse(reset=True)

    def move_selected_items_to_item_group(self):
        if self.item_group_under_mouse is not None:
            group_item = self.item_group_under_mouse
            item_fd = group_item.item_folder_data
            group_board_item_list = item_fd.board.board_items_list

            current_folder = self.LibraryData().current_folder()
            board_item_list = current_folder.board.board_items_list
            for bi in self.selected_items:
                if bi.type is not bi.types.ITEM_GROUP:
                    board_item_list.remove(bi)
                    group_board_item_list.append(bi)
                    if bi.type is bi.types.ITEM_IMAGE:
                        current_folder.images_list.remove(bi.image_data)
                        item_fd.images_list.append(bi.image_data)
                        bi.image_data.folder_data = item_fd

            group_item.update_corner_info()

            self.board_select_items([group_item])

    def check_item_group_under_mouse(self, reset=False):
        self.item_group_under_mouse = None
        self.group_inside_selection_items = False
        if reset:
            return
        self.group_inside_selection_items = any(bi.type == BoardItem.types.ITEM_GROUP for bi in self.selected_items)
        if not self.group_inside_selection_items:
            cf = self.LibraryData().current_folder()
            for bi in cf.board.board_items_list:
                if bi.type is BoardItem.types.ITEM_GROUP:
                    item_selection_area = bi.get_selection_area(board=self)
                    is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                    if is_under_mouse:
                        self.item_group_under_mouse = bi
                        break

    def any_item_area_under_mouse(self, add_selection):
        self.prevent_item_deselection = False
        current_folder = self.LibraryData().current_folder()
        if self.is_flyover_ongoing():
            return False
        # reversed для того, чтобы картинки на переднем плане чекались первыми
        for board_item in reversed(current_folder.board.board_items_list):
            item_selection_area = board_item.get_selection_area(board=self)
            is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)

            if is_under_mouse and not board_item._selected:
                if board_item.type == BoardItem.types.ITEM_FRAME:
                    _other_items = self.find_all_items_under_this_pos(current_folder, self.mapped_cursor_pos())
                    if len(_other_items) > 1:
                        continue

                if not add_selection:
                    for bi in current_folder.board.board_items_list:
                        bi._selected = False

                board_item._selected = True
                # вытаскиваем айтем на передний план при отрисовке
                current_folder.board.board_items_list.remove(board_item)
                current_folder.board.board_items_list.append(board_item)
                self.prevent_item_deselection = True
                return True
            if is_under_mouse and board_item._selected:
                return True
        return False

    def find_all_items_under_this_pos(self, folder_data, pos):
        undermouse_items = []
        for board_item in folder_data.board.board_items_list:
            item_selection_area = board_item.get_selection_area(board=self)
            is_under_mouse = item_selection_area.containsPoint(pos, Qt.WindingFill)
            if is_under_mouse:
                undermouse_items.append(board_item)
        return undermouse_items

    def board_selection_callback(self, add_to_selection):
        if self.is_flyover_ongoing():
            return
        current_folder = self.LibraryData().current_folder()
        if self.selection_rect is not None:
            selection_rect_area = QPolygonF(self.selection_rect)
            for board_item in current_folder.board.board_items_list:
                item_selection_area = board_item.get_selection_area(board=self)
                if item_selection_area.intersects(selection_rect_area):
                    board_item._selected = True
                else:
                    if add_to_selection and board_item._selected:
                        pass
                    else:
                        board_item._selected = False
        else:
            # reversed для того, чтобы картинки на переднем плане чекались первыми
            for board_item in reversed(current_folder.board.board_items_list):
                item_selection_area = board_item.get_selection_area(board=self)
                is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
                if add_to_selection and board_item._selected:
                    # subtract item from selection!
                    if is_under_mouse and not self.prevent_item_deselection:
                        board_item._selected = False
                else:
                    if board_item.type == BoardItem.types.ITEM_FRAME:
                        _other_items = self.find_all_items_under_this_pos(current_folder, self.mapped_cursor_pos())
                        if len(_other_items) > 1:
                            board_item._selected = False
                        else:
                            board_item._selected = is_under_mouse
                    else:
                        board_item._selected = is_under_mouse
        self.init_selection_bounding_box_widget(current_folder)

    def init_selection_bounding_box_widget(self, folder_data):
        self.selected_items = []
        for board_item in folder_data.board.board_items_list:
            if board_item._selected:
                self.selected_items.append(board_item)
        self.update_selection_bouding_box()

    def board_unselect_all_items(self):
        cf = self.LibraryData().current_folder()
        for board_item in cf.board.board_items_list:
            board_item._selected = False
        self.init_selection_bounding_box_widget(cf)

    def board_select_all_items(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.board_items_list:
            bi._selected = True
        self.update()

    def update_selection_bouding_box(self):
        self.selection_bounding_box = None
        if len(self.selected_items) == 1:
            self.selection_bounding_box = self.selected_items[0].get_selection_area(board=self)
        elif len(self.selected_items) > 1:
            bounding_box = QRectF()
            for board_item in self.selected_items:
                bounding_box = bounding_box.united(board_item.get_selection_area(board=self).boundingRect())
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
                # if bi.__item_rotation is not None:
                #     bi.item_rotation = bi.__item_rotation
                if bi.type != BoardItem.types.ITEM_FRAME:
                    if bi.__item_position is not None:
                        bi.item_position = bi.__item_position

            self.update_selection_bouding_box()

        self.__selection_bounding_box = QPolygonF(self.selection_bounding_box)
        pivot = self.selection_bounding_box.boundingRect().center()
        radius_vector = QPointF(event_pos) - pivot
        self.rotation_start_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())
        for bi in self.selected_items:
            bi.__item_rotation = bi.item_rotation
            bi.__item_position = bi.item_position

    def step_rotation(self, rotation_value):
        interval = 45.0
        # формулу подбирал в графическом калькуляторе desmos.com/calculator
        # value = math.floor((rotation_value-interval/2.0)/interval)*interval+interval
        # ниже упрощённый вариант
        value = (math.floor(rotation_value/interval-0.5)+1.0)*interval
        return value

    def board_DO_selected_items_ROTATION(self, event_pos):
        mutli_item_mode = len(self.selected_items) > 1
        ctrl_mod = QApplication.queryKeyboardModifiers() & Qt.ControlModifier
        pivot = self.selection_bounding_box.boundingRect().center()
        radius_vector = QPointF(event_pos) - pivot
        self.rotation_end_angle_rad = math.atan2(radius_vector.y(), radius_vector.x())
        self.rotation_delta = self.rotation_end_angle_rad - self.rotation_start_angle_rad
        rotation_delta_degrees = math.degrees(self.rotation_delta)
        if mutli_item_mode and ctrl_mod:
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
            bi.item_rotation = bi.__item_rotation + rotation_delta_degrees
            if not mutli_item_mode and ctrl_mod:
                bi.item_rotation = self.step_rotation(bi.item_rotation)
            # position component
            pos = bi.calculate_absolute_position(board=self, rel_pos=bi.__item_position)
            pos_radius_vector = pos - pivot
            pos_radius_vector = rotation.map(pos_radius_vector)
            new_absolute_position = pivot + pos_radius_vector
            rel_pos_global_scaled = new_absolute_position - self.board_origin
            new_item_position = QPointF(rel_pos_global_scaled.x()/self.board_scale_x, rel_pos_global_scaled.y()/self.board_scale_y)
            bi.item_position = new_item_position
        # bounding box transformation
        translate_to_coord_origin = QTransform()
        translate_back_to_place = QTransform()
        offset = - self.__selection_bounding_box.boundingRect().center()
        translate_to_coord_origin.translate(offset.x(), offset.y())
        offset = - offset
        translate_back_to_place.translate(offset.x(), offset.y())
        transform = translate_to_coord_origin * rotation * translate_back_to_place
        self.selection_bounding_box = transform.map(self.__selection_bounding_box)

    def board_FINISH_selected_items_ROTATION(self, event):
        self.rotation_ongoing = False
        cf = self.LibraryData().current_folder()
        self.init_selection_bounding_box_widget(cf)
        self.build_board_bounding_rect(cf)

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
        self.scaling_pivot_corner_point = QPointF(self.selection_bounding_box[pivot_point_index])

        x_axis = QVector2D(next_point - self.scaling_pivot_corner_point).normalized().toPointF()
        y_axis = QVector2D(prev_point - self.scaling_pivot_corner_point).normalized().toPointF()

        __vector  = x_axis + y_axis
        return math.degrees(math.atan2(__vector.y(), __vector.x()))

    def board_START_selected_items_SCALING(self, event, viewport_zoom_changed=False):
        self.scaling_ongoing = True

        if viewport_zoom_changed:
            for bi in self.selected_items:
                if bi.__item_scale_x is not None:
                    bi.item_scale_x = bi.__item_scale_x
                if bi.__item_scale_y is not None:
                    bi.item_scale_y = bi.__item_scale_y
                if bi.__item_position is not None:
                    bi.item_position = bi.__item_position

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
            bi.__item_scale_x = bi.item_scale_x
            bi.__item_scale_y = bi.item_scale_y
            bi.__item_position = bi.item_position
            position_vec = bi.calculate_absolute_position(board=self) - self.scaling_pivot_corner_point
            bi.normalized_pos_x, bi.normalized_pos_y = self.calculate_vector_projection_factors(x_axis, y_axis, position_vec)

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
        mutli_item_mode = len(self.selected_items) > 1
        alt_mod = QApplication.queryKeyboardModifiers() & Qt.AltModifier
        shift_mod = QApplication.queryKeyboardModifiers() & Qt.ShiftModifier
        center_is_pivot = alt_mod
        proportional_scaling = mutli_item_mode or shift_mod

        # отключаем модификатор alt для группы выделенных айтемов
        center_is_pivot = center_is_pivot and not mutli_item_mode

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
                if mutli_item_mode:
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

            bi.item_scale_x = bi.__item_scale_x * x_factor
            bi.item_scale_y = bi.__item_scale_y * y_factor
            if proportional_scaling and not mutli_item_mode and not center_is_pivot:
                bi.item_scale_x = math.copysign(1.0, bi.item_scale_x)*abs(bi.item_scale_y)

            # position component
            if center_is_pivot:
                bi.item_position = bi.__item_position
            else:
                pos = bi.calculate_absolute_position(board=self, rel_pos=bi.__item_position)
                scaling = QTransform()
                # эти нормализованные координаты актуальны для пропорционального и не для пропорционального редактирования
                scaling.scale(bi.normalized_pos_x, bi.normalized_pos_y)
                mapped_scaling_vector = scaling.map(scaling_vector)
                new_absolute_position = pivot + mapped_scaling_vector
                rel_pos_global_scaled = new_absolute_position - self.board_origin
                new_item_position = QPointF(rel_pos_global_scaled.x()/self.board_scale_x, rel_pos_global_scaled.y()/self.board_scale_y)
                bi.item_position = new_item_position

        # bounding box update
        self.update_selection_bouding_box()

    def board_FINISH_selected_items_SCALING(self, event):
        self.scaling_ongoing = False
        self.scaling_vector = None
        self.proportional_scaling_vector = None
        self.scaling_pivot_point = None
        cf = self.LibraryData().current_folder()
        self.init_selection_bounding_box_widget(cf)
        self.build_board_bounding_rect(cf)

    def boards_do_scaling_key_callback(self):
        if self.scaling_ongoing:
            self.board_DO_selected_items_SCALING(self.mapped_cursor_pos())

    def boards_key_release_callback(self, event):
        self.boards_do_scaling_key_callback()

    def boards_key_press_callback(self, event):
        self.boards_do_scaling_key_callback()

    def board_mousePressEvent(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        alt = event.modifiers() & Qt.AltModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if event.buttons() == Qt.LeftButton:
            if not alt:

                if self.is_over_scaling_activation_area(event.pos()):
                    self.board_START_selected_items_SCALING(event)

                elif self.is_over_rotation_activation_area(event.pos()):
                    self.board_START_selected_items_ROTATION(event.pos())

                elif self.any_item_area_under_mouse(event.modifiers() & Qt.ShiftModifier):
                    self.board_START_selected_items_TRANSLATION(event)
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
                self.start_origin_pos = self.board_origin
                self.update()

    def board_mouseMoveEvent(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        alt = event.modifiers() & Qt.AltModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if event.buttons() == Qt.LeftButton:

            if self.scaling_ongoing:
                self.board_DO_selected_items_SCALING(event.pos())

            elif self.rotation_ongoing:
                self.board_DO_selected_items_ROTATION(event.pos())

            elif no_mod and not self.selection_ongoing:
                self.board_DO_selected_items_TRANSLATION(event)
                self.update_selection_bouding_box()

            elif self.board_region_zoom_in_input_started:
                self.board_region_zoom_in_mouseMoveEvent(event)

            elif self.selection_ongoing is not None and not self.translation_ongoing:
                self.selection_end_point = QPointF(event.pos())
                if self.selection_start_point:
                    self.selection_rect = build_valid_rectF(self.selection_start_point, self.selection_end_point)
                    self.board_selection_callback(event.modifiers() == Qt.ShiftModifier)


        elif event.buttons() == Qt.MiddleButton:
            if self.transformations_allowed and self.board_camera_translation_ongoing:
                end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
                start_value = self.board_origin
                # delta = end_value-start_value
                self.board_origin = end_value
                self.update_selection_bouding_box()

        self.board_cursor_setter()
        self.update()

    def board_mouseReleaseEvent(self, event):
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier
        alt = event.modifiers() & Qt.AltModifier

        if event.button() == Qt.LeftButton:
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
                delta = QPointF(event.pos() - self.board_origin)
                delta = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)
                cf.board.board_user_points.append([delta, self.board_scale_x, self.board_scale_y])

        elif event.button() == Qt.MiddleButton:
            if no_mod:
                if self.transformations_allowed:
                    self.board_camera_translation_ongoing = False
                    self.update()
            elif alt:
                if self.transformations_allowed:
                    self.set_default_boardviewport_scale(keep_position=True)

        self.prevent_item_deselection = False

    def board_delete_selected_board_items(self):
        cf = self.LibraryData().current_folder()
        board_items_list = cf.board.board_items_list
        for bi in self.selected_items:
            board_items_list.remove(bi)
        self.init_selection_bounding_box_widget(cf)
        self.update()

    def get_relative_position(self, viewport_pos):
        delta = QPointF(viewport_pos - self.board_origin)
        return QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)

    def board_paste_selected_items(self):
        selected_items = []
        selection_center = self.get_relative_position(self.selection_bounding_box.boundingRect().center())
        rel_cursor_pos = self.get_relative_position(self.mapped_cursor_pos())
        for bi in self.LibraryData().current_folder().board.board_items_list:
            if bi._selected:
                selected_items.append(bi)
                bi._selected = False
        if selected_items:
            cf = self.LibraryData().current_folder()
            for sel_item in selected_items:
                new_item = sel_item.make_copy(self, cf)
                # new_item.item_position += QPointF(100, 100)
                delta = new_item.item_position - selection_center
                new_item.item_position = rel_cursor_pos + delta
                new_item._selected = True
            self.init_selection_bounding_box_widget(cf)

    def do_scale_board(self, scroll_value, ctrl, shift, no_mod,
                pivot=None, factor_x=None, factor_y=None, precalculate=False, board_origin=None, board_scale_x=None, board_scale_y=None):

        if not precalculate:
            self.board_region_zoom_do_cancel()

        if pivot is None:
            pivot = self.mapped_cursor_pos()

        scale_speed = 10.0
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

        _board_origin = board_origin if board_origin is not None else self.board_origin
        _board_scale_x = board_scale_x if board_scale_x is not None else self.board_scale_x
        _board_scale_y = board_scale_y if board_scale_y is not None else self.board_scale_y

        _board_scale_x *= factor_x
        _board_scale_y *= factor_y

        _board_origin -= pivot
        _board_origin = QPointF(_board_origin.x()*factor_x, _board_origin.y()*factor_y)
        _board_origin += pivot

        if precalculate:
            return _board_scale_x, _board_scale_y, _board_origin

        self.board_origin  = _board_origin
        self.board_scale_x = _board_scale_x
        self.board_scale_y = _board_scale_y

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

    def board_wheelEvent(self, event):
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
        for bi in cf.board.board_items_list:
            item_selection_area = bi.get_selection_area(board=self)
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

            folder_path = cf.folder_path

            filename = f'{time.time()}.jpg'
            filepath = os.path.join(folder_path, filename)
            pixmap.save(filepath)

        if pixmap is not None:

            image_data = self.LibraryData().create_image_data(filepath, cf)
            # image_data.source_width = pixmap.width()
            # image_data.source_height = pixmap.height()

            board_item = BoardItem(BoardItem.types.ITEM_IMAGE)
            board_item.image_data = image_data
            image_data.board_item = board_item
            cf.board.board_items_list.append(board_item)
            board_item.board_index = self.retrieve_new_board_item_index()
            board_item.item_position = self.get_relative_position(self.mapped_cursor_pos())
            cf.images_list.append(image_data)

            # делаем превьюшку и миинатюрку для этой картинки
            self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)

    def board_doubleclick_handler(self, obj, event):
        cf = self.LibraryData().current_folder()
        for board_item in cf.board.board_items_list:
            item_selection_area = board_item.get_selection_area(board=self)
            is_under_mouse = item_selection_area.containsPoint(self.mapped_cursor_pos(), Qt.WindingFill)
            if is_under_mouse:
                self.board_thumbnails_click_handler(None, board_item=board_item)
                break

    def board_thumbnails_click_handler(self, image_data, board_item=None):

        if board_item is None and (image_data is not None) and image_data.board_item is None:
            self.show_center_label("Этот элемент не представлен на доске", error=True)
        else:
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y

            if board_item is not None:
                pass
            else:
                board_item = image_data.board_item

            image_pos = QPointF(board_item.item_position.x()*board_scale_x, board_item.item_position.y()*board_scale_y)
            viewport_center_pos = self.get_center_position()

            self.board_origin = - image_pos + viewport_center_pos

            item_rect = board_item.get_selection_area(board=self, place_center_at_origin=False).boundingRect().toRect()
            fitted_rect = fit_rect_into_rect(item_rect, self.rect())
            self.do_scale_board(0, False, False, False,
                pivot=viewport_center_pos,
                factor_x=fitted_rect.width()/item_rect.width(),
                factor_y=fitted_rect.height()/item_rect.height(),
            )

        self.update()

    def set_default_boardviewport_scale(self, keep_position=False, center_as_pivot=False):
        if center_as_pivot:
            pivot = self.get_center_position()
        else:
            pivot = self.mapped_cursor_pos()
        if keep_position:
            self.do_scale_board(0, False, False, False,
                pivot=pivot,
                factor_x=1/self.board_scale_x,
                factor_y=1/self.board_scale_y,
            )
        else:
            self.board_scale_x = 1.0
            self.board_scale_y = 1.0

    def set_default_boardviewport_origin(self):
        self.board_origin = QPointF(600, 100)

    def retrieve_selected_item(self):
        cf = self.LibraryData().current_folder()
        for bi in cf.board.board_items_list:
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

        # надо менять и значение self.board_origin для того,
        # чтобы увеличивать относительно центра картинки и центра экрана,
        # а они совпадают в данном случае
        factor_x = self._board_scale_x/self.board_scale_x
        factor_y = self._board_scale_y/self.board_scale_y

        pivot = self.get_center_position()

        _board_origin = self.board_origin

        self.board_scale_x *= factor_x
        self.board_scale_y *= factor_y

        _board_origin -= pivot
        _board_origin = QPointF(_board_origin.x()*factor_x, _board_origin.y()*factor_y)
        _board_origin += pivot

        self.board_origin  = _board_origin

        self.update()

    def board_get_nearest_item(self, folder_data, by_window_center=False):
        min_distance = 9999999999999999
        min_distance_board_item = None
        if by_window_center:
            cursor_pos = self.get_center_position()
        else:
            cursor_pos = self.mapped_cursor_pos()
        for board_item in folder_data.board.board_items_list:

            pos = board_item.calculate_absolute_position(board=self)
            distance = QVector2D(pos - cursor_pos).length()
            if distance < min_distance:
                min_distance = distance
                min_distance_board_item = board_item

        return min_distance_board_item

    def board_move_viewport(self, _previous=False, _next=False):
        self.board_unselect_all_items()

        cf = self.LibraryData().current_folder()
        nearest_item = self.board_get_nearest_item(cf, by_window_center=True)

        if nearest_item is not None and len(cf.board.board_items_list) > 1:
            if _previous:
                reverse = True
            elif _next:
                reverse = False

            items_list = self.get_original_items_order(cf.board.board_items_list)
            _list = shift_list_to_became_first(items_list, nearest_item, reverse=reverse)

            first_item = _list[0]
            second_item = _list[1]
            pos = first_item.calculate_absolute_position(board=self)
            distance = QVector2D(pos - self.get_center_position()).length()
            if distance < 5.0:
                # если цент картинки практически совпадает с центром вьюпорта, то выбираем следующую картинку
                item_to_center_viewport = second_item
            else:
                item_to_center_viewport = first_item

            delta = QPointF(self.get_center_position() - self.board_origin)
            current_pos = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)

            item_point = item_to_center_viewport.item_position

            pos1 = QPointF(current_pos.x()*self.board_scale_x, current_pos.y()*self.board_scale_y)
            pos2 = QPointF(item_point.x()*self.board_scale_x, item_point.y()*self.board_scale_y)

            viewport_center_pos = self.get_center_position()

            pos1 = -pos1 + viewport_center_pos
            pos2 = -pos2 + viewport_center_pos


            board_item = item_to_center_viewport

            image_data = board_item.board_retrieve_image_data()
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y

            item_rect = board_item.get_selection_area(board=self, place_center_at_origin=False, apply_global_scale=False).boundingRect().toRect()

            fitted_rect = fit_rect_into_rect(item_rect, self.rect())
            bx = fitted_rect.width()/item_rect.width()
            by = fitted_rect.height()/item_rect.height()

            new_board_scale_x, new_board_scale_y, new_board_origin = self.do_scale_board(1.0,
                False,
                False,
                True,
                factor_x=bx/self.board_scale_x,
                factor_y=by/self.board_scale_y,
                precalculate=True,
                board_scale_x=self.board_scale_x,
                board_scale_y=self.board_scale_y,
                board_origin=pos2,
                pivot = self.get_center_position()
            )

            self.animate_properties(
                [
                    (self, "board_origin", pos1, new_board_origin, self.update),
                    (self, "board_scale_x", self.board_scale_x, new_board_scale_x, self.update),
                    (self, "board_scale_y", self.board_scale_y, new_board_scale_y, self.update),
                ],
                anim_id="flying",
                duration=0.7,
            )

    def get_original_items_order(self, items_list):
        return list(sorted(items_list, key=lambda x: x.board_index))

    def is_flyover_ongoing(self):
        return bool(self.fly_pairs)

    def board_fly_over(self, user_call=False):
        self.board_unselect_all_items()

        if user_call and self.fly_pairs:
            self.cancel_all_anim_tasks()
            self.fly_pairs = []
            return

        viewport_center_pos = self.get_center_position()
        cf = self.LibraryData().current_folder()
        pair = None

        current_pos = delta = QPointF(self.get_center_position() - self.board_origin)
        current_pos = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)

        if not self.fly_pairs:
            _list = []

            if cf.board.board_user_points:
                for point, bx, by in cf.board.board_user_points:
                    _list.append([point, bx, by])
            else:
                nearest_item = self.board_get_nearest_item(cf)
                board_items_list = self.get_original_items_order(cf.board.board_items_list)
                if nearest_item:
                    sorted_list = shift_list_to_became_first(board_items_list, nearest_item)
                else:
                    sorted_list = board_items_list
                for board_item in sorted_list:
                    point = board_item.item_position
                    _list.append([point, None, board_item])

            self.fly_pairs = get_cycled_pairs(_list)
            pair = [
                [current_pos, self.board_scale_x, self.board_scale_y],
                [_list[0][0], _list[0][1], _list[0][2], ]
            ]

        if pair is None:
            pair = next(self.fly_pairs)

        def animate_scale():
            bx = pair[1][1]
            by = pair[1][2]

            if bx is None:
                board_item = by
                board_scale_x = self.board_scale_x
                board_scale_y = self.board_scale_y

                item_rect = board_item.get_selection_area(board=self, place_center_at_origin=False, apply_global_scale=False).boundingRect().toRect()
                fitted_rect = fit_rect_into_rect(item_rect, self.rect())
                bx = fitted_rect.width()/item_rect.width()
                by = fitted_rect.height()/item_rect.height()

            self.animate_properties(
                [
                    (self, "_board_scale_x", self.board_scale_x, bx, self.animate_scale_update),
                    (self, "_board_scale_y", self.board_scale_y, by, self.animate_scale_update),
                ],
                anim_id="flying",
                duration=1.5,
                easing=QEasingCurve.InOutSine,
                callback_on_finish=self.board_fly_over,
            )

        def update_viewport_position():
            self.board_origin = -self.pr_viewport + viewport_center_pos
            self.update()


        delta = QPointF(self.get_center_position() - self.board_origin)
        current_pos_ = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)

        pair = [
            [current_pos_, self.board_scale_x, self.board_scale_y],
            pair[1],
        ]

        pos1 = QPointF(pair[0][0].x()*self.board_scale_x, pair[0][0].y()*self.board_scale_y)
        pos2 = QPointF(pair[1][0].x()*self.board_scale_x, pair[1][0].y()*self.board_scale_y)

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
        return self.LibraryData().current_folder().board.board_ready

    def board_viewport_show_first_item(self):
        self.board_unselect_all_items()
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
            if cf.board.board_items_list:
                items_list = self.get_original_items_order(cf.board.board_items_list)
                item = items_list[0]
                self.board_thumbnails_click_handler(None, item)

    def board_viewport_show_last_item(self):
        self.board_unselect_all_items()
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
           if cf.board.board_items_list:
                items_list = self.get_original_items_order(cf.board.board_items_list)
                item = items_list[-1]
                self.board_thumbnails_click_handler(None, item)

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
                        (self, "board_origin", self.board_origin, self.board_orig_origin, self.update),
                        (self, "board_scale_x", self.board_scale_x, self.board_orig_scale_x, self.update),
                        (self, "board_scale_y", self.board_scale_y, self.board_orig_scale_y, self.update),
                    ],
                    anim_id="board_region_zoom_out",
                    duration=0.4,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.board_scale_x = self.board_orig_scale_x
                self.board_scale_y = self.board_orig_scale_y
                self.board_origin = self.board_orig_origin
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
            before_pos = QPointF(self.board_origin)

            # 1. сдвинуть изображение так, чтобы позиция input_center оказалась в центре окна
            diff = self.rect().center() - input_center
            pos = self.board_origin + diff
            self.board_origin = pos

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
                        (self, "board_origin", before_pos, origin, self.update),
                        (self, "board_scale_x", self.board_scale_x, scale_x, self.update),
                        (self, "board_scale_y", self.board_scale_y, scale_y, self.update),
                        (self, "board_magnifier_input_rect_animated", self.board_magnifier_input_rect_animated, self.board_magnifier_projected_rect, self.update)
                    ],
                    anim_id="board_region_zoom_in",
                    duration=0.8,
                    easing=QEasingCurve.InOutCubic
                )
            else:
                self.board_origin = origin
                self.board_scale_x = scale_x
                self.board_scale_y = scale_y

    def board_region_zoom_in_mousePressEvent(self, event):
        if not self.board_zoom_region_defined:
            self.board_region_zoom_in_input_started = True
            self.board_INPUT_POINT1 = event.pos()
            self.board_magnifier_input_rect = None
            self.board_orig_scale_x = self.board_scale_x
            self.board_orig_scale_y = self.board_scale_y
            self.board_orig_origin = self.board_origin
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



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
