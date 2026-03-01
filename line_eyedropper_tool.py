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
from functools import partial

__import__('builtins').__dict__['_'] = __import__('gettext').gettext


class LineEyedropperToolMixin():


    def LET_init(self):
        """
            initializing slice pipette tool
        """
        self.let_tool_activated = False
        self.let_tool_input_points = []
        self.let_tool_line_points = []
        self.let_tool_pixels_colors = []

        self.let_input_point_dragging = False
        self.let_input_point_dragging_INDEX = -1

        self.let_input_point_dragging_START_CURSOR_POS = QPoint()
        self.let_input_point_dragging_START_INPUT_POS = QPoint()
        self.let_input_point_dragging_START_LINE = QLineF()

        self.let_input_point_rect_side_width = 51

        self.let_plots_pos = QPoint()

        self.let_show_red = True
        self.let_show_green = True
        self.let_show_blue = True

        self.let_show_hue = True
        self.let_show_saturation = True
        self.let_show_lightness = True

        self.let_plot1_rect = QRect()
        self.let_plot2_rect = QRect()

        self.draw_plp_index = -1

        self.let_pretty_plots = True

        self.let_hor_scale_factor = 1

        self.LET_hover_init()

    def LET_cycle_toggle_scale_factor_value(self):
        if self.let_tool_activated:
            values = [1, 2, 3, 4, 5]
            current_value = self.let_hor_scale_factor
            cycled_values = itertools.cycle(values)
            for value in cycled_values:
                if current_value == value:
                    break
            self.let_hor_scale_factor = next(cycled_values)
            self.show_center_label(_('Plot scale factor is {0}x').format(self.let_hor_scale_factor))
            self.update()

    def LET_update(self):
        if self.let_tool_activated:
            self._LET_update_plot()
            self.update()
        else:
            self.show_center_label(_('Slice Pipette tool is not activated!'), error=True)

    def LET_build_input_point_rect(self, pos):
        rsw = self.let_input_point_rect_side_width
        r = QRect(0, 0, rsw, rsw)
        r.moveCenter(pos)
        return r

    def LET_check_mouse_event_inside_input_point(self, event, set_mode=True):
        rsw = self.let_input_point_rect_side_width
        for n, pos in enumerate(self.let_tool_input_points):
            area = self.LET_build_input_point_rect(pos)
            if area.contains(event.pos()):
                if set_mode:
                    self.let_input_point_dragging_INDEX = n
                    self.let_input_point_dragging = True
                return True
        if set_mode:
            self.let_input_point_dragging_INDEX = -1
            self.let_input_point_dragging = False
        return False

    def LET_is_let_tool_activated(self):
        return self.let_tool_activated

    def LET_set_cursor(self):
        if self.let_tool_activated:
            if any((self.LET_hover_ends, self.LET_hover_line, self.LET_hover_plots)):
                self.setCursor(Qt.PointingHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

    def LET_find_point_perp_intersection(self, line, point):
        perpendic_line = QLineF(point, QPointF(point.x(), 0.0))
        perpendic_line.setAngle(90.0 + line.angle())
        result = line.intersects(perpendic_line)
        return result[1].toPoint()

    def LET_mousePressEvent(self, event):
        if self.let_input_point_dragging:
            self.let_input_point_dragging_START_CURSOR_POS = QPoint(event.pos())
            self.let_input_point_dragging_START_INPUT_POS = QPoint(self.let_tool_input_points[self.let_input_point_dragging_INDEX])
            self.let_input_point_dragging_START_LINE = QLineF(*self.let_tool_input_points)
            self.update()

    def LET_mouseMoveEvent(self, event):
        if self.let_input_point_dragging and self.let_input_point_dragging_INDEX > -1:
            _index = self.let_input_point_dragging_INDEX
            scp = self.let_input_point_dragging_START_CURSOR_POS
            sip = self.let_input_point_dragging_START_INPUT_POS

            cursor_pos = QPoint(event.pos())
            line_mapped_cursor_pos = self.LET_find_point_perp_intersection(self.let_input_point_dragging_START_LINE, cursor_pos)

            modifiers = QApplication.queryKeyboardModifiers()
            if modifiers == Qt.ControlModifier:
                cursor_pos = line_mapped_cursor_pos

            self.let_tool_input_points[_index] = sip + (cursor_pos - scp)
            self._LET_update_plot()
            self.update()

    def LET_mouseReleaseEvent(self, event):
        if self.let_input_point_dragging:
            self.let_input_point_dragging_INDEX = -1
            self.let_input_point_dragging = False

    def _LET_update_plot(self, new=False):
        p1 = self.let_tool_input_points[0]
        p2 = self.let_tool_input_points[1]
        self.let_tool_line_points = bresenhamsLineAlgorithm(p1.x(), p1.y(), p2.x(), p2.y())
        image = self.LET_generate_test_image()
        self.let_tool_pixels_colors = list()
        for pixel_coord in self.let_tool_line_points:
            color = image.pixelColor(pixel_coord)
            self.let_tool_pixels_colors.append(color)
        if new:
            p1, p2 = self.let_tool_input_points
            self.let_plots_pos = build_valid_rect(p1, p2).topRight() + QPoint(50, 50)

    def LET_set_plots_position(self):
        self.let_plots_pos = self.mapFromGlobal(QCursor().pos())

    def LET_copy_current_to_clipboard(self):
        if self.let_tool_activated:
            color = self.let_tool_pixels_colors[self.draw_plp_index]
            _hex = color.name()
            _r = color.red()
            _g = color.green()
            _b = color.blue()
            _rgb = f"rgb({_r}, {_g}, {_b})"
            color_repr = f"{_hex} {_rgb}"
            # self.colors_values_copied.append((color, color_repr))
            # color_reprs = [t[1] for t in self.colors_values_copied]
            # self.set_clipboard("\n".join(color_reprs))
            self.set_clipboard(color_repr)
            self.show_center_label(_('Color {0} has been copied to clipboard!').format(color_repr))
            self.update()
        else:
            self.show_center_label(_('Slice Pipette tool is not activated!'), error=True)

    def LET_toggle_tool_state(self):
        cursor_pos = self.mapFromGlobal(QCursor().pos())
        input_points_count = len(self.let_tool_input_points)
        msg = None
        desactivate = False
        if input_points_count < 2:
            self.let_tool_input_points.append(cursor_pos)
            self.let_tool_activated = True
            if len(self.let_tool_input_points) == 2:
                p1 = self.let_tool_input_points[0]
                p2 = self.let_tool_input_points[1]
                if QVector2D(p1 - p2).length() < 40:
                    desactivate = True
                    msg = _('Distance is too short!')
                else:
                    self._LET_update_plot(new=True)
        else:
            desactivate = True
        if desactivate:
            self.let_tool_input_points = []
            self.let_tool_activated = False
            self.let_tool_line_points = []
            self.let_tool_pixels_colors = []
            if msg is None:
                msg = _('Slice pipette disactivated!')
            self.show_center_label(msg, error=True)
        self.update()

    def LET_generate_test_image(self):
        rect = self.rect()
        event = QPaintEvent(rect)
        image = QImage(rect.size(), QImage.Format_ARGB32)
        painter = QPainter()
        painter.begin(image)
        let_tool_status = self.let_tool_activated
        self.let_tool_activated = False
        self._paintEvent(event, painter)
        self.let_tool_activated = let_tool_status
        painter.end()
        return image

    def _LET_draw_number(self, painter, pos, number):
        w = 20
        painter.save()
        plate_rect = QRectF(QPoint(0, 0), QSizeF(w, w))
        plate_rect.moveCenter(pos)
        painter.setBrush(QColor(220, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(plate_rect)
        painter.setPen(QPen(Qt.white))
        font = painter.font()
        font.setFamily("Consolas")
        font.setWeight(1600)
        painter.setFont(font)
        painter.drawText(plate_rect.adjusted(-20, -20, 20, 20), Qt.AlignCenter, str(number))
        painter.restore()

    def LET_is_context_menu_allowed(self):
        if self.let_tool_activated:
            cursor_pos = self.mapFromGlobal(QCursor().pos())
            if self.let_plot1_rect.contains(cursor_pos):
                return True
            if self.let_plot2_rect.contains(cursor_pos):
                return True
        return False

    def LET_context_menu(self, event):

        contextMenu = RoundedQMenu()
        contextMenu.setStyleSheet(self.context_menu_stylesheet)

        def toggle_boolean_var_generic(obj, attr_name):
            setattr(obj, attr_name, not getattr(obj, attr_name))
            self.update()

        checkboxes = [
            (_("show red"), self.let_show_red, partial(toggle_boolean_var_generic, self, "let_show_red")),
            (_("show green"), self.let_show_green, partial(toggle_boolean_var_generic, self, "let_show_green")),
            (_("show blue"), self.let_show_blue, partial(toggle_boolean_var_generic, self, "let_show_blue")),

            (_("show hue"), self.let_show_hue, partial(toggle_boolean_var_generic, self, "let_show_hue")),
            (_("show saturation"), self.let_show_saturation, partial(toggle_boolean_var_generic, self, "let_show_saturation")),
            (_("show lightness"), self.let_show_lightness, partial(toggle_boolean_var_generic, self, "let_show_lightness")),

            (_("prettify plots"), self.let_pretty_plots, partial(toggle_boolean_var_generic, self, "let_pretty_plots")),
        ]

        for title, value, callback in checkboxes:
            wa = QWidgetAction(contextMenu)
            chb = QCheckBox(title)
            chb.setStyleSheet(self.toggle_checkbox_stylesheet + self.context_menu_stylesheet)
            chb.setChecked(value)
            chb.stateChanged.connect(callback)
            wa.setDefaultWidget(chb)
            contextMenu.addAction(wa)

        action = contextMenu.exec_(self.mapToGlobal(event.pos()))

    def LET_hover_init(self):
        self.LET_hover_ends = False
        self.LET_hover_line = False
        self.LET_hover_plots = False

    def LET_draw_info(self, painter):
        if self.let_tool_activated and len(self.let_tool_input_points) > 0:
            self.LET_hover_init()

            cursor_pos = self.mapFromGlobal(QCursor().pos())
            if len(self.let_tool_input_points) < 2:
                p2 = cursor_pos
                p1 = self.let_tool_input_points[0]
            else:
                p1, p2 = self.let_tool_input_points

            PLOTS_POS = self.let_plots_pos

            WIDTH = len(self.let_tool_pixels_colors)*self.let_hor_scale_factor-1
            HEIGHT = 256
            plot1_pos = QPoint(PLOTS_POS)
            plot2_pos = PLOTS_POS + QPoint(0, HEIGHT+5)

            plp_index = -1
            plp = None

            backplate_rect1 = QRect(0, 0, WIDTH, HEIGHT)
            backplate_rect1.moveBottomLeft(plot1_pos)
            backplate_rect2 = QRect(0, 0, WIDTH, HEIGHT)
            backplate_rect2.moveBottomLeft(plot2_pos)

            self.let_plot1_rect = backplate_rect1
            self.let_plot2_rect = backplate_rect2

            if backplate_rect1.contains(cursor_pos):
                delta = cursor_pos - backplate_rect1.bottomLeft()
                plp_index = int(delta.x()/self.let_hor_scale_factor)
                self.LET_hover_plots = True
            elif backplate_rect2.contains(cursor_pos):
                delta = cursor_pos - backplate_rect2.bottomLeft()
                plp_index = int(delta.x()/self.let_hor_scale_factor)
                self.LET_hover_plots = True

            painter.save()

            # drawing proximity circle
            def calc_distance_to_cursor(x):
                return QVector2D(x-cursor_pos).length()
            def calc_distance_to_cursor_tuple(x):
                return calc_distance_to_cursor(x[1])

            painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.setBrush(Qt.NoBrush)

            painter.save()
            painter.setCompositionMode(QPainter.RasterOp_SourceXorDestination)

            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, False)


            if self.let_tool_line_points:
                sp_case = False
                if plp_index == -1:
                    line_points = sorted(enumerate(self.let_tool_line_points), key=calc_distance_to_cursor_tuple)
                    plp_index, plp = line_points[0]
                    if calc_distance_to_cursor(plp) < 30.0:
                        sp_case = True
                    else:
                        plp_index = -1
                else:
                    plp = self.let_tool_line_points[plp_index]
                    sp_case = True
                if plp is not None and sp_case:
                    self.LET_hover_line = True
                    r = self.LET_build_input_point_rect(plp)
                    r.adjust(15, 15, -15, -15)
                    painter.drawEllipse(r)

            self.draw_plp_index = plp_index

            # drawing pipette line
            painter.drawLine(p1, p2)


            # draw line ends hovers
            for i_pos in self.let_tool_input_points:
                r = self.LET_build_input_point_rect(i_pos)
                if r.contains(self.mapFromGlobal(QCursor().pos())):
                    painter.drawEllipse(r)
                    self.LET_hover_ends = True
                    break
            painter.restore()

            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

            line = QLineF(p1, p2)
            nv = line.normalVector()
            offset = QVector2D(nv.p1() - nv.p2())
            offset.normalize()
            offset *= 50.0
            offset = QPointF(offset.x(), offset.y())
            self._LET_draw_number(painter, p1 + offset, 1)
            self._LET_draw_number(painter, p2 + offset, 2)

            def draw_plot_line(pos, hue_level=False):
                if plp_index > -1:
                    _x = pos + QPoint(plp_index*self.let_hor_scale_factor, 0)
                    painter.setPen(QColor(200, 200, 200))
                    painter.drawLine(_x, _x+QPoint(0, -255))
                    if hue_level:
                        pc = self.let_tool_pixels_colors[plp_index]
                        hue = pc.hslHueF()
                        hue = max(0.0, hue) # hue будет -1.0 для чисто белого и чёрного цветов
                        value = int(hue*255)
                        hue_offset = QPoint(0, -value)
                        painter.drawLine(pos+hue_offset, pos+hue_offset+QPoint(len(self.let_tool_pixels_colors)*self.let_hor_scale_factor, 0))


            # draw plots
            if len(self.let_tool_input_points) > 1:

                # снимаем модификаторы, чтобы линия шириной 1px не размывалась на несколько пикселей
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, False)

                painter.fillRect(backplate_rect1, Qt.white)
                draw_plot_line(plot1_pos)

                # RGB plot
                prev_pc_pos = [None, None, None]
                for n, pc in enumerate(self.let_tool_pixels_colors):

                    for color_num, color in enumerate([Qt.red, Qt.green, Qt.blue]):
                        if color == Qt.red:
                            if not self.let_show_red:
                                continue
                            value = pc.red()
                        elif color == Qt.green:
                            if not self.let_show_green:
                                continue
                            value = pc.green()
                        elif color == Qt.blue:
                            if not self.let_show_blue:
                                continue
                            value = pc.blue()
                        plot_pos = QPoint(plot1_pos.x() + n*self.let_hor_scale_factor, plot1_pos.y() - value)
                        painter.setPen(QPen(color, 1))

                        # draw plot point
                        painter.drawPoint(plot_pos)

                        if self.let_pretty_plots:
                            # draw lines between plot points
                            _pos = prev_pc_pos[color_num]
                            if _pos is not None:
                                if abs(_pos.y() - plot_pos.y()) > 1 or abs(_pos.x() - plot_pos.x()) > 1:
                                    painter.drawLine(_pos, plot_pos)
                            prev_pc_pos[color_num] = QPoint(plot_pos)

                painter.fillRect(backplate_rect2, Qt.white)
                draw_plot_line(plot2_pos, hue_level=True)

                if plp_index > -1:
                    color = self.let_tool_pixels_colors[plp_index]
                    text = f'RGB: {color.redF():.05}  {color.greenF():.05}  {color.blueF():.05}'
                    text += f'\nHSL: {color.hslHueF():.05}  {color.hslSaturationF():.05}  {color.lightnessF():.05}'
                    rect = painter.boundingRect(QRect(), Qt.AlignLeft, text)

                    rect.moveTopLeft(plot2_pos + QPoint(plp_index*self.let_hor_scale_factor, 0) + QPoint(0, 10))

                    painter.setPen(Qt.black)

                    painter.fillRect(rect.adjusted(-5, -5, 5,5), Qt.white)
                    painter.drawText(rect, Qt.AlignLeft, text)

                # HSL plot
                prev_pc_pos = [None, None, None]
                for n, pc in enumerate(self.let_tool_pixels_colors):

                    for component in [0, 1, 2]:
                        hue = pc.hslHueF()
                        saturation = pc.hslSaturationF()
                        lightness = pc.lightnessF()
                        if component == 0:
                            if not self.let_show_hue:
                                continue
                            value = max(0.0, hue)  # hue будет -1.0 для чисто белого и чёрного цветов
                        elif component == 1:
                            if not self.let_show_saturation:
                                continue
                            value = saturation
                        elif component == 2:
                            if not self.let_show_lightness:
                                continue
                            value = lightness

                        value = int(value*255)
                        plot_pos = QPoint(plot2_pos.x() + n*self.let_hor_scale_factor, plot2_pos.y() - value)
                        if component == 0:
                            # color = pc
                            color = Qt.black
                        elif component == 1:
                            color = Qt.green
                        elif component == 2:
                            color = Qt.red
                        painter.setPen(QPen(color, 1))

                        # draw plot point
                        painter.drawPoint(plot_pos)

                        if self.let_pretty_plots:
                            # draw lines between plot points
                            _pos = prev_pc_pos[component]
                            if _pos is not None:
                                if abs(_pos.y() - plot_pos.y()) > 1 or abs(_pos.x() - plot_pos.x()) > 1:
                                    painter.drawLine(_pos, plot_pos)
                            prev_pc_pos[component] = QPoint(plot_pos)

                tech_color = QColor()

                # rainbow for HSL plot
                for n in range(HEIGHT):
                    tech_color.setHslF(n/255, 1.0, 0.5)
                    painter.setPen(QPen(tech_color, 1))
                    m = plot2_pos + QPoint(-2, -n)
                    a = m
                    b = m + QPoint(-20, 0)
                    painter.drawLine(a, b)
                # lightness version of hue rainbow
                plot2_pos += QPoint(-20, 0)
                for n in range(HEIGHT):
                    tech_color.setHslF(n/256, 1.0, 0.5)
                    l = tech_color.lightness()
                    R = tech_color.redF()
                    G = tech_color.greenF()
                    B = tech_color.blueF()
                    luminance = min(1.0, max(0.0, 0.2126*R + 0.7152*G + 0.0722*B))
                    luminance *= 255
                    luminance = int(luminance)
                    painter.setPen(QPen(QColor(luminance, luminance, luminance), 1))
                    m = plot2_pos + QPoint(-2, -n)
                    a = m
                    b = m + QPoint(-20, 0)
                    painter.drawLine(a, b)


                # возвращаем модификаторы обратно
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

            painter.restore()

# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
