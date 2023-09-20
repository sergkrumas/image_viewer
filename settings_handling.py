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


from on_windows_startup import (is_app_in_startup, add_to_startup, remove_from_startup)

class CustomSlider(QWidget):
    colorGrads = QLinearGradient(0, 0, 1, 0)
    colorGrads.setCoordinateMode(colorGrads.ObjectBoundingMode)
    xRatio = 1. / 6
    # rainbow gradient
    colorGrads.setColorAt(0, Qt.red)
    colorGrads.setColorAt(xRatio, Qt.magenta)
    colorGrads.setColorAt(xRatio * 2, Qt.blue)
    colorGrads.setColorAt(xRatio * 3, Qt.cyan)
    colorGrads.setColorAt(xRatio * 4, Qt.green)
    colorGrads.setColorAt(xRatio * 5, Qt.yellow)
    colorGrads.setColorAt(1, Qt.red)
    value_changed = pyqtSignal()
    def __init__(self, type, width, default_value):
        super().__init__()
        self.default_value = default_value
        self.value = self.default_value
        self.offset = 15
        self.changing = False
        self.control_width = 18
        self.type = type
        self.setFixedWidth(width)
        self.setFixedHeight(70)
        self.a = 0.0
        self.b = 1.0

    def resizeEvent(self, event):
        if self.type == "COLOR":
            self._inner_rect = self.rect()
            pixmap = QPixmap(self.rect().size())
            qp = QPainter(pixmap)
            qp.fillRect(self._inner_rect, self.colorGrads)
            qp.end()
            self.image = pixmap.toImage()

    def get_AB_rect(self):
        A, B = self.get_AB_points()
        offset = 3
        return QRect(A.toPoint() + QPoint(0, -offset), B.toPoint() + QPoint(0, offset))

    def get_AB_points(self):
        h = self.rect().height()/2
        A = QPointF(self.offset, h)
        B = QPointF(self.rect().width()-self.offset, h)
        return A, B

    def draw_bar(self, painter, color):
        A, B = self.get_AB_points()
        A += QPoint(0, 4)
        B += QPoint(0, 4)
        A1 = A + QPoint(0, -3)
        B1 = B + QPoint(0, -8)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        points = QPolygon([A.toPoint(), A1.toPoint(), B1.toPoint(), B.toPoint()])
        painter.drawPolygon(points)
        cr = QRect(
            B1.toPoint()-QPoint(4, 0),
            B.toPoint()+QPoint(8, 0)-QPoint(4, 1)
        )
        painter.drawEllipse(cr)

    def mask(self, painter, side):
        A, B = self.get_AB_points()
        center_point = A*(1-self.value) + B*self.value
        p = center_point.toPoint()
        if side == "a":
            r = QRect(QPoint(0,0), p)
            r.setBottom(self.rect().height())
        elif side == "b":
            p = QPoint(p.x(), 0)
            r = QRect(p, self.rect().bottomRight())
        painter.setClipRegion(QRegion(r))

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        # painter.fillRect(self.rect(), QColor("#303940"))
        if self.isEnabled():
            if self.type == "SCALAR":
                painter.setClipping(True)
                self.mask(painter, "b")
                self.draw_bar(painter, QColor("#1d2328"))
                self.mask(painter, "a")
                # draw bar
                # A, B = self.get_AB_points()
                # painter.setBrush(QBrush(QColor(self.color)))
                # painter.setPen(QPen(QColor(Qt.black), 1))
                # painter.drawLine(A, B)
                self.draw_bar(painter, Qt.gray)
                # no more mask
                painter.setClipping(False)
                painter.setPen(QPen(Qt.white))
                value = self.get_value()
                text = f"{value:.02f}"
                painter.drawText(self.rect(), Qt.AlignBottom, text)
            elif self.type == "COLOR":
                # gradient
                gradient_path = QPainterPath()
                rect = self.get_AB_rect()
                rect.adjust(-5, 0, 5, 0)
                gradient_path.addRoundedRect(QRectF(rect), 5, 5)
                painter.setClipping(True)
                painter.setClipRect(self.get_AB_rect())
                painter.fillPath(gradient_path, self.colorGrads)
                painter.setClipping(False)
                h = self.get_AB_rect().height()
                # white corner
                white_corner_path = QPainterPath(gradient_path)
                white_rect = self.get_AB_rect()
                white_rect = QRect(self.get_AB_rect().topLeft() - QPoint(h, 0), QSize(h, h))
                painter.setClipping(True)
                painter.setClipRect(white_rect)
                painter.fillPath(gradient_path, Qt.white)
                painter.setClipping(False)
                # black corner
                black_rect = self.get_AB_rect()
                black_rect = QRect(self.get_AB_rect().topRight(), QSize(h, h))
                painter.setClipping(True)
                painter.setClipRect(black_rect)
                painter.fillPath(gradient_path, Qt.black)
                painter.setClipping(False)
            # draw button
            path = QPainterPath()
            r = QRectF(self.build_hot_rect(float=True))
            path.addEllipse(r)
            painter.setPen(Qt.NoPen)
            offset = 5
            r2 = r.adjusted(offset, offset, -offset, -offset)
            path.addEllipse(r2)
            gradient = QRadialGradient(r.center()-QPoint(0, int(r.height()/3)), self.control_width)
            gradient.setColorAt(0, QColor(220, 220, 220))
            gradient.setColorAt(1, QColor(50, 50, 50))
            painter.setBrush(gradient)
            painter.drawPath(path)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawEllipse(r2)
            painter.setPen(QPen(QColor(100, 100, 150), 1))
            painter.drawEllipse(r.adjusted(1,1,-1,-1))
            if self.type == "SCALAR":
                color = QColor(220, 220, 220)
                painter.setBrush(color)
                painter.drawEllipse(r2)
            elif self.type == "COLOR":
                color = self.get_color()
                painter.setBrush(color)
                # r2.moveTop(r2.top()+10)
                # r2.adjust(1, 1, -1, -1)
                painter.drawEllipse(r2)
        painter.end()
        super().paintEvent(event)

    def get_color(self, value=None):
        parameter = value if value else self.value
        pos_x = int((self.image.width()-1)*parameter)
        if parameter == 0.0:
            return QColor(255, 255, 255)
        elif parameter == 1.0:
            return QColor(0, 0, 0)
        return QColor(self.image.pixel(pos_x, 1))

    def build_hot_rect(self, float=False):
        A, B = self.get_AB_points()
        center_point = A*(1-self.value) + B*self.value
        if not float:
            _w = int(self.control_width/2)
            return QRect(
                center_point.toPoint() - QPoint(_w, _w),
                QSize(self.control_width, self.control_width)
            )
        else:
            return QRectF(
                center_point - QPointF(self.control_width/2, self.control_width/2),
                QSizeF(self.control_width, self.control_width)
            )

    def build_click_rect(self):
        A, B = self.get_AB_points()
        a = A.toPoint() - QPoint(int(self.control_width/2), int(self.control_width/2))
        b = B.toPoint() + QPoint(int(self.control_width/2), int(self.control_width/2))
        return QRect(a, b)

    def do_changing(self, event):
        A, B = self.get_AB_points()
        P = event.pos()
        AB = B - A
        AP = P - A
        self.raw_value = dot(AP, AB)/dot(AB, AB)
        self.value = min(max(self.raw_value, 0.0), 1.0)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.do_changing(event)
            if self.build_hot_rect().contains(event.pos()):
                self.changing = True
        self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.changing:
                self.do_changing(event)
        self.update()
        self.value_changed.emit()
        super().mouseMoveEvent(event)

    def setRange(self, a, b):
        self.a = a
        self.b = b

    def get_value(self):
        out_value = self.a+(self.b-self.a)*self.value
        if not (self.a == 0.0 and self.b == 1.0):
            # out_value = int(out_value)
            out_value = round(out_value * 2) / 2
            out_value = max(self.a, out_value)
            out_value = min(self.b, out_value)
        return out_value

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.changing = False
            # for simple click
            if self.build_click_rect().contains(event.pos()):
                self.do_changing(event)
        self.update()
        self.value_changed.emit()
        super().mouseReleaseEvent(event)








