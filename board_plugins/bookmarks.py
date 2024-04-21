
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *



def paintEvent(self, painter, event):
    self.board_draw_main_default(painter, event)


def objectReceived(self, path):
    self.activateWindow()
    cf = self.LibraryData().current_folder()
    if cf.board.root_folder is not None:
        self.show_center_label('BOOKMARKS PLUGIN: Нельзя создавать группы во вложенных досках!', error=True)
        return 
    self.show_center_label(path)
    gi = self.board_add_item_group(
        move_selection_to_group=False,
        virtual_allowed=True,
        item_position=self.board_MapToBoard(self.rect().center())
    )
    gi.item_folder_data.board.plugin_filename = cf.board.plugin_filename

def dragEnterEvent(self, event):
    self.board_dragEnterEventDefault(event)

def dragMoveEvent(self, event):
    self.board_dragMoveEventDefault(event)

def dropEvent(self, event):
    if event.mimeData().hasUrls():
        event.setDropAction(Qt.CopyAction)
        event.accept()
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.path()
                if path:
                    path = path[1:]
                    objectReceived(self, path)
            else:
                self.show_center_label('Ссылки не поддерживаются')
        self.update()
    else:
        event.ignore()

def preparePluginBoard(self, plugin_info):
    fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
    self.board_make_board_current(fd)
    fd.board.ready = True
    fd.previews_done = True





def register(board_obj, plugin_info):
    plugin_info.name = 'BOOKMARKS'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.dragEnterEvent = dragEnterEvent
    plugin_info.dragMoveEvent = dragMoveEvent
    plugin_info.dropEvent = dropEvent


if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
