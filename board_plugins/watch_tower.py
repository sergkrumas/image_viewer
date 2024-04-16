







import sys
import subprocess
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *





folders = [
]


def append_note_item(self, cf, text, warning=False):
    ni = self.BoardItem(self.BoardItem.types.ITEM_NOTE)
    ni.board_index = self.retrieve_new_board_item_index()
    cf.board.board_items_list.append(ni)
    self.board_TextElementSetDefaults(ni, plain_text=text)
    ni.calc_local_data()
    if warning:
        ni.font_color = QColor(220, 50, 50)
    self.board_ImplantTextElement(ni)
    self.board_TextElementRecalculateGabarit(ni)
    return ni

def pluginBoardInit(self, plugin_info):
    self.board_long_loading_begin()

    fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
    self.board_make_board_current(fd)
    cf = self.LibraryData().current_folder()

    offset_point = QPointF(0, 0)
    if folders:
        for fn, folderpath in enumerate(folders):

            offset_point.setY(0)
            ni = append_note_item(self, cf, folderpath)
            size_rect = ni.get_size_rect(scaled=True)
            size_rect.moveBottomLeft(offset_point)
            ni.item_position = size_rect.center()

            # initial max width instead zero
            max_width = size_rect.width()

            items = []
            for ifn, filename in enumerate(os.listdir(folderpath)):
                filepath = os.path.join(folderpath, filename)
                bi = self.board_create_new_board_item_image(filepath, cf, place_at_cursor=False, make_previews=False)
                items.append(bi)

            self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)

            for bi in items:
                max_width = max(max_width, bi.get_size_rect(scaled=True).width())

            for item in items:
                r = item.get_size_rect(scaled=True)
                item.item_position = offset_point + r.center()
                offset_point += QPointF(0, r.height())

            offset_point += QPointF(max_width, 0)
    else:
        self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)
        ni = append_note_item(self, cf, "Список папок пуст!", warning=True)
        size_rect = ni.get_size_rect(scaled=True)
        size_rect.moveCenter(self.rect().center())
        ni.item_position = size_rect.center()

    self.board_long_loading_end()


def register(board_obj, plugin_info):
    plugin_info.name = 'WATCH TOWER'
    plugin_info.pluginBoardInit = pluginBoardInit



if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw"])
    sys.exit()
