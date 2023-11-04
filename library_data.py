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

import settings_handling
from commenting import CommentingLibraryDataMixin
from board import BoardLibraryDataMixin
from tagging import TaggingLibraryDataMixin

from collections import defaultdict
import datetime
import locale
import operator


ThreadRuntimeData = namedtuple("ThreadData", "id current count ui_name")

class ThumbnailsThread(QThread):
    update_signal = pyqtSignal(object)
    threads_pool = []
    def __init__(self, folder_data, _globals, run_from_library=False):
        QThread.__init__(self)
        self.needed_thread = True
        self.ui_name = folder_data.folder_path
        self.folder_data = folder_data
        images_data = folder_data.images_list
        in_process = images_data in [thread.images_data for thread in self.threads_pool]
        previews_done = folder_data.previews_done
        self.run_from_library = run_from_library
        if in_process or previews_done:
            # предотвращаем запуск второй копии треда
            self.images_data = []
            self.needed_thread = False
        else:
            self.images_data = images_data
        self.threads_pool.append(self)
        ############################################################
        self.update_signal.connect(lambda data: _globals.main_window.update_threads_info(data))

    def start(self):
        super().start(QThread.IdlePriority)

    def run(self):
        if self.needed_thread:
            LibraryData().make_viewer_thumbnails_and_library_previews(self.folder_data, self)

class LibraryModeImageColumn():
    def __init__(self):
        self.images = []
        self.height = 0

    def add_image(self, image_data):
        self.images.append(image_data)
        self.height += image_data.preview_size.height()

