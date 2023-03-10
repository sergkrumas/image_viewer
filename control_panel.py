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


class ControlPanelButton(QPushButton):
    def __init__(self, id, *args):
        super().__init__(*args)
        self.id = id

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

            if self.id == "play":
                painter.setPen(Qt.NoPen)
                painter.setBrush(orange)
                painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))
            elif self.underMouse():
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
                painter.setOpacity(0.3)
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
                QPointF(5, w/2),
                QPointF(w/2+2, 12),
                QPointF(w/2, 20),
                QPointF(w-5, 22),
                QPointF(w-5, 28),
                QPointF(w/2, 30),
                QPointF(w/2+2, 38),
                QPointF(5, w/2),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            # painter.setBrush(Qt.white)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

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
                QPointF(w, w) - QPointF(5, w/2),
                QPointF(w, w) - QPointF(w/2+2, 12),
                QPointF(w, w) - QPointF(w/2, 20),
                QPointF(w, w) - QPointF(w-5, 22),
                QPointF(w, w) - QPointF(w-5, 28),
                QPointF(w, w) - QPointF(w/2, 30),
                QPointF(w, w) - QPointF(w/2+2, 38),
                QPointF(w, w) - QPointF(5, w/2),
            ]
            poly = QPolygonF(points)
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(poly, fillRule=Qt.WindingFill)

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
        MW.show_center_label("scale")

    def zoom_out(self):
        MW = self.globals.main_window
        MW.do_scale_image(-0.05, cursor_pivot=False)
        MW.show_center_label("scale")

    def set_original_scale(self):
        MW = self.globals.main_window
        MW.set_original_scale()
        MW.show_center_label("scale")

    def show_settings_window(self):
        MW = self.globals.main_window
        MW.open_settings_window()

    def toggle_help(self):
        MW = self.globals.main_window
        MW.help_mode = not MW.help_mode
        MW.update()

    def quick_show(self):
        self.quick_show_flag = True

    def show_previous(self):
        self.LibraryData().show_previous_image()

    def play(self):
        MW = self.globals.main_window
        Slideshow.globals = self.globals
        Slideshow.start_slideshow()
        MW.update()

    def show_next(self):
        self.LibraryData().show_next_image()

    def correct_content_position_if_needed(self):
        MW = self.globals.main_window
        # ?????? ???????????????? ???????????? ?????????????????? ???? ??????????????????????/??????????????????
        if MW.animated:
            return
        class ContentCornerPoint():
            def __init__(self, point):
                super().__init__()
                self.point = point
                diff = point - MW.rect().center()
                self.distance = math.sqrt(pow(diff.x(), 2) + pow(diff.y(), 2))
            def __lt__(self, other):
                return self.distance > other.distance
        window_rect = MW.rect()
        content_rect = MW.get_image_viewport_rect(debug=False, respect_rotation=True)
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
        status = self.LibraryData().manage_favorite_list()
        if status == "added":
            self.favorite_btn.setText("-")
            self.favorite_btn.id = "favorite_added"
            MW.show_center_label("?????????????????? ?? ??????????????????")
        elif status == "removed":
            self.favorite_btn.setText("+")
            self.favorite_btn.id = "favorite"
            MW.show_center_label("?????????????? ???? ????????????????????")
        MW.update()

    def show_in_folder(self):
        MW = self.globals.main_window
        if MW.image_filepath:
            show_in_folder_windows(MW.image_filepath)
            MW.update()

    def update_folder_list(self):
        self.LibraryData().update_current_folder()
        MW = self.globals.main_window
        MW.show_center_label("??????????????????")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _main_layout = QVBoxLayout()
        _buttons_layout = QHBoxLayout()
        _label_layout = QHBoxLayout()

        self.zoom_out_btn = ControlPanelButton("zoom_out", "??????????????????")
        self.zoom_in_btn = ControlPanelButton("zoom_in", "??????????????????")
        self.original_scale_btn = ControlPanelButton("orig_scale", "1:1")
        self.help_btn = ControlPanelButton("help", "??????????????")
        self.settings_btn = ControlPanelButton("settings", "??????????????????")

        self.previous_btn = ControlPanelButton("previous", "????????????????????")
        self.play_btn = ControlPanelButton("play", "????????????????")
        self.next_btn = ControlPanelButton("next", "??????????????????")

        self.rotate_clockwise_btn = ControlPanelButton("rotate_clockwise", "??????????????????\n???? ?????????????? ??????????????")
        self.rotate_counterclockwise_btn = ControlPanelButton("rotate_counterclockwise", "?????????????????? ????????????\n?????????????? ??????????????")
        self.favorite_btn = ControlPanelButton("favorite", "??????????????????")
        self.open_in_explorer_btn = ControlPanelButton("", "??????????\n???? ??????????")
        self.open_in_google_chrome_btn = ControlPanelButton("", "?????????????? ??\nGoogle Chrome")

        self.control_panel_label = QLabel("picture.extension (1920x1080)", self)
        self.control_panel_label.setStyleSheet("font-weight: bold; color: white; font-size: 12pt; padding: 5px;")
        self.control_panel_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.update_list_btn = ControlPanelButton("update_list", "???????????????? ????????????")

        self.space_btn_generator = lambda: ControlPanelButton("space")

        _label_layout.addWidget(self.control_panel_label)
        effect = QGraphicsDropShadowEffect()
        effect.setColor(Qt.black)
        effect.setBlurRadius(5)
        effect.setXOffset(0)
        effect.setYOffset(0)
        self.control_panel_label.setGraphicsEffect(effect)

        self.buttons_list = [
            self.original_scale_btn,
            self.zoom_out_btn,
            self.zoom_in_btn,

            self.help_btn,
            self.settings_btn,

            self.previous_btn,
            self.play_btn,
            self.next_btn,

            self.rotate_clockwise_btn,
            self.rotate_counterclockwise_btn,
            self.favorite_btn,

            # self.space_btn_generator(),
            self.update_list_btn,
            self.space_btn_generator(),
        ]

        click_handlers = [
            self.set_original_scale,
            self.zoom_out,
            self.zoom_in,

            self.toggle_help,
            self.show_settings_window,

            self.show_previous,
            self.play,
            self.show_next,

            self.rotate_clockwise,
            self.rotate_counterclockwise,
            self.manage_favorite_list,

            self.update_folder_list,

            lambda: None,
        ]

        for button, handler in zip(self.buttons_list, click_handlers):
            button.clicked.connect(handler)
            button.setFixedWidth(50)
            button.setFixedHeight(50)

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
            button.setStyleSheet(style)
            button.setProperty("tooltip_text", button.text())
            button.setText("")
            # if button is self.favorite_btn:
            #   button.setText("+")
            _buttons_layout.addWidget(button)
        _buttons_layout.addStretch()

        self.buttons_list =  [but for but in self.buttons_list if but.id != "space"]

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

        self.place_and_resize()

        self.timer = QTimer()
        self.timer.timeout.connect(self.control_panel_timer_handler)
        self.timer.start(20)

        self.last_cursor_pos = QCursor().pos()
        self.opacity_effect = QGraphicsOpacityEffect(self)
        # ???? ??????????-???? ?????????????????????? ?????????????? ???????????? ???????????????? 1.0,
        # ?????????? ?????????????????? ????????????????
        self.MAX_OPACITY = 0.9999
        self.opacity_effect.setOpacity(self.MAX_OPACITY)
        self.setGraphicsEffect(self.opacity_effect)
        self.start_time = time.time()
        self.window_opacity = 15.0
        self.DELAY_OPACITY = 15.0
        self.MOUSE_SENSITIVITY = 10 # from zero to infinity
        self.touched = 0

        self.quick_show_flag = False

    def control_panel_timer_handler(self):
        self.opacity_handler()
        MW = self.globals.main_window
        if MW.handling_input:
            return

        # label
        text = None
        for btn in self.buttons_list:
            if btn.underMouse():
                text = btn.property("tooltip_text")
        text = text or MW.current_image_details()
        text = text.replace("\n", " ")
        self.control_panel_label.setText(text)

        # movie progress bar
        if MW.animated:
            MW.update()

        # global cursor
        SettingsWindow = self.SettingsWindow
        settings_win_under_mouse = hasattr(SettingsWindow, 'instance') \
                                        and SettingsWindow.instance.isVisible() \
                                        and SettingsWindow.instance.underMouse()
        if settings_win_under_mouse:
            MW.setCursor(Qt.PointingHandCursor)
        elif MW.library_mode:
            if MW.over_corner_button() or MW.over_corner_button(corner_attr="topLeft"):
                MW.setCursor(Qt.PointingHandCursor)
            elif MW.previews_list_active_item:
                MW.setCursor(Qt.PointingHandCursor)
            else:
                MW.setCursor(Qt.ArrowCursor)
        else:
            if MW.region_zoom_in_input_started:
                MW.setCursor(Qt.CrossCursor)
            elif any(btn.underMouse() for btn in self.buttons_list):
                MW.setCursor(Qt.PointingHandCursor)
            elif MW.over_corner_button() or MW.over_corner_button(corner_attr="topLeft"):
                MW.setCursor(Qt.PointingHandCursor)
            elif self.thumbnails_row_clicked(define_cursor_shape=True):
                MW.setCursor(Qt.PointingHandCursor)
            elif MW.is_cursor_over_image() and \
                    (not MW.library_mode) and \
                    (not self.globals.control_panel.underMouse()):
                MW.setCursor(Qt.SizeAllCursor)
            else:
                MW.setCursor(Qt.ArrowCursor)
        self.update()

    def opacity_handler(self):
        def setOpacity(value):
            safe_value = max(min(value, self.MAX_OPACITY), 0.0)
            self.opacity_effect.setOpacity(safe_value)

        main_window = self.globals.main_window
        if main_window.library_mode:
            self.window_opacity = 0.0
            setOpacity(self.window_opacity)
            return

        if not main_window.autohide_control_panel:
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
        # ???????????? ?????????????? ??????????????????
        if delta > 0+self.MOUSE_SENSITIVITY:
            if self.touched == 0:
                self.touched = 1

        elif delta < 0-self.MOUSE_SENSITIVITY and delta != 0:
            if self.touched == 0:
                self.touched = -1

        if not main_window.underMouse():
            # ?????????? ???? ??????????????????????,
            # ?????????? ?????????? ???? ???????????? ????????????????
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

        # self.window_opacity ?????????? ?????????????????? ??????????????????????
        # ???????? delta ?????????? ?????????? 0, ?????????????? ???? ???????????? ????????????????????????:
        if self.window_opacity < -100.0:
            self.window_opacity = 0.0

        setOpacity(self.window_opacity)

    def place_and_resize(self):
        MW = self.globals.main_window
        new_width = MW.rect().width()
        new_height = MW.BOTTOM_PANEL_HEIGHT
        self.resize(new_width, new_height)
        y_coord = MW.rect().height() - MW.BOTTOM_PANEL_HEIGHT
        self.move(0, y_coord)

    def thumbnails_row_drawing(self, painter, imgs_to_show, pos_x=0, pos_y=0,
                    library_mode_rect=None, current_index=None, draw_mirror=True,
                    additional_y_offset=30):
        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH

        if imgs_to_show is None:
            return
        if isinstance(imgs_to_show, self.LibraryData.FolderData):
            folder_data = imgs_to_show
            current_index = folder_data.current_index()
            overrided_current_index = False
            if not folder_data.images_list:
                return
            images_list = imgs_to_show.images_list
        else:
            overrided_current_index = True
            images_list = imgs_to_show
        first_thm = images_list[0].get_thumbnail()
        if not first_thm:
            return

        mouse_over_control_button = False
        if library_mode_rect:
            library_mode_rect = QRect(library_mode_rect)
            r = QRect(library_mode_rect)
        else:
            r = self.rect()
            library_mode_rect = r.adjusted(
                -THUMBNAIL_WIDTH,
                -THUMBNAIL_WIDTH,
                THUMBNAIL_WIDTH,
                THUMBNAIL_WIDTH
            )
            if (pos_x != 0 and pos_y != 0):
                for btn in self.buttons_list:
                    if btn.underMouse():
                        mouse_over_control_button = True
                        break
        # ?????????? ?????? ????????, ?????????? ???? ???????? ??????????????????
        s_thumb_rect = QRect(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)

        cursor_pos = self.mapFromGlobal(QCursor().pos())
        if overrided_current_index:
            offset_x = r.width()/2-THUMBNAIL_WIDTH/2
            current_thumb_rect = QRectF(int(offset_x), additional_y_offset+int(pos_y), THUMBNAIL_WIDTH, THUMBNAIL_WIDTH).toRect()
            painter.setPen(QPen(Qt.red, 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(current_thumb_rect)

        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.setPen(Qt.NoPen)
        for n, image_data in enumerate(images_list):
            thumbnail = image_data.get_thumbnail()
            if not thumbnail:
                continue
            offset_x = 0
            if pos_x:
                offset_x = pos_x + THUMBNAIL_WIDTH*n
            else:
                offset_x = r.width()/2-THUMBNAIL_WIDTH/2 + THUMBNAIL_WIDTH*(n-current_index)
            thumb_rect = QRectF(int(offset_x), additional_y_offset+int(pos_y), THUMBNAIL_WIDTH, THUMBNAIL_WIDTH).toRect()
            # ???????? ?????????????????? ???????????????????? ?? ???????????????????? ???????? library_mode_rect
            if library_mode_rect.contains(thumb_rect.center()):
                highlighted = thumb_rect.contains(cursor_pos)
                if (highlighted or pos_x) and not mouse_over_control_button:
                    painter.setOpacity(1.0)
                else:
                    painter.setOpacity(0.5)
                # draw thumbnail
                if thumbnail != self.globals.DEFAULT_THUMBNAIL:
                    painter.drawRect(thumb_rect)
                painter.drawPixmap(thumb_rect, thumbnail, s_thumb_rect)
                painter.setOpacity(1.0)
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

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        folder_data = self.LibraryData().current_folder()
        main_window = self.globals.main_window
        if main_window.show_backplate:
            painter.fillRect(self.rect(), QBrush(QColor(20, 20, 20)))
        self.thumbnails_row_drawing(painter, folder_data)
        painter.end()

    def mousePressEvent(self, event):
        if self.globals.main_window.library_mode:
            super().mousePressEvent(event)
        else:
            return
        # ?????????? ?????????? return, ?????????? ?? ???????????? ???????????????????? ???????????? ???????????? ????????????????????

    def mouseMoveEvent(self, event):
        # super().mouseMoveEvent(event)
        return

    def contextMenuEvent(self, event):

        MW = self.globals.main_window
        if MW.show_startpage:
            return
        CM = QMenu()
        self.contextMenuActivated = True
        cf = self.LibraryData().current_folder()
        current_sort_type = cf.sort_type
        current_reversed = cf.sort_type_reversed

        open_settings = CM.addAction("??????????????????")
        CM.addSeparator()
        deep_scan = CM.addAction("???????????????? ???????????????? ?????? ???????????????????? ?? ????????????????????????")
        CM.addSeparator()
        original_order = CM.addAction("???????????????? ??????????????")
        sort_filename_desc = CM.addAction("?????????????????????? ???? ?????????? (???? ????????????????)")
        sort_filename_incr = CM.addAction("?????????????????????? ???? ?????????? (???? ??????????????????????)")
        sort_cdate_desc = CM.addAction("?????????????????????? ???? ???????? ???????????????? (???? ????????????????)")
        sort_cdate_incr = CM.addAction("?????????????????????? ???? ???????? ???????????????? (???? ??????????????????????)")
        checkable_actions = (
            original_order,
            sort_filename_desc,
            sort_filename_incr,
            sort_cdate_desc,
            sort_cdate_incr,
            deep_scan,
        )
        for action in checkable_actions:
            action.setCheckable(True)
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

        action = CM.exec_(self.mapToGlobal(event.pos()))
        self.contextMenuActivated = False
        if action == sort_filename_desc:
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
        self.globals.control_panel.update()
        MW.update()

    def thumbnails_row_clicked(self, define_cursor_shape=False):
        THUMBNAIL_WIDTH = self.globals.THUMBNAIL_WIDTH
        folder = self.LibraryData().current_folder()
        images_list = folder.images_list
        r = self.rect()
        check_rect = r.adjusted(-THUMBNAIL_WIDTH, -THUMBNAIL_WIDTH, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
        cursor_pos = self.mapFromGlobal(QCursor().pos())
        s_rect = QRect(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
        for image_index, image_data in enumerate(images_list):
            thumbnail = image_data.get_thumbnail()
            offset = r.width()/2-THUMBNAIL_WIDTH/2+THUMBNAIL_WIDTH*(image_index-folder.current_index())
            d_rect = QRect(int(offset), 30, THUMBNAIL_WIDTH, THUMBNAIL_WIDTH)
            if check_rect.contains(d_rect.center()):
                if d_rect.contains(cursor_pos):
                    if define_cursor_shape:
                        return True
                    else:
                        self.LibraryData().jump_to_image(image_index)
                    break

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self.thumbnails_row_clicked()
        self.update()
        main_window = self.globals.main_window
        main_window.update()
        return

class Slideshow(QWidget):
    @classmethod
    def start_slideshow(cls):
        main_window = self.globals.main_window
        slideshow = Slideshow(main_window)
        desktop = QDesktopWidget()
        screen_geometry = desktop.screenGeometry(slideshow)
        slideshow.move(screen_geometry.x(), screen_geometry.y())
        slideshow.resize(screen_geometry.width(), screen_geometry.height())
        slideshow.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        slideshow.setAttribute(Qt.WA_TranslucentBackground)
        slideshow.show()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        c = QColor(Qt.black)
        painter.setBrush(QBrush(c))
        painter.setOpacity(self.opacity)
        painter.drawRect(self.rect())
        painter.setPen(QPen(QColor(Qt.white)))
        font = painter.font()
        font.setPixelSize(30)
        font.setWeight(1900)
        font.setFamily("Consolas")
        painter.setFont(font)
        painter.drawText(QRectF(self.rect()), Qt.AlignCenter, self.text)
        main_window = self.globals.main_window
        t = main_window.fit(
            time.time(),
            self.start_time,
            self.start_time+self.TRANSITION_DURATION,
            0.0,
            1.0
        )
        # t = min(t, 1.0)
        painter.setOpacity((1.0-t)*self.opacity)
        if self.p1:
            target = fit_rect_into_rect(self.p1.rect(), self.rect())
            painter.drawPixmap(target, self.p1, self.p1.rect())
        painter.setOpacity(t*self.opacity)
        if self.p2:
            target = fit_rect_into_rect(self.p2.rect(), self.rect())
            painter.drawPixmap(target, self.p2, self.p2.rect())
        painter.end()

    def __init__(self, *args, **kwargs):
        super().__init__( *args, **kwargs)
        self.timer = QTimer()
        self.timer.timeout.connect(self.inner_timer)
        self.timer_interval = 10
        self.timer.setInterval(self.timer_interval)
        self.timer.start()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        images_list = self.LibraryData().current_folder().images_list
        self.pairs = self.get_cycled_pairs(images_list)
        self.opacity = 0.001
        self.increase_opacity = True
        self.show_this()
        self.p1 = None
        self.p2 = None
        self.set_pics()
        main_window = self.globals.main_window
        self.TRANSITION_DURATION = main_window.slides_transition_duration
        self.DELAY_DURATION = main_window.slides_delay_duration

    def set_pics(self):
        pair = next(self.pairs)
        p1, p2, text = pair
        # ?????????????????? ????????????????
        self.p1 = QPixmap(p1.filepath)
        self.p2 = QPixmap(p2.filepath)
        # ?????????? ???????????????? ???????????? ?????????? ???????????????? ????????????????!
        self.start_time = time.time()
        self.text = text

    def inner_timer(self):
        self.update()

        SHOW_HIDE_SPEED = 0.03
        if self.increase_opacity:
            self.opacity += SHOW_HIDE_SPEED
        else:
            self.opacity -= SHOW_HIDE_SPEED
        self.opacity = min(max(0.0, self.opacity), 1.0)
        if self.opacity == 0.0 and not self.increase_opacity:
            self.close()
        # ??????????????, ???????? ???????? ???????????????? ??????????
        window_hwnd = int(self.winId())
        foreground_hwnd = ctypes.windll.user32.GetForegroundWindow()
        if foreground_hwnd != window_hwnd:
            self.close_this()

        if time.time() - self.start_time > (self.TRANSITION_DURATION + self.DELAY_DURATION):
            if self.increase_opacity:
                self.set_pics()
        self.setCursor(Qt.BlankCursor)

    def show_this(self):
        self.increase_opacity = True

    def close_this(self):
        self.increase_opacity = False

    def get_cycled_pairs(self, input_list):
        elements = input_list[:]
        l = len(elements)
        elements.insert(0, elements[0])
        pairs = []
        i = 1
        for n, el in enumerate(elements[:-1]):
            pairs.append((el, elements[n+1], f"{i}/{l}"))
            i += 1
        return itertools.cycle(pairs)

    def keyReleaseEvent(self, event):
        self.close_this()
