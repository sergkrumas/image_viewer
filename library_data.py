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

from collections import defaultdict
import datetime

import locale
locale.setlocale(locale.LC_ALL, "russian")

ThreadRuntimeData = namedtuple("ThreadData", "id current count ui_name")

class ThumbnailsThread(QThread):
    update_signal = pyqtSignal(object)
    threads_pool = []
    def __init__(self, folder_data, _globals):
        QThread.__init__(self)
        self.needed_thread = True
        self.ui_name = folder_data.folder_path
        self.folder_data = folder_data
        images_data = folder_data.images_list
        in_process = images_data in [thread.images_data for thread in self.threads_pool]
        previews_done = folder_data.previews_done
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

def get_id_from_image_data(image_data):
    return (image_data.md5, image_data.disk_size)

class CommentData(object):

    fields = [
        "md5",
        "disk_size",
        "filepath",
        "date",
        "date_str",
        "date_edited",
        "date_edited_str",
        "left",
        "top",
        "right",
        "bottom",
        "text",
        "separator_field",
    ]

    def __init__(self, *args, **kwargs):
        self.date = None
        self.date_edited = None

    def decode_data(self):

        self.disk_size = int(self.disk_size)

        self.date = float(self.date)
        try:
            self.date_edited = float(self.date_edited)
        except:
            self.date_edited = None

        self.left = float(self.left)
        self.top = float(self.top)
        self.right = float(self.right)
        self.bottom = float(self.bottom)

        self.text = self.text.replace("\\n", "\n").replace("\\t", "\t")

        self.update_strings()

    def update_strings(self):
        if self.date is not None:
            date_time = datetime.datetime.fromtimestamp( float(self.date) )
            self.date_str = date_time.strftime("%d %B %Y %X")
        else:
            self.date_str = ""

        if self.date_edited is not None:
            date_time = datetime.datetime.fromtimestamp( float(self.date_edited) )
            self.date_edited_str = date_time.strftime("%d %B %Y %X")
        else:
            self.date_edited_str = ""

    def encode_data(self):
        comm = CommentData()
        for attr_name in CommentData.fields:
            setattr(comm, attr_name, getattr(self, attr_name))

        return comm

    def get_title(self):
        SIZE_LIMIT = 10
        if len(self.text) > SIZE_LIMIT:
            return f'{self.text[:SIZE_LIMIT]}...'
        else:
            return self.text

    @classmethod
    def create_comment(cls, image_data, left, top, right, bottom):
        comm = CommentData()

        comm.md5 = image_data.md5
        comm.disk_size = int(image_data.disk_size)

        comm.filepath = image_data.filepath
        comm.date = time.time()
        comm.date_edited = None
        comm.update_strings()

        comm.left = left
        comm.top = top
        comm.right = right
        comm.bottom = bottom
        comm.text = ""

        comm.separator_field = ""

        _id = get_id_from_image_data(image_data)
        LibraryData().comments_dict[_id].append(comm)

        # добавление в папку
        comments_folder = LibraryData().comments_folder
        found = False
        for image in comments_folder.images_list:
            if image.md5 == image_data.md5 and image.disk_size == image_data.disk_size:
                found = True
        if not found:
            comments_folder.images_list.append(image_data)

        return comm