class LibraryData(BoardLibraryDataMixin, CommentingLibraryDataMixin, TaggingLibraryDataMixin):
    def __new__(cls, _globals=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LibraryData, cls).__new__(cls)
            locale.setlocale(locale.LC_ALL, "russian")
            i = cls.instance
            i._current_folder = None
            i.folders = []
            i._index = -1
            i.folderslist_scroll_offset = 0
            i.fav_folder = None
            i.viewed_list = []
            i.on_library_page = False
            i.phantom_image = ImageData("", None)
            i.phantom_image._is_phantom = True

            i.fav_folder = ...
            i.comments_folder = ...

            if not i.globals.lite_mode:
                i.load_fav_list()
                i.load_comments_list()
                i.load_tags()
                i.load_session_file()
            i.load_boards()
        return cls.instance

    @classmethod
    def find_lost_files(cls):

        dl = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        drives = ['%s:' % d for d in dl if os.path.exists('%s:' % d)]
        for drive in drives:
            files_count = 0
            for cur_folder, dirs, files in os.walk(drive):
                files_count += len(files)
                print(cur_folder, len(files))
            print(drive, files_count)

    @staticmethod
    def get_content_path(folder_data):
        ci = folder_data.current_image()
        content_path = ci.filepath
        if not os.path.exists(content_path):
            if os.path.exists(folder_data.folder_path):
                content_path = folder_data.folder_path
            else:
                content_path = None
        return content_path

    def update_progressbar(self):
        app = QApplication.instance()
        stray_icon = app.property("stray_icon")
        tray_icon_animation_step = app.property('tray_icon_animation_step')
        if stray_icon and tray_icon_animation_step:
            tray_icon_animation_step()

    def remove_progressbar(self):
        app = QApplication.instance()
        stray_icon = app.property("stray_icon")
        tray_icon_animation_reset = app.property('tray_icon_animation_reset')
        if stray_icon and tray_icon_animation_reset:
            tray_icon_animation_reset()

    def any_content(self):
        return bool(self.folders)

    def get_fav_folder(self):
        return self.fav_folder

    def create_folder_data(self, folder_path, files, image_filepath=None, virtual=False, library_loading=False, make_current=True):

        folder_data = FolderData(folder_path, files,
            image_filepath=image_filepath,
            virtual=virtual,
            library_loading=library_loading,
        )
        if make_current:
            self.folders.append(folder_data)

        # удаление дубликатов и копирование модификаторов с них
        for fd in LibraryData().folders:
            if os.path.normpath(fd.folder_path) == os.path.normpath(folder_path):
                if fd != folder_data:
                    # folder_data.set_modifiers(fd.get_modifiers())
                    LibraryData().folders.remove(fd)
                    to_print = f"dublicated folder item removed from LibraryData: {fd.folder_path}"
                    print(to_print)
                    # break
                    # иногда дубликатов получается больше, чем 2, поэтому break отменяется

        if make_current:
            # индекс задаём только после удаления дубликатов
            self.choose_that_folder(folder_data, write_view_history=False)
        else:
            # make_current = False только у папок тегов
            current_folder = self.current_folder()
            # вставляем папку тега сразу за последней виртуальной папкой в списке папок
            n = 0
            for n, fd in enumerate(self.folders):
                if fd.virtual:
                    index = n+1
            self.folders.insert(n, folder_data)

            # сохраняем текущую папку текущей
            self.choose_that_folder(current_folder, write_view_history=False)

        return folder_data

    def find_modifiers(self, path):
        for fd in LibraryData().folders:
            if fd.folder_path == path:
                return fd.get_modifiers()
        return ""

    def all_folders(self):
        return self.folders

    def current_folder(self):
        return self._current_folder

    def before_current_image_changed(self):
        im = LibraryData().current_folder().current_image()
        im.store_ui_data()

    def after_current_image_changed(self):
        MW = self.globals.main_window
        im = LibraryData().current_folder().current_image()
        MW.show_image(im)
        im.load_ui_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()

    def choose_that_folder(self, folder_data, write_view_history=True):
        self._index = self.folders.index(folder_data)
        self._current_folder = self.folders[self._index]
        if write_view_history:
            self.add_current_image_to_view_history()

    def go_to_folder_of_current_image(self):
        im = LibraryData().current_folder().current_image()
        path = None
        if os.path.exists(im.filepath):
            path = im.filepath
        else:
            path = os.path.dirname(im.filepath)
        LibraryData().handle_input_data(path)

    def choose_previous_folder(self):
        # self.before_current_image_changed()
        if self._index > 0:
            self._index -= 1
        else:
            self._index = len(self.folders)-1
        self._current_folder = self.folders[self._index]
        # self.after_current_image_changed()
        MW = self.globals.main_window
        MW.previews_list_active_item = None
        MW.autoscroll_set_or_reset()
        self.update_current_folder_columns()
        MW.update()

    @staticmethod
    def is_supported_file(filepath):
        return LibraryData.is_interest_file(filepath)

    @staticmethod
    def is_gif_file(filepath):
        return filepath.lower().endswith(".gif")

    @staticmethod
    def is_webp_file(filepath):
        return filepath.lower().endswith(".webp")

    @staticmethod
    def is_svg_file(filepath):
        return filepath.lower().endswith((".svg", ".svgz"))

    @staticmethod
    def is_avif_file(filepath):
        return filepath.lower().endswith((".avif", ".heif", ".heic"))

    @staticmethod
    def is_webp_file_animated(filepath):
        return LibraryData().is_webp_file(filepath) and is_webp_file_animated(filepath)

    def choose_next_folder(self):
        # self.before_current_image_changed()
        if self._index < len(self.folders)-1:
            self._index += 1
        else:
            self._index = 0
        self._current_folder = self.folders[self._index]
        # self.after_current_image_changed()
        MW = self.globals.main_window
        MW.previews_list_active_item = None
        MW.autoscroll_set_or_reset()
        self.update_current_folder_columns()
        MW.update()

    def choose_doom_scroll(self):
        if len(self.folders) == [0, 1]:
            return
        self.before_current_image_changed()
        self.save_board_data()
        indexes_it = itertools.cycle(range(len(self.folders)))
        index_ = None
        while index_ != self._index:
            index_ = next(indexes_it)
        self._index = next(indexes_it)
        self._current_folder = self.folders[self._index]
        self.after_current_image_changed()
        self.load_board_data()
        ThumbnailsThread(self._current_folder, self.globals).start()
        MW = self.globals.main_window
        MW.update()

    def save_board_data(self):
        cf = self.current_folder()
        MW = self.globals.main_window
        cf.board_scale_x = MW.board_scale_x
        cf.board_scale_y = MW.board_scale_y
        cf.board_origin = MW.board_origin

    def load_board_data(self):
        cf = self.current_folder()
        MW = self.globals.main_window
        if cf.board_scale_x is None:
            MW.set_default_boardviewport_scale()
        else:
            MW.board_scale_x = cf.board_scale_x
            MW.board_scale_y = cf.board_scale_y
        if cf.board_origin is None:
            MW.set_default_boardviewport_origin()
        else:
            MW.board_origin = cf.board_origin

    def delete_current_image(self):
        MW = self.globals.main_window
        cf = self.current_folder()
        ci = cf.current_image()
        if ci in cf.images_list: #служебные объекты ImageData не находятся в списке
            if cf.virtual:
                MW.show_center_label("Из виртуальных нельзя удалять изображения", error=True)
                return
            # prepare
            cf.set_current_index(max(0, cf.images_list.index(ci)-1))
            delete_to_recyclebin(ci.filepath)
            MW.show_center_label(f"Файл\n{ci.filepath}\n удален в корзину")
            cf.images_list.remove(ci)
            # show next
            im_data = self.current_folder().current_image()
            MW.show_image(im_data)
            cf.current_image().load_ui_data()
            MW.set_window_title(MW.current_image_details())
            LibraryData.update_current_folder_columns()
        else:
            MW.show_center_label("Это не удалить!", error=True)
        MW.update()

    def show_that_preview_on_viewer_page(self, image_data):
        fd = image_data.folder_data
        self._index = self.folders.index(fd)
        self._current_folder = self.folders[self._index]
        fd._index = fd.images_list.index(image_data)
        # change mode to preview
        MW = self.globals.main_window
        MW.change_page(MW.pages.VIEWER_PAGE)

        self.on_library_page = True

    def show_next_image(self):
        MW = self.globals.main_window
        if MW.isBlockedByAnimation():
            return
        MW.hide_center_label()
        cf = LibraryData().current_folder()
        old_current = cf.current_image()
        cf.current_image().store_ui_data()
        old_center_pos = MW.image_center_position
        im_data = cf.next_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_ui_data(cp=old_center_pos)
        else:
            cf.current_image().load_ui_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()
        if old_current == cf.current_image():
            self.globals.control_panel.quick_show()
        self.add_current_image_to_view_history()

    def show_previous_image(self):
        MW = self.globals.main_window
        if MW.isBlockedByAnimation():
            return
        MW.hide_center_label()
        cf = LibraryData().current_folder()
        old_current = cf.current_image()
        cf.current_image().store_ui_data()
        old_center_pos = MW.image_center_position
        im_data = cf.previous_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_ui_data(cp=old_center_pos)
        else:
            cf.current_image().load_ui_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()
        if old_current == cf.current_image():
            self.globals.control_panel.quick_show()
        self.add_current_image_to_view_history()

    def jump_to_image(self, index, leave_history_record=True):
        MW = self.globals.main_window
        if MW.isBlockedByAnimation():
            return
        MW.hide_center_label()
        cf = LibraryData().current_folder()
        cf.current_image().store_ui_data()
        old_center_pos = MW.image_center_position
        cf.set_current_index(index)
        im_data = cf.current_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_ui_data(cp=old_center_pos)
        else:
            cf.current_image().load_ui_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()
        if leave_history_record:
            self.add_current_image_to_view_history()

    def jump_to_first(self):
        cf = LibraryData().current_folder()
        if cf.images_list:
            self.jump_to_image(0)

    def jump_to_last(self):
        cf = LibraryData().current_folder()
        last_index = len(cf.images_list) - 1
        if cf.images_list:
            self.jump_to_image(last_index)

    def show_viewed_image(self, direction):
        if direction == ">":
            direction = -1
        elif direction == "<":
            direction = 1
        cf = LibraryData().current_folder()
        if not cf:
            return
        c_im = cf.current_image()
        viewed_list = self.get_viewed_list()
        if not viewed_list:
            return
        # print(viewed_list)
        index = viewed_list.index(c_im)
        index += direction
        try:
            if index < 0:
                raise Exception("")
            selected_im = viewed_list[index]
        except:
            MW = self.globals.main_window
            MW.show_center_label("достигнут край истории просмотров")
            return
        # if selected_im not in cf.images_list:
        #     return

        index = selected_im.folder_data.images_list.index(selected_im)

        # change folder if needed
        if cf is not selected_im.folder_data:
            self.before_current_image_changed()
            new_fd = selected_im.folder_data
            self._current_folder = new_fd
            self._index = self.folders.index(new_fd)
            self.after_current_image_changed()

        self.jump_to_image(index, leave_history_record=False)

    def get_viewed_list(self):
        folder_data = LibraryData().current_folder()
        if self.globals.USE_GLOBAL_LIST_VIEW_HISTORY:
            viewed_list = self.viewed_list
        else:
            viewed_list = folder_data.viewed_list
        return viewed_list

    def set_viewed_list(self, viewed_list):
        folder_data = LibraryData().current_folder()
        if self.globals.USE_GLOBAL_LIST_VIEW_HISTORY:
            obj = self
        else:
            obj = folder_data
        setattr(obj, 'viewed_list', viewed_list)

    def add_current_image_to_view_history(self):
        folder_data = LibraryData().current_folder()
        im = folder_data.current_image()
        viewed_list = self.get_viewed_list()
        if viewed_list and viewed_list[0] is im:
            return
        viewed_list.insert(0, im)
        viewed_list = viewed_list[:self.globals.VIEW_HISTORY_SIZE]
        self.set_viewed_list(viewed_list)

    def show_viewed_image_prev(self):
        self.show_viewed_image(">")

    def show_viewed_image_next(self):
        self.show_viewed_image("<")

    def delete_current_folder(self):
        MW = self.globals.main_window
        cf = self.current_folder()
        if cf.virtual:
            MW.show_center_label('Нельзя удалять виртуальные папки из библиотеки', error=True)
            return
        elif len(self.folders) == 1:
            MW.show_center_label('Нельзя удалить единственную папку из библиотеки', error=True)
            return
        else:
            LibraryData().choose_previous_folder()
            LibraryData().folders.remove(cf)
        LibraryData().store_session_file()
        MW.update()

    def update_current_folder(self):
        cf = LibraryData().current_folder()
        if cf.virtual:
            return
        print("updating current folder...")
        current_filepath = cf.current_image().filepath
        old_images = cf.images_list[:]
        cf.images_list.clear()

        files = LibraryData().list_interest_files(
            cf.folder_path,
            deep_scan=cf.deep_scan
        )
        cf.init_images(files, prev=old_images)
        if cf.images_list:
            is_set = False
            for image_data in cf.images_list:
                if os.path.normpath(image_data.filepath) == os.path.normpath(current_filepath):
                    cf._index = cf.images_list.index(image_data)
                    is_set = True
                    break
            if not is_set:
                cf._index = 0
            cf.previews_done = False
            ThumbnailsThread(cf, self.globals).start()
        else:
            cf._index = 0
        self.globals.main_window.update()

    @staticmethod
    def get_session_filepath():
        filepath = os.path.join(os.path.dirname(__file__), "user_data", LibraryData().globals.SESSION_FILENAME)
        create_pathsubfolders_if_not_exist(os.path.dirname(filepath))
        return filepath

    @staticmethod
    def load_session_file():
        if LibraryData().globals.lite_mode:
            return
        data = []
        path = LibraryData().get_session_filepath()
        fields = [
            "folder_path",
            "content_hash",
            "modifiers",
            "separator_field",
        ]
        SR = namedtuple("SessionRecord", fields)
        if os.path.exists(path):
            errors = False
            print("loading session data")
            with open(path, "r", encoding="utf8") as session_file:
                txt_data = session_file.read()
                try:
                    elements = txt_data.split("\n")
                    fields_count = SR._fields.__len__()
                    data = itertools.zip_longest(*(iter(elements),)*fields_count)
                    data = [SR(*item) for item in data]
                except:
                    errors = True
            if errors:
                to_print = f'Файл сессии повреждён и должен быть удалён {path}'
                # очень интересно посмотреть на повреждения, поэтому файл пока что не удаляется
                # os.remove(path)
        for item in data:
            if os.path.exists(item.folder_path):
                msg = f"LIBRARY LOADING: Reading folder data in {item.folder_path}"
                print(msg)
                LibraryData().handle_input_data(
                    item.folder_path,
                    pre_load=True,
                    content_hash=item.content_hash,
                    modifiers=item.modifiers,
                    library_loading=True,
                )
        if LibraryData().globals.is_path_exists:
            # сохраняем заново, чтобы отвалилось всё то,
            # что корректно не открылось в handle_input_data
            LibraryData().store_session_file()


    @staticmethod
    def store_session_file():
        if LibraryData().globals.lite_mode:
            return
        # TODO здесь из-за f_d.current_image().filepath может быть баг,
        # когда папка не сохранится, потому что данных нет
        folders_list = []
        for fd in LibraryData().folders:
            ok_1 = not fd.virtual
            ok_2 = fd.current_image().filepath
            if all((ok_1, ok_2)):
                folders_list.append(fd)
        data_to_out = []
        for fd in folders_list:
            info_lines = (
                f'{fd.folder_path}',
                f'{fd.current_image().md5}',
                f'{fd.get_modifiers()}',
            )
            fd_data = "\n".join(info_lines)
            data_to_out.append(f'{fd_data}\n')
        data_to_write = "\n".join(data_to_out)
        with open(LibraryData().get_session_filepath(), "w+", encoding="utf8") as session_file:
            session_file.write(data_to_write)

    def get_fav_list_path(self):
        filepath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.FAV_FILENAME)
        create_pathsubfolders_if_not_exist(os.path.dirname(filepath))
        return filepath

    def load_fav_list(self):
        ItemRecord = namedtuple("ItemRecord", "filepath md5 disk_size separator_field")
        files = []
        if os.path.exists(self.get_fav_list_path()):
            print("loading favourite data")
            errors = False
            with open(self.get_fav_list_path(), "r", encoding="utf8") as fav_file:
                txt_data = fav_file.read()
                try:
                    elements = txt_data.split("\n")
                    fileds_count = ItemRecord._fields.__len__()
                    data = itertools.zip_longest(*(iter(elements),)*fileds_count)
                    for item in data:
                        item = ItemRecord(*item)
                        files.append(item.filepath)
                except Exception as e:
                    errors = True
            if errors:
                _path = self.get_fav_list_path()
                to_print = f'Ошибки при чтении файла {_path}'
                print(to_print)
                # пока ещё не удаляем, мало ли что
                # os.remove(self.get_fav_list_path())
        self.fav_folder = self.create_folder_data("Избранное", files, image_filepath=None, virtual=True)

    def store_fav_list(self):
        images = self.get_fav_virtual_folder().images_list
        data_to_out = []
        for im in images:
            info_lines = (
                f"{im.filepath}",
                f"{im.md5}",
                f"{im.disk_size}",
            )
            favi_data = "\n".join(info_lines)
            data_to_out.append(f'{favi_data}\n')
        data_to_write = "\n".join(data_to_out)
        with open(self.get_fav_list_path(), "w+", encoding="utf8") as fav_file:
            fav_file.write(data_to_write)

    def create_empty_virtual_folder(self):
        # создаётся одна виртуальная папка, чтобы приложение не крашилось при перелистывании страниц,
        # ведь код каждой из страниц подразумевает, что существует какая-то папка
        self.empty_virtual_folder = self.create_folder_data("Стартовая виртуальная папка", [], image_filepath=None, virtual=True, make_current=True)
        self.empty_virtual_folder.previews_done = True

    def get_comm_virutal_folder(self):
        return self.comments_folder

    def get_fav_virtual_folder(self):
        return self.fav_folder

    def fav_list_filepaths(self):
        return [a.filepath for a in self.get_fav_virtual_folder().images_list]

    def manage_favorite_list(self):
        # image_data = LibraryData().current_folder().current_image()
        image_data = self.globals.main_window.image_data
        if not image_data.filepath:
            return
        if not LibraryData.is_interest_file(image_data.filepath):
            return "rejected"
        fav_folder = self.get_fav_virtual_folder()
        if image_data.filepath in self.fav_list_filepaths():
            for im_data in self.get_fav_virtual_folder().images_list:
                if im_data.filepath == image_data.filepath:
                    break
            fav_folder.images_list.remove(im_data)
            self.store_fav_list()
            LibraryData.update_folder_columns(fav_folder)
            return "removed"
        else:
            fav_folder.images_list.append(image_data)
            self.store_fav_list()
            LibraryData.update_folder_columns(fav_folder)
            return "added"

    def is_in_fav_list(self, image_data):
        return image_data.filepath in self.fav_list_filepaths()

    @staticmethod
    def is_text_file(filepath):
        exts = (
            ".log",
            ".txt",
            ".url",
            ".ini",
            ".pyw",
            ".py",
            ".bat",
        )
        return filepath.lower().endswith(exts)

    @staticmethod
    def is_interest_file(filepath):
        # поддерживаемые самим Qt форматы для чтения
            # >>> list(map(lambda x: x.data().decode(), QImageReader.supportedImageFormats()))
            # [
            #     'bmp',
            #     'cur',
            #     'gif',
            #     'icns',
            #     'ico',
            #     'jpeg',
            #     'jpg',
            #     'pbm',
            #     'pgm',
            #     'png',
            #     'ppm',
            #     'svg',
            #     'svgz',
            #     'tga',
            #     'tif',
            #     'tiff',
            #     'wbmp',
            #     'webp',
            #     'xbm',
            #     'xpm'
            # ]
            # дополнительно через QMovie поддерживаются форматы
                # .gif
                # .webp (animated)
        exts = (
            ".jpg", ".jpeg",
            ".jfif", # внутри jfif-файлы то же самое, что и внутри jpeg или jpg
            ".bmp",
            ".gif",
            ".png",
            ".tga",
            ".svg",
            ".svgz",
            ".ico",
            ".tif", ".tiff",
            ".webp",
            ".avif", ".heif", ".heic",
        )
        return filepath.lower().endswith(exts)

    @staticmethod
    def list_interest_files(folder_path, deep_scan=False, all_allowed=None):
        filepaths = []
        if all_allowed is None:
            all_allowed = not settings_handling.SettingsWindow.get_setting_value("browse_images_only")
        if os.path.exists(folder_path):
            for cur_dir, dirs, files in os.walk(folder_path):
                for name in files:
                    filepath = os.path.join(cur_dir, name)
                    if LibraryData.is_interest_file(filepath) or all_allowed:
                        filepaths.append(filepath)
                if not deep_scan:
                    break
        return filepaths

    @staticmethod
    def make_viewer_thumbnails_and_library_previews(folder_data, thread_instance):

        current_image = folder_data.current_image()
        if thread_instance is not None and not thread_instance.run_from_library:
            images_list = list(get_index_centered_list(folder_data.images_list,
                                                                      folder_data.current_image()))
        else:
            images_list = folder_data.images_list
        folder_data.previews_done = False
        image_count = len(images_list)
        Globals = LibraryData().globals
        for n, image_data in enumerate(images_list):
            if image_data.thumbnail != Globals.DEFAULT_THUMBNAIL:
                continue

            if thread_instance:
                # switch to main thread
                thread_instance.msleep(1)

            try:
                # try only for .avif-files
                source = load_image_respect_orientation(image_data.filepath)
                image_data.preview_error = False
            except:
                source = QPixmap()
                image_data.preview_error = True

            if source.isNull():
                source = Globals.ERROR_PREVIEW_PIXMAP
                image_data.preview_error = True
            if not image_data.is_supported_filetype:
                source = Globals.NOT_SUPPORTED_PIXMAP
                image_data.preview_error = True
            # thumbnail
            THUMBNAIL_WIDTH = Globals.THUMBNAIL_WIDTH
            thumbnail = source.scaled(THUMBNAIL_WIDTH, THUMBNAIL_WIDTH,
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            image_data.set_thumbnail(thumbnail)
            if thread_instance is not None:
                data = ThreadRuntimeData(
                    int(id(thread_instance)),
                    n+1,
                    image_count,
                    thread_instance.ui_name,
                )
                thread_instance.update_signal.emit(data)
            # preview
            image_data.source_width = ow = source.width()
            image_data.source_height = oh = source.height()
            if LibraryData().is_svg_file(image_data.filepath):
                image_data.source_width *= DEFAULT_SVG_SCALE_FACTOR
                image_data.source_height *= DEFAULT_SVG_SCALE_FACTOR
            preview_height = int(oh*Globals.PREVIEW_WIDTH/ow) if ow > 0 else 0
            image_data.preview_size = QSize(Globals.PREVIEW_WIDTH, preview_height)
            if ow != 0:
                preview = source.scaled(Globals.PREVIEW_WIDTH, preview_height,
                    Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                image_data.preview = preview
            else:
                image_data.preview = ERROR_PREVIEW_PIXMAP
            if thread_instance is not None:
                thread_instance.update_signal.emit(None)
                if folder_data not in LibraryData().all_folders():
                    data = ThreadRuntimeData(
                        int(id(thread_instance)),
                        image_count,
                        image_count,
                        "",
                    )
                    thread_instance.update_signal.emit(data)
                    return

        folder_data.previews_done = True
        folder_data.create_library_columns(6, Globals.PREVIEW_WIDTH, thread_instance=thread_instance)

    @classmethod
    def update_folder_columns(cls, folder_data):
        Globals = LibraryData().globals
        if folder_data and folder_data.previews_done:
            column_space = Globals.main_window.rect().width()/2
            count = int(column_space/Globals.PREVIEW_WIDTH)
            count = max(count, 1)
            folder_data.create_library_columns(count, Globals.PREVIEW_WIDTH)

    @classmethod
    def update_current_folder_columns(cls):
        cf = LibraryData().current_folder()
        cls.update_folder_columns(cf)

    @classmethod
    def get_user_rotations_filepath(cls, folder_data):
        j = os.path.join
        n = os.path.normpath
        path = n(j(folder_data.folder_path, LibraryData().globals.USERROTATIONS_FILENAME))
        return path

    @classmethod
    def read_user_rotations_for_folder(cls, folder_data):
        filepath = cls.get_user_rotations_filepath(folder_data)
        data = []
        if os.path.exists(filepath):
            to_print = f"\treading image rotations in {filepath}"
            print(to_print)
            with open(filepath, "r", encoding="utf8") as f:
                txt_data = f.read()
                elements = txt_data.split("\n")
                fileds_count = 3
                data = itertools.zip_longest(*(iter(elements),)*fileds_count)
        def filter_rotation_data(value):
            try:
                value = int(value)
            except:
                value = 0
            if value not in [90, 180, 270]:
                value = 0
            return value
        return [(filename, filter_rotation_data(rotation_value)) for filename, rotation_value, empty_field in data]

    @classmethod
    def write_rotations_for_folder(cls):
        cf = LibraryData().current_folder()
        filepath = cls.get_user_rotations_filepath(cf)
        if os.path.exists(filepath):
            os.remove(filepath)
        data = []
        for image_data in cf.images_list:
            rotation = image_data.image_rotation
            if rotation != 0:
                dir_path = os.path.basename(image_data.filepath)
                imd_r_str = f"{dir_path}\n{rotation}\n"
                data.append(imd_r_str)
        if os.path.exists(filepath):
            # приходится вызвать, чтобы не было Permission Denied
            win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_NORMAL)

        with open(filepath, "w+", encoding="utf8") as f:
            f.write("\n".join(data))
            to_print = f'rotations written to: {filepath}'
            print(to_print)
        win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

    @staticmethod
    def handle_input_data(input_path,
                pre_load=False,
                content_hash=None,
                modifiers="",
                library_loading=False):

        # все пути приводим к единому виду, чтобы не было разных слэшей в путях,
        # из-за которых в библиотеке могут ходить разные дубликаты одной и той же папки
        input_path = os.path.normpath(input_path)

        Globals = LibraryData().globals
        MW = Globals.main_window
        if not pre_load:
            MW.handling_input = True
            MW.viewer_reset(simple=True)
            MW.activateWindow()
            processAppEvents()

        def back_to_current_on_fail():
            MW.handling_input = False
            ci = LibraryData().current_folder().current_image()
            MW.show_image(ci)
            # MW.show_startpage = not LibraryData().any_content()

        def close_app_if_empty():
            if not LibraryData().any_content():
                app = QApplication.instance()
                # app.exit()
                sys.exit()

        # analyze input
        fd = None
        if not os.path.exists(input_path):
            if not pre_load:
                QMessageBox.critical(None, "Error", f"Not exists:\n{input_path}")
                close_app_if_empty()
                back_to_current_on_fail()
                return

        is_file = os.path.isfile(input_path)
        if is_file:
            image_path = input_path
            folder_path = os.path.dirname(input_path)
        else:
            image_path = None
            folder_path = input_path
        if not modifiers:
            modifiers = LibraryData().find_modifiers(folder_path)
        files = LibraryData().list_interest_files(folder_path, deep_scan='-deep_scan' in modifiers)

        # creation
        if files:
            fd = LibraryData().create_folder_data(folder_path, files, image_filepath=image_path, library_loading=library_loading)
            if modifiers:
                fd.set_modifiers(modifiers)
        else:
            if not pre_load:
                QMessageBox.critical(None, "Error", f"No interesting files to show in \n{path}")
                close_app_if_empty()
                back_to_current_on_fail()
                return

        if fd and not pre_load:
            # ui prepare
            MW = Globals.main_window
            if MW.is_library_page_active():
                # выходим из страницы библиотеки для показа картинки
                MW.change_page(MW.pages.VIEWER_PAGE)
            MW.show_image(fd.current_image(), only_set_thumbnails_offset=True)
            # MW.update_thumbnails_row_relative_offset(fd, only_set=True)
            fd.current_image().update_fav_button_state()
            if MW.isAnimationEffectsAllowed():
                MW.animate_properties(
                    [(MW, "image_scale", 0.01, MW.image_scale, MW.update)],
                    anim_id = "image_transform_start"
                )
            MW.update()
            MW.activateWindow()

            MW.change_page(MW.pages.VIEWER_PAGE, force=True)

            LibraryData().add_current_image_to_view_history()
            LibraryData().store_session_file()

            if not Globals.DEBUG:
                LibraryData().write_history_file(input_path)

            # make thumbnails
            ThumbnailsThread(fd, Globals).start()
            # old make thumbnials
            # LibraryData().make_viewer_thumbnails_and_library_previews(fd, None)

        elif fd and pre_load and content_hash:
            for n, image_data in enumerate(fd.images_list):
                if compare_md5_strings(image_data.md5, content_hash):
                    fd.set_current_index(n)

        if not pre_load:
            MW.handling_input = False

    @staticmethod
    def write_history_file(path):
        root = os.path.dirname(__file__)
        history_file_path = os.path.join(root, "user_data", "history.log")
        create_pathsubfolders_if_not_exist(os.path.dirname(history_file_path))
        date = datetime.datetime.now().strftime("%d %b %Y %X")
        with open(history_file_path, "a+", encoding="utf8") as file:
            record = "%s %s\n" % (date, path)
            file.write(record)

    def show_finder_window(self):
        FinderWindow(self.globals.main_window).show()

    def retrieve_lost_records(self):
        # 1) выявить все записи, где файлы по записанному пути не находятся. Из записи взять размер в байтах и значение md5-хэша
        # 2) сканировать все файлы в папках для поиска
                # 1 - проверять совпадение расширения
                # 2 - проведерять совпадение размера в байтах
                # 3 - вычислить md5-хэш и проверить совпадение с записанным md5-хэша
        # 3) исправить запись
        pass


class FolderData():

    def check_insert_position(self, index):
        cf = self
        if index == 0:
            return True
        if index == len(cf.images_list):
            return True
        if cf.images_list[index]._selected:
            if index > 0 and not cf.images_list[index-1]._selected:
                return True
            else:
                return False
        return True

    def get_images_order_filepath(self):
        return os.path.normpath(os.path.join(self.folder_path, "viewer_order.ini"))

    def save_images_order(self):
        data_to_write = []
        for image_data in self.images_list:
            if image_data.md5:
                data_to_write.append(image_data.md5)
        data_to_write = "\n".join(data_to_write)
        filepath = self.get_images_order_filepath()

        if os.path.exists(filepath):
            # приходится вызвать, чтобы не было Permission Denied
            win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_NORMAL)

        with open(filepath, "w+", encoding="utf8") as file:
            file.write(data_to_write)


        win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)
        MW = LibraryData().globals.main_window
        MW.show_center_label('Порядок изображений сохранён в файл')

    def do_rearrangement(self, insert_index):

        # всегда првоеряемся перед делом
        if not self.check_insert_position(insert_index):
            return False

        length = len(self._images_list_selected)
        msg = f'{insert_index} {length}'
        # print(msg)

        insert_at_head = insert_index == 0
        insert_at_tail = insert_index == len(self.images_list)

        # special case handling
        if not insert_at_tail:
            special_case = False
            if self.images_list[insert_index]._selected:
                if insert_index > 0 and not self.images_list[insert_index-1]._selected:
                    insert_index -= 1
                    special_case = True
        # сначала запоминаем текущее изображение
        current_image = self.current_image()

        if insert_at_head or insert_at_tail:
            insert_index_element = None
        else:
            # надо запомнить позицию куда (около которой) будет вставка,
            # и на этой позиции надо найти элемент и запомнить его
            insert_index_element = self.images_list[insert_index]

        # все отмеченные элементы удалить из списка
        self.images_list = [im_data for im_data in self.images_list if not im_data._selected]

        if insert_index_element:
            # найти теперь новый индекс элемента, который запоминали
            insert_position = self.images_list.index(insert_index_element)

            if special_case:
                insert_position += 1
            a = self.images_list[:insert_position]
            b = self.images_list[insert_position:]

        result = []
        if insert_index_element:
            # добавить в этот индекс все удалённые элементы
            result.extend(a)
            result.extend(self._images_list_selected)
            result.extend(b)
        elif insert_at_head:
            result.extend(self._images_list_selected)
            result.extend(self.images_list)
        elif insert_at_tail:
            result.extend(self.images_list)
            result.extend(self._images_list_selected)

        for im_data in self._images_list_selected:
            im_data._selected = False
            im_data._touched = False
        self._images_list_selected.clear()

        self.images_list = result

        # текущей картинке восстанавливаем её статус текущей картинки
        self.set_current_index(self.images_list.index(current_image))

        self.sort_type = 'reordered'

        if settings_handling.SettingsWindow.get_setting_value("autosave_on_reordering"):
            self.save_images_order()


        return True

    def find_in_prev(self, filepath, prev):
        for image_data in prev:
            if os.path.normpath(filepath) == os.path.normpath(image_data.filepath):
                return image_data
        return None

    def init_images(self, files, prev=None, library_loading=False):
        for filepath in files:
            processAppEvents(update_only=False)
            if os.path.exists(filepath): # проверка нужна для папки Избранное
                im_data = None
                if prev:
                    im_data = self.find_in_prev(filepath, prev)
                if not im_data:
                    im_data = ImageData(filepath, self)
                LibraryData().update_progressbar()
                self.images_list.append(im_data)
        self.original_list = self.images_list[:]
        self.sort_type = "original"
        self.sort_type_reversed = False
        if not self.virtual:
            items = LibraryData.read_user_rotations_for_folder(self)
            for image_data in self.images_list:
                for filename, value in items:
                    if os.path.basename(image_data.filepath) == filename:
                        image_data.image_rotation = value
        LibraryData().remove_progressbar()
        for image_data in self.images_list:
            image_data.is_supported_filetype = LibraryData.is_interest_file(image_data.filepath)

        images_order_filepath = self.get_images_order_filepath()
        if os.path.exists(images_order_filepath):
            hashes = []
            with open(images_order_filepath, "r", encoding="utf8") as file:
                hashes = file.read().split("\n")
            if hashes:
                found_images = []
                for hash_value in hashes:
                    self._find_image_by_hash_and_retrieve(hash_value, found_images)

                images_left_list = self.images_list[:]
                result = []
                result.extend(found_images)
                result.extend(images_left_list)

                self.images_list = result
                self.sort_type = 'reordered'

    def _find_image_by_hash_and_retrieve(self, hash_value, temp_list):
        for image_data in self.images_list:
            if compare_md5_strings(image_data.md5, hash_value):
                temp_list.append(image_data)
                self.images_list.remove(image_data)
                break

    def __init__(self, folder_path, files,
                    image_filepath=None,
                    virtual=False,
                    library_loading=False):

        super().__init__()

        self.virtual = virtual
        self.tag_data = None
        self.folder_path = folder_path
        self.folder_name = os.path.basename(folder_path)
        self._index = -1
        self.before_index = -1
        self.images_list = []
        self.previews_done = False
        self.deep_scan = False
        self.viewed_list = []
        self._images_list_selected = list()

        self.sort_type = "original"
        self.sort_type_reversed = False

        self.board_origin = None
        self.board_scale_x = None
        self.board_scale_y = None
        self.board_ready = False

        self.board_user_points = []
        self.board_items_list = []

        self.preview_error = False

        self.relative_thumbnails_row_offset_x = 0
        self.absolute_board_thumbnails_row_offset_x = 0

        self.init_images(files, library_loading=library_loading)
        if image_filepath:
            for n, image in enumerate(self.images_list):
                if os.path.normpath(image.filepath) == os.path.normpath(image_filepath):
                    self._index = n
            if self._index == -1:
                # it happens when image_filepath points to non-image file
                if self.images_list:
                    self.index = 0
                # raise Exception("Should never happen")
        else:
            self._index = 0
        self.columns = []

    modifiers_attrs = [
        'deep_scan',
    ]

    def get_phantomed_image_list(self):
        phantom_image = LibraryData().phantom_image
        return itertools.chain(self.images_list, [phantom_image])

    def get_phantomed_image_rows(self, count):
        rows = []
        images = self.images_list
        for i in range(0, len(images), count):
            row = images[i:i+count]
            row.append(LibraryData().phantom_image)
            rows.append(row)
        return rows

    def get_modifiers(self):
        modifiers = []
        for ma in self.modifiers_attrs:
            if getattr(self, ma, None):
                s = f'-{ma}'
                modifiers.append(s)
        return " ".join(modifiers)

    def set_modifiers(self, modifiers_string):
        # print('set_modifiers')
        for ma in self.modifiers_attrs:
            s = f'-{ma}'
            value = s in modifiers_string
            setattr(self, ma, value)
            to_print = f"{ma} is set to {value}"
            # print(to_print)

    def do_sort(self, sort_type, reversed=False):
        image_data = self.current_image()
        key_function = None
        if sort_type != "original":
            if sort_type == "filename":
                key_function = operator.attrgetter("filename")
            elif sort_type == "creation_date":
                key_function = operator.attrgetter("creation_date")
            self.images_list = list(sorted(
                self.images_list,
                key=key_function,
                reverse=reversed
            ))
        else:
            self.images_list = self.original_list[:]
        self._index = self.images_list.index(image_data)
        self.sort_type = sort_type
        self.sort_type_reversed = reversed

    def get_current_image_name(self):
        try:
            im = self.images_list[self._index]
            return os.path.basename(im.filepath)
        except:
            return ""

    def current_image(self):
        try:
            return self.images_list[self._index]
        except:
            return ImageData("", None)

    def next_image(self):
        if self._index < len(self.images_list)-1:
            # self._index += 1
            self.set_current_index(self._index + 1)
        return self.current_image()

    def previous_image(self):
        if self._index > 0:
            # self._index -= 1
            self.set_current_index(self._index - 1)
        return self.current_image()

    def count(self):
        return len(self.images_list)

    def get_current_index(self):
        return self._index

    def set_current_index(self, index):
        self.before_index = self._index
        self._index = index
        # folder_data = self
        # mw = LibraryData.globals.main_window
        # mw.update_thumbnails_row_relative_offset(folder_data)

    def is_fav_folder(self):
        return LibraryData().fav_folder is self

    def is_tag_folder(self):
        return self.tag_data is not None

    def is_comments_folder(self):
        return LibraryData().comments_folder is self

    def get_current_thumbnail(self):
        if self.is_fav_folder():
            return LibraryData().globals.FAV_BIG_ICON
        elif self.is_tag_folder():
            return LibraryData().globals.TAG_BIG_ICON
        elif self.is_comments_folder():
            return LibraryData().globals.COMMENTS_BIG_ICON
        else:
            try:
                return self.images_list[self._index].get_thumbnail()
            except:
                path = os.path.join(os.path.dirname(__file__), "missing.jpg")
                ico = QIcon()
                ico.addPixmap(QPixmap(path))
                return ico.pixmap(QSize(50, 50))

    def create_library_columns(self, columns_count, preview_width, thread_instance=None):
        if self.images_list:
            columns = []
            for i in range(columns_count):
                columns.append(LibraryModeImageColumn())
            def choose_min_height_column():
                min_height = 100000000000000
                min_col = None
                for col in columns:
                    if min_height > col.height:
                        min_height = col.height
                        min_col = col
                return min_col
            for n, image_data in enumerate(self.images_list):
                col = choose_min_height_column()
                col.add_image(image_data)

            self.columns = columns
            self.previews_scroll_offset = 0
            self.columns_count = columns_count
        self.column_width = preview_width

        if thread_instance is not None:
            thread_instance.update_signal.emit(None)
        else:
            LibraryData().globals.main_window.update()

