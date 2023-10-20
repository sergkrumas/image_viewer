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

BOARD_DEBUG = True

class BoardLibraryDataMixin():

    def get_boards_root(self):
        rootpath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.BOARDS_ROOT)
        create_pathsubfolders_if_not_exist(rootpath)
        return rootpath

    def load_boards(self):
        if os.path.exists(self.get_boards_root()):
            print("loading boards data")

class BoardItem():

    class types():
        ITEM_IMAGE = 1
        ITEM_FOLDER = 2
        ITEM_GROUP = 3

    def __init__(self, item_type, image_data, items):
        super().__init__()
        self.type = item_type
        self.image_data = image_data
        image_data.board_item = self
        items.append(self)

        self.pixmap = None
        self.animated = False

        self.board_scale_x = 1.0
        self.board_scale_y = 1.0
        self.board_position = QPointF()
        self.board_rotation = 0

        if BOARD_DEBUG:
            self.board_scale_x = 0.5
            self.board_rotation = 10

    def calculate_absolute_position(self, board=None):
        _scale_x = board.board_scale_x
        _scale_y = board.board_scale_y
        rel_pos = self.board_position
        return QPointF(board.board_origin) + QPointF(rel_pos.x()*_scale_x, rel_pos.y()*_scale_y)

    def get_size_rect(self):
        if self.type == self.types.ITEM_IMAGE:
            return QRectF(0, 0, self.image_data.source_width, self.image_data.source_height)
        elif self.type == self.types.ITEM_FOLDER:
            raise NotImplemented
        elif self.type == self.types.ITEM_GROUP:
            raise NotImplemented

    def get_selection_polygon(self, board=None):
        size_rect = self.get_size_rect()
        size_rect.moveCenter(QPointF(0, 0))
        points = [
            size_rect.topLeft(),
            size_rect.topRight(),
            size_rect.bottomRight(),
            size_rect.bottomLeft(),
        ]
        polygon = QPolygonF(points)

        local_scaling = QTransform()
        rotation = QTransform()
        global_scaling = QTransform()
        translation = QTransform()

        local_scaling.scale(self.board_scale_x, self.board_scale_y)
        rotation.rotate(self.board_rotation)
        pos = self.calculate_absolute_position(board=board)
        translation.translate(pos.x(), pos.y())
        global_scaling.scale(board.board_scale_x, board.board_scale_y)
        transform = local_scaling * rotation * global_scaling * translation

        return transform.map(polygon)

