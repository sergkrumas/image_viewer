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

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

class CustomSlider(QWidget):

    TYPE_SCALAR = 0
    TYPE_COLOR = 1

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
        self.offset = 40
        self.changing = False
        self.control_width = 18
        self.type = type
        self.setFixedWidth(width)
        self.setFixedHeight(70)
        self.a = 0.0
        self.b = 1.0

    def resizeEvent(self, event):
        if self.type == self.TYPE_COLOR:
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
        left_offset = self.offset
        right_offset = 8 #self.offset
        A = QPointF(left_offset, h)
        B = QPointF(self.rect().width()-right_offset, h)
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
            if self.type == self.TYPE_SCALAR:
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
            elif self.type == self.TYPE_COLOR:
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
            if False: 
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
            if True:
                pass
            elif self.type == self.TYPE_SCALAR:
                color = QColor(220, 220, 220)
                painter.setBrush(color)
                painter.drawEllipse(r2)
            elif self.type == self.TYPE_COLOR:
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
        if not (self.a >= 0.0 and self.b <= 1.0):
            # custom range handling
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


    button_style = """QPushButton{
        font-size: 20px;
        color: #303940;
        text-align: center;
        border-radius: 5px;
        background: rgb(220, 220, 220);
        font-family: 'Consolas';
        font-weight: bold;
        border: 3px dashed #303940;
        padding: 5px;
        height: 40px;
    }
    QPushButton:hover{
        background-color: rgb(253, 203, 54);
        color: black;
    }
    QPushButton#exit, QPushButton#save{
        color: rgb(210, 210, 210);
        background-color: none;
        border: none;
    }
    QPushButton#save{
        color: rgb(70, 200, 70);
        background-color: rgba(50, 220, 50, 0.05);
    }
    QPushButton#exit{
        color: rgb(220, 70, 70);
        background-color: rgba(220, 50, 50, 0.05);
    }
    QPushButton#exit:hover{
        color: rgb(200, 0, 0);
        background-color: rgba(220, 50, 50, 0.1);
    }
    QPushButton#save:hover{
        color: rgb(0, 220, 0);
        background-color: rgba(50, 220, 50, 0.1);
    }
    """

    def is_on(self, id):
        return self.checkboxes_widgets[id].isChecked()

    def get_value(self, id):
        return self.values_widgets[id].get_value()

    def on_change_handler(self):
        MW = self.globals.main_window
        cp = self.globals.control_panel
        cls = self.__class__
        for id, params in cls.matrix.items():
            current_val = params[0]
            text = params[-1]
            if isinstance(current_val, bool):
                setattr(MW, f'STNG_{id}', self.is_on(id))
                cls.matrix[id] = (self.is_on(id), text)
            elif isinstance(current_val, float):
                range = params[1]
                setattr(MW, f'STNG_{id}', self.get_value(id))
                cls.matrix[id] = (self.get_value(id), range, text)
            elif isinstance(current_val, str):
                pass

        # page_transparency
        MW.update_current_page_transparency_value()

        self.load_settings_to_globals()
        MW.update_thumbnails_row_relative_offset(None, only_set=True)
        MW.update()

        # когда окно настроек открывается на стартовой странице cp будет None
        if cp is not None:
            cp.update()

    @classmethod
    def load_settings_to_globals(cls):
        cls.globals.THUMBNAIL_WIDTH = int(cls.get_setting_value('thumbnail_width'))
        cls.globals.USE_GLOBAL_LIST_VIEW_HISTORY = cls.get_setting_value('use_global_view_history')

    @classmethod
    def settings_init(cls, main_window):
        for id, (current_value, *_) in cls.matrix.items():
            setattr(main_window, f'STNG_{id}', current_value)

    @classmethod
    def filepath(cls):
        filepath = os.path.join(os.path.dirname(__file__), 'user_data', "settings.json")
        create_pathsubfolders_if_not_exist(os.path.dirname(filepath))
        return filepath

    @classmethod
    def get_setting_value(cls, setting_id):
        if setting_id in cls.matrix.keys():
            return cls.matrix[setting_id][0]
        raise Exception('no setting with such ID', setting_id)

    @classmethod
    def set_setting_value(cls, setting_id, setting_value):
        valid = False
        if setting_id in cls.matrix.keys():
            setting_data = list(cls.matrix[setting_id])
            setting_data[0] = setting_value
            cls.matrix[setting_id] = tuple(setting_data)
            valid = True
        if valid:
            cls.store_to_disk()
        else:
            raise Exception('no setting with such ID', setting_id)

    @classmethod
    def langs(cls):
        return {
            'en': _('English'),
            'ru': _('Russian'),

            'de': _('German'),
            'fr': _('French'),
            'it': _('Italian'),
            'es': _('Spanish'),
        }

    @classmethod
    def set_ui_language(cls):
        lang = cls.matrix['ui_lang'][0]
        allowed_langs = [ # according to /locales folder
            'en',
            'ru',

            'de',
            'fr',
            'it',
            'es',
        ]
        if lang not in allowed_langs:
            lang = 'en'

        if lang == 'en':
            # there's no special EN-locale, here we're using module `gettext` instead object class one
            __import__('builtins').__dict__['_'] = __import__('gettext').gettext
        else:
            el = __import__('gettext').translation('base', localedir='locales', languages=[lang])
            el.install() # copies el.gettext as _ to builtins for all app modules
            # SettingsWindow.actualize_matrix_data()

    @classmethod
    def langs_list(cls, lang_id):
        return cls.langs().get(lang_id)

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
            cls.matrix.update(data['settings'])

            cls.set_ui_language()

            # convert tuples to lists because tuples don't support item assignment
            for key in cls.matrix.keys():
                if key.startswith('---'):
                    cls.matrix[key] = ''.join(cls.matrix[key])
                else:
                    cls.matrix[key] = list(cls.matrix[key])

            SettingsWindow.actualize_matrix_data()

            # apply settings to global variables
            cls.load_settings_to_globals()

    @classmethod
    def actualize_matrix_data(cls):
        actual_settings_matrix = cls.generate_localized_matrix()
        # удаляем старые неактуальные ключи настроек
        for setting_key in list(cls.matrix.keys()):
            if setting_key not in actual_settings_matrix.keys():
                cls.matrix.pop(setting_key)
        # копирем актуальные переводы описаний настроек
        for setting_key in cls.matrix.keys():
            if setting_key in actual_settings_matrix.keys():
                if setting_key.startswith('---'):
                    cls.matrix[setting_key] = actual_settings_matrix[setting_key]
                else:
                    description = actual_settings_matrix[setting_key][-1]
                    data = cls.matrix[setting_key]
                    data[-1] = description
                    cls.matrix[setting_key] = data
        # обновляем минимально и максимально допустимые значения настроек типа float
        for setting_key, setting_data in cls.matrix.items():
            if setting_key in actual_settings_matrix.keys():
                default_value = setting_data[0]
                if isinstance(default_value, float):
                    stored_matrix_span = setting_data[1]
                    actual_matrix_span = list(actual_settings_matrix[setting_key][1])
                    if stored_matrix_span != actual_matrix_span:

                        s_data = cls.matrix[setting_key]
                        s_data[1] = actual_matrix_span
                        cls.matrix[setting_key] = s_data
                        msg = f"setting span mismatch fixed for {setting_key}, span loaded from file: {stored_matrix_span} --> actual span: {actual_matrix_span}"
                        print(msg)

    @classmethod
    def store_to_disk(cls):
        data = {
            'settings': cls.matrix,
        }
        if os.path.exists(cls.filepath()):
            os.remove(cls.filepath())
        with open(cls.filepath(), 'w+', encoding="utf8") as file:
            json.dump(data, file, indent=True, ensure_ascii=False)

    @staticmethod
    def generate_localized_matrix():

        matrix = {
            '---general': _('General'),
            'ui_lang': ('en', _('UI language')),
            'desaturated_corner_buttons_and_corner_menus': (False, _('Desaturated corner buttons and corner menus')),
            'run_on_windows_startup': (True, _('Run on Windows Startup')),
            'open_app_on_waterfall_page': (False, _('Open application on Waterfall page')),
            'do_not_show_start_dialog': (True, _('Supress start dialog and run lite mode')),
            'show_fullscreen': (True, _('Full-screen mode on application start')),
            'doubleclick_toggle': (True, _('Toggle between full-screen and window mode via double click')),
            'hide_to_tray_on_close': (True, _('Hide to tray on close')),
            'hide_on_app_start': (False, _('Hide to tray on app start')),
            'show_console_output': (True, _('Show standard (console) output overlay')),
            'effects': (True, _('Animated effects')),
            'show_noise_cells': (True, _('Show animated cells overlay')),
            'gamepad_dead_zone_radius': (0.1, (0.0, 0.9), _('Gamepad dead zone radius')),
            'show_gamepad_monitor': (False, _('Show gamepad monitor (for setting dead zone radius)')),
            'gamepad_move_stick_ease_in_expo_param': (2.0, (1.0, 4.0), _('Gamepad move stick easeInExpro parameter')),
            'gamepad_move_stick_speed': (20.0, (1.0, 50.0), _('Gamepad move stick speed')),


            '---viewerpage': _('Viewer page'),
            'animated_zoom': (False, _('Animated zoom')),
            'draw_control_panel_backplate': (False, _('Draw backplate for control panel')),
            'thumbnail_width': (50.0, (30.0, 100.0), _('Thumbnails size')),
            'zoom_on_mousewheel': (True, _('Enable mouse wheel to zoom and Ctrl+mouse wheel to navigate through image list')),
            'draw_default_thumbnail': (True, _('Show dummy-default thumbnail while generated one is not ready')),
            'show_thirds': (False, _('Show thirds')),
            'show_cyberpunk': (False, _('Cyberpunk frame')),
            'show_image_center': (False, _('Show image center')),
            'show_deep_secrets_at_zoom': (True, _('Show random secret when approaching high zoom level')),
            'autohide_control_panel': (True, _('Autohide control panel')),
            'use_global_view_history': (False, _('Enable global viewing history instead per-folder one')),
            'show_image_metadata': (True, _('Show image metadata')),
            'autosave_on_reordering': (True, _('Autosave thumbnails order to disk on reordering ones')),
            'browse_images_only': (False, _('Allow browsing image filetypes only')),
            'small_images_fit_factor': (0.0, (0.0, 1.0), _('Fit factor for small images')),


            '---waterfallpage': _('Waterfall page'),
            'waterfall_columns_number': (0.0, (0.0, 40.0), _('Desired number of Waterfall page columns')),
            'waterfall_grid_spacing': (8.0, (0.0, 50.0), _('Waterfall page grid spacing')),
            'waterfall_corner_radius': (20.0, (0.0, 250.0), _('Waterfall page corner radius')),

            '---boardpage': _('Board page'),
            'board_draw_origin_compass': (False, _('Show origin compass and zoom level')),
            'board_draw_canvas_origin': (False, _('Show board origin')),
            'board_vertical_items_layout': (False, _('Vertical items layout')),
            'board_draw_grid': (False, _('Show board grid')),
            'board_unloading': (False, _('Do unloading for images not shown in the viewer at the momoment')),
            'board_move_to_current_on_first_open': (True, _('Focus board viewport on the current image when board is first time opened')),
            'transform_widget_activation_area_size': (16.0, (12.0, 20.0), _('Scaling and rotating activation-spot size')),
            'use_cbor2_instead_of_json': (True, _('Enable CBOR2 instead JSON for writing board data')),
            'one_key_selected_items_scaling_factor': (20.0, (5.0, 300.0), _('Diagonal factor for one-key selected items scaling (in screen pixels)')),


            '---pagestransparent': _('Pages transparent setting for full-screen mode'),
            'viewer_page_transparency': (0.7, (0.0, 1.0), _('Viewer page transparent value')),
            'library_page_transparency': (0.9, (0.0, 1.0), _('Library page transparent value')),
            'board_page_transparency': (0.7, (0.0, 1.0), _('Board page transparent value')),
            'start_page_transparency': (0.9, (0.0, 1.0), _('Start page transparent value')),
            'waterfall_page_transparency': (0.9, (0.0, 1.0), _('Waterfall page transparent value')),


            '---viewerpageslideshow': _('Slideshow for Viewer page'),
            'slides_transition_duration': (1.0, (0.1, 10.0), _('Transition duration in seconds')),
            'slides_delay_duration': (2.0, (0.1, 240.0), _('Delay duration in seconds')),


            '---paths': _('Paths'),
            'inframed_folderpath': ('.', _('Folder to put framed images in (could be changed in dialog by pressing Ctrl+R)')),
        }
        return matrix

    matrix = generate_localized_matrix()

    isWindowVisible = False

    is_initialized = False

    STARTUP_CONFIG = (
        'ImageViewerLauncher',
        os.path.join(os.path.dirname(__file__), "viewer.pyw")
    )

    @classmethod
    def get_setting_span(cls, setting_id):
        data = cls.matrix[setting_id]
        value = data[0]
        if isinstance(value, (int, float)):
            span = data[1]
            return span
        else:
            return None

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

    @classmethod
    def set_new_lang_across_entire_app(cls, new_lang):
        # записываем в настройки
        cls.matrix['ui_lang'][0] = new_lang
        # задаём выбранную локаль по всему приложению
        cls.set_ui_language()
        # обновляем описания настроек в соответствии с языком
        cls.actualize_matrix_data()
        cls.store_to_disk()

        # пересоздаём элементы панели управления, чтобы подсказки обновились
        MW = cls.globals.main_window
        MW.recreate_control_panel(requested_page=MW.current_page)
        # пересоздаём окно настроек, чтобы обновился интерфейс
        def callback():
            if hasattr(SettingsWindow, 'instance') and SettingsWindow.isWindowVisible:
                SettingsWindow.isWindowVisible = False
                SettingsWindow.instance.close()
                del SettingsWindow.instance
                MW.open_settings_window()
                del cls.globals._timer

        millisecs_delay = 1
        cls.globals._timer = timer = QTimer.singleShot(millisecs_delay, callback)

    def __init__(self, parent):
        if self.is_initialized:
            return
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.resize(1500, 700)
        # show at center
        SettingsWindow.pos_at_center(self)
        # ui init
        main_style = "font-size: 11pt; font-family: 'Consolas';"
        style = "color: white; " + main_style
        style_partition_label = "color: black; background-color: gray; padding-left: 20px; " + main_style
        main_style_button = "font-size: 13pt; padding: 5px 0px;"
        combobox_style = """
            QComboBox {
                font-size: 11pt;
                font-family: 'Consolas';
                font-weight: bold;
                color: white;
                background-color: transparent;
                border: none;
            }
            QComboBox::drop-down {
                color: white;
                font-weight: normal;
            }
            QComboBox QAbstractItemView {
                background-color: #101010;
                color: white;
                font-weight: normal;
                selection-color: black;
                border: 1px solid #101010;
                selection-background-color: white;

            }
            QComboBox:on{
                padding-left: 10px;
            }
        """
        checkbox_style = """
            QCheckBox {
                font-size: 11pt;
                font-family: 'Consolas';
                color: white;
                font-weight: normal;
            }
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                /*background: gray;*/
                image: url(resources/switch_off.png);
            }
            QCheckBox::indicator:checked {
                /*background: green;*/
                image: url(resources/switch_on.png);
            }
            QCheckBox:checked {
                /* background-color: rgba(150, 150, 150, 50);*/
                color: rgb(100, 255, 100);
            }
            QCheckBox:unchecked {
                color: white;
            }
            QCheckBox:disabled {
                background: rgba(127, 127, 127, 10);
                color: rgba(127, 127, 127, 127);
            }
            QCheckBox::indicator:disabled {
                background: black;
            }
        """
        warn_style = """
            color: rgb(200, 40, 40);
            font-weight: 900;
            font-size: 11pt;
        """

        self.checkboxes_widgets = {}
        self.values_widgets = {}

        self.scroll_area = QScrollArea()
        self.scroll_area.verticalScrollBar().setStyleSheet("""
            QScrollBar {
                border-radius: 5px;
                background: rgb(40, 50, 60);
            }
            QScrollBar:vertical {
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle {
                background: rgb(210, 210, 210);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                width: 10px;
                min-height: 10px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                 background: transparent;
            }
            QScrollBar::sub-line:vertical {
                 background: transparent;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                 background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                 background: transparent;
            }

            """)

        self.scroll_area.setStyleSheet("""
            QScrollArea:vertical {
                height: 15px;
                background-color: transparent;
                border: none;
            }
            """)

        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("QWidget#central {background-color: transparent;}")
        self.central_widget.setObjectName("central")
        central_widget_layout = QVBoxLayout()

        for index, (id, params) in enumerate(self.matrix.items()):

            current_val = params[0]
            text = params[-1]

            if id.startswith('---'):
                label = QLabel()
                text = ''.join(params).upper()
                label.setText(f"<b>{text}</b>")
                label.setStyleSheet(style_partition_label)
                layout = QVBoxLayout()
                layout.addWidget(label)
                if index != 0:
                    central_widget_layout.addSpacing(40)
                central_widget_layout.addLayout(layout)
                central_widget_layout.addSpacing(10)

            elif id == 'ui_lang':
                lang_combo_box = QComboBox()

                current_lang_key = SettingsWindow.matrix['ui_lang'][0]
                for n, (lang_key, lang_name) in enumerate(self.langs().items()):
                    icon = getattr(self.globals, f'lang_{lang_key}_icon')
                    lang_combo_box.addItem(icon, lang_name)
                    lang_combo_box.setItemData(n, lang_key)
                    if lang_key == current_lang_key:
                        lang_combo_box.setCurrentIndex(n)

                lang_combo_box.setStyleSheet(combobox_style)

                label = QLabel()
                label.setText(_("UI language"))
                label.setStyleSheet(style)
                warn_label = QLabel()
                warn_label.setText(_("Restart app to take effect across the entire app!"))
                warn_label.setStyleSheet(warn_style)
                warn_label.setVisible(False)
                # warn_label.setAlignment(Qt.AlignRight)

                layout = QHBoxLayout()
                layout.addWidget(label)
                layout.addWidget(lang_combo_box)
                layout_main = QVBoxLayout()
                layout_main.addLayout(layout)
                layout_main.addWidget(warn_label)

                central_widget_layout.addLayout(layout_main)
                central_widget_layout.addSpacing(10)

                def lang_combobox_index_changed_callback(index):
                    new_lang = lang_combo_box.itemData(index)
                    SettingsWindow.set_new_lang_across_entire_app(new_lang)
                    warn_label.setVisible(True)

                lang_combo_box.currentIndexChanged.connect(lang_combobox_index_changed_callback)

            elif isinstance(current_val, bool):
                chb = QCheckBox(text)
                self.checkboxes_widgets[id] = chb
                chb.setStyleSheet(checkbox_style)
                if id == 'run_on_windows_startup':
                    chb.setChecked(is_app_in_startup(self.STARTUP_CONFIG[0]))
                    chb.stateChanged.connect(lambda: self.handle_windows_startup_chbx(chb))
                else:
                    chb.setChecked(current_val)
                    chb.stateChanged.connect(self.on_change_handler)
                central_widget_layout.addWidget(chb)

                if id == 'show_gamepad_monitor':
                    chb.stateChanged.connect(lambda state, x=chb: self.handle_show_gamepad_monitor_chbox(state, x))

                # if id == 'open_app_on_waterfall_page':
                #     chb.stateChanged.connect(lambda state, x=chb: self.handle_child_checkboxes(state, x))

                # if id == 'enter_modal_viewer_mode_on_app_start':
                #     # на старте надо определится с видом чекбокса в зависимости от значения радителя
                #     self.handle_child_checkboxes(None, self.checkboxes_widgets['open_app_on_waterfall_page'])


            elif isinstance(current_val, float):
                range_ = params[1]
                a, b = range_
                val = (current_val-a)/(b-a)
                sb = CustomSlider(CustomSlider.TYPE_SCALAR, 400, val)
                sb.setFixedHeight(20)
                sb.setRange(*range_)
                self.values_widgets[id] = sb
                sb.value_changed.connect(self.on_change_handler)
                label = QLabel()
                label.setText(f"{text}:")
                label.setStyleSheet(style)
                layout = QHBoxLayout()
                layout.addWidget(label)
                layout.addWidget(sb)
                central_widget_layout.addLayout(layout)

                if id == 'small_images_fit_factor':
                    sb.value_changed.connect(self.on_small_images_fit_factor_change)

                elif id == 'gamepad_dead_zone_radius':
                    sb.value_changed.connect(lambda x=sb: self.on_gamepad_dead_zone_radius_change(x))

            elif isinstance(current_val, str):
                label = QLabel()
                label.setText(f"{text}: <b>{os.path.abspath(current_val)}</b>")
                label.setStyleSheet(style)
                layout = QHBoxLayout()
                layout.addWidget(label)
                central_widget_layout.addLayout(layout)


        self.central_widget.setLayout(central_widget_layout)

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.central_widget)
        self.scroll_area.setMaximumHeight(700)


        main_layout = QVBoxLayout()

        head_label = QLabel()
        head_label.setText(_("Settings"))
        head_label.setFixedHeight(50)
        head_label.setAlignment(Qt.AlignCenter)
        head_label.setStyleSheet(style + '; font-weight: bold;')
        main_layout.addWidget(head_label)

        main_layout.addWidget(self.scroll_area)

        save_button = QPushButton(_("Save and close"))
        save_button.clicked.connect(self.save_button_handler)
        save_button.setStyleSheet(main_style_button)
        exit_button = QPushButton(_("Close"))
        exit_button.clicked.connect(self.exit_button_handler)
        exit_button.setStyleSheet(main_style_button)

        save_button.setObjectName("save")
        exit_button.setObjectName("exit")
        for button in [save_button, exit_button]:
            button.setStyleSheet(self.button_style)
            button.setCursor(Qt.PointingHandCursor)
        buttons = QHBoxLayout()
        buttons.addWidget(save_button)
        buttons.addWidget(exit_button)
        main_layout.addSpacing(5)
        main_layout.addLayout(buttons)

        self.setLayout(main_layout)

        # если задавать родителя в super().__init__(parent), то форма становится модальной.
        # Иначе в случае ниже - не становится модальной.
        # self.setParent(self.globals.main_window)

        SettingsWindow.isWindowVisible = True

        self.is_initialized = True

    def on_small_images_fit_factor_change(self):
        MW = type(self).globals.main_window
        if MW.is_viewer_page_active():
            MW.restore_image_transformations()

    def on_gamepad_dead_zone_radius_change(self, sb):
        MW = type(self).globals.main_window
        if MW.gamepad_thread_instance is not None:
            MW.gamepad_thread_instance.dead_zone_radius = sb.get_value()

    def handle_show_gamepad_monitor_chbox(self, state, chb):
        MW = type(self).globals.main_window
        if MW.gamepad_thread_instance is not None:
            MW.gamepad_thread_instance.pass_deadzone_values = chb.isChecked()

    def handle_child_checkboxes(self, state, chb):
        MW = type(self).globals.main_window
        self.checkboxes_widgets['enter_modal_viewer_mode_on_app_start'].setEnabled(chb.isChecked())
        self.update()

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




# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
