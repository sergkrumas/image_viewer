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


import time
import math
import sys
import subprocess
import os
import random
import traceback
import psutil
import ctypes
import itertools
import locale
import hashlib
import platform
import webbrowser
import json
import platform
import datetime
from functools import lru_cache
from collections import namedtuple
import argparse

import PIL
import pillow_avif
from PIL import Image

import win32con, win32api


DEFAULT_SVG_SCALE_FACTOR = 20

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

def execute_clickable_text(text):
    url = text.strip()
    if (url[1] == ":" and url[2] in ["\\", "/"]) or (url.startswith("file:/")):
        win32api.ShellExecute(0, "open", url, None, ".", 1)
    else:
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://"+ url
        webbrowser.open(url)

def get_file_size(filepath):
    try:
        return os.path.getsize(filepath)
    except Exception as e:
        return 0

def check_scancode_for(event, data):
    if data is None:
        return False
    code = event.nativeScanCode()
    if isinstance(data, str):
        data = data.upper()[0]
        return SCANCODES_FROM_LATIN_CHAR[data] == code
    elif isinstance(data, (list, tuple)):
        return any(SCANCODES_FROM_LATIN_CHAR[ch] == code for ch in data)

def get_cycled_pairs_slideshow(input_list):
    images_list = input_list[:]
    count = len(images_list)

    start_empty_image = namedtuple("ImageData", "filepath")
    start_empty_image.filepath = ""

    filename = os.path.basename(input_list[0].filepath)
    yield (start_empty_image, input_list[0], f"1/{count}\n{filename}")

    # переставляем последний элемент на первое место,
    # чтобы изначальная первая картинка показалась первой,
    # а не так, чтобы вторая стала первой согласно текущему алгоритму смены слайдов
    last_el = images_list.pop(-1)
    images_list.insert(0, last_el)

    # добавляем первый элемент в конец для получения всех паросочетаний,
    # которые можно потом зациклить
    images_list.append(images_list[0])
    pairs = []
    number = 1

    for index, im_data in enumerate(images_list[:-1]):
        next_im_data = images_list[index+1]
        filename = os.path.basename(next_im_data.filepath)
        pairs.append([im_data, next_im_data, f"{number}/{count}\n{filename}"])
        number += 1

    iterator = itertools.cycle(pairs)
    # skip one slide
    next(iterator)

    yield from iterator

def get_cycled_pairs(input_list):
    elements = input_list[:]
    count = len(elements)

    # добавляем первый элемент в конец для получения всех паросочетаний,
    # которые можно потом зациклить
    elements.append(elements[0])
    pairs = []
    number = 1
    for index, el in enumerate(elements[:-1]):
        pairs.append([el, elements[index+1], f"{number}/{count}"])
        number += 1
    return itertools.cycle(pairs)

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
    pm = QPixmap(0, 0)
    try:
        pm = PIL_to_QPixmap(Image.open(filepath))
    except PIL.UnidentifiedImageError:
        pass
    return pm

