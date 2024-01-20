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
from collections import defaultdict


class CommentingLibraryDataMixin():
    pass

    def get_comments_list_path(self):
        filepath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.COMMENTS_FILENAME)
        create_pathsubfolders_if_not_exist(os.path.dirname(filepath))
        return filepath

    def load_comments_list(self):
        self.comments_storage = defaultdict(list)

        ItemRecord = namedtuple("ItemRecord", CommentData.fields)
        files = []
        if os.path.exists(self.get_comments_list_path()):
            print("loading comment data")
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
                    self.comments_storage[comment_id].append(comment)
            except Exception as e:
                # raise
                errors = True
            if errors:
                _path = self.get_comments_list_path()
                to_print = f"Ошибки при чтении файла {_path}"
                print(to_print)
        files = list(set(files))

        self.comments_folder = self.create_folder_data("С комментариями", files, image_filepath=None, virtual=True)

    def store_comments_list(self):
        elements = []
        for img_id, comments_list in self.comments_storage.items():
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

    def image_data_comment_id(self, image_data):
        return (image_data.md5, image_data.disk_size)

    def delete_comment(self, comment):
        ret = QMessageBox.question(None,'Удаление комментария',
            f'Комент "{comment.get_title()}". Удалить его?',
            QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.No:
            return

        ci = self.current_folder().current_image()
        _id = self.image_data_comment_id(ci)
        try:
            self.comments_storage[_id].remove(comment)
        except:
            pass
        # удаляем из папки, если коментов нет
        if not self.comments_storage[_id]:
            comments_folder = self.comments_folder
            for image in comments_folder.images_list:
                if compare_md5_strings(image.md5, ci.md5) and image.disk_size == ci.disk_size:
                    comments_folder.images_list.remove(image)
        self.store_comments_list()

    def add_image_to_comments_folder(self, image_data):
        comments_folder = None
        for folder_data in self.folders:
            if folder_data.comm:
                comments_folder = folder_data
                break
        comments_folder.images_list.append(image_data)

    def retrieve_lost_records_in_comments(self):
        lost_records = []
        for image_id, image_comments in self.comments_storage.items():
            for comment in image_comments:
                path = comment.filepath
                if not os.path.exists(path):
                    lost_records.append(
                        (comment.md5, comment.disk_size, comment.filepath, 'comment')
                    )
        return lost_records

    def get_comments_for_image(self):
        ci = self.current_folder().current_image()
        _id = self.image_data_comment_id(ci)
        return self.comments_storage[_id]

class CommentingMixin():

    def get_comment_rect_info(self):
        rect = build_valid_rect(self.COMMENT_RECT_INPUT_POINT1, self.COMMENT_RECT_INPUT_POINT2)
        im_rect = self.get_image_viewport_rect()
        screen_delta1 = rect.topLeft() - im_rect.topLeft()
        screen_delta2 = rect.bottomRight() - im_rect.topLeft()

        left = screen_delta1.x()/im_rect.width()
        top = screen_delta1.y()/im_rect.height()

        right = screen_delta2.x()/im_rect.width()
        bottom = screen_delta2.y()/im_rect.height()

        return left, top, right, bottom

    def image_comment_mousePressEvent(self, event):
        if self.Globals.lite_mode:
            self.show_center_label("Комментарии нельзя задавать и просматривать в упрощённом режиме", error=True)
            return
        cf = self.LibraryData().current_folder()
        ci = cf.current_image()
        if ci:
            self.COMMENT_RECT_INPUT_POINT1 = event.pos()
            self.COMMENT_RECT_INPUT_POINT2 = event.pos()
            if self.comment_data_candidate:
                self.comment_data = self.comment_data_candidate
                self.image_comment_update_rect(event)
            else:
                left, top, right, bottom = self.get_comment_rect_info()
                self.comment_data = CommentData.create_comment(self.LibraryData, ci, left, top, right, bottom)
        self.update()

    def image_comment_update_rect(self, event):
        if self.comment_data is not None:
            self.COMMENT_RECT_INPUT_POINT2 = event.pos()
            left, top, right, bottom = self.get_comment_rect_info()
            self.comment_data.left = left
            self.comment_data.top = top
            self.comment_data.right = right
            self.comment_data.bottom = bottom
        self.update()

    def image_comment_mouseMoveEvent(self, event):
        if self.Globals.lite_mode:
            return
        self.image_comment_update_rect(event)
        self.update()

    def image_comment_mouseReleaseEvent(self, event):
        if self.Globals.lite_mode:
            return
        self.image_comment_update_rect(event)
        self.LibraryData().store_comments_list()
        if self.comment_data_candidate is None:
            CommentWindow(self).show(self.comment_data, 'new')
        self.comment_data = None
        self.comment_data_candidate = None
        self.update()

    def draw_comments(self, painter):

        if self.Globals.lite_mode:
            return

        old_pen = painter.pen()
        old_brush = painter.brush()

        for comment in self.LibraryData().get_comments_for_image():
            painter.setPen(QPen(Qt.yellow, 1))
            painter.setBrush(Qt.NoBrush)
            im_rect = self.get_image_viewport_rect()

            base_point = im_rect.topLeft()

            # abs is for backwards compatibility
            screen_left = base_point.x() + im_rect.width()*comment.left
            screen_top = base_point.y() + im_rect.height()*comment.top

            screen_right = base_point.x() + im_rect.width()*comment.right
            screen_bottom = base_point.y() + im_rect.height()*comment.bottom

            comment_rect = QRectF(
                QPointF(screen_left, screen_top),
                QPointF(screen_right, screen_bottom)
            ).toRect()
            comment.screen_rect = comment_rect
            cursor_inside = comment_rect.contains(self.mapFromGlobal(QCursor().pos()))
            if cursor_inside:
                painter.setOpacity(1.0)
            else:
                painter.setOpacity(0.5)
            painter.drawRect(comment_rect)
            painter.setOpacity(1.0)

            text_to_draw = f'{comment.date_str}\n{comment.date_edited_str}\n{comment.text}'
            rect = painter.drawText(QRect(), Qt.AlignLeft, text_to_draw)

            if cursor_inside:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(Qt.black))
                rect.moveTopLeft(comment_rect.bottomLeft())
                painter.drawRect(rect)
                painter.setPen(QPen(Qt.white))
                painter.drawText(rect, Qt.AlignLeft, text_to_draw)

        painter.setPen(old_pen)
        painter.setBrush(old_brush)

    def center_comment_window(self):
        CommentWindow.center_if_on_screen()

    def show_comment_form(self, sel_comment):
        CommentWindow(self).show(sel_comment, 'edit')


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
    def create_comment(cls, LibraryData, image_data, left, top, right, bottom):
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

        _id = LibraryData().image_data_comment_id(image_data)
        LibraryData().comments_storage[_id].append(comm)

        # добавление в папку
        comments_folder = LibraryData().comments_folder
        found = False
        for image in comments_folder.images_list:
            if compare_md5_strings(image.md5, image_data.md5) and image.disk_size == image_data.disk_size:
                found = True
        if not found:
            comments_folder.images_list.append(image_data)

        return comm


