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






def draw(self, painter):
    old_font = painter.font()
    font = QFont(old_font)
    font.setPixelSize(250)
    font.setWeight(1900)
    painter.setFont(font)
    pen = QPen(QColor(180, 180, 180), 1)
    painter.setPen(pen)
    painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, "PUREREF MODE")
    painter.setFont(old_font)

def mousePressEvent(self, event):
    pass

def mouseMoveEvent(self, event):
    pass

def mouseReleaseEvent(self, event):
    pass

def wheelEvent(self, event):
    scroll_value = event.angleDelta().y()/240
    ctrl = event.modifiers() & Qt.ControlModifier
    shift = event.modifiers() & Qt.ShiftModifier
    no_mod = event.modifiers() == Qt.NoModifier


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
