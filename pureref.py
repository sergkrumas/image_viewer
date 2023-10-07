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

class PureRefLibraryDataMixin():

    def get_pureref_boards_root(self):
        rootpath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.PUREREF_BOARDS_ROOT)
        create_pathsubfolders_if_not_exist(rootpath)
        return rootpath

    def load_pureref_boards(self):
        if os.path.exists(self.get_pureref_boards_root()):
            print("loading pureRef boards data")

class PureRefBoardItem():

    class types():
        ITEM_IMAGE = 1
        ITEM_FOLDER = 2
        ITEM_GROUP = 3

    def __init__(self, item_type, image_data, items):
        super().__init__()
        self.type = item_type
        self.image_data = image_data
        image_data.pureref_item = self
        items.append(self)

        self.board_scale = 1.0
        self.board_position = QPointF()
        self.board_rotation = None


class PureRefMixin():

    def pureref_init(self):
        self.pureref_mode = False

        self.board_origin = self.get_center_position()
        self.board_scale_x = 1.0
        self.board_scale_y = 1.0

        self.board_translating = True

        self.pureref_show_minimap = False

        self.pr_viewport = QPointF(0, 0)

        self.fly_pairs = []
        self._board_scale_x = 1.0
        self._board_scale_y = 1.0

    def pureref_toggle_minimap(self):
        self.pureref_show_minimap = not self.pureref_show_minimap

    def pureref_draw_stub(self, painter):
        font.setPixelSize(250)
        font.setWeight(1900)
        painter.setFont(font)
        pen = QPen(QColor(180, 180, 180), 1)
        painter.setPen(pen)
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, "PUREREF BOARDS")

    def pureref_draw(self, painter):
        old_font = painter.font()
        font = QFont(old_font)

        self.pureref_draw_main(painter)
        # pureref_draw_stub(self, painter)

        painter.setFont(old_font)

    def pureref_draw_wait_label(self, painter):
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

        items_list = folder_data.pureref_items_list = []

        for image_data in folder_data.images_list:
            if not image_data.preview_error:
                prbi = PureRefBoardItem(PureRefBoardItem.types.ITEM_IMAGE, image_data, items_list)
                prbi.board_scale = 1.0
                prbi.board_position = offset + QPointF(image_data.source_width, image_data.source_height)/2
                offset += QPointF(image_data.source_width, 0)

        self.build_bounding_rect(folder_data)

        folder_data.board_ready = True

    def pureref_draw_content(self, painter, folder_data):
        
        if not folder_data.board_ready:
            self.prepare_board(folder_data)
        else:

            painter.setPen(QPen(Qt.white, 1))
            font = painter.font()
            font.setWeight(300)
            font.setPixelSize(12)
            painter.setFont(font)
            for prbi in folder_data.pureref_items_list:
                image_data = prbi.image_data

                item_scale = prbi.board_scale
                board_scale_x = self.board_scale_x
                board_scale_y = self.board_scale_y
                w = image_data.source_width*item_scale*board_scale_x
                h = image_data.source_height*item_scale*board_scale_y
                image_rect = QRectF(0, 0, w, h)
                pos = QPointF(self.board_origin)
                pos += QPointF(prbi.board_position.x()*board_scale_x, prbi.board_position.y()*board_scale_y)
                image_rect.moveCenter(pos)

                painter.setBrush(Qt.NoBrush)
                painter.drawRect(image_rect)

                text = f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
                max_rect = self.rect()
                alignment = Qt.AlignCenter

                painter.drawText(image_rect, alignment, text)

                painter.drawPixmap(image_rect, image_data.preview, QRectF(QPointF(0, 0), QSizeF(image_data.preview.size())))

    def pureref_draw_grid(self, painter):
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

    def pureref_draw_user_points(self, painter, cf):

        painter.setPen(QPen(Qt.red, 5))
        for point, board_scale_x, board_scale_y in cf.board_user_points:
            p = self.board_origin + QPointF(point.x()*self.board_scale_x, point.y()*self.board_scale_y)
            painter.drawPoint(p)

    def pureref_draw_main(self, painter):

        cf = self.LibraryData().current_folder()
        if cf.previews_done:
            self.pureref_draw_grid(painter)
            self.pureref_draw_content(painter, cf)
        else:
            self.pureref_draw_wait_label(painter)


        self.draw_center_label_main(painter)

        if self.Globals.DEBUG:
            self.pureref_draw_board_origin(painter)
            self.pureref_draw_origin_compass(painter)

        self.pureref_draw_user_points(painter, cf)

        self.pureref_draw_minimap(painter)

    def pureref_draw_origin_compass(self, painter):

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

    def pureref_draw_board_origin(self, painter):
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
        for prbi in folder_data.pureref_items_list:
            image_data = prbi.image_data
            rf = QRectF(0, 0, image_data.source_width, image_data.source_height)
            rf.moveCenter(prbi.board_position)
            points.append(rf.topLeft())
            points.append(rf.bottomRight())
        p1, p2 = get_bounding_points(points)
        bounding_rect = build_valid_rectF(p1, p2)
        self.board_bounding_rect = bounding_rect

    def pureref_draw_minimap(self, painter):
        if not self.pureref_show_minimap:
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

            for prbi in cf.pureref_items_list:
                image_data = prbi.image_data

                delta = prbi.board_position - self.board_bounding_rect.topLeft()
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


    def pureref_mousePressEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if event.buttons() == Qt.LeftButton:
            if self.transformations_allowed:
                self.board_translating = True
                self.start_cursor_pos = self.mapped_cursor_pos()
                self.start_origin_pos = self.board_origin
                self.update()


    def pureref_mouseMoveEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if event.buttons() == Qt.LeftButton:
            if self.transformations_allowed and self.board_translating:
                end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
                start_value = self.board_origin
                # delta = end_value-start_value
                self.board_origin = end_value
        self.update()

    def pureref_mouseReleaseEvent(self, event):

        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        if event.button() == Qt.LeftButton:
            if self.transformations_allowed:
                self.board_translating = False
                self.update()
        if event.button() == Qt.MiddleButton:
            if self.transformations_allowed:
                self.set_default_boardviewport_scale(keep_position=True)

        if event.button() == Qt.LeftButton and ctrl and not shift:
            cf = self.LibraryData().current_folder()
            delta = QPointF(event.pos() - self.board_origin)
            delta = QPointF(delta.x()/self.board_scale_x, delta.y()/self.board_scale_y)
            cf.board_user_points.append([delta, self.board_scale_x, self.board_scale_y])

    def do_scale_board(self, scroll_value, ctrl, shift, no_mod, pivot=None, factor_x=None, factor_y=None, precalculate=False):

        curpos = self.mapped_cursor_pos()
        if pivot is None:
            pivot = curpos

        _board_origin = self.board_origin

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

        self.board_scale_x *= factor_x
        self.board_scale_y *= factor_y

        _board_origin -= pivot
        _board_origin = QPointF(_board_origin.x()*factor_x, _board_origin.y()*factor_y)
        _board_origin += pivot

        self.board_origin  = _board_origin

        self.update()

    def pureref_do_scale_board(self, scroll_value):
        self.do_scale_board(scroll_value, False, False, False, pivot=self.get_center_position())

    def pureref_wheelEvent(self, event):
        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        control_panel_undermouse = self.is_control_panel_under_mouse()
        if control_panel_undermouse:
            return
        elif no_mod:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif ctrl:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)
        elif shift:
            self.do_scale_board(scroll_value, ctrl, shift, no_mod)

    def pureref_thumbnails_click_handler(self, image_data):

        if image_data.pureref_item is None:
            self.show_center_label("Этот элемент не представлен на доске", error=True)
        else:
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y

            prbi = image_data.pureref_item
            image_pos = QPointF(prbi.board_position.x()*board_scale_x, prbi.board_position.y()*board_scale_y)
            viewport_center_pos = self.get_center_position()

            self.board_origin = - image_pos + viewport_center_pos

            image_width = image_data.source_width*prbi.board_scale*board_scale_x
            image_height = image_data.source_height*prbi.board_scale*board_scale_y
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

        # надо менять и значение self.board_origin для того, чтобы увеличивать относительно центра картинки и центра экрана (они совпадают)
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

    def pureref_fly_over_board(self, user_call=False):

        if user_call and self.fly_pairs:
            # создаём таску с тем же anim_id, чтобы отменить циклическую анимацию
            self.animate_properties(
                [
                    (self, "pr_viewport", self.pr_viewport, self.pr_viewport, self.update),
                ],
                anim_id="flying",
                duration=0.001,
            )
            self.fly_pairs = list()
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
                for prbi in cf.pureref_items_list:
                    point = prbi.board_position
                    _list.append([point, None, prbi])
                    # _list.append([point, bx, by, prbi])

            self.fly_pairs = get_cycled_pairs(_list, slideshow=False)
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
                prbi = by
                image_data = by.image_data
                board_scale_x = self.board_scale_x
                board_scale_y = self.board_scale_y
                # переменные пришлось закоментить, чтобы работало с любым изначальным скейлом
                image_width = image_data.source_width*prbi.board_scale #*board_scale_x
                image_height = image_data.source_height*prbi.board_scale #*board_scale_y
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
                callback_on_finish=self.pureref_fly_over_board,
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
            # callback_on_finish=self.pureref_fly_over_board
        )



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
