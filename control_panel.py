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
import help_text

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

class ControlPanelButton(QPushButton):
    def __init__(self, id, *args, callback=None):
        super().__init__(*args)
        self.id = id
        # для того, чтобы подсказка изменялась в лейбле панели управления
        self.setMouseTracking(True)
        if callback:
            self.clicked.connect(callback)

    def set_font(self, painter, large=True):
        font = painter.font()
        if large:
            offset = 15
        else:
            offset = 30
        font.setPixelSize(self.rect().height()-offset)
        font.setWeight(1900)
        painter.setFont(font)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.set_font(painter, large=False)

        orange = QColor(0xFF, 0xA0, 0x00)

        if self.id != "space":
            path = QPainterPath()
            path.addRoundedRect(QRectF(self.rect()), 5, 5)

            if self.underMouse():
                if self.id == "play":
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(orange)
                else:
                    painter.setBrush(QBrush(Qt.black))
                    painter.setPen(Qt.NoPen)
                painter.setOpacity(0.8)
                painter.drawPath(path)
                painter.setOpacity(1.0)
                painter.setPen(Qt.white)
                painter.setBrush(QBrush(Qt.white))
            else:
                painter.setBrush(QBrush(Qt.black))
                painter.setPen(Qt.NoPen)
                painter.setOpacity(0.5)
                painter.drawPath(path)
                painter.setOpacity(1.0)
                painter.setPen(Qt.white)
                painter.setBrush(QBrush(Qt.white))

                color = QColor(180, 180, 180)
                painter.setPen(QPen(color))
                painter.setBrush(QBrush(color))

        # buttons draw switch
        if self.id == "zoom_in":

            rect = self.rect().adjusted(10, 10, -10, -10)
            pen = QPen(painter.brush().color(), 4)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
            painter.drawLine(
                rect.topLeft()/2 + rect.topRight()/2 + QPoint(0, 8),
                rect.bottomLeft()/2 + rect.bottomRight()/2 + QPoint(0, -8)
            )
            painter.drawLine(
                rect.topLeft()/2 + rect.bottomLeft()/2 + QPoint(8, 0),
                rect.topRight()/2 + rect.bottomRight()/2 + QPoint(-8, 0)
            )

        elif self.id == "zoom_out":

            rect = self.rect().adjusted(10, 10, -10, -10)
            pen = QPen(painter.brush().color(), 4)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect)
            # painter.drawLine(
            #     rect.topLeft()/2 + rect.topRight()/2 + QPoint(0, 8),
            #     rect.bottomLeft()/2 + rect.bottomRight()/2 + QPoint(0, -8)
            # )
            painter.drawLine(
                rect.topLeft()/2 + rect.bottomLeft()/2 + QPoint(8, 0),
                rect.topRight()/2 + rect.bottomRight()/2 + QPoint(-8, 0)
            )

        elif self.id == "orig_scale":

            r = painter.drawText(self.rect(), Qt.AlignCenter, "1:1")

        elif self.id == "help":

            self.set_font(painter)
            r = painter.drawText(self.rect(), Qt.AlignCenter, "?")

        elif self.id == "previous":

            w = self.rect().width()
            points = [
                QPointF(w/2+3, w/2) + QPointF(0, -10),
                QPointF(w/2+3, w/2) + QPointF(-10, 0),
                QPointF(w/2+3, w/2) + QPointF(0, 10),
            ]
            pen = painter.pen()
            pen.setWidth(6)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(points[0].x(), points[0].y())
            path.lineTo(points[1].x(), points[1].y())
            path.lineTo(points[2].x(), points[2].y())
            painter.drawPath(path)

        elif self.id == "play":

            w = self.rect().width()
            points = [
                QPointF(15, 10),
                QPointF(40, w/2),
                QPointF(15, 40),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            if self.underMouse():
                painter.setBrush(Qt.white)
                painter.setOpacity(1.0)
            else:
                painter.setBrush(Qt.white)
                painter.setOpacity(0.8)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

        elif self.id == "next":

            w = self.rect().width()
            points = [
                QPointF(w/2-3, w/2) + QPointF(0, -10),
                QPointF(w/2-3, w/2) + QPointF(10, 0),
                QPointF(w/2-3, w/2) + QPointF(0, 10),
            ]
            pen = painter.pen()
            pen.setWidth(6)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            path = QPainterPath()
            path.moveTo(points[0].x(), points[0].y())
            path.lineTo(points[1].x(), points[1].y())
            path.lineTo(points[2].x(), points[2].y())
            painter.drawPath(path)

        elif self.id == "rotate_clockwise":

            path = QPainterPath()
            painter.setClipping(True)
            rg1 = QRegion(self.rect())
            rg2 = QRegion(QRect(25, 25, 50, 50))
            rg3=rg1.subtracted(rg2)
            painter.setClipRegion(rg3)
            path.addEllipse(QRectF(self.rect().adjusted(10, 10, -10, -10)))
            path.addEllipse(QRectF(self.rect().adjusted(15, 15, -15, -15)))
            painter.setPen(Qt.NoPen)
            # painter.setBrush(Qt.white)
            painter.drawPath(path)
            painter.setClipping(False)
            w = self.rect().width()
            points = [
                QPointF(44, w/2),
                QPointF(31, w/2),
                QPointF(37.5, w/2+8),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            # painter.setBrush(Qt.white)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

        elif self.id == "rotate_counterclockwise":

            path = QPainterPath()
            painter.setClipping(True)
            rg1 = QRegion(self.rect())
            rg2 = QRegion(QRect(0, 25, 25, 50))
            rg3=rg1.subtracted(rg2)
            painter.setClipRegion(rg3)
            path.addEllipse(QRectF(self.rect().adjusted(10, 10, -10, -10)))
            path.addEllipse(QRectF(self.rect().adjusted(15, 15, -15, -15)))
            painter.setPen(Qt.NoPen)
            # painter.setBrush(Qt.white)
            painter.drawPath(path)
            painter.setClipping(False)
            w = self.rect().width()
            points = [
                QPointF(50, 50) - QPointF(44, w/2),
                QPointF(50, 50) - QPointF(31, w/2),
                QPointF(50, 50) - QPointF(37.5, w/2-8),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            # painter.setBrush(Qt.white)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

        elif self.id == "update_list":

            pen = painter.pen()
            pen.setWidth(5)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            rectangle = QRectF(self.rect().adjusted(13, 13, -13, -13))
            startAngle = 60 * 16
            spanAngle = (180-60) * 16
            painter.drawArc(rectangle, startAngle, spanAngle)

            startAngle = (180+60) * 16
            spanAngle = (360-180-60) * 16
            painter.drawArc(rectangle, startAngle, spanAngle)

            w = self.rect().width()
            points = [
                QPointF(50, 50) - QPointF(44, w/2),
                QPointF(50, 50) - QPointF(31, w/2),
                QPointF(50, 50) - QPointF(37.5, w/2-8),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

            points = [
                QPointF(44, w/2),
                QPointF(31, w/2),
                QPointF(37.5, w/2-8),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

        elif self.id.startswith("favorite"):

            start_angle = -0.34
            w = self.rect().width()-10
            points = []
            for i in range(5):
                points.append(QPointF(
                    5+w*(0.5 + 0.5 * math.cos(start_angle + 0.8 * i * 3.14)),
                    5+w*(0.5 + 0.5 * math.sin(start_angle + 0.8 * i * 3.14))
                ))
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            if self.id.endswith("_added"):
                color = orange
            else:
                color = Qt.white
            if self.underMouse():
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(.8)
            painter.setBrush(color)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)
            painter.setOpacity(1.0)

        elif self.id == "settings":

            w = self.rect().width()
            painter.setClipping(True)
            # draw base
            path = QPainterPath()
            value = 20
            r = self.rect().adjusted(value, value, -value, -value)
            path.addRect(QRectF(self.rect()))
            path.addEllipse(QRectF(r))
            painter.setClipPath(path)
            value = 10
            painter.drawEllipse(self.rect().adjusted(value, value, -value, -value))
            # draw tips
            path = QPainterPath()
            value = 5
            r2 = self.rect().adjusted(value, value, -value, -value)
            path.addEllipse(QRectF(r2))
            value = 15
            r = self.rect().adjusted(value, value, -value, -value)
            path.addEllipse(QRectF(r))
            painter.setClipPath(path)
            painter.setPen(QPen(painter.brush().color(), 8))
            painter.drawLine(QPoint(int(w/2), 0), QPoint(int(w/2), w))
            painter.drawLine(QPoint(0, int(w/2)), QPoint(w, int(w/2)))
            painter.drawLine(QPoint(0, 0), QPoint(w, w))
            painter.drawLine(QPoint(0, w), QPoint(w, 0))
            painter.setClipping(False)

        elif self.id == "space":
            pass

        painter.end()

class ControlPanel(QWidget, UtilsMixin):

    def zoom_in(self):
        MW = self.globals.main_window
        MW.do_scale_image(0.05, cursor_pivot=False)
        MW.show_center_label(MW.label_type.SCALE)

    def zoom_out(self):
        MW = self.globals.main_window
        MW.do_scale_image(-0.05, cursor_pivot=False)
        MW.show_center_label(MW.label_type.SCALE)

    def set_original_scale(self):
        MW = self.globals.main_window
        MW.set_original_scale()
        MW.show_center_label(MW.label_type.SCALE)

    def show_settings_window(self):
        MW = self.globals.main_window
        MW.open_settings_window()

    def toggle_help(self):
        MW = self.globals.main_window
        MW.toggle_infopanel()
        MW.update()

    def quick_show(self):
        self.quick_show_flag = True

    def show_previous(self):
        self.LibraryData().show_previous_image()

    def play(self):
        self.globals.main_window.start_slideshow_for_current_folder()

    def show_next(self):
        self.LibraryData().show_next_image()

    def correct_content_position_if_needed(self):
        MW = self.globals.main_window
        # для картинок сильно вытянутых по горизонтали/вертикали
        if MW.animated:
            return
        class ContentCornerPoint():
            def __init__(self, point):
                super().__init__()
                self.point = point
                diff = point - MW.rect().center()
                self.distance = QVector2D(diff).length()
            def __lt__(self, other):
                return self.distance > other.distance
        window_rect = QRectF(MW.rect())
        content_rect = MW.get_image_viewport_rect(debug=False)
        i_rect = window_rect.intersected(content_rect)
        if i_rect.width() == 0 or i_rect.height() == 0:
            cp1 = ContentCornerPoint(content_rect.topLeft())
            cp2 = ContentCornerPoint(content_rect.topRight())
            cp3 = ContentCornerPoint(content_rect.bottomLeft())
            cp4 = ContentCornerPoint(content_rect.bottomRight())
            cp = min([cp1, cp2, cp3, cp4])
            center = MW.rect().center()
            MW.image_center_position -= (cp.point - center)

    def rotate_clockwise(self):
        MW = self.globals.main_window
        angles = [0, 90, 180, 270, 0]
        new_index = angles.index(MW.image_rotation) + 1
        MW.image_rotation = angles[new_index]
        imd = MW.image_data
        if imd and not MW.copied_from_clipboard:
            imd.image_rotation = MW.image_rotation
        MW.get_rotated_pixmap(force_update=True)
        self.correct_content_position_if_needed()
        self.LibraryData.write_rotations_for_folder()
        MW.update()

    def rotate_counterclockwise(self):
        MW = self.globals.main_window
        angles = [0, 270, 180, 90, 0]
        new_index = angles.index(MW.image_rotation) + 1
        MW.image_rotation = angles[new_index]
        imd = MW.image_data
        if imd and not MW.copied_from_clipboard:
            imd.image_rotation = MW.image_rotation
        MW.get_rotated_pixmap(force_update=True)
        self.correct_content_position_if_needed()
        self.LibraryData.write_rotations_for_folder()
        MW.update()

    def manage_favorite_list(self):
        MW = self.globals.main_window
        if self.globals.lite_mode:
            MW.show_center_label(_("This feature is not working in lite mode\nRerun programm in standart mode via context menu command"), error=True)
            return
        status = self.LibraryData().manage_favorite_list()
        if status == "added":
            self.favorite_btn.setText("-")
            self.favorite_btn.id = "favorite_added"
            MW.show_center_label(_("Added to favorites"))
        elif status == "removed":
            self.favorite_btn.setText("+")
            self.favorite_btn.id = "favorite"
            MW.show_center_label(_("Removed from favorites"))
        elif status == "rejected":
            self.favorite_btn.setText("+")
            self.favorite_btn.id = "favorite"
            MW.show_center_label(_("Files with such extensions are not allowed to be added to favorites!"), error=True)
        MW.update()

    def show_in_folder(self):
        MW = self.globals.main_window
        if MW.image_filepath:
            show_in_folder_windows(MW.image_filepath)
            MW.update()

    def update_folder_list(self):
        MW = self.globals.main_window
        cf = self.LibraryData().current_folder()
        if cf.virtual:
            MW.show_center_label(_("Virtual folders are not allowed to be updated!"), error=True)
            return
        self.LibraryData().update_current_folder()
        MW.update_thumbnails_row_relative_offset(cf, only_set=True)
        MW.show_center_label(_("Updated"))
        self.update()

    def board_set_default_scale(self):
        MW = self.globals.main_window
        MW.set_default_boardviewport_scale(keep_position=True, center_as_pivot=True)

    def board_zoom_out(self):
        MW = self.globals.main_window
        MW.do_scale_board(-1.0, False, False, True, pivot=MW.get_center_position())

    def board_zoom_in(self):
        MW = self.globals.main_window
        MW.do_scale_board(1.0, False, False, True, pivot=MW.get_center_position())

    def __init__(self, *args, requested_page=None, **kwargs):
        super().__init__(*args, **kwargs)

        _main_layout = QVBoxLayout()
        _buttons_layout = QHBoxLayout()
        _label_layout = QHBoxLayout()


        self.space_btn_generator = lambda: ControlPanelButton("space")

        self.control_panel_label = QLabel(" ", self) #"picture_filename.extension (XxW)"
        self.control_panel_label.setMouseTracking(True)
        self.control_panel_label.setStyleSheet("font-weight: bold; color: white; font-size: 12pt; padding: 5px;")
        self.control_panel_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)


        _label_layout.addWidget(self.control_panel_label)
        effect = QGraphicsDropShadowEffect()
        effect.setColor(Qt.black)
        effect.setBlurRadius(5)
        effect.setXOffset(0)
        effect.setYOffset(0)
        self.control_panel_label.setGraphicsEffect(effect)

        main_window = self.parent()

        if requested_page is None or requested_page == main_window.pages.VIEWER_PAGE:
            self.favorite_btn = ControlPanelButton("favorite", _("Favorites"),
                                                        callback=self.manage_favorite_list)
            self.all_buttons = [
                ControlPanelButton("orig_scale", _("1:1"), callback=self.set_original_scale),
                ControlPanelButton("zoom_out", _("Image zoom out"), callback=self.zoom_out),
                ControlPanelButton("zoom_in", _("Image zoom in"), callback=self.zoom_in),

                ControlPanelButton("help", _("Help"), callback=self.toggle_help),
                ControlPanelButton("settings", _("Settings"), callback=self.show_settings_window),

                ControlPanelButton("previous", _("Show previous"), callback=self.show_previous),
                ControlPanelButton("play", _("Slideshow"), callback=self.play),
                ControlPanelButton("next", _("Show next"), callback=self.show_next),

                ControlPanelButton("rotate_counterclockwise", _("Rotate counterclockwise"),
                                                    callback=self.rotate_counterclockwise),
                ControlPanelButton("rotate_clockwise", _("Rotate clockwise"),
                                                    callback=self.rotate_clockwise),
                self.favorite_btn,
                ControlPanelButton("update_list", _("Update files list"), callback=self.update_folder_list),
                self.space_btn_generator(),
            ]
        elif requested_page == main_window.pages.BOARD_PAGE:
            self.all_buttons = [
                ControlPanelButton("settings", _("Settings"), callback=self.show_settings_window),
                ControlPanelButton("help", _("Help"), callback=self.toggle_help),

                self.space_btn_generator(),

                ControlPanelButton("orig_scale", _("1:1"), callback=self.board_set_default_scale),
                ControlPanelButton("zoom_out", _("Image zoom out"), callback=self.board_zoom_out),
                ControlPanelButton("zoom_in", _("Image zoom in"), callback=self.board_zoom_in),

                self.space_btn_generator(),
                ControlPanelButton("update_list", _("Update files list"), callback=self.update_folder_list),
            ]
        else:
            self.all_buttons = []


        self.buttons_list = self.all_buttons[:]

        style = """
            QPushButton {
                color: black;
                background-color: gray;

                font-size: 11pt;
                height: 50px;
                border: none;
                padding: 0px 0px;
                margin: 0px 0px;
                text-align: center;

                background-color: #67d8ef;
                background-color: none;
            }
            QPushButton:hover {
                background-color: #aaaaaa;
                color: black;
                background-color: #ff4400;
                color: white;
            }
        """
        _buttons_layout.addStretch()
        for button in self.buttons_list:
            button.setFixedWidth(50)
            button.setFixedHeight(50)
            button.setStyleSheet(style)
            button.setProperty("tooltip_text", button.text())
            button.setText("")
            button.setFocusPolicy(Qt.NoFocus)
            # if button is self.favorite_btn:
            #   button.setText("+")
            _buttons_layout.addWidget(button)
        _buttons_layout.addStretch()

        self.buttons_list = [but for but in self.buttons_list if but.id != "space"]

        _main_layout.addLayout(_label_layout)
        _main_layout.addLayout(_buttons_layout)

        _label_layout.setContentsMargins(0, 0, 0, 0)
        _label_layout.setSpacing(0)
        _buttons_layout.setContentsMargins(10, 10, 10, 10)
        # _buttons_layout.setContentsMargins(0, 0, 0, 0)
        # _buttons_layout.setSpacing(1)
        _buttons_layout.setSpacing(0)
        _main_layout.setContentsMargins(0, 0, 0, 0)
        # _main_layout.setSpacing(10)

        self.setLayout(_main_layout)

        self.fullscreen_flag = False

        self.place_and_resize()

        self.last_cursor_pos = QCursor().pos()
        self.opacity_effect = QGraphicsOpacityEffect(self)
        # по какой-то неизвестной причине нельзя задавать 1.0,
        # иначе приложуха крашится
        self.MAX_OPACITY = 0.9999
        self.opacity_effect.setOpacity(self.MAX_OPACITY)
        self.setGraphicsEffect(self.opacity_effect)
        self.start_time = time.time()
        self.window_opacity = 15.0
        self.DELAY_OPACITY = 15.0
        self.MOUSE_SENSITIVITY = 10 # from zero to infinity
        self.touched = 0

        self.quick_show_flag = False

        self.group_selecting = False
        self.cursor_rect_index = None

        self.multirow_scroll_y = 0

        self.underMouseImageData = None

        self.setMouseTracking(True)

    def control_panel_timer_handler(self):
        self.opacity_handler()

        # если обновлять здесь,
        # то активно будет сжираться CPU
        # обновлять лучше внутри opacity_handler и делать это только тогда,
        # когда значение opacity меняется, а равняется одному и тому же значению
        # self.update()

    def label_text_update(self):
        MW = self.globals.main_window

        # control panel label
        text = ""
        if MW.is_viewer_page_active():
            text = None
            for btn in self.buttons_list:
                if btn.underMouse():
                    text = btn.property("tooltip_text").replace("\n", " ")
                    break
            text = text or MW.current_image_details()

        elif MW.is_board_page_active():

            if self.underMouseImageData is not None:
                image_data = self.underMouseImageData

                w = image_data.source_width
                h = image_data.source_height
                filename = image_data.filename
                foldername = image_data.folder_data.folder_name

                text = f"{foldername} \\ {filename} {w} x {h}"
            else:
                text = _("board page")

        self.control_panel_label.setText(text)

        self.update()

    def opacity_handler(self):
        def setOpacity(value):
            safe_value = max(min(value, self.MAX_OPACITY), 0.0)
            if self.opacity_effect.opacity() != safe_value:
                self.opacity_effect.setOpacity(safe_value)
                if safe_value == 0.0:
                    self.parent().update()
                    self.update()
                else:
                    self.update()

        main_window = self.globals.main_window
        if main_window.is_library_page_active():
            self.window_opacity = 0.0
            setOpacity(self.window_opacity)
            return

        if not main_window.STNG_autohide_control_panel:
            self.window_opacity = 1.0
            setOpacity(self.window_opacity)
            return

        # для поддержки UX-фичи, которая даёт возможность начать выделение миниатюрок
        # на территории главного окна, а не на территории окна миниатюрок
        if self.group_selecting:
            self.window_opacity = 1.0
            setOpacity(self.window_opacity)
            return

        if not main_window.isActiveWindow():
            self.window_opacity = 0.0
            setOpacity(self.window_opacity)
            return

        if self.underMouse():
            self.window_opacity = self.DELAY_OPACITY
            setOpacity(self.window_opacity)
            return

        cursor_pos = QCursor().pos()
        delta = (cursor_pos - self.last_cursor_pos).y()
        self.last_cursor_pos = cursor_pos

        if delta > 0+self.MOUSE_SENSITIVITY:
            if self.touched == 0:
                self.touched = 1

        elif delta < 0-self.MOUSE_SENSITIVITY and delta != 0:
            if self.touched == 0:
                self.touched = -1

        if not main_window.underMouse():
            # чтобы не реагировало,
            # когда мышка на другом мониторе
            self.touched = 0
        if main_window.image_translating:
            self.touched = 0

        if self.quick_show_flag:
            self.quick_show_flag = False
            self.touched = 1

        if self.touched == 0:
            self.window_opacity -= 0.10

        if self.touched == 1:
            if self.window_opacity > self.DELAY_OPACITY-.5:
                self.touched = 0
            else:
                self.window_opacity += 0.25
                if self.window_opacity > self.MAX_OPACITY:
                    self.window_opacity = self.DELAY_OPACITY
                if self.window_opacity < 0.0:
                    self.window_opacity = 0.0

        if self.touched == -1:
            if self.window_opacity < 0.2:
                self.touched = 0
                self.window_opacity = 0.0
            else:
                self.window_opacity -= 0.10
                if self.window_opacity > self.MAX_OPACITY:
                    self.window_opacity = 1.0

        # self.window_opacity будет постоянно уменьшаться
        # если delta будет равна 0, поэтому на случай переполнения:
        if self.window_opacity < -100.0:
            self.window_opacity = 0.0

        setOpacity(self.window_opacity)

    def place_and_resize(self):
        MW = self.globals.main_window
        new_width = MW.rect().width()
        if self.fullscreen_flag:
            new_height = MW.rect().height()
            y_coord = 0
            self.control_panel_label.setVisible(False)
            self.buttons_visibility(False)
        else:
            new_height = MW.BOTTOM_PANEL_HEIGHT
            y_coord = MW.rect().height() - MW.BOTTOM_PANEL_HEIGHT
            self.control_panel_label.setVisible(True)
            self.buttons_visibility(True)
        self.resize(new_width, new_height)
        self.move(0, y_coord)

    def buttons_visibility(self, visibilty):
        for button in self.all_buttons:
            button.setVisible(visibilty)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        folder_data = self.LibraryData().current_folder()
        main_window = self.globals.main_window

        if not main_window.is_start_page_active():

            if self.fullscreen_flag:
                painter.fillRect(self.rect(), QBrush(QColor(10, 10, 10)))
            elif main_window.STNG_draw_control_panel_backplate or self.group_selecting:
                painter.fillRect(self.rect(), QBrush(QColor(20, 20, 20)))

            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

            self.thumbnails_drawing(painter, folder_data)
        painter.end()

    def selection_MousePressEvent(self, event, override=False):
        if event.buttons() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                folder_data = self.LibraryData().current_folder()
                for image_data in folder_data.images_list:
                    image_data._touched = False

                self.group_selecting = True
                pos = self.mapped_cursor_pos()
                if override:
                    pos = self.mapFromGlobal(override)
                    pos.setY(2) # для отрисовки, чтобы рамка выделения не вываливалась одной своей стороной
                self.oldCursorPos = pos
        self.update()

    def selection_MouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.group_selecting:
                selection_rect = build_valid_rect(self.oldCursorPos, self.mapped_cursor_pos())
                self.thumbnails_click(selection_rect=selection_rect)
        self.update()

    def selection_MouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.group_selecting:
                self.group_selecting = False
                selection_rect = build_valid_rect(self.oldCursorPos, self.mapped_cursor_pos())
                self.thumbnails_click(selection_rect=selection_rect)

                folder_data = self.LibraryData().current_folder()
                for image_data in folder_data.images_list:
                    image_data._touched = False

        self.update()

    def multirow_area_width(self):
        return self.rect().width() - 100

    def calculate_row_length(self):
        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH

        min_count = 10
        calculated = (self.multirow_area_width() // THUMBNAIL_WIDTH)-5
        return max(min_count, calculated)

    def get_multirow_thumbnail_pos(self, index, count):

        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH
        MULTIROW_THUMBNAILS_PADDING = self.globals.MULTIROW_THUMBNAILS_PADDING
        AUGMENTED_THUBNAIL_INCREMENT = self.globals.AUGMENTED_THUBNAIL_INCREMENT

        horizontal_offset = (self.rect().width() - THUMBNAIL_WIDTH*count)/2

        x = (index % count)*THUMBNAIL_WIDTH
        y = (index // count)*(THUMBNAIL_WIDTH+AUGMENTED_THUBNAIL_INCREMENT)

        x_offset = horizontal_offset + x
        y_offset = y + MULTIROW_THUMBNAILS_PADDING - self.multirow_scroll_y

        return QPointF(x_offset, y_offset)

    def thumbnails_drawing(self, painter, imgs_to_show, pos_x=0, pos_y=0,
                    library_page_rect=None, current_index=None, draw_mirror=True,
                    additional_y_offset=30):
        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH
        AUGMENTED_THUBNAIL_INCREMENT = self.globals.AUGMENTED_THUBNAIL_INCREMENT
        MULTIROW_THUMBNAILS_PADDING = self.globals.MULTIROW_THUMBNAILS_PADDING

        is_call_from_main_window = isinstance(self, self.globals.main_window.__class__)
        multirow = not is_call_from_main_window and self.fullscreen_flag
        draw_mirror = draw_mirror and (not is_call_from_main_window) and (not self.fullscreen_flag)
        is_board_page_active = self.globals.main_window.is_board_page_active()

        if not is_call_from_main_window:
            ROW_LENGTH = self.calculate_row_length()

        if imgs_to_show is None:
            return
        elif isinstance(imgs_to_show, self.LibraryData.FolderData):
            # library folders rows and control panel row
            folder_data = imgs_to_show
            current_index = folder_data.get_current_index()
            overrided_current_index = False
            if not folder_data.images_list:
                return
            images_list = imgs_to_show.images_list
            _images_list_selected = folder_data._images_list_selected
        else:
            # history row
            overrided_current_index = True
            _images_list_selected = None
            images_list = imgs_to_show

        # закомментировано из-за вызова get_index_centered_list в модуле LibraryData,
        # иначе не будет того желаемого эффекта,
        # когда превьюшки создаются рядом с текущей на данный момент картинкой по обе стороны,
        # а не как раньше, когда они отсортированы от первой до последней в исходном списке.
        # Но смутные воспоминания отбрасывают неясную тень на это решение,
        # ведь я мог добавить эти три строчки, чтобы пофиксить очередной краш,
        # поэтому посмотрю как код будет вести себя,
        # и уже потом решу окончательно, выпиливать или нет
        # first_thm = images_list[0].get_thumbnail()
        # if not first_thm:
        #     return


        mouse_over_control_button = False
        if library_page_rect:
            library_page_rect = QRect(library_page_rect)
            r = QRect(library_page_rect)
        else:
            r = self.rect()
            library_page_rect = r.adjusted(
                -THUMBNAIL_WIDTH,
                -THUMBNAIL_WIDTH,
                THUMBNAIL_WIDTH,
                THUMBNAIL_WIDTH
            )
            if not is_call_from_main_window:
                for btn in self.buttons_list:
                    if btn.underMouse():
                        mouse_over_control_button = True
                        break
        # нужно для того, чтобы не было искажений картинки
        s_thumb_rect = QRect(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)

        cursor_pos = self.mapFromGlobal(QCursor().pos())
        if overrided_current_index:
            main_frame_offset_x = r.width()/2-THUMBNAIL_WIDTH/2
            current_thumb_rect = QRectF(main_frame_offset_x, additional_y_offset+pos_y, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH).toRect()
            painter.setPen(QPen(Qt.red, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(current_thumb_rect)


        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(Qt.NoPen)

        if multirow:

            # отрисовка рядов в полноэкранном режиме
            for image_index, image_data in enumerate(images_list):
                thumbnail = image_data.get_thumbnail()
                if not thumbnail:
                    continue

                thumb_rect = QRectF(
                        self.get_multirow_thumbnail_pos(image_index, ROW_LENGTH),
                        QSizeF(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
                    ).toRect()

                if image_data._selected:
                    thumb_rect_ = thumb_rect.adjusted(0, -AUGMENTED_THUBNAIL_INCREMENT, 0, 0)
                    # специальные параметры, чтобы увеличенное изоражение не косоёбило
                    # _offset высчитывает смещение в координатах s_thumb_rect через проекцию
                    percentage = AUGMENTED_THUBNAIL_INCREMENT/(THUMBNAIL_WIDTH+AUGMENTED_THUBNAIL_INCREMENT)
                    _offset = percentage*THUMBNAIL_WIDTH
                    x = _offset/2
                    y = 0
                    w = THUMBNAIL_WIDTH - _offset
                    h = THUMBNAIL_WIDTH
                    s_thumb_rect_ = QRectF(x, y, w, h).toRect()

                else:
                    thumb_rect_ = thumb_rect
                    s_thumb_rect_ = s_thumb_rect

                if library_page_rect.contains(thumb_rect_.center()):
                    if thumbnail != self.globals.DEFAULT_THUMBNAIL:
                        painter.drawRect(thumb_rect_)
                    painter.drawPixmap(thumb_rect_, thumbnail, s_thumb_rect_)

        else:

            if not is_call_from_main_window:
                self.underMouseImageData = None

            # отрисовка одного ряда в панели управления, в истории прсмотров и в папках библиотеки
            for image_index, image_data in enumerate(images_list):
                thumbnail = image_data.get_thumbnail()
                if not thumbnail:
                    continue
                offset_x = 0
                if pos_x:
                    offset_x = pos_x + THUMBNAIL_WIDTH*image_index
                else:
                    # ради анимационного эффекта пришлось разделить выражение
                    # offset_x = r.width()/2-THUMBNAIL_WIDTH/2+THUMBNAIL_WIDTH*(image_index-current_index)
                    # на зависимую и независимую от current_index части
                    if isinstance(imgs_to_show, self.LibraryData.FolderData):
                        # control panel row
                        relative_offset_x = folder_data.relative_thumbnails_row_offset_x
                    else:
                        # history row
                        relative_offset_x = -THUMBNAIL_WIDTH*current_index

                    if is_board_page_active and not is_call_from_main_window:
                        offset_x = THUMBNAIL_WIDTH*(image_index + 1) + folder_data.absolute_board_thumbnails_row_offset_x
                    else:
                        offset_x = r.width()/2+THUMBNAIL_WIDTH*image_index-THUMBNAIL_WIDTH/2 + relative_offset_x
                thumb_rect = QRectF(offset_x, additional_y_offset+pos_y, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH).toRect()

                if image_data._selected and not is_call_from_main_window:
                    thumb_rect_ = thumb_rect.adjusted(0, -AUGMENTED_THUBNAIL_INCREMENT, 0, 0)
                    # специальные параметры, чтобы увеличенное изоражение не косоёбило
                    # _offset высчитывает смещение в координатах s_thumb_rect через проекцию
                    percentage = AUGMENTED_THUBNAIL_INCREMENT/(THUMBNAIL_WIDTH+AUGMENTED_THUBNAIL_INCREMENT)
                    _offset = percentage*THUMBNAIL_WIDTH
                    x = _offset/2
                    y = 0
                    w = THUMBNAIL_WIDTH - _offset
                    h = THUMBNAIL_WIDTH
                    s_thumb_rect_ = QRectF(x, y, w, h).toRect()

                else:
                    thumb_rect_ = thumb_rect
                    s_thumb_rect_ = s_thumb_rect

                # если миниатюра помещается в отведённой зоне library_page_rect
                if library_page_rect.contains(thumb_rect_.topRight()):
                    highlighted = thumb_rect.contains(cursor_pos)
                    if highlighted and not is_call_from_main_window:
                        self.underMouseImageData = image_data
                    cases = (
                                highlighted,
                                is_call_from_main_window,
                                _images_list_selected,
                                not is_call_from_main_window and self.fullscreen_flag,
                            )
                    if any(cases) and not mouse_over_control_button:
                        painter.setOpacity(1.0)
                    else:
                        painter.setOpacity(0.5)
                    # draw thumbnail
                    if thumbnail != self.globals.DEFAULT_THUMBNAIL:
                        painter.drawRect(thumb_rect)

                    if image_data._selected:
                        painter.setOpacity(1.0)

                    painter.drawPixmap(thumb_rect_, thumbnail, s_thumb_rect_)
                    painter.setOpacity(1.0)

                    if image_index == current_index and self.globals.DEBUG:
                        old_pen = painter.pen()
                        old_brush = painter.brush()
                        offset = 4
                        bigger_rect = thumb_rect.adjusted(-offset, -offset, offset, offset)
                        points = [
                            bigger_rect.topLeft() + QPoint(offset, 0),

                            bigger_rect.topRight() + QPoint(-offset, 0),
                            bigger_rect.topRight() + QPoint(0, offset),

                            bigger_rect.bottomRight() + QPoint(0, -offset),
                            bigger_rect.bottomRight() + QPoint(-offset, 0),

                            bigger_rect.bottomLeft() + QPoint(offset, 0),
                            bigger_rect.bottomLeft() + QPoint(0, -offset),

                            bigger_rect.topLeft() + QPoint(0, offset),

                            bigger_rect.topLeft() + QPoint(offset, 0),
                        ]
                        painter.setPen(QPen(Qt.red, 1))
                        painter.setBrush(Qt.NoBrush)
                        for n, point in enumerate(points[:-1]):
                            painter.drawLine(point, points[n+1])
                        painter.setPen(old_pen)
                        painter.setBrush(old_brush)

                    # draw thumbnail mirrored copy
                    if draw_mirror:
                        thumb_rect = QRectF(
                            offset_x,
                            30+THUMBNAIL_WIDTH,
                            THUMBNAIL_WIDTH,
                            THUMBNAIL_WIDTH
                        ).toRect()
                        if highlighted and not mouse_over_control_button:
                            painter.setOpacity(0.5)
                        else:
                            painter.setOpacity(0.2)
                        center = thumb_rect.center()
                        painter.translate(center)
                        painter.rotate(180)
                        thumb_rect = QRectF(
                            -THUMBNAIL_WIDTH+THUMBNAIL_WIDTH/2+1,
                            -THUMBNAIL_WIDTH+THUMBNAIL_WIDTH/2,
                            THUMBNAIL_WIDTH, THUMBNAIL_WIDTH
                        ).toRect()
                        painter.scale(-1.0, 1.0)
                        painter.drawPixmap(thumb_rect, thumbnail, s_thumb_rect)
                        painter.resetTransform()
                        painter.setOpacity(1.0)



        if is_call_from_main_window:
            return

        cursor_rect = None
        self.cursor_rect_index = None

        # positions to insert cursor
        if multirow:
            image_index = -1
            image_index_draw = -1
            image_rows = folder_data.get_phantomed_image_rows(ROW_LENGTH)
            for ri, image_row in enumerate(image_rows):
                for iri, image_data in enumerate(image_row):

                    _ROW_LENGTH = ROW_LENGTH + 1
                    image_index_draw += 1
                    image_index += 1

                    sel_rect = QRectF(
                            self.get_multirow_thumbnail_pos(image_index_draw, _ROW_LENGTH),
                            QSizeF(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
                        ).toRect()

                    sel_rect.adjust(5, 0, -5, 0) # немного сплющиваем

                    if sel_rect.contains(self.mapped_cursor_pos()):
                        if folder_data.check_insert_position(image_index):
                            cursor_rect = sel_rect
                            self.cursor_rect_index = image_index
                        painter.setOpacity(1.0)
                    else:
                        painter.setOpacity(0.3)

                    if self.globals.DEBUG:
                        painter.setPen(QPen(Qt.green))
                        painter.setBrush(Qt.NoBrush)
                        painter.drawRect(sel_rect)
                    painter.setOpacity(1.0)


                image_index -= 1

        else:

            for image_index, image_data in enumerate(folder_data.get_phantomed_image_list()):

                relative_offset_x = folder_data.relative_thumbnails_row_offset_x

                if is_board_page_active and not is_call_from_main_window:
                    offset_x = THUMBNAIL_WIDTH*(image_index + 1) - THUMBNAIL_WIDTH/2 + folder_data.absolute_board_thumbnails_row_offset_x
                else:
                    offset_x = r.width()/2+THUMBNAIL_WIDTH*image_index - THUMBNAIL_WIDTH + relative_offset_x
                sel_rect = QRectF(offset_x, additional_y_offset+pos_y, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH).toRect()

                sel_rect.adjust(5, 0, -5, 0) # немного сплющиваем

                if sel_rect.contains(self.mapped_cursor_pos()):
                    if folder_data.check_insert_position(image_index):
                        cursor_rect = sel_rect
                        self.cursor_rect_index = image_index
                    painter.setOpacity(1.0)
                else:
                    painter.setOpacity(0.3)

                if self.globals.DEBUG:
                    painter.setPen(QPen(Qt.green))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(sel_rect)

                painter.setOpacity(1.0)

        # отрисовка курсора для визуализации места вставки
        if cursor_rect and _images_list_selected:
            painter.setPen(QPen(QColor(200, 0, 0), 4))
            a = cursor_rect.center() - QPoint(0, cursor_rect.height()//2)
            b = cursor_rect.center() + QPoint(0, cursor_rect.height()//2)
            painter.drawLine(a, b)
            p = a
            painter.drawLine(p + QPoint(5, -3), p)
            painter.drawLine(p + QPoint(-5, -3), p)
            p = b
            painter.drawLine(p + QPoint(5, 3), p)
            painter.drawLine(p + QPoint(-5, 3), p)

            if self.globals.DEBUG:
                pp = a + QPoint(0, -15)
                pp_rect = QRect(0, 0, 20, 20)
                pp_rect.moveCenter(pp)
                painter.fillRect(pp_rect, QBrush(Qt.black))
                painter.drawText(pp_rect, Qt.AlignCenter | Qt.AlignVCenter, str(self.cursor_rect_index))

        # отрисовка прямоугольника выделения
        if self.group_selecting:
            painter.setPen(QPen(Qt.green))
            painter.setBrush(Qt.NoBrush)
            rect = QRect(self.oldCursorPos, self.mapped_cursor_pos())
            painter.drawRect(rect)


    def thumbnails_click(
                    self,
                    define_cursor_shape=False,
                    select=False,
                    selection_rect=None,
                    click=False,
                    click_handler=None,
            ):
        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH
        AUGMENTED_THUBNAIL_INCREMENT = self.globals.AUGMENTED_THUBNAIL_INCREMENT
        MULTIROW_THUMBNAILS_PADDING = self.globals.MULTIROW_THUMBNAILS_PADDING

        is_call_from_main_window = isinstance(self, self.globals.main_window.__class__)
        is_board_page_active = self.globals.main_window.is_board_page_active()

        ROW_LENGTH = self.calculate_row_length()

        folder_data = self.LibraryData().current_folder()
        _images_list_selected = folder_data._images_list_selected
        images_list = folder_data.images_list
        current_index = folder_data.get_current_index()
        r = self.rect()
        check_rect = r.adjusted(-THUMBNAIL_WIDTH, -THUMBNAIL_WIDTH, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
        pos = QCursor().pos()
        cursor_pos = self.mapFromGlobal(pos)

        def toggle_selection_flag(im_data):
            if not im_data._is_phantom:
                pass
            im_data._selected = not im_data._selected
            if im_data._selected:
                _images_list_selected.append(im_data)
            else:
                _images_list_selected.remove(im_data)


        is_call_from_main_window = isinstance(self, self.globals.main_window.__class__)
        multirow = not is_call_from_main_window and self.fullscreen_flag

        if multirow:

            image_index = -1
            image_index_draw = -1
            image_rows = folder_data.get_phantomed_image_rows(ROW_LENGTH)
            for ri, image_row in enumerate(image_rows):
                for iri, image_data in enumerate(image_row):

                    # обратить внимание, что именно здесь фантомный элемент в рачёт не берём,
                    # поэтому здесь единица не прибавляется
                    _ROW_LENGTH = ROW_LENGTH
                    image_index_draw += 1
                    image_index += 1


                    d_rect = QRectF(
                            self.get_multirow_thumbnail_pos(image_index_draw, _ROW_LENGTH),
                            QSizeF(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
                        ).toRect()

                    d_rect.adjust(5, 0, -5, 0) # немного сплющиваем

                    if image_data._selected:
                        d_rect = d_rect.adjusted(0, -AUGMENTED_THUBNAIL_INCREMENT, 0, 0)

                    case1 = d_rect.contains(cursor_pos) and selection_rect is None
                    case2 = (selection_rect is not None and not selection_rect.intersected(d_rect).isNull())

                    if case1 or case2:
                        if define_cursor_shape:
                            return True
                        elif select:
                            # не нужно, потому что прямоугольное выделение решает и этот частный случай
                            toggle_selection_flag(image_data)
                            return
                        elif selection_rect:
                            if not image_data._touched:
                                image_data._touched = True
                                toggle_selection_flag(image_data)
                        elif click:
                            self.LibraryData().jump_to_image(image_index)
                            return
                        elif click_handler:
                            click_handler(image_data)
                            return


                image_index_draw -= 1
                image_index -= 1

        else:

            for image_index, image_data in enumerate(images_list):
                thumbnail = image_data.get_thumbnail()
                # ради анимационного эффекта пришлось разделить выражение
                # offset_x = r.width()/2-THUMBNAIL_WIDTH/2+THUMBNAIL_WIDTH*(image_index-current_index)
                # на зависимую и независимую от current_index части
                if False:
                    relative_offset_x = -THUMBNAIL_WIDTH*current_index
                else:
                    relative_offset_x = folder_data.relative_thumbnails_row_offset_x
                if is_board_page_active and not is_call_from_main_window:
                    offset_x = THUMBNAIL_WIDTH*(image_index+1) + folder_data.absolute_board_thumbnails_row_offset_x
                else:

                    offset_x = r.width()/2+THUMBNAIL_WIDTH*image_index-THUMBNAIL_WIDTH/2 + relative_offset_x
                d_rect = QRect(int(offset_x), 30, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)

                if image_data._selected:
                    d_rect = d_rect.adjusted(0, -AUGMENTED_THUBNAIL_INCREMENT, 0, 0)

                case1 = d_rect.contains(cursor_pos) and selection_rect is None
                case2 = selection_rect is not None and not selection_rect.intersected(d_rect).isNull()
                if check_rect.contains(d_rect.center()):
                    if case1 or case2:
                        if define_cursor_shape:
                            return True
                        # elif select:
                        #     toggle_selection_flag(image_data)
                        #     return
                        elif selection_rect:
                            if not image_data._touched:
                                image_data._touched = True
                                toggle_selection_flag(image_data)
                        elif click:
                            self.LibraryData().jump_to_image(image_index)
                            return
                        elif click_handler:
                            click_handler(image_data)
                            return


    def wheelEvent(self, event):
        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

        MW = self.globals.main_window

        THUMBNAIL_WIDTH = step_value = self.globals.THUMBNAIL_WIDTH
        if self.fullscreen_flag:
            AUGMENTED_THUBNAIL_INCREMENT = self.globals.AUGMENTED_THUBNAIL_INCREMENT
            MULTIROW_THUMBNAILS_PADDING = self.globals.MULTIROW_THUMBNAILS_PADDING

            if scroll_value > 0:
                self.multirow_scroll_y -= step_value*3
            else:
                self.multirow_scroll_y += step_value*3

            cf = self.LibraryData().current_folder()
            images_list_count = len(cf.images_list)

            count = images_list_count // self.calculate_row_length()
            # добавляем 2=1+1:
            # первая 1 это необходимая высота для вычисления общей высоты всех рядов
            # и ещё одна 1 добавлена для того, чтобы прокручивая было наглядно видно,
            # что мы докрутили до конца списка при полностью заполненных рядах
            content_height = (count+2)*(THUMBNAIL_WIDTH+AUGMENTED_THUBNAIL_INCREMENT)
            viewer_height = self.rect().height()

            max_value =  (content_height - viewer_height) + MULTIROW_THUMBNAILS_PADDING
            min_value = - MULTIROW_THUMBNAILS_PADDING

            self.multirow_scroll_y = min(max_value, max(self.multirow_scroll_y, min_value))

        elif MW.is_board_page_active() and not self.fullscreen_flag:
            libdata = self.LibraryData()
            cf = libdata.current_folder()
            if scroll_value > 0:
                step = THUMBNAIL_WIDTH
            else:
                step = -THUMBNAIL_WIDTH
            cf.absolute_board_thumbnails_row_offset_x -= step

            cf = self.LibraryData().current_folder()
            images_list_count = len(cf.images_list)

            content_width = images_list_count*THUMBNAIL_WIDTH
            viewer_width = self.rect().width() - THUMBNAIL_WIDTH*2

            max_value = 0
            min_value = viewer_width - content_width

            cf.absolute_board_thumbnails_row_offset_x = min(max_value, max(cf.absolute_board_thumbnails_row_offset_x, min_value))

            status = f'{max_value}, {min_value}'
            # print(status)

        MW.update()


    def mousePressEvent(self, event):
        MW = self.globals.main_window
        if MW.is_library_page_active():
            super().mousePressEvent(event)

        elif MW.is_viewer_page_active():
            self.selection_MousePressEvent(event)
            return
        elif MW.is_start_page_active():
            # для того, чтобы можно было повторно кликать
            # на кнопки выбора языка на стартовой странице.
            # Иначе панель будет воровать клики,
            # а она как раз из-за смены языка
            # (пере)создаётся прозрачной и без кнопок
            super().mousePressEvent(event)

        # убрал здесь return, чтобы на странице библиотеки мышкой можно быдо выделить папку, находящаяся с самом низу на месте панели управления

    def mouseMoveEvent(self, event):
        MW = self.globals.main_window

        self.label_text_update()
        MW.cursor_setter()

        if MW.is_library_page_active():
            super().mouseMoveEvent(event)

        elif MW.is_viewer_page_active():
            self.selection_MouseMoveEvent(event)

        elif MW.is_start_page_active():
            # для того, чтобы можно было повторно кликать
            # на кнопки выбора языка на стартовой странице.
            # Иначе панель будет воровать клики,
            # а она как раз из-за смены языка
            # (пере)создаётся прозрачной и без кнопок
            super().mouseMoveEvent(event)

        return

    def mouseReleaseEvent(self, event):

        MW = self.globals.main_window

        cf = self.LibraryData().current_folder()


        if MW.is_library_page_active():
            super().mouseReleaseEvent(event)

        elif MW.is_viewer_page_active():
            if event.button() == Qt.LeftButton:
                self.selection_MouseReleaseEvent(event)

                if self.group_selecting:
                    pass

                elif (not event.modifiers() & Qt.ControlModifier) and cf._images_list_selected and self.cursor_rect_index is not None:
                    cf.do_rearrangement(self.cursor_rect_index)
                    MW.update_thumbnails_row_relative_offset(cf)

                elif event.modifiers() == Qt.NoModifier and not cf._images_list_selected:
                    self.thumbnails_click(click=True)

        elif MW.is_board_page_active():
            self.thumbnails_click(click_handler=MW.board_thumbnails_click_handler)


        elif MW.is_start_page_active():
            # для того, чтобы можно было повторно кликать
            # на кнопки выбора языка на стартовой странице.
            # Иначе панель будет воровать клики,
            # а она как раз из-за смены языка
            # (пере)создаётся прозрачной и без кнопок
            super().mouseReleaseEvent(event)

        self.update()
        MW.update()

        return

    def do_toggle_fullscreen(self):
        self.fullscreen_flag = not self.fullscreen_flag
        self.place_and_resize()
        # if self.fullscreen_flag:
        #     self.activateWindow()
        # else:
        #     self.parent().activateWindow()

    def contextMenuEvent(self, event):
        MW = self.globals.main_window
        if MW.is_start_page_active():
            return
        CM = RoundedQMenu()
        CM.setStyleSheet(self.parent().context_menu_stylesheet)
        CM.setAttribute(Qt.WA_TranslucentBackground, True)
        self.contextMenuActivated = True
        cf = self.LibraryData().current_folder()
        current_sort_type = cf.sort_type
        current_reversed = cf.sort_type_reversed

        open_settings = CM.addAction(_("Settings"))
        CM.addSeparator()
        deep_scan = CM.addAction(_("Include subfolers when updating files list and scanning on openning"))
        CM.addSeparator()
        original_order = CM.addAction(_("Original order"))
        sort_filename_desc = CM.addAction(_("Sort by filename (descending)"))
        sort_filename_incr = CM.addAction(_("Sort by filename (ascending)"))
        sort_cdate_desc = CM.addAction(_("Sort by creation date (descending)"))
        sort_cdate_incr = CM.addAction(_("Sort by creation date (ascending)"))
        save_images_order = CM.addAction(_("Save order metadata to disk"))
        CM.addSeparator()
        toggle_fullscreen = CM.addAction(_("Show control panel in full-screen mode"))

        checkable_actions = (
            original_order,
            sort_filename_desc,
            sort_filename_incr,
            sort_cdate_desc,
            sort_cdate_incr,
            deep_scan,
            toggle_fullscreen,
        )
        for action in checkable_actions:
            action.setCheckable(True)
        if current_sort_type != "reordered":
            if current_sort_type == "original":
                original_order.setChecked(True)
            elif current_sort_type == "filename" and current_reversed:
                sort_filename_desc.setChecked(True)
            elif current_sort_type == "filename" and not current_reversed:
                sort_filename_incr.setChecked(True)
            elif current_sort_type == "creation_date" and current_reversed:
                sort_cdate_desc.setChecked(True)
            elif current_sort_type == "creation_date" and not current_reversed:
                sort_cdate_incr.setChecked(True)
            if cf.deep_scan:
                deep_scan.setChecked(cf.deep_scan)
        toggle_fullscreen.setChecked(self.fullscreen_flag)


        action = CM.exec_(self.mapToGlobal(event.pos()))
        self.contextMenuActivated = False
        if action == None:
            pass
        elif action == sort_filename_desc:
            cf.do_sort("filename", reversed=True)
        elif action == sort_filename_incr:
            cf.do_sort("filename")
        elif action == sort_cdate_desc:
            cf.do_sort("creation_date", reversed=True)
        elif action == sort_cdate_incr:
            cf.do_sort("creation_date")
        elif action == original_order:
            cf.do_sort("original")
        elif action == open_settings:
            MW.open_settings_window()
        elif action == deep_scan:
            cf.deep_scan = not cf.deep_scan
        elif action == save_images_order:
            cf.save_images_order()
        elif toggle_fullscreen:
            self.do_toggle_fullscreen()
        self.globals.control_panel.update()
        MW.update()

# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
