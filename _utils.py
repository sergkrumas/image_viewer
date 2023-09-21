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

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import  QSvgRenderer

import PIL
import pillow_avif

import time, math, sys, subprocess, os, random, \
     traceback, psutil, ctypes, itertools, locale,\
     hashlib, platform, json, platform, datetime, argparse
from functools import lru_cache
from PIL import Image
from collections import namedtuple

import win32con, win32api

SCANCODES_FROM_LATIN_CHAR = {
    "Q": 16,
    "W": 17,
    "E": 18,
    "R": 19,
    "T": 20,
    "Y": 21,
    "U": 22,
    "I": 23,
    "O": 24,
    "P": 25,
    "A": 30,
    "S": 31,
    "D": 32,
    "F": 33,
    "G": 34,
    "H": 35,
    "J": 36,
    "K": 37,
    "L": 38,
    "Z": 44,
    "X": 45,
    "C": 46,
    "V": 47,
    "B": 48,
    "N": 49,
    "M": 50,
    "[": 26,
    "]": 27,
}

def PIL_to_QPixmap(im):
    if im.mode == "RGB":
      r, g, b = im.split()
      im = Image.merge("RGB", (b, g, r))
    elif  im.mode == "RGBA":
      r, g, b, a = im.split()
      im = Image.merge("RGBA", (b, g, r, a))
    elif im.mode == "L":
      im = im.convert("RGBA")
    im2 = im.convert("RGBA")
    data = im2.tobytes("raw", "RGBA")
    qim = QImage(data, im.size[0], im.size[1], QImage.Format_ARGB32)
    pixmap = QPixmap.fromImage(qim)
    return pixmap

def read_AVIF_to_QPixmap(filepath):
    # `pip install pillow-avif-plugin` required for reading
    return PIL_to_QPixmap(Image.open(filepath))

def get_index_centered_list(listed_data, value_in_list_to_start_from):
    if len(listed_data) == 0:
        return []
    if value_in_list_to_start_from not in listed_data:
        return listed_data
    right_or_left_side = True
    index = listed_data.index(value_in_list_to_start_from)
    yield value_in_list_to_start_from # first element
    right_index = index + 1
    left_index = index - 1
    while (right_index < len(listed_data) or left_index > -1):
        if right_or_left_side:
            if right_index < len(listed_data):
                yield listed_data[right_index]
                right_index += 1
            else:
                yield listed_data[left_index]
                left_index -= 1
        else:
            if left_index > -1:
                yield listed_data[left_index]
                left_index -= 1
            else:
                yield listed_data[right_index]
                right_index += 1
        right_or_left_side = not right_or_left_side

def check_scancode_for(event, data):
    if data is None:
        return False
    code = event.nativeScanCode()
    if isinstance(data, str):
        data = data.upper()[0]
        return SCANCODES_FROM_LATIN_CHAR[data] == code
    elif isinstance(data, (list, tuple)):
        return any(SCANCODES_FROM_LATIN_CHAR[ch] == code for ch in data)

from win32com.shell import shell, shellcon
def delete_to_recyclebin(filename):
    if not os.path.exists(filename):
        return True
    res = shell.SHFileOperation((
        0,
        shellcon.FO_DELETE,
        filename,
        None,
        shellcon.FOF_SILENT | shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION,
        None,
        None
    ))
    if not res[1]:
        if os.path.exists(filename):
            os.system('del "%s"' % filename)


def convert_md5_to_int_tuple(md5_str):
    md5_by_parts = []
    for i in range(4):
        part_str = md5_str[i*8:i*8+8]
        part_value = int(part_str, 16)
        md5_by_parts.append(part_value)
    return tuple(md5_by_parts)

