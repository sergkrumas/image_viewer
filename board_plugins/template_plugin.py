
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def get_plugin_data_filepath(self):
    return self.get_user_data_filepath('template_plugin.data.txt')

def paintEvent(self, painter, event):
    self.board_draw_main_default(painter, event)

def mousePressEvent(self, event):
    self.board_mousePressEventDefault(event)

def mouseMoveEvent(self, event):
    self.board_mouseMoveEventDefault(event)

def mouseReleaseEvent(self, event):
    self.board_mouseReleaseEventDefault(event)

def wheelEvent(self, event):
    self.board_wheelEventDefault(event)

def contextMenu(self, event, contextMenu, checkboxes):
    self.board_contextMenuDefault(event, contextMenu, checkboxes)

def keyPressEvent(self, event):
    self.board_keyPressEventDefault(event)

def keyReleaseEvent(self, event):
    self.board_keyReleaseEventDefault(event)

def dragEnterEvent(self, event):
    self.board_dragEnterEventDefault(event)

def dragMoveEvent(self, event):
    self.board_dragMoveEventDefault(event)

def dropEvent(self, event):
    self.board_dropEventDefault(event)

def getBoardFilepath(self):
    return self.board_getBoardFilepathDefault()


def preparePluginBoard(self, plugin_info):
    pass

def register(board_obj, plugin_info):

    plugin_info.name = 'TEMPLATE PLUGIN'

    # plugin_info.add_to_menu = False

    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.mousePressEvent = mousePressEvent
    plugin_info.mouseMoveEvent = mouseMoveEvent
    plugin_info.mouseReleaseEvent = mouseReleaseEvent

    plugin_info.wheelEvent = wheelEvent
    plugin_info.contextMenu = contextMenu

    plugin_info.dragEnterEvent = dragEnterEvent
    plugin_info.dragMoveEvent = dragMoveEvent
    plugin_info.dropEvent = dropEvent

    plugin_info.getBoardFilepath = getBoardFilepath


if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