class ImageData():
    def get_creation_date(self, path_to_file):
        if platform.system() == 'Windows':
            return os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                return stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                return stat.st_mtime

    def get_disk_size(self, filepath):
        try:
            return os.path.getsize(filepath)
        except Exception as e:
            return 0

    def __init__(self, filepath, folder_data):
        super().__init__()
        self.scale = None
        self.position = None
        self.hint_position = None
        self.image_rotation = 0
        self.is_supported_filetype = True
        self.thumbnail = None or LibraryData().globals.DEFAULT_THUMBNAIL
        self.folder_data = folder_data
        self.filename = os.path.basename(filepath)
        self.filepath = filepath
        self.preview_size = QSize(0, 0)
        self.anim_paused = False
        self.svg_scale_factor = 20
        self.anim_cur_frame = 0

        self.source_width = 0
        self.source_height = 0

        if self.filepath and not LibraryData().globals.lite_mode:
            if LibraryData.is_interest_file(self.filepath):
                self.md5, self.md5_tuple = generate_md5(self.filepath)
            else:
                self.md5, self.md5_tuple = "", ()
            self.creation_date = self.get_creation_date(self.filepath)
            self.image_metadata = dict()
            self.disk_size = self.get_disk_size(self.filepath)
        else:
            self.creation_date = 0
            self.md5, self.md5_tuple = "", ()
            self.image_metadata = dict()
            self.disk_size = 0
            # надо для boards, иначе будет вылет
            self.preview = generate_info_pixmap("В группе\nнет изображений", "", size=1000, no_background=False)
            self.source_width = self.preview.width()
            self.source_height = self.preview.height()

        self.board_item = None

        # UI
        self._touched = False               # обнуляется после отпускания кнопки мыши
        self._selected = False              # обнуляется после каждого перемещения
        self._is_phantom = False

    def store_ui_data(self):
        MW = LibraryData().globals.main_window
        self.scale = MW.image_scale
        self.position = MW.image_center_position - QPointF(MW.width()/2, MW.height()/2).toPoint()
        self.image_rotation = MW.image_rotation
        if MW.animated:
            self.anim_cur_frame = MW.movie.currentFrameNumber()

    def load_ui_data(self, cp=None):
        MW = LibraryData().globals.main_window
        if self.scale:
            MW.image_scale = self.scale
        if self.position or True:
            new_pos = (self.position or QPoint(0, 0)) + QPointF(MW.width()/2, MW.height()/2).toPoint()
            animation_needed = cp != new_pos
            if not animation_needed:
                pass
                # print("позиции центральной точки одинаковые, анимация не нужна")
            if cp and animation_needed:
                MW.block_paginating = True
                MW.animate_properties(
                    [(MW, "image_center_position", cp, new_pos, MW.update)],
                    duration=0.1,
                    callback_on_finish=lambda: setattr(MW, "block_paginating", False),
                    anim_id="paginating"
                )
            else:
                MW.image_center_position = new_pos
        if self.image_rotation:
            MW.image_rotation = self.image_rotation
        self.update_fav_button_state()
        if MW.animated and self.anim_paused:
            MW.movie.jumpToFrame(self.anim_cur_frame)
            MW.get_rotated_pixmap(force_update=True)

    def update_fav_button_state(self):
        if LibraryData().globals.lite_mode:
            return
        favorite_btn = LibraryData().globals.control_panel.favorite_btn
        if LibraryData().is_in_fav_list(self):
            favorite_btn.setText("-")
            favorite_btn.id = "favorite_added"
        else:
            favorite_btn.setText("+")
            favorite_btn.id = "favorite"

    def set_thumbnail(self, thumbnail):
        self.thumbnail = thumbnail

    def get_thumbnail(self):
        return self.thumbnail

    def __repr__(self):
        filename = os.path.basename(self.filepath)
        return f'IMAGE from {filename}'