def generate_md5(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    md5_str = hash_md5.hexdigest()
    return md5_str, convert_md5_to_int_tuple(md5_str)

def read_meta_info(filepath):
    try:
        im = PIL.Image.open(filepath)
    except PIL.UnidentifiedImageError:
        return {}
    im.load()
    data = {}
    if im.info:
        data = dict(im.info)
    del im
    return data

def find_browser_exe_file(exe_filename="chrome.exe"):
    import psutil
    exe_filepath = None
    for proc in psutil.process_iter():
        try:
            if proc.name() == exe_filename:
                exe_filepath = proc.cmdline()[0]
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        except Exception as e:
            pass
    return exe_filepath

def open_in_google_chrome(filepath):
    CHROME_EXE = find_browser_exe_file()
    if CHROME_EXE:
        args = [CHROME_EXE, filepath]
        subprocess.Popen(args)
    else:
        QMessageBox.critical(None, "Error", "Невозможно открыть в браузере.\nСначала откройте браузер Google Chrome!")

def show_in_folder_windows(filepath):
    os.system('explorer /select,"%s"' % filepath)

def fit_rect_into_rect(source_rect, input_rect):
    # main_rect = input_rect or self.rect()
    main_rect = QRect(input_rect)
    size_rect = QRect(source_rect)
    w = size_rect.width()
    h = size_rect.height()
    nw = size_rect.width()
    nh = size_rect.height()
    if size_rect.width() == 0 or size_rect.height() == 0:
        return source_rect
    if size_rect.width() > main_rect.width() or size_rect.height() > main_rect.height():
        # если контент не влазит на экран
        image_scale1 = main_rect.width()/size_rect.width()
        image_scale2 = main_rect.height()/size_rect.height()
        new_width1 = w*image_scale1
        new_height1 = h*image_scale1
        new_width2 = w*image_scale2
        new_height2 = h*image_scale2
        nw = min(new_width1, new_width2)
        nh = min(new_height1, new_height2)
    elif size_rect.width() < main_rect.width() or size_rect.height() < main_rect.height():
        # если контент меньше экрана
        image_scale1 = main_rect.width()/size_rect.width()
        image_scale2 = main_rect.height()/size_rect.height()
        new_width1 = w*image_scale1
        new_height1 = h*image_scale1
        new_width2 = w*image_scale2
        new_height2 = h*image_scale2
        nw = min(new_width1, new_width2)
        nh = min(new_height1, new_height2)
    center = main_rect.center()
    new_width = int(nw)
    new_height = int(nh)
    return QRectF(QPointF(center) - QPointF(new_width/2-1, new_height/2-1), QSizeF(new_width, new_height)).toRect()

def build_valid_rect(p1, p2):
    MAX = sys.maxsize
    left = MAX
    right = -MAX
    top = MAX
    bottom = -MAX
    for p in [p1, p2]:
        left = min(p.x(), left)
        right = max(p.x(), right)
        top = min(p.y(), top)
        bottom = max(p.y(), bottom)
    return QRect(QPoint(int(left), int(top)), QPoint(int(right), int(bottom)))

def is_webp_file_animated(filepath):
    result = False
    file_h = open(filepath, "rb")
    file_h.seek(12)
    if file_h.read(4) == b"VP8X":
        file_h.seek(20)
        byte = file_h.read(1)
        if (ord(byte)>>1) & 1:
            result = True
        else:
            result = False
    file_h.close()
    return result

def draw_cyberpunk_corners(self, painter, image_rect):
    painter.setClipping(True)
    rg1 = QRegion(self.rect())
    rg2 = QRegion(image_rect)
    rg3=rg1.subtracted(rg2)
    painter.setClipRegion(rg3)

    # draw corners
    max_alpha = 200.0
    value = min(image_rect.height(), image_rect.width())
    max_alpha = max_alpha * min(max((value-200)/500, 0.0), 1.0)
    color = QColor(255, 255, 255, int(max_alpha))
    brush = QBrush(color)
    painter.setPen(Qt.NoPen)
    painter.setBrush(brush)
    offset = 4
    # top left corner
    c = image_rect.topLeft()
    c += QPoint(-offset, -offset)
    f1 = c + QPoint(85, 0)
    f2 = c + QPoint(0, 85)
    d1 = f1 + QPoint(20, 40)
    d2 = f2 + QPoint(40, 20)
    points = QPolygon([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # top right corner
    c = image_rect.topRight()
    c += QPoint(offset, -offset)
    f1 = c + QPoint(-85, 0)
    f2 = c + QPoint(0, 85)
    d1 = f1 + QPoint(-20, 40)
    d2 = f2 + QPoint(-40, 20)
    points = QPolygon([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # bottom right corner
    c = image_rect.bottomRight()
    c += QPoint(offset, offset)
    f1 = c + QPoint(-85, 0)
    f2 = c + QPoint(0, -85)
    d1 = f1 + QPoint(-20, -40)
    d2 = f2 + QPoint(-40, -20)
    points = QPolygon([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # bottom left corner
    c = image_rect.bottomLeft()
    c += QPoint(-offset, offset)
    f1 = c + QPoint(85, 0)
    f2 = c + QPoint(0, -85)
    d1 = f1 + QPoint(20, -40)
    d2 = f2 + QPoint(40, -20)
    points = QPolygon([d1, f1, c, f2, d2])
    painter.drawPolygon(points)

    painter.setClipping(False)

def draw_thirds(self, painter, image_rect):
    # draw lines
    painter.setPen(QPen(QColor(255, 255 ,255 ,25), 2))
    offset = image_rect.topLeft()
    w = image_rect.width()
    h = image_rect.height()
    # vertical
    painter.drawLine(QPoint(w//3, 0)+offset, QPoint(w//3, h)+offset)
    painter.drawLine(QPoint(w//3*2, 0)+offset, QPoint(w//3*2, h)+offset)
    # horizontal
    painter.drawLine(QPoint(0, h//3)+offset, QPoint(w, h//3)+offset)
    painter.drawLine(QPoint(0, h//3*2)+offset, QPoint(w, h//3*2)+offset)

@lru_cache(maxsize=8)
def generate_gradient(type, shadow_size, color1_hex, color2_hex):
    # hex colors for hashability of the function
    color1 = QColor(color1_hex)
    color2 = QColor(color2_hex)
    # https://doc.qt.io/qtforpython-5/PySide2/QtGui/QGradient.html
    # https://doc.qt.io/qtforpython-5/PySide2/QtGui/QConicalGradient.html
    # https://doc.qt.io/qtforpython-5/PySide2/QtGui/QRadialGradient.html
    # https://doc.qt.io/qt-5/qlineargradient.html
    gradients = [
        ("top_left",        (shadow_size, shadow_size), ),
        ("bottom_right",    (shadow_size, shadow_size), ),
        ("bottom_left",     (shadow_size, shadow_size), ),
        ("top_right",       (shadow_size, shadow_size), ),
        ("top",             (1, shadow_size),           ),
        ("bottom",          (1, shadow_size),           ),
        ("left",            (shadow_size, 1),           ),
        ("right",           (shadow_size, 1),           ),
    ]
    current_gradient_info = None
    for gradient_info in gradients:
        if type == gradient_info[0]:
            current_gradient_info = gradient_info
    if not current_gradient_info:
        raise
    size = current_gradient_info[1]
    gradient_type_pxm = QPixmap(*size)
    gradient_type_pxm.fill(Qt.transparent)
    p = QPainter()
    p.begin(gradient_type_pxm)
    p.setRenderHint(QPainter.HighQualityAntialiasing, True)
    if type == "top_left":
        gradient = QRadialGradient(QPoint(shadow_size, shadow_size), shadow_size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    if type == "top_right":
        gradient = QRadialGradient(QPoint(0, shadow_size), shadow_size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    if type == "bottom_right":
        gradient = QRadialGradient(QPoint(0, 0), shadow_size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    if type == "bottom_left":
        gradient = QRadialGradient(QPoint(shadow_size, 0), shadow_size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    if type == "top":
        gradient = QLinearGradient(0, 0, *size)
        gradient.setColorAt(1, color1)
        gradient.setColorAt(0, color2)
    if type == "bottom":
        gradient = QLinearGradient(0, 0, *size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    if type == "left":
        gradient = QLinearGradient(0, 0, *size)
        gradient.setColorAt(1, color1)
        gradient.setColorAt(0, color2)
    if type == "right":
        gradient = QLinearGradient(0, 0, *size)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
    p.fillRect(QRect(0, 0, *size), gradient)
    p.end()
    del p
    return gradient_type_pxm

def draw_shadow(self, painter, rect, shadow_size, color1_hex, color2_hex):
    if not rect:
        return
    sr = rect
    # rectangle sides
    gradient_pxm = generate_gradient("top", shadow_size, color1_hex, color2_hex)
    top_left = sr.topLeft() + QPoint(1, -shadow_size)
    bottom_right = sr.topRight() + QPoint(-1, 0)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("bottom", shadow_size, color1_hex, color2_hex)
    top_left = sr.bottomLeft() + QPoint(1, 0)
    bottom_right = sr.bottomRight() + QPoint(-1, -shadow_size)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("left", shadow_size, color1_hex, color2_hex)
    top_left = sr.topLeft() + QPoint(-shadow_size, 1)
    bottom_right = sr.bottomLeft() + QPoint(0, -1)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("right", shadow_size, color1_hex, color2_hex)
    top_left = sr.topRight() + QPoint(0, 1)
    bottom_right = sr.bottomRight() + QPoint(shadow_size, -1)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    # rectangle corners
    gradient_pxm = generate_gradient("top_left", shadow_size, color1_hex, color2_hex)
    top_left = sr.topLeft() + QPoint(-shadow_size, -shadow_size)
    bottom_right = sr.topLeft() + QPoint(0, 0)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("top_right", shadow_size, color1_hex, color2_hex)
    top_left = sr.topRight() + QPoint(0, -shadow_size)
    bottom_right = sr.topRight() + QPoint(shadow_size, 0)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("bottom_right", shadow_size, color1_hex, color2_hex)
    top_left = sr.bottomRight() + QPoint(0, 0)
    bottom_right = sr.bottomRight() + QPoint(shadow_size, shadow_size)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

    gradient_pxm = generate_gradient("bottom_left", shadow_size, color1_hex, color2_hex)
    top_left = sr.bottomLeft() + QPoint(-shadow_size, 0)
    bottom_right = sr.bottomLeft() + QPoint(0, -shadow_size)
    target = QRectF(top_left, bottom_right)
    painter.drawPixmap(target, gradient_pxm, QRectF(gradient_pxm.rect()))

def webRGBA(qcolor_value):
    return "#{:02x}{:02x}{:02x}{:02x}".format(
                qcolor_value.alpha(),
                qcolor_value.red(),
                qcolor_value.green(),
                qcolor_value.blue(),
    )

def dot(p1, p2):
    return p1.x()*p2.x() + p1.y()*p2.y()

def draw_grid(self, painter):
    if not hasattr(self, "image_scale"):
        return
    LINES_INTERVAL = int(300 * self.image_scale)
    r = self.rect().adjusted(-LINES_INTERVAL*2, -LINES_INTERVAL*2, LINES_INTERVAL*2, LINES_INTERVAL*2)
    value = self.fit(self.image_scale, 0.5, 1.0, 0, 50)
    pen = QPen(QColor(0, 255, 0, value), 1)
    painter.setPen(pen)
    icp = self.image_center_position
    offset = QPoint(icp.x() % LINES_INTERVAL, icp.y() % LINES_INTERVAL)
    for i in range(r.left(), r.right(), LINES_INTERVAL):
        painter.drawLine(offset+QPoint(i, r.top()), offset+QPoint(i, r.bottom()))
    for i in range(r.top(), r.bottom(), LINES_INTERVAL):
        painter.drawLine(offset+QPoint(r.left(), i), offset+QPoint(r.right(), i))

def fit(t, input_a, input_b, output_a, output_b):
    t = max(input_a, min(input_b, t))
    factor = (t-input_a)/(input_b-input_a)
    return output_a + factor*(output_b-output_a)

def fit01(t, output_a, output_b):
    return fit(t, 0.0, 1.0, output_a, output_b)

def load_image_respect_orientation(filepath):
    if filepath.lower().endswith((".avif", ".heif", ".heic")):
        return read_AVIF_to_QPixmap(filepath)
    else:
        imgReader = QImageReader(filepath)
        imgReader.setAutoTransform(True)
        img = imgReader.read()
        return QPixmap().fromImage(img)

def load_svg(path, scale_factor=20):
    renderer =  QSvgRenderer(path)
    size = renderer.defaultSize()
    rastered_image = QImage(
        size.width()*scale_factor,
        size.height()*scale_factor,
        QImage.Format_ARGB32
    )
    rastered_image.fill(Qt.transparent)
    painter = QPainter(rastered_image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(rastered_image)

def processAppEvents(_all=False):
    app = QApplication.instance()
    if _all:
        app.processEvents()
    else:
        app.processEvents(QEventLoop.ExcludeUserInputEvents)

class UtilsMixin:
    def set_window_style(self):
        qtw1 = Qt.WindowMinimizeButtonHint
        qtw2 = Qt.WindowMaximizeButtonHint
        qtw3 = Qt.WindowCloseButtonHint
        flags_not_frameless = qtw1 | qtw2 | qtw3
        flags = flags_not_frameless | Qt.FramelessWindowHint
        if self.stay_on_top:
            flags = flags | Qt.WindowStaysOnTopHint
            flags_not_frameless = flags_not_frameless | Qt.WindowStaysOnTopHint
        if self.frameless_mode:
            self.setWindowFlags(flags)
        else:
            self.setWindowFlags(flags_not_frameless)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mapped_cursor_pos(self):
        # этот маппинг нужен для того, чтобы всё работало
        # правильно и на втором экране тоже
        return self.mapFromGlobal(QCursor().pos())

    def cursor_in_rect(self, r):
        return r.contains(self.mapped_cursor_pos())