class LibraryData(object):
    def __new__(cls, _globals=None):
        if not hasattr(cls, 'instance'):
            cls.instance = super(LibraryData, cls).__new__(cls)
            i = cls.instance
            i._current_folder = None
            i.folders = []
            i._index = -1
            i.folderslist_scroll_offset = 0
            i.fav_folder = None
            i.viewed_list = []
            i.from_library_mode = False
            i.load_fav_list()
            i.load_comments_list()
            i.load_session_file()
        return cls.instance

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

    def any_content(self):
        return bool(self.folders)

    def get_fav_folder(self):
        return self.fav_folder

    def get_comments_list_path(self):
        return os.path.join(os.path.dirname(__file__), self.globals.COMMENTS_FILENAME)

    def load_comments_list(self):
        print("loading comment data")
        self.comments_dict = defaultdict(list)
        ItemRecord = namedtuple("ItemRecord", CommentData.fields)
        files = []
        if os.path.exists(self.get_comments_list_path()):
            errors = False
            with open(self.get_comments_list_path(), "r", encoding="utf8") as comments_file:
                txt_data = comments_file.read()
            try:
                elements = txt_data.split("\n")
                fields_count = ItemRecord._fields.__len__()
                data = itertools.zip_longest(*(iter(elements),)*fields_count)
                for item in data:
                    item = ItemRecord(*item)
                    if item.filepath is None:
                        continue
                    files.append(item.filepath)
                    comment = CommentData()
                    for attr_name in ItemRecord._fields:
                        setattr(comment, attr_name, getattr(item, attr_name))
                    comment.decode_data()
                    comment_id = (comment.md5, comment.disk_size)
                    self.comments_dict[comment_id].append(comment)
            except Exception as e:
                # raise
                errors = True
            if errors:
                _path = self.get_comments_list_path()
                to_print = f"Ошибки при чтении файла {_path}"
                print(to_print)
        files = list(set(files))
        self.create_folder_data("С комментариями", files, image_filepath=None, comm=True)

    def store_comments_list(self):
        elements = []
        for img_id, comments_list in self.comments_dict.items():
            for comment in comments_list:
                elements.append(comment)
        data_to_out = []
        for el in elements:
            encoded_text = repr(el.text).strip("'")
            info_lines = (
                f"{el.md5}",
                f"{el.disk_size}",
                f"{el.filepath}",
                f"{el.date}",
                f"{el.date_str}",
                f"{el.date_edited}",
                f"{el.date_edited_str}",
                f"{el.left}",
                f"{el.top}",
                f"{el.right}",
                f"{el.bottom}",
                f"{encoded_text}",
                f"{el.separator_field}"
            )
            comment_data = "\n".join(info_lines)
            data_to_out.append(f'{comment_data}')
        data_to_write = "\n".join(data_to_out)
        with open(self.get_comments_list_path(), "w+", encoding="utf8") as comments_file:
            comments_file.write(data_to_write)

    @classmethod
    def delete_comment(cls, comment):

        ret = QMessageBox.question(None,'',
            f'Комент "{comment.get_title()}". Удалить его?',
            QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return

        ci = LibraryData().current_folder().current_image()
        _id = get_id_from_image_data(ci)
        try:
            LibraryData().comments_dict[_id].remove(comment)
        except:
            pass
        # удаляем из папки, если коментов нет
        if not LibraryData().comments_dict[_id]:
            comments_folder = LibraryData().comments_folder
            for image in comments_folder.images_list:
                if image.md5 == ci.md5 and image.disk_size == ci.disk_size:
                    comments_folder.images_list.remove(image)
        LibraryData().store_comments_list()

    @classmethod
    def get_comments_for_image(cls):
        ci = LibraryData().current_folder().current_image()
        _id = get_id_from_image_data(ci)
        return LibraryData().comments_dict[_id]

    def create_folder_data(self, folder_path, files, image_filepath=None, fav=False, comm=False):
        folder_data = FolderData(folder_path, files,
            image_filepath=image_filepath,
            fav=fav,
            comm=comm
        )
        self.folders.append(folder_data)
        if fav:
            self.fav_folder = folder_data
        if comm:
            self.comments_folder = folder_data
        self._current_folder = folder_data

        # удаление дубликатов и копирование модификаторов с них
        for fd in LibraryData().folders:
            if fd.folder_path == folder_path:
                if fd != folder_data:
                    # folder_data.set_modifiers(fd.get_modifiers())
                    LibraryData().folders.remove(fd)
                    to_print = f"dublicated item removed: {fd.folder_path}"
                    print(to_print)
                    # break
                    # иногда дубликатов получается больше, чем 2, поэтому break отменяется

        # индекс задаём только после удаления дубликатов
        self._index = self.folders.index(folder_data)
        return self._current_folder

    def find_modifiers(self, path):
        for fd in LibraryData().folders:
            if fd.folder_path == path:
                return fd.get_modifiers()
        return ""

    def all_folders(self):
        return self.folders

    def current_folder(self):
        return self._current_folder

    def pre_choose(self):
        im = LibraryData().current_folder().current_image()
        im.save_data()

    def post_choose(self):
        MW = self.globals.main_window
        im = LibraryData().current_folder().current_image()
        MW.show_image(im)
        im.load_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()

    def choose_that_folder(self, folder_data):
        self._index = self.folders.index(folder_data)
        self._current_folder = self.folders[self._index]
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
        # self.pre_choose()
        if self._index > 0:
            self._index -= 1
        else:
            self._index = len(self.folders)-1
        self._current_folder = self.folders[self._index]
        # self.post_choose()
        MW = self.globals.main_window
        MW.previews_list_active_item = None
        MW.autoscroll_set_or_reset()
        self.update_current_folder_columns()
        MW.update()

    def choose_next_folder(self):
        # self.pre_choose()
        if self._index < len(self.folders)-1:
            self._index += 1
        else:
            self._index = 0
        self._current_folder = self.folders[self._index]
        # self.post_choose()
        MW = self.globals.main_window
        MW.previews_list_active_item = None
        MW.autoscroll_set_or_reset()
        self.update_current_folder_columns()
        MW.update()

    def choose_doom_scroll(self):
        if len(self.folders) == [0, 1]:
            return
        self.pre_choose()
        indexes_it = itertools.cycle(range(len(self.folders)))
        index_ = None
        while index_ != self._index:
            index_ = next(indexes_it)
        self._index = next(indexes_it)
        self._current_folder = self.folders[self._index]
        self.post_choose()
        ThumbnailsThread(self._current_folder, self.globals).start()
        MW = self.globals.main_window
        MW.update()

    def delete_current_image(self):
        cf = self.current_folder()
        ci = cf.current_image()
        if ci in cf.images_list: #служебные объекты ImageData не находятся в списке
            # prepare
            cf.set_current_index(max(0, cf.images_list.index(ci)-1))
            delete_to_recyclebin(ci.filepath)
            MW = self.globals.main_window
            MW.show_center_label(f"Файл\n{ci.filepath}\n удален в корзину")
            cf.images_list.remove(ci)
            # show next
            im_data = self.current_folder().current_image()
            MW.show_image(im_data)
            cf.current_image().load_data()
            MW.set_window_title(MW.current_image_details())
            LibraryData.update_current_folder_columns()
            MW.update()

    def show_that_preview_in_viewer_mode(self, image_data):
        fd = image_data.folder_data
        self._index = self.folders.index(fd)
        self._current_folder = self.folders[self._index]
        fd._index = fd.images_list.index(image_data)
        # change mode to preview
        MW = self.globals.main_window
        MW.toggle_viewer_library_mode()
        self.from_library_mode = True

    def show_next_image(self):
        MW = self.globals.main_window
        if MW.isBlockedByAnimation():
            return
        MW.hide_center_label()
        cf = LibraryData().current_folder()
        old_current = cf.current_image()
        cf.current_image().save_data()
        old_center_pos = MW.image_center_position
        im_data = cf.next_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_data(cp=old_center_pos)
        else:
            cf.current_image().load_data()
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
        cf.current_image().save_data()
        old_center_pos = MW.image_center_position
        im_data = cf.previous_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_data(cp=old_center_pos)
        else:
            cf.current_image().load_data()
        MW.set_window_title(MW.current_image_details())
        MW.update()
        if old_current == cf.current_image():
            self.globals.control_panel.quick_show()
        self.add_current_image_to_view_history()

    def move_image(self, before_index, after_index, dec_index):
        if before_index is None:
            return

        cf = self.current_folder()
        # получаем сначала текущее изображение
        current_image = cf.current_image()

        if dec_index:
            after_index -=1
        after_index = max(0, after_index)
        the_image = cf.images_list[before_index]
        self.current_folder().images_list.remove(the_image)
        self.current_folder().images_list.insert(after_index, the_image)

        # оставляем текущую картинку текущей
        cf.set_current_index(cf.images_list.index(current_image))

    def jump_to_image(self, index, leave_history_record=True):
        MW = self.globals.main_window
        if MW.isBlockedByAnimation():
            return
        MW.hide_center_label()
        cf = LibraryData().current_folder()
        cf.current_image().save_data()
        old_center_pos = MW.image_center_position
        cf.set_current_index(index)
        im_data = cf.current_image()
        MW.show_image(im_data)
        if MW.isAnimationEffectsAllowed():
            cf.current_image().load_data(cp=old_center_pos)
        else:
            cf.current_image().load_data()
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
            self.pre_choose()
            new_fd = selected_im.folder_data
            self._current_folder = new_fd
            self._index = self.folders.index(new_fd)
            self.post_choose()

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
        cf = LibraryData().current_folder()
        if cf.fav:
            MW.show_center_label('Нельзя удалять изображение находясь в папке Избранное')
            return
        else:
            LibraryData().choose_previous_folder()
            LibraryData().folders.remove(cf)
        LibraryData().store_session_file()
        MW.update()

    def update_current_folder(self):
        cf = LibraryData().current_folder()
        if cf.fav:
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
        return os.path.join(os.path.dirname(__file__), LibraryData().globals.SESSION_FILENAME)

    @staticmethod
    def load_session_file():
        if LibraryData().globals.isolated_mode:
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
                LibraryData().handle_input_data(
                    item.folder_path,
                    pre_load=True,
                    content_hash=item.content_hash,
                    modifiers=item.modifiers
                )
        if LibraryData().globals.is_path_exists:
            # сохраняем заново, чтобы отвалилось всё то,
            # что корректно не открылось в handle_input_data
            LibraryData().store_session_file()

    @staticmethod
    def store_session_file():
        if LibraryData().globals.isolated_mode:
            return
        # TODO здесь из-за f_d.current_image().filepath может быть баг,
        # когда папка не сохранится, потому что данных нет
        is_ok = lambda x: not x.fav and x.current_image().filepath
        folders_data = [f_d for f_d in LibraryData().folders if is_ok(f_d)]
        data_to_out = []
        for fd in folders_data:
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
        return os.path.join(os.path.dirname(__file__), self.globals.FAV_FILENAME)

    def load_fav_list(self):
        print("loading favourite data")
        ItemRecord = namedtuple("ItemRecord", "md5 filepath disk_size separator_field")
        files = []
        if os.path.exists(self.get_fav_list_path()):
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
        self.create_folder_data("Избранное", files, image_filepath=None, fav=True)

    def store_fav_list(self):
        images = self.get_fav_virtual_folder().images_list
        data_to_out = []
        for im in images:
            info_lines = (
                f"{im.md5}",
                f"{im.filepath}",
                f"{im.disk_size}",
            )
            favi_data = "\n".join(info_lines)
            data_to_out.append(f'{favi_data}\n')
        data_to_write = "\n".join(data_to_out)
        with open(self.get_fav_list_path(), "w+", encoding="utf8") as fav_file:
            fav_file.write(data_to_write)

    def get_comm_virutal_folder(self):
        for folder in self.folders:
            if folder.comm:
                return folder

    def get_fav_virtual_folder(self):
        for folder in self.folders:
            if folder.fav:
                return folder

    def fav_list_filepaths(self):
        return [a.filepath for a in self.get_fav_virtual_folder().images_list]

    def manage_favorite_list(self):
        # image_data = LibraryData().current_folder().current_image()
        image_data = self.globals.main_window.image_data
        if not image_data.filepath:
            return
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
        exts = [
            ".jpg", ".jpeg",
            ".jfif", # внутри jfif-файлы то же самое, что и jpeg или jpg
            ".bmp",
            ".gif",
            ".png",
            ".tga",
            ".svg",
            ".svgz",
            ".ico",
            ".tif", ".tiff",
            ".webp",
        ]
        for ext in exts:
            filepath = filepath.lower()
            if filepath.endswith(ext):
                return True
        return False

    @staticmethod
    def list_interest_files(folder_path, deep_scan=False):
        filepaths = []

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
        images_data = folder_data.images_list
        folder_data.previews_done = False
        data_length = len(images_data)
        Globals = LibraryData().globals
        for n, image_data in enumerate(images_data):
            if image_data.thumbnail != Globals.DEFAULT_THUMBNAIL:
                continue

            if thread_instance:
                # switch to main thread
                thread_instance.msleep(1)
            source = load_image_respect_orientation(image_data.filepath)
            if source.width() == 0 or source.height() == 0:
                source = Globals.ERROR_PREVIEW_PIXMAP
            if not image_data.is_supported_filetype:
                source = Globals.NOT_SUPPORTED_PIXMAP
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
                    data_length,
                    thread_instance.ui_name,
                )
                thread_instance.update_signal.emit(data)
            # preview
            ow = source.width()
            oh = source.height()
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
                        data_length,
                        data_length,
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
        to_print = f"reading image rotations in {filepath}"
        print(to_print)
        data = []
        if os.path.exists(filepath):
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
        with open(filepath, "w+", encoding="utf8") as f:
            data = []
            for image_data in cf.images_list:
                rotation = image_data.image_rotation
                if rotation != 0:
                    dir_path = os.path.basename(image_data.filepath)
                    imd_r_str = f"{dir_path}\n{rotation}\n"
                    data.append(imd_r_str)
            f.write("\n".join(data))
            to_print = f'Rotations written to: {filepath}'
            print(to_print)
        win32api.SetFileAttributes(filepath, win32con.FILE_ATTRIBUTE_HIDDEN)

    @staticmethod
    def handle_input_data(input_path, pre_load=False, content_hash=None, modifiers=""):

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
            fd = LibraryData().create_folder_data(folder_path, files, image_filepath=image_path)
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
            MW.show_image(fd.current_image())
            fd.current_image().update_fav_button_state()
            if MW.isAnimationEffectsAllowed():
                MW.animate_properties(
                    [("image_scale", 0.01, MW.image_scale)]
                )
            MW.update()
            MW.activateWindow()

            if MW.show_startpage:
                MW.show_startpage = False

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
                if f'{image_data.md5}' == content_hash:
                    fd.set_current_index(n)

        if not pre_load:
            MW.handling_input = False

    @staticmethod
    def write_history_file(path):
        root = os.path.dirname(__file__)
        history_file_path = os.path.join(root, "history.log")
        date = datetime.datetime.now().strftime("%d %b %Y %X")
        with open(history_file_path, "a+", encoding="utf8") as file:
            record = "%s %s\n" % (date, path)
            file.write(record)

