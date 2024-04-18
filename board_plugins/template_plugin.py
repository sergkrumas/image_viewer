
import sys
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def get_plugin_data_filepath(self):
    return self.get_user_data_filepath('template_plugin.data.txt')

def paintEvent(self, painter, event):
    self.board_draw_main_default(painter)

def mousePressEvent(self, event):
    self.board_mousePressEventDefault(event)

def mouseMoveEvent(self, event):
    self.board_mouseMoveEventDefault(event)

def mouseReleaseEvent(self, event):
    self.board_mouseReleaseEventDefault(event)

def wheelEvent(self, event):
    self.board_wheelEventDefault(event)

def contextMenu(self, event, contextMenu, checkboxes):
    self.board_ContextMenuDefault(event, contextMenu, checkboxes)

def keyPressEvent(self, event):
    self.board_keyPressEventDefault(event)

def keyReleaseEvent(self, event):
    self.board_keyReleaseEventDefault(event)



def pluginBoardInit(self, plugin_info):
    pass

def register(board_obj, plugin_info):
    
    plugin_info.name = 'TEMPLATE PLUGIN'

    # plugin_info.add_to_menu = False

    plugin_info.pluginBoardInit = pluginBoardInit

    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

    plugin_info.wheelEvent = wheelEvent
    plugin_info.contextMenu = contextMenu




if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw"])
    sys.exit()
