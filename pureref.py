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
    self.board_scale = 1.0

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
    font.setPixelSize(30)
    font.setWeight(1900)
    painter.setFont(font)
    max_rect = self.rect()
    alignment = Qt.AlignCenter

    text = "подождите"
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
            board_scale = self.board_scale
            w = image_data.source_width*image_scale*board_scale
            h = image_data.source_height*image_scale*board_scale
            image_rect = QRectF(0, 0, w, h)
            pos = QPointF(self.board_origin)
            pos += QPointF(image_data.board_position.x()*board_scale, image_data.board_position.y()*board_scale)
            image_rect.moveCenter(pos)

            painter.drawRect(image_rect)

            text = f'{image_data.filename}\n{image_data.source_width} x {image_data.source_height}'
            max_rect = self.rect()
            alignment = Qt.AlignCenter

            painter.drawText(image_rect, alignment, text)




def draw_main(self, painter):

    if Vars.Globals.DEBUG:
        draw_board_origin(self, painter)
        draw_origin_compass(self, painter)

    cf = Vars.LibraryData.current_folder()
    if cf.previews_done:
        draw_content(self, painter, cf)
    else:
        draw_wait_label(self, painter)

def draw_origin_compass(self, painter):

    curpos = self.mapFromGlobal(QCursor().pos())

    pos = self.board_origin

    def distance(p1, p2):
        return math.sqrt((p1.x() - p2.x())**2 + (p1.y() - p2.y())**2)

    # self.board_origin
    old_pen = painter.pen()

    painter.setPen(QPen(QColor(200, 200, 200), 1))
    painter.drawLine(QPointF(pos).toPoint(), curpos)

    dist = distance(pos, curpos)
    text = f'{dist:.2f}'
    font = painter.font()
    font.setPixelSize(10)
    painter.setFont(font)
    max_rect = self.rect()
    alignment = Qt.AlignCenter

    painter.setPen(QPen(Qt.red))

    text_rect = calculate_text_rect(font, max_rect, text, alignment)

    text_rect.moveCenter(QPointF(curpos).toPoint() + QPoint(0, -10))
    painter.drawText(text_rect, alignment, text)

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

def do_scale_board(self, scroll_value, ctrl, shift, no_mod):

    curpos = self.mapped_cursor_pos()
    pivot = curpos

    _board_origin = self.board_origin

    scale_speed = 10.0
    if scroll_value > 0:
        factor = scale_speed/(scale_speed-1)
    else:
        factor = (scale_speed-1)/scale_speed

    self.board_scale *= factor

    _board_origin -= pivot
    _board_origin = QPointF(_board_origin.x()*factor, _board_origin.y()*factor)
    _board_origin += pivot

    self.board_origin  = _board_origin
    # print(self.board_scale)

def wheelEvent(self, event):
    scroll_value = event.angleDelta().y()/240
    ctrl = event.modifiers() & Qt.ControlModifier
    shift = event.modifiers() & Qt.ShiftModifier
    no_mod = event.modifiers() == Qt.NoModifier

    do_scale_board(self, scroll_value, ctrl, shift, no_mod)

def mode_enter(self):
    self.pureref_mode = True
    # тут можно стопать таймеры анимации и прочее

    self.update()

def mode_leave(self):
    self.pureref_mode = False


    self.update()



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