class FolderData():

    def find_in_prev(self, filepath, prev):
        for image_data in prev:
            if os.path.normpath(filepath) == os.path.normpath(image_data.filepath):
                return image_data
        return None

    def init_images(self, files, prev=None):
        for filepath in files:
            processAppEvents(_all=True)
            if os.path.exists(filepath): # проверка нужна для папки Избранное
                im_data = None
                if prev:
                    im_data = self.find_in_prev(filepath, prev)
                if not im_data:
                    im_data = ImageData(filepath, self)
                self.images_list.append(im_data)
        self.original_list = self.images_list[:]
        self.sort_type = "original"
        self.sort_type_reversed = False
        if not self.fav and not self.comm:
            items = LibraryData.read_user_rotations_for_folder(self)
            for image_data in self.images_list:
                for filename, value in items:
                    if os.path.basename(image_data.filepath) == filename:
                        image_data.image_rotation = value
        for image_data in self.images_list:
            image_data.is_supported_filetype = LibraryData.is_interest_file(image_data.filepath)

    def __init__(self, folder_path, files, image_filepath=None, fav=False, comm=False):
        super().__init__()
        self.folder_path = folder_path
        self.fav = fav
        self.comm = comm
        self._index = -1
        self.images_list = []
        self.previews_done = False
        self.deep_scan = False
        self.viewed_list = []
        self.init_images(files)
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
        import operator
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
            self._index += 1
        return self.current_image()

    def previous_image(self):
        if self._index > 0:
            self._index -= 1
        return self.current_image()

    def count(self):
        return len(self.images_list)

    def current_index(self):
        return self._index

    def set_current_index(self, index):
        self._index = index

    def get_current_thumbnail(self):
        if self.fav:
            return LibraryData().globals.FAV_BIG_ICON
        else:
            try:
                return self.images_list[self.current_index()].get_thumbnail()
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

    # решение проблемы циклических импортов
    get_tags_func = None
    @classmethod
    def get_tags_function(cls):
        if cls.get_tags_func is None:
            cls.get_tags_func = __import__("tagging").get_tags_for_image_data
        return cls.get_tags_func

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
        self.tags_list = list()
        if self.filepath:
            self.md5, self.md5_tuple = generate_md5(self.filepath)
            self.creation_date = self.get_creation_date(self.filepath)
            self.image_metadata = dict()
            self.tags_list = ImageData.get_tags_function()(self)
            self.disk_size = self.get_disk_size(self.filepath)

    def save_data(self):
        MW = LibraryData().globals.main_window
        self.scale = MW.image_scale
        self.position = MW.image_center_position - QPointF(MW.width()/2, MW.height()/2).toPoint()
        self.hint_position = MW.hint_center_position
        self.image_rotation = MW.image_rotation
        if MW.animated:
            self.anim_cur_frame = MW.movie.currentFrameNumber()

    def load_data(self, cp=None):
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
                    [("image_center_position", cp, new_pos)],
                    duration=0.1,
                    callback_on_finish=lambda: setattr(MW, "block_paginating", False)
                )
            else:
                MW.image_center_position = new_pos
        if self.hint_position:
            MW.hint_center_position = self.hint_position
        if self.image_rotation:
            MW.image_rotation = self.image_rotation
        self.update_fav_button_state()
        if MW.animated and self.anim_paused:
            MW.movie.jumpToFrame(self.anim_cur_frame)
            MW.get_rotated_pixmap(force_update=True)

    def update_fav_button_state(self):
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

# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