class SettingsWindow(QWidget):

    def is_on(self, id):
        return self.checkboxes_widgets[id].isChecked()

    def get_value(self, id):
        return self.values_widgets[id].get_value()

    def on_change_handler(self):
        MW = self.globals.main_window
        cp = self.globals.control_panel
        cls = self.__class__
        for id, (current_val, text) in cls.checkboxes.items():
            setattr(MW, id, self.is_on(id))
            cls.checkboxes[id] = (self.is_on(id), text)
        for id, (current_val, range, text) in cls.values.items():
            setattr(MW, id, self.get_value(id))
            cls.values[id] = (self.get_value(id), range, text)
        self.load_settings_to_globals()
        MW.update()
        cp.update()

    @classmethod
    def load_settings_to_globals(cls):
        cls.globals.THUMBNAIL_WIDTH = int(cls.get_setting_value('thumbnail_width'))
        cls.globals.USE_GLOBAL_LIST_VIEW_HISTORY = cls.get_setting_value('use_global_view_history')

    @classmethod
    def settings_init(cls, main_window):
        for id, (current_value, text) in cls.checkboxes.items():
            setattr(main_window, id, current_value)
        for id, (current_value, params, text) in cls.values.items():
            setattr(main_window, id, current_value)

    @classmethod
    def filepath(cls):
        return os.path.join(os.path.dirname(__file__), "settings.json")

    @classmethod
    def get_setting_value(cls, setting_id):
        if setting_id in cls.checkboxes.keys():
            return cls.checkboxes[setting_id][0]
        if setting_id in cls.values.keys():
            return cls.values[setting_id][0]
        if setting_id in cls.strings.keys():
            return cls.strings[setting_id][0]
        raise Exception('no setting with such ID', setting_id)

    @classmethod
    def set_setting_value(cls, setting_id, setting_value):
        valid = False
        if setting_id in cls.checkboxes.keys():
            setting_data = list(cls.checkboxes[setting_id])
            setting_data[0] = setting_value
            cls.checkboxes[setting_id] = tuple(setting_data)
            valid = True
        if setting_id in cls.values.keys():
            setting_data = list(cls.values[setting_id])
            setting_data[0] = setting_value
            cls.values[setting_id] = tuple(setting_data)
            valid = True
        if setting_id in cls.strings.keys():
            setting_data = list(cls.strings[setting_id])
            setting_data[0] = setting_value
            cls.strings[setting_id] = tuple(setting_data)
            valid = True
        if valid:
            cls.store_to_disk()
        else:
            raise Exception('no setting with such ID', setting_id)

    @classmethod
    def load_from_disk(cls):
        if not os.path.exists(cls.filepath()):
            data = {}
        else:
            with open(cls.filepath(), "r", encoding="utf8") as file:
                try:
                    data = json.load(file)
                except:
                    data = {}
        if data:
            if "checkboxes" in data.keys():
                cls.checkboxes.update(data["checkboxes"])
            if "values" in data.keys():
                cls.values.update(data["values"])
            if "strings" in data.keys():
                cls.strings.update(data["strings"])
            # convert tuples to lists
            for key in cls.checkboxes.keys():
                cls.checkboxes[key] = list(cls.checkboxes[key])
            for key in cls.values.keys():
                cls.values[key] = list(cls.values[key])
            for key in cls.strings.keys():
                cls.strings[key] = list(cls.strings[key])
            # copy actual comments from program file, not from settings file
            for key in cls.checkboxes.keys():
                info = cls.backup_checkboxes[key][-1]
                data = cls.checkboxes[key]
                data[-1] = info
                cls.checkboxes[key] = data
            for key in cls.values.keys():
                info = cls.backup_values[key][-1]
                data = cls.values[key]
                data[-1] = info
                cls.values[key] = data
            for key in cls.strings.keys():
                info = cls.backup_strings[key][-1]
                data = cls.strings[key]
                data[-1] = info
            # apply settings to global variables
            cls.load_settings_to_globals()

    @classmethod
    def store_to_disk(cls):
        data = {
            "values": cls.values,
            "checkboxes": cls.checkboxes,
            "strings": cls.strings,
        }
        if os.path.exists(cls.filepath()):
            os.remove(cls.filepath())
        with open(cls.filepath(), 'w+', encoding="utf8") as file:
            json.dump(data, file, indent=True, ensure_ascii=False)

    checkboxes = {
        "show_thirds": (False, "Показывать трети"),
        "show_cyberpunk": (False, "Кибирпунк"),
        "show_image_center": (False, "Показывать центр"),
        "doubleclick_toggle": (True, "Переключение между оконным и полноэкранным режимом через двойной клик"),
        "show_secrets_at_zoom": (True, "Показывать рандомную вселенскую истину при сильном увеличении"),
        "autohide_control_panel": (True, "Автоматически скрывать панель с действиями"),
        "zoom_on_mousewheel": (True, "Мастабирование с помощью колёсика мыши (для навигации удерживать Ctrl)"),
        "show_backplate": (False, "Подложка под миниатюры и кнопки"),
        "show_fullscreen": (True, "Открываться в полноэкранном режиме"),
        "effects": (True, "Анимационные эффекты"),
        "draw_default_thumbnail": (True, "Рисовать дефолтную мелкую превьюшку, пока не сгенерировалась настоящая"),
        "hide_to_tray_on_close": (True, "Прятаться в трей при закрытии окна"),
        "show_console_output": (True, "Показывать поверх контента консольный вывод"),
        "use_global_view_history": (False, "Выключить историю просмотра для каждой папки отдельно и включить глобальную"),
        "hide_on_app_start": (False, "Прятать окно в трей на старте"),
        "show_image_metadata": (True, "Показывать метаданные изображения"),
        "show_noise_cells": (True, "Показывать анимированнную сетку"),
        "do_not_show_start_dialog": (True, "Запускать упрощённый режим сразу и без диалога"),
        "browse_images_only": (False, "Показывать только изображения"),
        "legacy_image_scaling": (False, "Активировать прежний способ масштабирования изображений (раньшебылолучше)"),        
    }
    values = {
        "viewer_mode_transparency": (0.7, (0.0, 1.0), "Прозрачность режима вьювера"),
        "library_mode_transparency": (0.9, (0.0, 1.0), "Прозрачность режима библиотеки"),
        "slides_transition_duration": (1.0, (0.1, 10.0), "Длительность перехода в сек (для слайдшоу)"),
        "slides_delay_duration": (2.0, (0.1, 240.0), "Длительность удержания в сек (для слайдшоу)"),
        "thumbnail_width": (50.0, (30.0, 100.0), "Размер миниатюр в режиме просмотра"),
    }

    strings = {
        "inframed_folderpath": (".", "Папка для кадрированных картинок (изменяется через Ctrl+R вне окна настроек)"),
    }

    isWindowVisible = False

    backup_checkboxes = dict(checkboxes)
    backup_values = dict(values)
    backup_strings = dict(strings)

    is_initialized = False

    STARTUP_CONFIG = (
        'ImageViewerLauncher',
        os.path.join(os.path.dirname(__file__), "viewer.pyw")
    )

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(SettingsWindow, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    @classmethod
    def center_if_on_screen(cls):
        if hasattr(cls, "instance"):
            window = cls.instance
            if window.isVisible():
                cls.pos_at_center(window)

    @classmethod
    def pos_at_center(cls, self):
        MW = self.globals.main_window
        cp = QDesktopWidget().availableGeometry().center()
        cp = MW.rect().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft() + QPoint(0, -50))
        self.activateWindow()

    def handle_windows_startup_chbx(self, sender):
        if sender.isChecked():
            add_to_startup(*self.STARTUP_CONFIG)
        else:
            remove_from_startup(self.STARTUP_CONFIG[0])

    def __init__(self, parent):
        if self.is_initialized:
            return
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # layout почему-то не задаёт высоту, приходится делать это вручную
        # и даже поправлять, когда настроек становится слишком много
        WINDOW_HEIGHT = 0
        WINDOW_HEIGHT += 40*len(self.checkboxes)
        WINDOW_HEIGHT += 50*len(self.values)
        WINDOW_HEIGHT += 40*len(self.strings)
        WINDOW_HEIGHT += 50 #buttons
        self.resize(1000, WINDOW_HEIGHT)
        # show at center
        SettingsWindow.pos_at_center(self)
        # ui init
        main_style = "font-size: 11pt; font-family: 'Consolas'"
        style = "color: white; " + main_style
        main_style_button = "font-size: 13pt; padding: 5px 0px;"
        checkbox_style = """
            QCheckBox {
                font-size: 11pt;
                font-family: 'Consolas';
                color: white;
                font-weight: normal;
            }
            QCheckBox::indicator:unchecked {
                background: gray;
            }
            QCheckBox::indicator:checked {
                background: green;
            }
            QCheckBox:checked {
                background-color: rgba(150, 150, 150, 50);
                color: rgb(100, 255, 100);
            }
            QCheckBox:unchecked {
                color: gray;
            }
        """
        main_layout = QVBoxLayout()
        label = QLabel()
        label.setText("Настройки")
        label.setFixedHeight(50)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(style)
        main_layout.addWidget(label)
        self.checkboxes_widgets = {}
        self.values_widgets = {}
        for id, (current_val, text) in self.checkboxes.items():
            chb = QCheckBox(text)
            self.checkboxes_widgets[id] = chb
            chb.setChecked(current_val)
            chb.setStyleSheet(checkbox_style)
            chb.stateChanged.connect(self.on_change_handler)
            main_layout.addWidget(chb)

        chb = QCheckBox("Запускать при старте Windows")
        self.checkboxes_widgets['run_on_windows_startup'] = chb
        chb.setChecked(is_app_in_startup(self.STARTUP_CONFIG[0]))
        chb.setStyleSheet(checkbox_style)
        chb.stateChanged.connect(lambda: self.handle_windows_startup_chbx(chb))
        main_layout.addWidget(chb)

        for id, (current_val, range, text) in self.values.items():
            a, b = range
            val = (current_val-a)/(b-a)
            sb = CustomSlider("SCALAR", 400, val)
            sb.setFixedHeight(50)
            sb.setRange(*range)
            self.values_widgets[id] = sb
            sb.value_changed.connect(self.on_change_handler)
            label = QLabel()
            label.setText(f"{text}:")
            label.setStyleSheet(style)
            layout = QHBoxLayout()
            layout.addWidget(label)
            layout.addWidget(sb)
            main_layout.addLayout(layout)
            main_layout.addSpacing(20)

        for id, (current_val, text) in self.strings.items():
            label = QLabel()
            label.setText(f"{text}: <b>{os.path.abspath(current_val)}</b>")
            label.setStyleSheet(style)
            layout = QHBoxLayout()
            layout.addWidget(label)
            main_layout.addLayout(layout)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_button_handler)
        save_button.setStyleSheet(main_style_button)
        exit_button = QPushButton("Закрыть")
        exit_button.clicked.connect(self.exit_button_handler)
        exit_button.setStyleSheet(main_style_button)
        buttons = QHBoxLayout()
        buttons.addWidget(save_button)
        buttons.addWidget(exit_button)
        main_layout.addSpacing(100)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # если задавать родителя в super().__init__(parent), то форма становится модальной.
        # Иначе в случае ниже - не становится модальной.
        # self.setParent(self.globals.main_window)         

        SettingsWindow.isWindowVisible = True

        self.is_initialized = True

    def exit_button_handler(self):
        self.hide()

    def save_button_handler(self):
        SettingsWindow.store_to_disk()
        self.hide()

    def hide(self):
        SettingsWindow.isWindowVisible = False
        super().hide()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setOpacity(0.9)
        painter.setBrush(QBrush(Qt.black))
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)
        painter.end()

    # pass для того, чтобы метод предка не вызывался
    # и событие не ушло в родительское окно
    def mousePressEvent(self, event):
        pass
    def mouseMoveEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        if event.nativeScanCode() == 0x29:
            self.hide()
