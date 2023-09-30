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
import math

class Vars():

    Globals = None
    LibraryData = None



def get_pureref_boards_root():
    rootpath = os.path.join(os.path.dirname(__file__), "user_data", Vars.Globals.PUREREF_BOARDS_ROOT)
    create_pathsubfolders_if_not_exist(rootpath)
    return rootpath

def load_pureref_boards(libdata):

    Vars.Globals = libdata.globals
    Vars.LibraryData = libdata

    if os.path.exists(get_pureref_boards_root()):
        print("loading pureRef boards data")


def init(self):
    self.pureref_mode = False

    self.board_origin = self.get_center_position()
    self.board_scale_x = 1.0
    self.board_scale_y = 1.0

    self.board_translating = True


def draw_stub(self, painter):
    font.setPixelSize(250)
    font.setWeight(1900)
    painter.setFont(font)
    pen = QPen(QColor(180, 180, 180), 1)
    painter.setPen(pen)
    painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, "PUREREF BOARDS")


def calculate_text_rect(font, max_rect, text, alignment):
    pic = QPicture()
    painter = QPainter(pic)
    painter.setFont(font)
    text_rect = painter.drawText(max_rect, alignment, text)
    painter.end()
    del painter
    del pic
    return text_rect

def draw(self, painter):
    old_font = painter.font()
    font = QFont(old_font)

    draw_main(self, painter)
    # draw_stub(self, painter)

    painter.setFont(old_font)

def draw_wait_label(self, painter):
    font = painter.font()
    font.setPixelSize(100)
    font.setWeight(1900)
    painter.setFont(font)
    max_rect = self.rect()
    alignment = Qt.AlignCenter

    painter.setPen(QPen(QColor(240, 10, 50, 100), 1))
    text = "  ".join("ПОДОЖДИ")
    text_rect = calculate_text_rect(font, max_rect, text, alignment)
    text_rect.moveCenter(self.rect().center() + QPoint(0, -80))
    painter.drawText(text_rect, alignment, text)

def prepare_board(self, folder_data):

    offset = QPointF(0, 0)
    for image_data in folder_data.images_list:
        if image_data.is_supported_filetype:
            image_data.board_scale = 1.0
            image_data.board_position = offset + QPointF(image_data.source_width, image_data.source_height)/2
            offset += QPointF(image_data.source_width, 0)

    folder_data.board_ready = True

def draw_content(self, painter, folder_data):
    
    if not folder_data.board_ready:
        prepare_board(self, folder_data)
    else:

        painter.setPen(QPen(Qt.white, 1))
        font = painter.font()
        font.setWeight(300)
        font.setPixelSize(12)
        painter.setFont(font)
        for image_data in folder_data.images_list:
            if not image_data.board_position:
                continue
            image_scale = image_data.board_scale
            board_scale_x = self.board_scale_x
            board_scale_y = self.board_scale_y
            w = image_data.source_width*image_scale*board_scale_x
            h = image_data.source_height*image_scale*board_scale_y
            image_rect = QRectF(0, 0, w, h)
            pos = QPointF(self.board_origin)
            pos += QPointF(image_data.board_position.x()*board_scale_x, image_data.board_position.y()*board_scale_y)
            image_rect.moveCenter(pos)

            painter.setBrush(Qt.NoBrush)
            painter.drawRect(image_rect)

            text = f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
            max_rect = self.rect()
            alignment = Qt.AlignCenter

            painter.drawText(image_rect, alignment, text)

            painter.drawPixmap(image_rect, image_data.preview, QRectF(QPointF(0, 0), QSizeF(image_data.preview.size())))


def draw_main(self, painter):

    cf = Vars.LibraryData.current_folder()
    if cf.previews_done:
        draw_content(self, painter, cf)
    else:
        draw_wait_label(self, painter)


    self.draw_center_label_main(painter)

    if Vars.Globals.DEBUG:
        draw_board_origin(self, painter)
        draw_origin_compass(self, painter)