class BoardMixin():

    def board_init(self):

        self.board_origin = self.get_center_position()
        self.board_scale_x = 1.0
        self.board_scale_y = 1.0

        self.board_translating = False

        self.board_show_minimap = False

        self.pr_viewport = QPointF(0, 0)

        self.fly_pairs = []
        self._board_scale_x = 1.0
        self._board_scale_y = 1.0

        self.board_item_under_mouse = None
        self.images_drawn = 0

        self.context_menu_allowed = True

        self.board_region_zoom_in_init()

    def board_toggle_minimap(self):
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

    def board_draw_wait_label(self, painter):
        font = painter.font()
        font.setPixelSize(100)
        font.setWeight(1900)
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter

        painter.setPen(QPen(QColor(240, 10, 50, 100), 1))
        text = "  ".join("ПОДОЖДИ")
        text_rect = calculate_text_rect(font, max_rect, text, alignment)
        text_rect.moveCenter(self.rect().center() + QPoint(0, -80))
        painter.drawText(text_rect, alignment, text)

    def prepare_board(self, folder_data):

        if self.Globals.DEBUG:
            offset = QPointF(0, 0) - QPointF(500, 0)
        else:
            offset = QPointF(0, 0)

        items_list = folder_data.board_items_list = []

        for image_data in folder_data.images_list:
            if not image_data.preview_error:
                board_item = BoardItem(BoardItem.types.ITEM_IMAGE, image_data, items_list)
                board_item.board_scale = 1.0
                board_item.board_position = offset + QPointF(image_data.source_width, image_data.source_height)/2
                offset += QPointF(image_data.source_width, 0)

        self.build_bounding_rect(folder_data)

        folder_data.board_ready = True
        self.update()

    def board_draw_content(self, painter, folder_data):

        if not folder_data.board_ready:
            self.prepare_board(folder_data)
        else:

            painter.setPen(QPen(Qt.white, 1))
            font = painter.font()
            font.setWeight(300)
            font.setPixelSize(12)
            painter.setFont(font)

            self.images_drawn = 0
            self.board_item_under_mouse = None
            for board_item in folder_data.board_items_list:
                self.board_draw_item(painter, board_item)

            self.draw_selection(painter, folder_data)

            painter.drawText(self.rect().bottomLeft() + QPoint(50, -150), f'perfomance status: {self.images_drawn} images drawn')

    def draw_selection(self, painter, folder_data):
        old_pen = painter.pen()
        pen = QPen(Qt.green, 1)
        painter.setPen(pen)

        for board_item in folder_data.board_items_list:
            painter.drawPolygon(board_item.get_selection_polygon(board=self))

        painter.setPen(old_pen)

    def board_draw_item(self, painter, board_item):
        image_data = board_item.image_data
        item_scale = board_item.board_scale
        board_scale_x = self.board_scale_x
        board_scale_y = self.board_scale_y
        w = image_data.source_width*item_scale*board_scale_x
        h = image_data.source_height*item_scale*board_scale_y
        image_rect = QRectF(0, 0, w, h)
        pos = QPointF(self.board_origin)
        pos += QPointF(board_item.board_position.x()*board_scale_x, board_item.board_position.y()*board_scale_y)
        image_rect.moveCenter(pos)

        if image_rect.intersected(QRectF(self.rect())).isNull():
            self.trigger_board_item_pixmap_unloading(board_item)

        else:
            self.images_drawn += 1

            painter.setBrush(Qt.NoBrush)
            painter.drawRect(image_rect)
            text = f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
            alignment = Qt.AlignCenter
            painter.drawText(image_rect, alignment, text)

            image_to_draw = None
            if image_rect.width() < 250 or image_rect.height() < 250:
                image_to_draw = image_data.preview
            else:
                self.trigger_board_item_pixmap_loading(board_item)
                image_to_draw = board_item.pixmap

            if image_rect.contains(self.mapped_cursor_pos()):
                self.board_item_under_mouse = board_item

            if image_to_draw:
                painter.drawPixmap(image_rect, image_to_draw, QRectF(QPointF(0, 0), QSizeF(image_to_draw.size())))

            if board_item == self.board_item_under_mouse and board_item.animated:
                # painter.drawText(image_rect.topLeft(), board_item.status)

                alignment = Qt.AlignCenter | Qt.AlignVCenter
                text_rect = calculate_text_rect(painter.font(), image_rect, board_item.status, alignment)
                text_rect.adjust(-5, -5, 5, 5)
                text_rect.moveTopLeft(image_rect.topLeft())

                if text_rect.width() < image_rect.width():
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(text_rect), 5, 5)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(50, 60, 90)))
                    painter.drawPath(path)

                    painter.setPen(QPen(Qt.white, 1))
                    painter.drawText(text_rect, alignment, board_item.status)



    def trigger_board_item_pixmap_unloading(self, board_item):
        if board_item.pixmap is None:
            return

        dist = calculate_distance(
                board_item.calculate_absolute_position(board=self),
                self.get_center_position()
        )
        if dist > 10000.0:
            board_item.pixmap = None
            board_item.movie = None

            filepath = board_item.image_data.filepath
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
            self.update_scroll_status(board_item)
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

        filepath = board_item.image_data.filepath
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
        for point, board_scale_x, board_scale_y in cf.board_user_points:
            p = self.board_origin + QPointF(point.x()*self.board_scale_x, point.y()*self.board_scale_y)
            painter.drawPoint(p)

    def board_draw_main(self, painter):

        cf = self.LibraryData().current_folder()
        if cf.previews_done:
            self.board_draw_grid(painter)
            self.board_draw_content(painter, cf)
        else:
            self.board_draw_wait_label(painter)


        if self.Globals.DEBUG:
            self.board_draw_board_origin(painter)
            self.board_draw_origin_compass(painter)

        self.board_draw_user_points(painter, cf)

        self.board_draw_minimap(painter)

        self.board_region_zoom_in_draw(painter)

    def board_draw_origin_compass(self, painter):

        curpos = self.mapFromGlobal(QCursor().pos())

        pos = self.board_origin

        def distance(p1, p2):
            return math.sqrt((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)

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
        painter.drawEllipse(ellipse_rect)

        dist = distance(pos, curpos)
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
        painter.setFont(font)
        max_rect = self.rect()
        alignment = Qt.AlignCenter


        text_rect = calculate_text_rect(font, max_rect, text, alignment)

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
        text_rect = calculate_text_rect(font, max_rect, text, alignment)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, -80))
        painter.drawText(text_rect, alignment, text)

        text = "КООРДИНАТ"
        text_rect = calculate_text_rect(font, max_rect, text, alignment)
        text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, 80))
        painter.drawText(text_rect, alignment, text)

    def build_bounding_rect(self, folder_data):
        points = []
        points.append(self.board_origin)
        for board_item in folder_data.board_items_list:
            image_data = board_item.image_data
            rf = QRectF(0, 0, image_data.source_width, image_data.source_height)
            rf.moveCenter(board_item.board_position)
            points.append(rf.topLeft())
            points.append(rf.bottomRight())
        p1, p2 = get_bounding_points(points)
        bounding_rect = build_valid_rectF(p1, p2)
        self.board_bounding_rect = bounding_rect

    def board_draw_minimap(self, painter):
        if not self.board_show_minimap:
            return

        cf = self.LibraryData().current_folder()
        if cf.board_ready:
            painter.fillRect(self.rect(), QBrush(QColor(20, 20, 20, 220)))

            minimap_rect = self.board_bounding_rect
            map_width = max(400, self.rect().width() - 300)
            factor = map_width / self.board_bounding_rect.width()
            map_height = self.board_bounding_rect.height()*factor
            minimap_rect = QRectF(0, 0, map_width, map_height)
            minimap_rect.moveCenter(self.get_center_position())

            # backplate
            minimap_backplate = minimap_rect.adjusted(-10, -10, 10, 10)
            painter.fillRect(minimap_backplate, QBrush(QColor(0, 0, 0, 150)))
            # gray frame
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.drawRect(minimap_rect)

            for board_item in cf.board_items_list:
                image_data = board_item.image_data

                delta = board_item.board_position - self.board_bounding_rect.topLeft()
                delta = QPointF(
                    abs(delta.x()/self.board_bounding_rect.width()),
                    abs(delta.y()/self.board_bounding_rect.height())
                )
                point = minimap_rect.topLeft() + QPointF(delta.x()*map_width, delta.y()*map_height)
                painter.setPen(QPen(Qt.red, 4))
                painter.drawPoint(point)

                w = map_width   *   image_data.source_width/self.board_bounding_rect.width()
                h = map_height   *   image_data.source_height/self.board_bounding_rect.height()
                image_frame_rect = QRectF(0, 0, w, h)
                image_frame_rect.moveCenter(point)

                painter.setPen(QPen(Qt.green, 1))
                painter.drawRect(image_frame_rect)

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


    def board_mousePressEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier


        if self.isLeftClickAndShift(event):
            self.board_region_zoom_in_mousePressEvent(event)

        elif event.buttons() == Qt.MiddleButton:
            if self.transformations_allowed:
                self.board_translating = True
                self.start_cursor_pos = self.mapped_cursor_pos()
                self.start_origin_pos = self.board_origin
                self.update()

    def isLeftClickAndShift(self, event):
        return event.buttons() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier

    def board_mouseMoveEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier


        if self.isLeftClickAndShift(event) or self.board_region_zoom_in_input_started:
            self.board_region_zoom_in_mouseMoveEvent(event)
        elif event.buttons() == Qt.MiddleButton:
            if self.transformations_allowed and self.board_translating:
                end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
                start_value = self.board_origin
                # delta = end_value-start_value
                self.board_origin = end_value

        self.update()

    def board_mouseReleaseEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if self.isLeftClickAndShift(event) or self.board_region_zoom_in_input_started:
            self.board_region_zoom_in_mouseReleaseEvent(event)

        if event.button() == Qt.MiddleButton:
            if self.transformations_allowed:
                self.board_translating = False
                self.update()
        if event.button() == Qt.MiddleButton and event.modifiers() == Qt.AltModifier:
            if self.transformations_allowed:
                self.set_default_boardviewport_scale(keep_position=True)

        if event.button() == Qt.LeftButton and ctrl and not shift:
            cf = self.LibraryData().current_folder()
            delta = QPointF(event.pos() - self.board_origin)
            delta = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)
            cf.board_user_points.append([delta, self.board_scale_x, self.board_scale_y])

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

        self.update()

    def board_do_scale(self, scroll_value):
        self.do_scale_board(scroll_value, False, False, False, pivot=self.get_center_position())

    def update_scroll_status(self, board_item):
        current_frame = board_item.movie.currentFrameNumber()
        frame_count = board_item.movie.frameCount()
        if frame_count > 0:
            current_frame += 1
        board_item.status = f'{current_frame}/{frame_count}'

    def board_item_scroll_animation(self, board_item, scroll_value):
        frames_list = list(range(0, board_item.movie.frameCount()))
        if scroll_value > 0:
            pass
        else:
            frames_list = list(reversed(frames_list))
        frames_list.append(0)
        i = frames_list.index(board_item.movie.currentFrameNumber()) + 1
        board_item.movie.jumpToFrame(frames_list[i])
        board_item.pixmap = board_item.movie.currentPixmap()
        self.update_scroll_status(board_item)
        self.update()

    def board_wheelEvent(self, event):
        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        control_panel_undermouse = self.is_control_panel_under_mouse()
        if control_panel_undermouse:
            return
        elif self.board_translating:
            return
        elif self.board_item_under_mouse is not None and event.buttons() == Qt.RightButton:
            board_item = self.board_item_under_mouse
            self.context_menu_allowed = False
            if board_item.animated and board_item.type == board_item.types.ITEM_IMAGE:
                self.board_item_scroll_animation(board_item, scroll_value)
        elif no_mod:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif ctrl:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif shift:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)

    def board_thumbnails_click_handler(self, image_data):

        if image_data.board_item is None:
            self.show_center_label("Этот элемент не представлен на доске", error=True)
        else:
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y

            board_item = image_data.board_item
            image_pos = QPointF(board_item.board_position.x()*board_scale_x, board_item.board_position.y()*board_scale_y)
            viewport_center_pos = self.get_center_position()

            self.board_origin = - image_pos + viewport_center_pos

            image_width = image_data.source_width*board_item.board_scale*board_scale_x
            image_height = image_data.source_height*board_item.board_scale*board_scale_y
            image_rect = QRect(0, 0, int(image_width), int(image_height))
            fitted_rect = fit_rect_into_rect(image_rect, self.rect())
            self.do_scale_board(0, False, False, False,
                pivot=viewport_center_pos,
                factor_x=fitted_rect.width()/image_rect.width(),
                factor_y=fitted_rect.height()/image_rect.height(),
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
        self.board_origin = QPointF(300, 300)

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
        for board_item in folder_data.board_items_list:

            pos = board_item.calculate_absolute_position(board=self)
            distance = calculate_distance(pos, cursor_pos)
            if distance < min_distance:
                min_distance = distance
                min_distance_board_item = board_item

        return min_distance_board_item

    def board_move_viewport(self, _previous=False, _next=False):

        cf = self.LibraryData().current_folder()
        nearest_item = self.board_get_nearest_item(cf, by_window_center=True)

        if nearest_item is not None and len(cf.board_items_list) > 1:
            if _previous:
                reverse = True
            elif _next:
                reverse = False

            _list = shift_list_to_became_first(cf.board_items_list, nearest_item, reverse=reverse)

            first_item = _list[0]
            second_item = _list[1]
            pos = first_item.calculate_absolute_position(board=self)
            distance = calculate_distance(pos, self.get_center_position())
            if distance < 5.0:
                # если цент картинки практически совпадает с центром вьюпорта, то выбираем следующую картинку
                item_to_center_viewport = second_item
            else:
                item_to_center_viewport = first_item

            delta = QPointF(self.get_center_position() - self.board_origin)
            current_pos = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)

            item_point = item_to_center_viewport.board_position

            pos1 = QPointF(current_pos.x()*self.board_scale_x, current_pos.y()*self.board_scale_y)
            pos2 = QPointF(item_point.x()*self.board_scale_x, item_point.y()*self.board_scale_y)

            viewport_center_pos = self.get_center_position()

            pos1 = -pos1 + viewport_center_pos
            pos2 = -pos2 + viewport_center_pos


            board_item = item_to_center_viewport
            image_data = board_item.image_data
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y

            # переменные пришлось закоментить, чтобы работало с любым изначальным скейлом
            image_width = image_data.source_width*board_item.board_scale #*board_scale_x
            image_height = image_data.source_height*board_item.board_scale #*board_scale_y
            image_rect = QRect(0, 0, int(image_width), int(image_height))
            fitted_rect = fit_rect_into_rect(image_rect, self.rect())
            bx = fitted_rect.width()/image_rect.width()
            by = fitted_rect.height()/image_rect.height()

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




    def board_fly_over(self, user_call=False):

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

            if cf.board_user_points:
                for point, bx, by in cf.board_user_points:
                    _list.append([point, bx, by])
            else:
                nearest_item = self.board_get_nearest_item(cf)
                if nearest_item:
                    sorted_list = shift_list_to_became_first(cf.board_items_list, nearest_item)
                else:
                    sorted_list = cf.board_items_list
                for board_item in sorted_list:
                    point = board_item.board_position
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
                image_data = by.image_data
                board_scale_x = self.board_scale_x
                board_scale_y = self.board_scale_y
                # переменные пришлось закоментить, чтобы работало с любым изначальным скейлом
                image_width = image_data.source_width*board_item.board_scale #*board_scale_x
                image_height = image_data.source_height*board_item.board_scale #*board_scale_y
                image_rect = QRect(0, 0, int(image_width), int(image_height))
                fitted_rect = fit_rect_into_rect(image_rect, self.rect())
                bx = fitted_rect.width()/image_rect.width()
                by = fitted_rect.height()/image_rect.height()

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
        return self.LibraryData().current_folder().board_ready


    def board_viewport_show_first_item(self):
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
            if cf.board_items_list:
                self.board_thumbnails_click_handler(cf.board_items_list[0].image_data)

    def board_viewport_show_last_item(self):
        cf = self.LibraryData().current_folder()
        if self.is_board_ready():
           if cf.board_items_list:
                self.board_thumbnails_click_handler(cf.board_items_list[-1].image_data)







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

    def board_region_zoom_build_magnifier_input_rect(self):
        if self.board_INPUT_POINT1 and self.board_INPUT_POINT2:
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
