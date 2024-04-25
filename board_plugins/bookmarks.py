
import sys
import os
import subprocess
from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

sys.path.append('../')
import _utils



def paintEvent(self, painter, event):
    # default
    self.board_draw_main_default(painter, event)

    # plugin overlay
    painter.save()
    painter.setPen(Qt.white)
    font = painter.font()
    font.setPixelSize(25)
    painter.setFont(font)
    cf = self.LibraryData().current_folder()
    board = cf.board
    for bi in board.items_list:
        if bi.type in [self.BoardItem.types.ITEM_GROUP]:
            area = bi.get_selection_area(board=self)
            area_rect = area.boundingRect()
            area_rect.moveLeft(area_rect.left()+25)
            area_rect.moveBottomLeft(area_rect.bottomRight())
            text = '\n\n'.join(str(x) for x in bi.metainfo.values())
            painter.drawText(area_rect, Qt.TextWordWrap, text)
    painter.restore()

def objectReceived(self, path):
    self.activateWindow()
    cf = self.LibraryData().current_folder()
    if cf.board.root_folder is not None:
        self.show_center_label('BOOKMARKS PLUGIN: Нельзя создавать закладки во вложенных досках!', error=True)
        return
    self.show_center_label(path)
    gi = self.board_add_item_group(
        move_selection_to_group=False,
        virtual_allowed=True,
        item_position=self.board_MapToBoard(self.rect().center())
    )
    gi.item_folder_data.board.plugin_filename = cf.board.plugin_filename

    file_md5 = _utils.generate_md5(path)[0]
    file_size = _utils.get_file_size(path)
    filepath = path
    filename = os.path.basename(path)
    pagenumber = 0

    gi.metainfo = {
        'file_md5': file_md5,
        'file_size': file_size,
        'filepath': filepath,
        'filename': filename,
        'pagenumber': pagenumber,
    }

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
    board_filepath = getBoardFilepath(self)
    if os.path.exists(board_filepath):
        self.board_loadBoard(path=board_filepath)
    else:
        fd = self.board_CreatePluginVirtualFolder(plugin_info.name)
        self.board_make_board_current(fd)
        fd.board.ready = True
        fd.previews_done = True

def getBoardFilepath(self):
    board_filepath = self.board_BuildBoardFilename(self.get_boards_user_data_folder(), 'bookmarks_board')
    return board_filepath

def any_group_item(self):
    pos = self.context_menu_exec_point
    item_under_mouse = None
    cf = self.LibraryData().current_folder()
    for item in cf.board.items_list:
        if item.type == self.BoardItem.types.ITEM_GROUP:
            if item.get_selection_area(board=self).containsPoint(pos, Qt.WindingFill):
                item_under_mouse = item
                break
    if cf.board.root_folder is not None:
        # такое доступно только на корневой доске
        item_under_mouse = None
    return item_under_mouse

def edit_group_metadata(self, invoke_cause=''):
    item = any_group_item(self)
    if item is not None:
        if invoke_cause == 'edit_name':
            out, status = QInputDialog.getMultiLineText(self, '', '', item.metainfo['filename'])
            if status:
                item.metainfo['filename'] = out
        elif invoke_cause == 'edit_pagenum':
            out, status = QInputDialog.getInt(self, '', '', item.metainfo['pagenumber'])
            if status:
                item.metainfo['pagenumber'] = out

def implantToContextMenu(self, contextMenu):
    if any_group_item(self):
        contextMenu.addSeparator()
        edit_name = contextMenu.addAction('Bookmarks: Редактировать имя файла')
        edit_name.triggered.connect(partial(edit_group_metadata, self, 'edit_name'))

        edit_pagenum = contextMenu.addAction('Bookmarks: Редактировать страницу')
        edit_pagenum.triggered.connect(partial(edit_group_metadata, self, 'edit_pagenum'))

def contextMenu(self, event, contextMenu, checkboxes):
    # self.board_contextMenuDefault(event, contextMenu, checkboxes, plugin_implant=implantToContextMenu)
    implantToContextMenu(self, contextMenu)
    self.board_ContextMenuPluginsDefault(event, contextMenu)



def register(board_obj, plugin_info):
    plugin_info.name = 'BOOKMARKS'
    plugin_info.preparePluginBoard = preparePluginBoard

    plugin_info.paintEvent = paintEvent

    plugin_info.dragEnterEvent = dragEnterEvent
    plugin_info.dragMoveEvent = dragMoveEvent
    plugin_info.dropEvent = dropEvent

    plugin_info.getBoardFilepath = getBoardFilepath

    plugin_info.contextMenu = contextMenu

if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
