







import sys
import subprocess
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *





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

    folders = []

    folders_list_filepath = self.get_user_data_filepath('watch_tower.data')
    if os.path.exists(folders_list_filepath):
        with open(folders_list_filepath, 'r', encoding='utf8') as file:
            lines = file.readlines()
            for line in lines:
                if line:
                    folders.append(line.strip())

    self.board_long_loading_begin()

    fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
    self.board_make_board_current(fd)

    cf = self.LibraryData().current_folder()

    if folders:
        offset_point = QPointF(0, 0)
        for fn, folderpath in enumerate(folders):

            offset_point.setY(0)

            ni = append_note_item(self, cf, folderpath)
            size_rect = ni.get_size_rect(scaled=True)
            size_rect.moveBottomLeft(offset_point)
            ni.item_position = size_rect.center()

            # initial max width instead zero
            max_width = size_rect.width()

            if not os.path.exists(folderpath):
                ni = append_note_item(self, cf, 'Путь не найден!', warning=True)
                size_rect = ni.get_size_rect(scaled=True)
                size_rect.moveTopLeft(offset_point)
                ni.item_position = size_rect.center()
            else:

                items = []
                for ifn, filename in enumerate(os.listdir(folderpath)):
                    filepath = os.path.join(folderpath, filename)
                    is_library_file = self.LibraryData.is_interest_file(filepath)
                    if os.path.isfile(filepath) and is_library_file:
                        bi = self.board_create_new_board_item_image(filepath, cf, place_at_cursor=False, make_previews=False)
                        imd = bi.image_data
                        if imd.creation_date == 0:
                            imd.creation_date = imd.get_creation_date()
                        items.append(bi)

                items = list(sorted(items, key=lambda x: x.image_data.creation_date, reverse=True))

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