class FinderWindow(QWidget):

    isWindowVisible = False
    is_initialized = False

    button_style = """QPushButton{
        font-size: 20px;
        color: #303940;
        text-align: center;
        border-radius: 5px;
        background: rgb(220, 220, 220);
        font-family: 'Consolas';
        font-weight: bold;
        border: 3px dashed #303940;
        padding: 5px;
        height: 40px;
    }
    QPushButton:hover{
        background-color: rgb(253, 203, 54);
        color: black;
    }
    QPushButton#red, QPushButton#green{
        color: rgb(210, 210, 210);
        background-color: none;
        border: none;
    }
    QPushButton#green{
        color: rgb(70, 200, 70);
    }
    QPushButton#red{
        color: rgb(220, 70, 70);
    }
    QPushButton#red:hover{
        color: rgb(200, 0, 0);
        background-color: rgba(220, 50, 50, 0.1);
    }
    QPushButton#green:hover{
        color: rgb(0, 220, 0);
        background-color: rgba(50, 220, 50, 0.1);
    }
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(FinderWindow, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    @classmethod
    def center_if_on_screen(cls):
        if hasattr(cls, "instance"):
            window = cls.instance
            if window.isVisible():
                cls.pos_at_center(window)

    def show(self, *args):
        super().show()

    @classmethod
    def pos_at_center(cls, self):

        MW = self.parent()
        cp = QDesktopWidget().availableGeometry().center()
        cp = MW.rect().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.activateWindow()

    def __init__(self, parent):
        if self.is_initialized:
            return

        super().__init__(parent)

        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self.resize(parent.rect().width()-200, parent.rect().height()-400)
        # show at center
        FinderWindow.pos_at_center(self)
        # ui init
        main_style = "font-size: 11pt; font-family: 'Consolas'; "
        style = main_style + " color: white; "
        editfieled_style = style + " background-color: transparent; border: none; "
        main_style_button = "font-size: 13pt; padding: 5px 0px;"

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        label = QLabel()
        label.setText("Поиск потерянных файлов")
        label.setFixedHeight(50)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(style)
        main_layout.addWidget(label)

        self.first_label = QLabel()
        self.first_label.setStyleSheet(style)
        main_layout.addWidget(self.first_label)

        self.second_label = QLabel()
        self.second_label.setStyleSheet(style)
        main_layout.addWidget(self.second_label)

        self.output_field = QTextEdit()
        self.output_field.setStyleSheet(editfieled_style)
        self.output_field.setText("\n"*59)


        scroll_bars_style = """
            QScrollBar {
                border-radius: 5px;
                background: rgb(40, 50, 60);
            }
            QScrollBar:vertical {
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle {
                background: rgb(210, 210, 210);
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                width: 10px;
                min-height: 10px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                 background: transparent;
            }
            QScrollBar::sub-line:vertical {
                 background: transparent;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                 background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                 background: transparent;
            }

            QScrollArea:vertical {
                height: 15px;
                background-color: transparent;
                border: none;
            }

            QTextEdit{
                color: white;
                background-color: transparent;
                border: none;
            }

            """


        self.output_field.setStyleSheet(scroll_bars_style)
        main_layout.addWidget(self.output_field)

        green_button = QPushButton("Зелёная")
        green_button.clicked.connect(self.green_button_handler)
        green_button.setStyleSheet(main_style_button)


        red_button = QPushButton("Красная")
        red_button.clicked.connect(self.red_button_handler)
        red_button.setStyleSheet(main_style_button)
        red_button.setCursor(Qt.PointingHandCursor)

        green_button.setStyleSheet(self.button_style)
        green_button.setObjectName("green")
        green_button.setCursor(Qt.PointingHandCursor)

        red_button.setStyleSheet(self.button_style)
        red_button.setObjectName("red")

        buttons = QHBoxLayout()
        buttons.addWidget(green_button)
        buttons.addWidget(red_button)
        # main_layout.addSpacing(0)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # self.setParent(parent)

        FinderWindow.isWindowVisible = True
        self.is_initialized = True

    def red_button_handler(self):
        self.hide()

    def green_button_handler(self):
        self.hide()

    def hide(self):
        FinderWindow.isWindowVisible = False
        super().hide()

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setOpacity(0.9)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(Qt.black))
        painter.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)
        painter.end()


    def mousePressEvent(self, event):
        pass
    def mouseMoveEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        pass


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.red_button_handler()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.red_button_handler()


# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