def draw_origin_compass(self, painter):

    curpos = self.mapFromGlobal(QCursor().pos())

    pos = self.board_origin

    def distance(p1, p2):
        return math.sqrt((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)

    # self.board_origin
    old_pen = painter.pen()

    painter.setPen(QPen(QColor(200, 200, 200), 1))
    # painter.drawLine(QPointF(pos).toPoint(), curpos)

    radius = 40
    delta = curpos - QPointF(pos).toPoint() 
    radians_angle = math.atan2(delta.y(), delta.x())
    # painter.translate(curpos)
    # painter.rotate(180/3.14*radians_angle-180)
    # painter.drawLine(QPoint(0, 0), QPoint(radius-40, 0))
    # painter.resetTransform()




    ellipse_rect = QRect(0, 0, radius*2, radius*2)
    ellipse_rect.moveCenter(curpos)
    painter.drawEllipse(ellipse_rect)

    dist = distance(pos, curpos)
    radius += 10
    radians_angle += math.pi
    if dist < radius:
        point = pos
    else:
        point = QPointF(curpos) + QPointF(math.cos(radians_angle)*radius, math.sin(radians_angle)*radius)

    # painter.setPen(QPen(Qt.red, 5))
    # painter.drawPoint(point)

    # text_rect_center = QPointF(curpos).toPoint() + QPoint(0, -10)
    text_rect_center = point.toPoint()

    scale_percent_x = math.ceil(self.board_scale_x*100)
    scale_percent_y = math.ceil(self.board_scale_y*100)
    text = f'{dist:.2f}\n{scale_percent_x:,}% {scale_percent_y:,}%'.replace(',', ' ')
    font = painter.font()
    font.setPixelSize(10)
    painter.setFont(font)
    max_rect = self.rect()
    alignment = Qt.AlignCenter


    text_rect = calculate_text_rect(font, max_rect, text, alignment)

    text_rect.moveCenter(text_rect_center)
    painter.setBrush(QBrush(QColor(10, 10, 10)))
    painter.setPen(Qt.NoPen)
    painter.drawRect(text_rect)
    painter.setPen(QPen(Qt.red))
    painter.drawText(text_rect, alignment, text)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(old_pen)


def draw_board_origin(self, painter):
    pos = self.board_origin
    pen = QPen(QColor(220, 220, 220, 200), 5)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    offset = QPoint(50, 50)
    center_rect = QRect(QPointF(pos).toPoint() - offset, QPointF(pos).toPoint() + offset)
    painter.drawEllipse(center_rect)

    # offset = QPoint(10, 10)
    # rect = QRect(QPointF(pos).toPoint() - offset, QPointF(pos).toPoint() + offset)
    # painter.drawRect(rect)

    painter.drawLine(QPointF(pos).toPoint() + QPoint(0, -20), QPointF(pos).toPoint() + QPoint(0, 20))
    painter.drawLine(QPointF(pos).toPoint() + QPoint(-20, 0), QPointF(pos).toPoint() + QPoint(20, 0))

    font = painter.font()
    font.setPixelSize(30)
    font.setWeight(1900)
    painter.setFont(font)
    max_rect = self.rect()
    alignment = Qt.AlignCenter

    text = "НАЧАЛО"
    text_rect = calculate_text_rect(font, max_rect, text, alignment)
    text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, -80))
    painter.drawText(text_rect, alignment, text)

    text = "КООРДИНАТ"
    text_rect = calculate_text_rect(font, max_rect, text, alignment)
    text_rect.moveCenter(QPointF(pos).toPoint() + QPoint(0, 80))
    painter.drawText(text_rect, alignment, text)

def mousePressEvent(self, event):

    if event.buttons() == Qt.LeftButton:
        if self.transformations_allowed:
            self.board_translating = True
            self.start_cursor_pos = self.mapped_cursor_pos()
            self.start_origin_pos = self.board_origin
            self.update()