class CommentWindow(QWidget):

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
    QPushButton#exit, QPushButton#save{
        color: rgb(210, 210, 210);
        background-color: none;
        border: none;
    }
    QPushButton#save{
        color: rgb(70, 200, 70);
    }
    QPushButton#exit{
        color: rgb(220, 70, 70);
    }
    QPushButton#exit:hover{
        color: rgb(200, 0, 0);
        background-color: rgba(220, 50, 50, 0.1);
    }
    QPushButton#save:hover{
        color: rgb(0, 220, 0);
        background-color: rgba(50, 220, 50, 0.1);
    }
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls.instance = super(CommentWindow, cls).__new__(cls, *args, **kwargs)
        return cls.instance

    @classmethod
    def center_if_on_screen(cls):
        if hasattr(cls, "instance"):
            window = cls.instance
            if window.isVisible():
                cls.pos_at_center(window)

    def show(self, *args):
        if args:
            self.comment, reason = args
            if reason == "edit":
                self.comment.date_edited = time.time()
                self.comment.update_strings()
            self.editfield.setText(self.comment.text)
            self.date_label.setText(f'Создано: {self.comment.date_str}')
            if self.comment.date_edited:
                self.date_edited_label.setText(f'Отредактировано: {self.comment.date_edited_str}')
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

        self.resize(1000, 400)
        # show at center
        CommentWindow.pos_at_center(self)
        # ui init
        main_style = "font-size: 11pt; font-family: 'Consolas'; "
        style = main_style + " color: white; "
        editfieled_style = style + " background-color: transparent; border: none; "
        main_style_button = "font-size: 13pt; padding: 5px 0px;"

        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignTop)
        label = QLabel()
        label.setText("Редактирование комента")
        label.setFixedHeight(50)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(style)
        main_layout.addWidget(label)

        self.date_label = QLabel()
        self.date_label.setStyleSheet(style)
        main_layout.addWidget(self.date_label)

        self.date_edited_label = QLabel()
        self.date_edited_label.setStyleSheet(style)
        main_layout.addWidget(self.date_edited_label)

        self.editfield = QTextEdit()
        self.editfield.setFixedHeight(300)
        self.editfield.setStyleSheet(editfieled_style)
        main_layout.addWidget(self.editfield)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_button_handler)
        save_button.setStyleSheet(main_style_button)
        exit_button = QPushButton("Закрыть")
        exit_button.clicked.connect(self.exit_button_handler)
        exit_button.setStyleSheet(main_style_button)

        save_button.setStyleSheet(self.button_style)
        save_button.setObjectName("save")

        exit_button.setStyleSheet(self.button_style)
        exit_button.setObjectName("exit")

        buttons = QHBoxLayout()
        buttons.addWidget(save_button)
        buttons.addWidget(exit_button)
        # main_layout.addSpacing(0)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        # self.setParent(parent)

        CommentWindow.isWindowVisible = True
        self.is_initialized = True

    def exit_button_handler(self):
        self.hide()

    def save_button_handler(self):
        self.comment.text = self.editfield.toPlainText()
        self.parent().LibraryData().store_comments_list()
        self.hide()

    def hide(self):
        CommentWindow.isWindowVisible = False
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

    # pass для того, чтобы метод предка не вызывался
    # и событие не ушло в родительское окно
    def mousePressEvent(self, event):
        pass
    def mouseMoveEvent(self, event):
        pass
    def mouseReleaseEvent(self, event):
        pass


    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.exit_button_handler()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.exit_button_handler()



# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
