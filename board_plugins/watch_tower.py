







import sys
import subprocess
import os
import platform
import datetime
from functools import partial

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *




def get_watch_tower_data_filepath(self):
    return self.get_boards_user_data_filepath('watch_tower.data.txt')

def append_note_item(self, cf, text, warning=False):
    ni = self.BoardItem(self.BoardItem.types.ITEM_NOTE)
    ni.board_index = self.retrieve_new_board_item_index()
    cf.board.items_list.append(ni)
    self.board_TextElementSetDefaults(ni, plain_text=text)
    ni.calc_local_data()
    if warning:
        ni.font_color = QColor(220, 50, 50)
    self.board_TextElementInitAfterLoadFromFile(ni)
    return ni

def preparePluginBoard(self, plugin_info):

    folders = []

    folders_list_filepath = get_watch_tower_data_filepath(self)
    if os.path.exists(folders_list_filepath):
        with open(folders_list_filepath, 'r', encoding='utf8') as file:
            lines = file.readlines()
            for line in lines:
                if line:
                    folders.append(line.strip())

    with self.show_longtime_process_ongoing(self, 'Загрузка папок'):
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
                ni.position = size_rect.center()

                # initial max width instead zero
                max_width = size_rect.width()

                if not os.path.exists(folderpath):
                    ni = append_note_item(self, cf, 'Путь не найден!', warning=True)
                    size_rect = ni.get_size_rect(scaled=True)
                    size_rect.moveTopLeft(offset_point)
                    ni.position = size_rect.center()
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
                            dt = datetime.datetime.fromtimestamp(imd.creation_date)
                            bi.status = dt.strftime("%A, %d %B %Y %X").capitalize()
                            items.append(bi)

                    items = list(sorted(items, key=lambda x: x.image_data.creation_date, reverse=True))

                    # вызов нужен, чтобы bi.get_size_rect вернул актуальные значения
                    self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)

                    for bi in items:
                        max_width = max(max_width, bi.get_size_rect(scaled=True).width())

                    for item in items:
                        r = item.get_size_rect(scaled=True)
                        item.position = offset_point + r.center()
                        offset_point += QPointF(0, r.height())

                offset_point += QPointF(max_width, 0)
        else:
            self.LibraryData().make_viewer_thumbnails_and_library_previews(cf, None)
            ni = append_note_item(self, cf, "Список папок пуст!", warning=True)
            size_rect = ni.get_size_rect(scaled=True)
            size_rect.moveCenter(self.rect().center())
            ni.position = size_rect.center()


def open_data_file(self):
    filepath = get_watch_tower_data_filepath(self)
    if not os.path.exists(filepath):
        with open(filepath, "a+", encoding='utf8') as file:
            pass
    if platform.system() == "Windows":
        __import__('win32api').ShellExecute(0, "open", filepath, None, ".", 1)
    else:
        system = platform.system()
        self.show_center_label(f'Команда не поддерживается на {system}', error=True)

def implantToContextMenu(self, contextMenu):
    contextMenu.addSeparator()
    action = contextMenu.addAction('Watch Tower: Открыть файл путей для показа')
    action.triggered.connect(partial(open_data_file, self))

def contextMenu(self, event, contextMenu, checkboxes):
    # нет смысла в полном меню, поэтому оставлю только имплант
    # self.board_contextMenuDefault(event, contextMenu, checkboxes, plugin_implant=implantToContextMenu)
    implantToContextMenu(self, contextMenu)

    self.board_ContextMenuPluginsDefault(event, contextMenu)

def register(board_obj, plugin_info):
    plugin_info.name = 'WATCH TOWER'
    plugin_info.preparePluginBoard = preparePluginBoard
    plugin_info.contextMenu = contextMenu


if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