def mouseMoveEvent(self, event):

    if event.buttons() == Qt.LeftButton:
        if self.transformations_allowed and self.board_translating:
            end_value =  self.start_origin_pos - (self.start_cursor_pos - self.mapped_cursor_pos())
            start_value = self.board_origin
            # delta = end_value-start_value
            self.board_origin = end_value
    self.update()

def mouseReleaseEvent(self, event):

    if event.button() == Qt.LeftButton:
        if self.transformations_allowed:
            self.board_translating = False
            self.update()
    if event.button() == Qt.MiddleButton:
        if self.transformations_allowed:
            set_default_viewport_scale(self, keep_position=True)

def do_scale_board(self, scroll_value, ctrl, shift, no_mod, pivot=None, factor_x=None, factor_y=None):

    curpos = self.mapped_cursor_pos()
    if pivot is None:
        pivot = curpos

    _board_origin = self.board_origin

    scale_speed = 10.0
    if scroll_value > 0:
        factor = scale_speed/(scale_speed-1)
    else:
        factor = (scale_speed-1)/scale_speed

    if factor_x is None:
        factor_x = factor

    if factor_y is None:
        factor_y = factor


    if ctrl:
        factor_x = factor
        factor_y = 1.0
    elif shift:
        factor_x = 1.0
        factor_y = factor

    self.board_scale_x *= factor_x
    self.board_scale_y *= factor_y

    _board_origin -= pivot
    _board_origin = QPointF(_board_origin.x()*factor_x, _board_origin.y()*factor_y)
    _board_origin += pivot

    self.board_origin  = _board_origin

    self.update()

def wheelEvent(self, event):
    scroll_value = event.angleDelta().y()/240
    ctrl = event.modifiers() & Qt.ControlModifier
    shift = event.modifiers() & Qt.ShiftModifier
    no_mod = event.modifiers() == Qt.NoModifier

    control_panel_undermouse = self.is_control_panel_under_mouse()
    if control_panel_undermouse:
        return
    elif no_mod:
        do_scale_board(self, scroll_value, ctrl, shift, no_mod)
    elif ctrl:
        do_scale_board(self, scroll_value, ctrl, shift, no_mod)
    elif shift:
        do_scale_board(self, scroll_value, ctrl, shift, no_mod)

def thumbnails_click_handler(image_data):

    self = Vars.Globals.main_window
    if image_data.board_position is None:
        Vars.Globals.main_window.show_center_label("Этот элемент не представлен на доске", error=True)
    else:
        board_scale_x = self.board_scale_x
        board_scale_y = self.board_scale_y

        image_pos = QPointF(image_data.board_position.x()*board_scale_x, image_data.board_position.y()*board_scale_y)
        viewport_center_pos = self.get_center_position()

        self.board_origin = self.board_origin - image_pos + viewport_center_pos - self.board_origin 

        image_width = image_data.source_width*image_data.board_scale*board_scale_x
        image_height = image_data.source_height*image_data.board_scale*board_scale_y
        image_rect = QRect(0, 0, int(image_width), int(image_height))
        fitted_rect = fit_rect_into_rect(image_rect, self.rect())
        do_scale_board(self, 0, False, False, False,
            pivot=viewport_center_pos,
            factor_x=fitted_rect.width()/image_rect.width(),
            factor_y=fitted_rect.height()/image_rect.height(),
        )

    self.update()

def set_default_viewport_scale(self, keep_position=False):
    if keep_position:
        do_scale_board(self, 0, False, False, False,
            pivot=self.mapped_cursor_pos(),
            factor_x=1/self.board_scale_x,
            factor_y=1/self.board_scale_y,
        )
    else:
        self.board_scale_x = 1.0
        self.board_scale_y = 1.0

def set_default_viewport_origin(self):
    self.board_origin = QPointF(300, 300)



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
