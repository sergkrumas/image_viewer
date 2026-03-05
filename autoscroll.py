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

        AUTOSCROLL.desactivation_pass = False

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
            print('make')
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
        cursor_offset = self.mapped_cursor_pos() - self.AUTOSCROLL.startpos
        diff_l = QVector2D(cursor_offset).length()
        self.AUTOSCROLL.inside_activation_zone = diff_l < OUTER_ZONE_ACTIVATION_RADIUS
        if not self.AUTOSCROLL.inside_activation_zone:
            # fixing velocity, because it should be 0.0 at the radius border, not greater than 0.0
            diff_l = max(0.0, diff_l - OUTER_ZONE_ACTIVATION_RADIUS)
            vec = QVector2D(cursor_offset).normalized()*diff_l
            velocity_vec = vec.toPointF()
            speed_factor = self.autoscroll_get_speed_factor()
            if self.is_board_page_active():
                self.canvas_origin -= velocity_vec*speed_factor/25.0
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
        if self.AUTOSCROLL.timer.isActive():
            if self.AUTOSCROLL.inside_activation_zone:
                painter.save()

                painter.setOpacity(0.7)
                gray = QColor(100, 100, 100)
                painter.setPen(gray)
                painter.setBrush(QBrush(Qt.white))
                el_rect = QRectF(0, 0, 6, 6)
                el_rect.moveCenter(self.AUTOSCROLL.startpos)
                painter.drawEllipse(el_rect)

                o = self.AUTOSCROLL.startpos
                if int(time.time()*4) % 2 == 0:
                    f = 18
                else:
                    f = 32

                points = [
                    QPointF(0, f),
                    QPointF(-7, f-10),
                    QPointF(7, f-10),
                ]

                if self.AUTOSCROLL.draw_vertical:
                    painter.drawPolygon([p + o for p in points])
                    painter.drawPolygon([QPointF(p.x(), -p.y()) + o for p in points])
                if self.AUTOSCROLL.draw_horizontal:
                    painter.drawPolygon([QPointF(p.y(), p.x()) + o for p in points])
                    painter.drawPolygon([QPointF(-p.y(), p.x()) + o for p in points])

                painter.setBrush(Qt.NoBrush)

                painter.setPen(QPen(gray, 2))
                el_rect = QRectF(0, 0, 39, 39)
                el_rect.moveCenter(self.AUTOSCROLL.startpos)
                painter.drawEllipse(el_rect)

                painter.setPen(QPen(Qt.white, 1))
                el_rect = QRectF(0, 0, 38, 38)
                el_rect.moveCenter(self.AUTOSCROLL.startpos)
                painter.drawEllipse(el_rect)

                painter.restore()


if __name__ == '__main__':

    # для запуска программы прямо из этого файла при разработке и отладке
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