def create_pathsubfolders_if_not_exist(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

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

def md5_tuple_to_string(md5_tuple):
    return "".join([f'{part:08x}' for part in md5_tuple])

def compare_md5_strings(a1, a2):
    # вроде как в Python строки сравниваются по хэшам,
    # отсюда пришлось перестраховываться и проверять строки посимвольно
    for a1, a2 in zip(a1, a2):
        if a1 != a2:
            return False
    return True

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

def find_exe_file_in_opened_processes(exe_filename="chrome.exe"):
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
    CHROME_EXE = find_exe_file_in_opened_processes()
    if CHROME_EXE:
        args = [CHROME_EXE, filepath]
        subprocess.Popen(args)
    else:
        QMessageBox.critical(None, "Error", "Невозможно открыть в браузере.\nСначала откройте браузер Google Chrome!")

def show_in_folder_windows(filepath):
    os.system('explorer /select,"%s"' % filepath)

def fit_rect_into_rect(source_rect, input_rect, float_mode=False):
    # main_rect = input_rect or self.rect()
    if float_mode:
        main_rect = QRectF(input_rect)
        size_rect = QRectF(source_rect)
    else:
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
    result = QRectF(QPointF(center) - QPointF(new_width/2-1, new_height/2-1), QSizeF(new_width, new_height))
    if float_mode:
        return result
    else:
        return result.toRect()

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

def build_valid_rectF(p1, p2):
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
    return QRectF(QPointF(left, top), QPointF(right, bottom))

def is_apng_file_animated(filepath):
    result = False
    file_h = open(filepath, "rb")
    data_bytes = file_h.read()
    acTL = data_bytes.find(b"\x61\x63\x54\x4C")
    if acTL > 0: # find returns -1 if it cant find anything
        iDAT = data_bytes.find(b"\x49\x44\x41\x54")
        if acTL < iDAT:
            result = True
    file_h.close()
    return result

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
    rg2 = QRegion(QRectF(image_rect).toRect())
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
    points = QPolygonF([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # top right corner
    c = image_rect.topRight()
    c += QPoint(offset, -offset)
    f1 = c + QPoint(-85, 0)
    f2 = c + QPoint(0, 85)
    d1 = f1 + QPoint(-20, 40)
    d2 = f2 + QPoint(-40, 20)
    points = QPolygonF([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # bottom right corner
    c = image_rect.bottomRight()
    c += QPoint(offset, offset)
    f1 = c + QPoint(-85, 0)
    f2 = c + QPoint(0, -85)
    d1 = f1 + QPoint(-20, -40)
    d2 = f2 + QPoint(-40, -20)
    points = QPolygonF([d1, f1, c, f2, d2])
    painter.drawPolygon(points)
    # bottom left corner
    c = image_rect.bottomLeft()
    c += QPoint(-offset, offset)
    f1 = c + QPoint(85, 0)
    f2 = c + QPoint(0, -85)
    d1 = f1 + QPoint(20, -40)
    d2 = f2 + QPoint(40, -20)
    points = QPolygonF([d1, f1, c, f2, d2])
    painter.drawPolygon(points)

    painter.setClipping(False)

def draw_thirds(self, painter, image_rect):
    # draw lines
    painter.setPen(QPen(QColor(255, 255 ,255 ,25), 2))
    offset = image_rect.topLeft()
    w = image_rect.width()
    h = image_rect.height()
    # vertical
    painter.drawLine(QPointF(w/3, 0)+offset, QPointF(w/3, h)+offset)
    painter.drawLine(QPointF(w/3*2, 0)+offset, QPointF(w/3*2, h)+offset)
    # horizontal
    painter.drawLine(QPointF(0, h/3)+offset, QPointF(w, h/3)+offset)
    painter.drawLine(QPointF(0, h/3*2)+offset, QPointF(w, h/3*2)+offset)

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

def load_image_respect_orientation(filepath, highres_svg=False):
    if filepath.lower().endswith((".avif", ".heif", ".heic")):
        return read_AVIF_to_QPixmap(filepath)
    elif highres_svg:
        return load_svg(filepath)
    else:
        imgReader = QImageReader(filepath)
        imgReader.setAutoTransform(True)
        img = imgReader.read()
        return QPixmap().fromImage(img)

def load_svg(path, scale_factor=DEFAULT_SVG_SCALE_FACTOR):
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

def processAppEvents(update_only=True):
    app = QApplication.instance()
    if update_only:
        app.processEvents(QEventLoop.ExcludeUserInputEvents)
    else:
        app.processEvents()

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
            # если qtw1 тут не будет,
            # то невозможно будет скрыть окно
            # кликнув по иконке приложения через панель задач
            self.setWindowFlags(flags | qtw1)
        else:
            self.setWindowFlags(flags_not_frameless)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def mapped_cursor_pos(self):
        # этот маппинг нужен для того, чтобы всё работало
        # правильно и на втором экране тоже
        return self.mapFromGlobal(QCursor().pos())

    def cursor_in_rect(self, r):
        return r.contains(self.mapped_cursor_pos())

def get_bounding_points(points):
    MAX = sys.maxsize
    left = MAX
    right = -MAX
    top = MAX
    bottom = -MAX
    if not points:
        raise Exception("Empty list!")
    for p in points:
        left = min(int(p.x()), left)
        right = max(int(p.x()), right)
        top = min(int(p.y()), top)
        bottom = max(int(p.y()), bottom)
    return QPointF(left, top), QPointF(right, bottom)

def shift_list_to_became_first(_list, should_be_the_first_in_list, reverse=False):
    if reverse:
        _list = list(reversed(_list))
    index = _list.index(should_be_the_first_in_list)
    part1 = _list[0:index]
    part2 = _list[index:]
    part2.extend(part1)
    result = part2
    return result

def generate_info_pixmap(title, message, size=1000, no_background=False):

    pxm = QPixmap(size, size)
    p = QPainter()
    p.begin(pxm)

    p.setRenderHint(QPainter.HighQualityAntialiasing, True)
    p.fillRect(QRect(0, 0, size, size), QBrush(QColor(0, 0, 0)))

    p.setPen(Qt.NoPen)
    if not no_background:
        gradient = QLinearGradient(QPointF(0, size/2).toPoint(), QPoint(0, size))
        gradient.setColorAt(1.0, Qt.red)
        gradient.setColorAt(0.0, Qt.yellow)
        brush = QBrush(gradient)
        points = QPolygonF([
            QPoint(size//2, size//2),
            QPoint(size//2, size//2) + QPoint(size//40*3, size//8)*1.4,
            QPoint(size//2, size//2) + QPoint(-size//40*3, size//8)*1.4,
        ])
        pp = QPainterPath()
        pp.addPolygon(points)
        p.fillPath(pp, brush)
        p.setBrush(QBrush(Qt.black))
        p.drawRect(size//2-10, size//2-10 + 150, 20, 20)
        points = QPolygonF([
            QPoint(size//2+15, size//2-15 + 60),
            QPoint(size//2-15, size//2-15 + 60),
            QPoint(size//2-10, size//2+75 + 60),
            QPoint(size//2+10, size//2+75 + 60),
        ])
        p.drawPolygon(points)

    p.setPen(QColor(255, 0, 0))
    font = p.font()
    font.setPixelSize(50)
    font.setWeight(1900)
    p.setFont(font)
    r = QRectF(0, size/2, size, size/2).toRect()
    p.drawText(r, Qt.AlignCenter | Qt.TextWordWrap, title.upper())
    p.setPen(QColor(255, 0, 0))
    font = p.font()
    font.setPixelSize(20)
    font.setWeight(100)
    font.setFamily("Consolas")
    p.setFont(font)
    p.setPen(QColor(255, 255, 255))
    p.drawText(QRect(0, 0, size, size-50).adjusted(20, 20, -20, -20), Qt.TextWordWrap, message)

    p.end()
    return pxm
