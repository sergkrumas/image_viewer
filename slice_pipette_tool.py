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


class SlicePipetteToolMixin():


    def SPT_init(self):
        """
            initializing slice pipette tool
        """
        self.spt_tool_activated = False
        self.spt_tool_input_points = []
        self.spt_tool_line_points = []
        self.spt_tool_pixels_colors = []

        self.spt_input_point_dragging = False
        self.spt_input_point_dragging_INDEX = -1

        self.spt_input_point_dragging_START_CURSOR_POS = QPoint()
        self.spt_input_point_dragging_START_INPUT_POS = QPoint()

        self.spt_input_point_rect_side_width = 50

    def SPT_update(self):
        self._SPT_update_plot()
        self.update()

    def SPT_build_input_point_rect(self, pos):
        rsw = self.spt_input_point_rect_side_width
        r = QRect(0, 0, rsw, rsw)
        r.moveCenter(pos)
        return r

    def SPT_check_mouse_event_inside_input_point(self, event, set_mode=True):
        rsw = self.spt_input_point_rect_side_width
        for n, pos in enumerate(self.spt_tool_input_points):
            area = self.SPT_build_input_point_rect(pos)
            if area.contains(event.pos()):
                if set_mode:
                    self.spt_input_point_dragging_INDEX = n
                    self.spt_input_point_dragging = True
                return True
        if set_mode:
            self.spt_input_point_dragging_INDEX = -1
            self.spt_input_point_dragging = False
        return False

    def SPT_mousePressEvent(self, event):
        if self.spt_input_point_dragging:
            self.spt_input_point_dragging_START_CURSOR_POS = QPoint(event.pos())
            self.spt_input_point_dragging_START_INPUT_POS = QPoint(self.spt_tool_input_points[self.spt_input_point_dragging_INDEX])
            self.update()

    def SPT_mouseMoveEvent(self, event):
        if self.spt_input_point_dragging and self.spt_input_point_dragging_INDEX > -1:
            _index = self.spt_input_point_dragging_INDEX
            scp = self.spt_input_point_dragging_START_CURSOR_POS
            sip = self.spt_input_point_dragging_START_INPUT_POS
            self.spt_tool_input_points[_index] = sip + (QPoint(event.pos()) - scp)
            self._SPT_update_plot()
            self.update()

    def SPT_mouseReleaseEvent(self, event):
        if self.spt_input_point_dragging:
            self.spt_input_point_dragging_INDEX = -1
            self.spt_input_point_dragging = False

    def _SPT_update_plot(self):
        p1 = self.spt_tool_input_points[0]
        p2 = self.spt_tool_input_points[1]
        self.spt_tool_line_points = bresenhamsLineAlgorithm(p1.x(), p1.y(), p2.x(), p2.y())
        image = self.SPT_generate_test_image()
        self.spt_tool_pixels_colors = list()
        for pixel_coord in self.spt_tool_line_points:
            color = image.pixelColor(pixel_coord)
            self.spt_tool_pixels_colors.append(color)

    def SPT_toggle_tool_state(self):
        cursor_pos = self.mapFromGlobal(QCursor().pos())
        input_points_count = len(self.spt_tool_input_points)
        msg = None
        desactivate = False
        if input_points_count < 2:
            self.spt_tool_input_points.append(cursor_pos)
            self.spt_tool_activated = True
            if len(self.spt_tool_input_points) == 2:
                p1 = self.spt_tool_input_points[0]
                p2 = self.spt_tool_input_points[1]
                if QVector2D(p1 - p2).length() < 40:
                    desactivate = True
                    msg = 'Distance is too short!'
                else:
                    self._SPT_update_plot()
        else:
            desactivate = True
        if desactivate:
            self.spt_tool_input_points = []
            self.spt_tool_activated = False
            self.spt_tool_line_points = []
            self.spt_tool_pixels_colors = []
            if msg is None:
                msg = 'Slice pipette disactivated!'
            self.show_center_label(msg, error=True)
        self.update()

    def SPT_generate_test_image(self):
        rect = self.rect()
        event = QPaintEvent(rect)
        image = QImage(rect.size(), QImage.Format_ARGB32)
        painter = QPainter()
        painter.begin(image)
        spt_tool_status = self.spt_tool_activated
        self.spt_tool_activated = False
        self._paintEvent(event, painter)
        self.spt_tool_activated = spt_tool_status
        painter.end()
        return image

    def _SPT_draw_number(self, painter, pos, number):
        w = 20
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

    def SPT_draw_info(self, painter):
        if self.spt_tool_activated and len(self.spt_tool_input_points) > 0:
            if len(self.spt_tool_input_points) < 2:
                p2 = QCursor().pos()
                p1 = self.spt_tool_input_points[0]
            else:
                p1, p2 = self.spt_tool_input_points
            painter.save()
            painter.drawLine(p1, p2)

            line = QLineF(p1, p2)
            nv = line.normalVector()
            offset = QVector2D(nv.p1() - nv.p2())
            offset.normalize()
            offset *= 50.0
            offset = QPointF(offset.x(), offset.y())
            self._SPT_draw_number(painter, p1 + offset, 1)
            self._SPT_draw_number(painter, p2 + offset, 2)
            plots_pos = build_valid_rect(p1, p2).topRight() + QPoint(50, 50)
            pixels_count = len(self.spt_tool_pixels_colors)
            width = pixels_count
            height = 255

            for i_pos in self.spt_tool_input_points:
                r = self.SPT_build_input_point_rect(i_pos)
                if r.contains(self.mapFromGlobal(QCursor().pos())):
                    painter.save()
                    painter.setPen(QPen(Qt.black, 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(r)
                    painter.restore()
                    break

            if len(self.spt_tool_input_points) > 1:
                backplate_rect = QRect(0, 0, width, height)
                backplate_rect.moveBottomLeft(plots_pos)
                painter.fillRect(backplate_rect, Qt.white)

                for n, pc in enumerate(self.spt_tool_pixels_colors):

                    for color in [Qt.red, Qt.green, Qt.blue]:
                        if color == Qt.red:
                            value = pc.red()
                        elif color == Qt.green:
                            value = pc.green()
                        elif color == Qt.blue:
                            value = pc.blue()
                        plot_pos = QPoint(plots_pos.x() + n, plots_pos.y() - value)
                        painter.setPen(QPen(color, 1))
                        painter.drawPoint(plot_pos)

                pos2 = plots_pos + QPoint(0, height+5)
                backplate_rect = QRect(0, 0, width, height)
                backplate_rect.moveBottomLeft(pos2)
                painter.fillRect(backplate_rect, Qt.white)

                for n, pc in enumerate(self.spt_tool_pixels_colors):

                    for component in [0, 1, 2]:
                        hue = pc.hslHueF()
                        saturation = pc.hslSaturationF()
                        lightness = pc.lightnessF()
                        if component == 0:
                            value = hue
                        elif component == 1:
                            value = saturation
                        elif component == 2:
                            value = lightness

                        value = int(value*255)
                        plot_pos = QPoint(pos2.x() + n, pos2.y() - value)
                        if component == 0:
                            color = pc
                            color = Qt.black
                        elif component == 1:
                            color = Qt.green
                        elif component == 2:
                            color = Qt.red
                        painter.setPen(QPen(color, 1))
                        painter.drawPoint(plot_pos)

                tech_color = QColor()
                for n in range(height):
                    tech_color.setHslF(n/255, 1.0, 0.5)
                    painter.setPen(QPen(tech_color, 1))
                    m = pos2 + QPoint(0, -n)
                    a = m
                    b = m + QPoint(-20, 0)
                    painter.drawLine(a, b)

            painter.restore()

# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
