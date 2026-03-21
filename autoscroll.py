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

__import__('builtins').__dict__['_'] = __import__('gettext').gettext




class AutoscrollMixin():

    def autoscroll_init(self):
        self.AUTOSCROLL = AUTOSCROLL = type("AUTOSCROLL", (), {})()

        AUTOSCROLL.timer = QTimer()
        AUTOSCROLL.timer.setInterval(10)
        AUTOSCROLL.timer.timeout.connect(self.autoscroll_timer)
        AUTOSCROLL.inside_activation_zone = False
        AUTOSCROLL.is_moved_while_middle_button_pressed = False

        AUTOSCROLL.desactivation_pass = False

        AUTOSCROLL.direction_vector = QPointF()
        AUTOSCROLL.board_item_transform = False
        self.AUTOSCROLL.INNER_OUTER_OFFSET = 100

    def autoscroll_cursor_over_origin(self):
        return self.AUTOSCROLL.timer.isActive() and self.AUTOSCROLL.inside_activation_zone

    def autoscroll_set_speed_factor(self, scroll_value):
        if self.is_board_page_active():
            setting_id = 'board_autoscroll_speed'
        elif self.is_library_page_active():
            setting_id = 'library_autoscroll_speed'
        elif self.is_waterfall_page_active():
            setting_id = 'waterfall_autoscroll_speed'
        DEFAULT_FACTOR = 1.0
        factors = [0.01, 0.10, 0.25, 0.5, 0.75, DEFAULT_FACTOR, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        current_speed_factor = self.autoscroll_get_speed_factor()
        if current_speed_factor not in factors:
            # в окне настроек можно выставить совершенно произвольные значения, которых нет в factors
            current_speed_factor = DEFAULT_FACTOR
        if scroll_value > 0:
            index_change = +1
        else:
            index_change = -1
        new_index = factors.index(current_speed_factor) + index_change
        new_index %= len(factors)
        speed_factor = factors[new_index]
        setattr(self.STNG, setting_id, speed_factor)
        self.Settings.postponed_set(setting_id, speed_factor)
        speed_percent = "{0:.0f}%".format(speed_factor*100)
        self.show_center_label(_("autoscroll speed {0}").format(speed_percent), duration=2.0)

    def autoscroll_get_speed_factor(self):
        if self.is_board_page_active():
            setting_id = 'board_autoscroll_speed'
        elif self.is_library_page_active():
            setting_id = 'library_autoscroll_speed'
        elif self.is_waterfall_page_active():
            setting_id = 'waterfall_autoscroll_speed'
        else:
            setting_id = None
        if setting_id is not None:
            return getattr(self.STNG, setting_id)
        else:
            return 1.0

    def autoscroll_set_current_page_indicator(self):
        self.AUTOSCROLL.draw_vertical = False
        self.AUTOSCROLL.draw_horizontal = False
        if self.is_board_page_active():
            self.AUTOSCROLL.draw_vertical = True
            self.AUTOSCROLL.draw_horizontal = True
        elif self.is_library_page_active():
            self.AUTOSCROLL.draw_vertical = True
        elif self.is_waterfall_page_active():
            self.AUTOSCROLL.draw_vertical = True

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
        cursor_pos = self.mapped_cursor_pos()
        cursor_offset = cursor_pos - self.AUTOSCROLL.startpos
        diff_l = QVector2D(cursor_offset).length()
        self.AUTOSCROLL.inside_activation_zone = diff_l < OUTER_ZONE_ACTIVATION_RADIUS
        if not self.AUTOSCROLL.inside_activation_zone:
            # fixing velocity, because it should be 0.0 at the radius border, not greater than 0.0
            diff_l = max(0.0, diff_l - OUTER_ZONE_ACTIVATION_RADIUS)
            vec = QVector2D(cursor_offset).normalized()*diff_l
            velocity_vec = vec.toPointF()
            self.AUTOSCROLL.direction_vector = QVector2D(velocity_vec).normalized().toPointF()
            speed_factor = self.autoscroll_get_speed_factor()

            if self.is_board_page_active():
                if self.AUTOSCROLL.board_item_transform:
                    o, i = self.autoscroll_activation_zones_for_board_item_transform()
                    # у внешних границ должна быть максимальная скорость, у внутренних - минимальная, то есть нулевая
                    s1 = fit(cursor_pos.y(), o.top(), i.top(), 1.0, 0.0)
                    s2 = fit(cursor_pos.y(), i.bottom(), o.bottom(), 0.0, 1.0)
                    s3 = fit(cursor_pos.x(), o.left(), i.left(), 1.0, 0.0)
                    s4 = fit(cursor_pos.x(), i.right(), o.right(), 0.0, 1.0)
                    sf = max((s1, s2, s3, s4))
                    speed_factor *= sf
                    # переназначем изначальную скорость, отводим "курсор" из центра до верхней границы окна
                    length = QVector2D(self.AUTOSCROLL.startpos - QPoint(self.AUTOSCROLL.startpos.x(), 0)).length()
                    velocity_vec = QVector2D(velocity_vec).normalized().toPointF()*length
                    speed_factor /= 4.0
                    # self.show_center_label(f'{sf}: {s1} {s2} {s3} {s4}')

                self.canvas_origin -= velocity_vec*speed_factor/25.0
                if self.AUTOSCROLL.board_item_transform:
                    if self.translation_ongoing:
                        self.board_DO_selected_items_TRANSLATION(cursor_pos)
                    if self.rotation_ongoing:
                        self.board_DO_selected_items_ROTATION(cursor_pos)
                    if self.scaling_ongoing:
                        self.board_DO_selected_items_SCALING(cursor_pos)
                else:
                    self.update_selection_bouding_box()

            elif self.is_library_page_active() or self.is_waterfall_page_active():
                vs = self.vertical_scrollbars
                sb_index = self.autoscroll_is_scrollbar_available()
                if sb_index == vs.NO_SCROLLBAR:
                    self.autoscroll_finish()
                else:
                    self.autoscroll_do_for_LibraryWaterfall_pages(velocity_vec.y()*speed_factor/8.0)

        self.update()

    def autoscroll_intro_for_LibraryWaterfall_pages(self, scrollbar_index):
        LibraryData = self.LibraryData

        vs = self.vertical_scrollbars
        sb_data = vs.data[scrollbar_index]
        vs.capture_index = scrollbar_index
        vs.captured_thumb_rect_at_start = QRectF(sb_data.thumb_rect)
        if scrollbar_index == vs.LIBRARY_PAGE_FOLDERS_LIST:
            vs.captured_scroll_offset = LibraryData().folderslist_scroll_offset
        elif scrollbar_index == vs.LIBRARY_PAGE_PREVIEWS_LIST:
            cf = LibraryData().current_folder()
            vs.captured_scroll_offset = cf.library_previews.scroll_offset

    def autoscroll_do_for_LibraryWaterfall_pages(self, velocity_y):
        LibraryData = self.LibraryData

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
                cf.library_previews.scroll_offset -= velocity_y
                content_height = self.library_page_previews_columns_content_height(cf)
                cf.library_previews.scroll_offset = self.apply_scroll_and_limits(
                                                            cf.library_previews.scroll_offset,
                                                            0,
                                                            content_height,
                                                            LIBRARY_VIEWFRAME_HEIGHT,
                                                        )


            elif index in [vs.WATERFALL_PAGE_LEFT, vs.WATERFALL_PAGE_RIGHT]:
                cf = LibraryData().current_folder()
                cf.waterfall_previews.scroll_offset -= velocity_y
                content_height = self.waterfall_page_previews_columns_content_height(cf)
                cf.waterfall_previews.scroll_offset = self.apply_scroll_and_limits(
                                                            cf.waterfall_previews.scroll_offset,
                                                            0,
                                                            content_height,
                                                            WATERFALL_VIEWFRAME_HEIGHT,
                                                        )

            self.update()

    def autoscroll_outro_for_LibraryWaterfall_pages(self):
        vs = self.vertical_scrollbars
        vs.capture_index = vs.NO_SCROLLBAR

    def autoscroll_start(self):
        self.AUTOSCROLL.inside_activation_zone = False
        self.autoscroll_set_current_page_indicator()
        if self.is_library_page_active() or self.is_waterfall_page_active():
            sb_index = self.autoscroll_is_scrollbar_available()
            if sb_index != self.vertical_scrollbars.NO_SCROLLBAR:
                self.autoscroll_intro_for_LibraryWaterfall_pages(sb_index)
                self.AUTOSCROLL.timer.start()
        else:
            self.AUTOSCROLL.timer.start()

    def autoscroll_finish(self):
        if self.is_library_page_active() or self.is_waterfall_page_active():
            self.autoscroll_outro_for_LibraryWaterfall_pages()
        self.AUTOSCROLL.timer.stop()
        self.setCursor(Qt.ArrowCursor)

    def autoscroll_middleMousePressEvent(self, event):
        self.AUTOSCROLL.is_moved_while_middle_button_pressed = False
        if self.AUTOSCROLL.timer.isActive():
            self.AUTOSCROLL.desactivation_pass = True
            self.autoscroll_finish()
        else:
            self.AUTOSCROLL.desactivation_pass = False
            self.AUTOSCROLL.startpos = event.pos()

    def autoscroll_middleMouseMoveEvent(self):
        self.AUTOSCROLL.is_moved_while_middle_button_pressed = True

    def autoscroll_middleMouseReleaseEvent(self):
        if self.is_board_page_active():
            if not self.AUTOSCROLL.desactivation_pass:
                if not self.AUTOSCROLL.is_moved_while_middle_button_pressed:
                    self.autoscroll_start()
        elif self.is_library_page_active() or self.is_waterfall_page_active():
            if not self.AUTOSCROLL.desactivation_pass:
                self.autoscroll_start()
        self.AUTOSCROLL.is_moved_while_middle_button_pressed = False

    def autoscroll_draw(self, painter):
        if not self.AUTOSCROLL.timer.isActive():
            return
        if not self.AUTOSCROLL.inside_activation_zone:
            return

        painter.save()

        painter.setOpacity(0.7)
        gray = QColor(100, 100, 100)
        painter.setPen(gray)
        painter.setBrush(QBrush(Qt.white))
        el_rect = QRectF(0, 0, 9, 9)
        el_rect.moveCenter(self.AUTOSCROLL.startpos)
        painter.drawEllipse(el_rect)

        center = self.AUTOSCROLL.startpos
        if int(time.time()*4) % 2 == 0:
            offset = 12.0
        else:
            offset = 30.0

        if self.AUTOSCROLL.draw_vertical:
            self.autoscroll_draw_arrow(painter, center, QPointF(0, 1), offset)
            self.autoscroll_draw_arrow(painter, center, QPointF(0, -1), offset)

        if self.AUTOSCROLL.draw_horizontal:
            self.autoscroll_draw_arrow(painter, center, QPointF(1, 0), offset)
            self.autoscroll_draw_arrow(painter, center, QPointF(-1, 0), offset)

        painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(Qt.white, 2))
        el_rect = QRectF(0, 0, 49, 49)
        el_rect.moveCenter(self.AUTOSCROLL.startpos)
        painter.setBrush(QBrush(QColor(255, 255, 255, 100)))
        painter.drawEllipse(el_rect)

        painter.restore()

    def autoscroll_get_cursor(self):
        size_rect = QRect(0, 0, 50, 50)
        pixmap = QPixmap(size_rect.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        color = QColor(255, 255, 255, 200)
        center = size_rect.center()
        center_el = QRect(0, 0, 9, 9)
        center_el.moveCenter(center)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.gray)
        painter.drawEllipse(center_el)


        direction = self.AUTOSCROLL.direction_vector

        if not self.AUTOSCROLL.draw_vertical:
            direction.setY(0.0)
            direction.setX(math.copysign(1.0, direction.x()))
        if not self.AUTOSCROLL.draw_horizontal:
            direction.setX(0.0)
            direction.setY(math.copysign(1.0, direction.y()))

        self.autoscroll_draw_arrow(painter, center, direction, 12.0)

        painter.end()

        return QCursor(pixmap)

    def autoscroll_draw_arrow(self, painter, center, norm_direction, distance):
        color = QColor(255, 255, 255, 200)
        pen = QPen(color, 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        c1 = center + QPointF(norm_direction)*(0.0 + distance)
        a = c1 + QPointF(norm_direction.y(), -norm_direction.x())*6.5
        b = c1 + QPointF(-norm_direction.y(), norm_direction.x())*6.5
        c2 = c1 + QPointF(norm_direction)*6.0
        painter.drawPolyline(a, c2, b)

    def autoscroll_is_cursor_activated(self):
        return self.AUTOSCROLL.timer.isActive() and not self.AUTOSCROLL.inside_activation_zone

    def autoscroll_set_cursor(self):
        self.setCursor(self.autoscroll_get_cursor())

    def autoscroll_activation_zones_for_board_item_transform(self):
        outer_rect = self.rect()
        outer_rect.setBottom(self.globals.control_panel.frameGeometry().top())
        OFFSET = self.AUTOSCROLL.INNER_OUTER_OFFSET
        inner_rect = outer_rect.adjusted(OFFSET, OFFSET, -OFFSET, -OFFSET)
        return outer_rect, inner_rect

    def autoscroll_activate_board_item_transform_autoscroll(self):
        o, i = self.autoscroll_activation_zones_for_board_item_transform()
        cursor_pos = self.mapped_cursor_pos()
        on_border = o.contains(cursor_pos) and not i.contains(cursor_pos)
        over_control_panel = not o.contains(cursor_pos)
        if on_border or over_control_panel:
            if not self.AUTOSCROLL.board_item_transform:
                self.AUTOSCROLL.board_item_transform = True
                o, i = self.autoscroll_activation_zones_for_board_item_transform()
                self.AUTOSCROLL.startpos = o.center()
                self.autoscroll_start()
        else:
            self.autoscroll_desactivate_board_item_transform_autoscroll()

    def autoscroll_desactivate_board_item_transform_autoscroll(self):
        if self.AUTOSCROLL.board_item_transform:
            self.AUTOSCROLL.board_item_transform = False
            self.autoscroll_finish()

if __name__ == '__main__':

    # для запуска программы прямо из этого файла при разработке и отладке
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
