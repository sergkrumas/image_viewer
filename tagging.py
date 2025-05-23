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

import re
from collections import namedtuple


import urllib.parse
import random
import tempfile

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

HTML_FILEPATH = "generated.html"
HTML_FILEPATH = os.path.join(tempfile.gettempdir(), HTML_FILEPATH)
UI_TAGGING_ELEMENTS_IN_A_ROW = 14


class Vars():
    TAGS_BASE = dict()
    CURRENT_MAX_TAG_ID = 0

def text_to_list(t):
    t = t.strip()
    t = t.split(" ")
    t = [el.strip(",").strip(" ").strip() for el in t]
    # избавляемся от элементов типа пустых строк ""
    # которые образуются, если между словами было больше одного пробела
    t = [el for el in t if el]
    t = list(set(t))
    return t

def list_to_text(l):
    return " ".join(l)

def print_tag_to_html(tag):

    files_list = [record.filepath for record in tag.records]

    def to_URL(path):
            fpath_lower = os.path.normpath(path.lower())
            safe_string = urllib.parse.quote_plus(fpath_lower, safe='/\\ ', encoding=None, errors=None)
            return safe_string.replace("+", " ")

    files_list = [to_URL(filepath) for filepath in files_list]

    style = """
    <style type="text/css">
    body{
      padding: 0px;
      margin: 0px;
    }
    </style>
    """

    with open(HTML_FILEPATH, "w+", encoding="utf8") as file:
        file.write(style)
        file.write("<div>")

        file.write("<center><div><b>%s</b><br>%s</div><br><br><br></center>" % (tag.name, tag.description))

        for filepath in files_list:
            img = "<center><img src='file:///%s'></center>" % (filepath.replace("\\", "/"))
            file.write(img)

        file.write("</div>")

    os.system("start %s" % HTML_FILEPATH)

def get_base_tags():
    return list(Vars.TAGS_BASE.values())

def get_base_tag(tag_name):
    for tag in get_base_tags():
        if tag.name.lower() == tag_name.lower():
            return tag
    return None

class TagListRecord():

    def __init__(self, md5_str, disk_size, filepath):
        self.md5_str = md5_str
        self.disk_size = disk_size
        self.filepath = filepath

class Tag():

    def __init__(self, _id, name, description):
        self.id = _id
        self.name = name
        self.description = description
        self.records = []

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __hash__(self):
        return self.id

class TaggingLibraryDataMixin():

    def retrieve_lost_records_in_tags(self):
        lost_records = []
        for tag_id, tag_data in Vars.TAGS_BASE.items():
            for image_record in tag_data.records:
                path = image_record.filepath
                if not os.path.exists(path):
                    lost_records.append(
                        (image_record.md5_str, image_record.disk_size, image_record.filepath, 'tag')
                    )
        return lost_records

    def restore_tag_record(self, found_path, filepath, md5_str, disk_size):
        for tag_id, tag_data in Vars.TAGS_BASE.items():
            for image_record in tag_data.records:
                if filepath == image_record.filepath:
                    image_record.filepath = found_path
                    return tag_data
        return None

    def get_tagging_folderpath(self):
        folderpath = os.path.join(os.path.dirname(__file__), "user_data", self.globals.TAGS_ROOT)
        create_pathsubfolders_if_not_exist(folderpath)
        return folderpath

    def get_tags_for_image_data(self, image_data):
        return_list = list()
        for key, tag in Vars.TAGS_BASE.items():
            for record in tag.records:
                if compare_md5_strings(record.md5_str, image_data.md5):
                    return_list.append(tag)
        # status_string = f"{len(return_list)} get_tags_for_image_data {image_data.filepath}"
        # print(status_string)
        return return_list

    def delete_tag_from_library(self, tag):
        info_filepath, list_filepath = self.get_tag_data_filepaths(tag)

        if os.path.exists(info_filepath):
            os.remove(info_filepath)
        if os.path.exists(list_filepath):
            os.remove(list_filepath)

        for key, _tag in Vars.TAGS_BASE.items():
            if _tag is tag:
                Vars.TAGS_BASE.pop(key)
                break

        for fd in self.folders:
            if fd.virtual and fd.tag_data is tag:
                self.folders.remove(fd)
                break

    def get_tag_data_filepaths(self, tag):
        filename = f"ID{tag.id:04}"
        info_filepath = os.path.join(self.get_tagging_folderpath(), "%s.info" % filename)
        list_filepath = os.path.join(self.get_tagging_folderpath(), "%s.list" % filename)
        return info_filepath, list_filepath

    def store_tag_to_disk(self, tag):
        if not os.path.exists(self.get_tagging_folderpath()):
            os.mkdir(self.get_tagging_folderpath())

        info_filepath, list_filepath = self.get_tag_data_filepaths(tag)

        info_data = "\n".join([str(tag.name), tag.description])

        # !!!! пусть всегда должен быть последним, потому что в нём могут быть пробелы
        list_data = "\n".join([f"{r.md5_str} {r.disk_size} {r.filepath}" for r in tag.records])

        with open(info_filepath, "w+", encoding="utf8") as file:
            file.write(info_data)

        with open(list_filepath, "w+", encoding="utf8") as file:
            file.write(list_data)

    def load_tags(self):

        if not os.path.exists(self.get_tagging_folderpath()):
            print('load_tags_info::', self.get_tagging_folderpath(), "doesn't exist! Abort")
            return

        print('loading tags data')
        for filename in os.listdir(self.get_tagging_folderpath()):
            filepath = os.path.join(self.get_tagging_folderpath(), filename)

            # файлы в папке должны быть либо так
            #       `IDxxxx.info`
            # либо
            #       `IDxxxx.list`

            match_data = re.fullmatch(r"ID(\d{4})\.info", filename)
            if not match_data:
                continue

            # print(filepath)

            id_ = match_data.groups()[0]
            id_int = int(id_)

            # чтение описания
            with open(filepath, "r", encoding="utf8") as file:
                data = file.read().split("\n")

            if data:
                name = data[0]
                description = "\n".join(data[1:])
                tag = Tag(id_int, name, description)
                # print("\tTAG INFO:", id_int, name, description)

                list_path = os.path.join(self.get_tagging_folderpath(), f"ID{id_}.list")

                tag_files = []
                # чтение списка
                if os.path.exists(list_path):
                    list_data = []
                    with open(list_path, "r", encoding="utf8") as file:
                        list_data = file.read().split("\n")

                    for record in list_data:
                        # максимум 3 части, здесь это нужно указать,
                        # потому что в самом пути могут быть пробелы,
                        # поэтому на записи файла путь пишется в последнюю очередь
                        parts = record.split(" ", 2)
                        if len(parts) > 1:
                            md5_str = parts[0]
                            disk_size = parts[1]
                            filepath = parts[2]
                            tag.records.append(TagListRecord(md5_str, disk_size, filepath))
                            tag_files.append(filepath)

                folder_data = self.create_folder_data(f'#{name}', tag_files, virtual=True)
                folder_data.tag_data = tag

                Vars.TAGS_BASE[id_int] = tag
            else:
                print(f"\t ERROR {filepath}")

            Vars.CURRENT_MAX_TAG_ID = max(Vars.CURRENT_MAX_TAG_ID, id_int)

    def update_or_create_tag_virtual_folder(self, im_data, tag, delete=False):

        found_folder_data = None
        for folder_data in self.folders:
            if folder_data.virtual and folder_data.tag_data is tag:
                found_folder_data = folder_data
                break

        if found_folder_data is not None:
            if delete:
                for _image_data in found_folder_data.images_list[:]:
                    if compare_md5_strings(_image_data.md5, im_data.md5):
                        found_folder_data.images_list.remove(_image_data)
                        break

            else:
                found_folder_data.images_list.append(im_data)

        else:
            if not delete:
                # создать новую папку
                tag_files = [im_data.filepath, ]
                folder_data = self.create_folder_data(f'#{tag.name}', tag_files, virtual=True, make_current=False)
                folder_data.tag_data = tag
            else:
                raise Exception("impossible")

    def apply_new_tag_list_to_current_image_data(self, before_tags_list, new_tags_list):

        im_data = self.current_folder().current_image()

        image_record = TagListRecord(im_data.md5, im_data.disk_size, im_data.filepath)

        base_tags_list = [tag.name for tag in get_base_tags()]

        # TODO: попробовать переписать обработку тегов таким способом:
        # old_set = {1, 2, 3, 7}
        # new_set = {2, 3, 5}
        # old_set = {3, 1, 2}
        # new_set = {1, 4}
        # sd = old_set.symmetric_difference(new_set)
        # #то, чего нет в new_set
        # deleted = old_set.intersection(sd)
        # print( deleted )
        # #то, чего нет в old_set
        # added = new_set.intersection(sd)
        # print( added )


        # обработка добавленных тегов
        for tag_text in new_tags_list:
            if tag_text in base_tags_list:
                # заносим существующий тег
                tag = get_base_tag(tag_text)
                # сохранение в данных изображения и в базе тегов

                # это изображение уже может быть в базе, поэтому сначала проверяем есть ли оно там
                is_there_any_record = False
                for record in tag.records:
                    if compare_md5_strings(record.md5_str, im_data.md5):
                        is_there_any_record = True
                        break
                if not is_there_any_record:
                    tag.records.append(image_record)
                    self.store_tag_to_disk(tag)
                    self.update_or_create_tag_virtual_folder(im_data, tag)

            else:
                # создаём новый тег в базе и тоже отмечаем
                Vars.CURRENT_MAX_TAG_ID += 1
                tag = Tag(Vars.CURRENT_MAX_TAG_ID, tag_text, "")
                Vars.TAGS_BASE[Vars.CURRENT_MAX_TAG_ID] = tag

                # сохранение в данных изображения и в базе
                tag.records.append(image_record)
                self.store_tag_to_disk(tag)
                self.update_or_create_tag_virtual_folder(im_data, tag)

        # обработка снятых тегов
        tags_list_set = set(new_tags_list)
        before_tags_list_set = set([tag.name for tag in before_tags_list])
        deleted_tags_set = before_tags_list_set - tags_list_set

        # info = "deleted tags " + ", ".join(deleted_tags)

        def delete_record(tag, idata):
            for record in tag.records[:]:
                if compare_md5_strings(record.md5_str, idata.md5):
                    tag.records.remove(record)

        for deleted_tag_name in deleted_tags_set:
            for tag in get_base_tags():
                if tag.name == deleted_tag_name:
                    delete_record(tag, im_data)
                    self.store_tag_to_disk(tag)
                    self.update_or_create_tag_virtual_folder(im_data, tag, delete=True)

        # обновление тегов у board_item
        tags_list = self.get_tags_for_image_data(im_data)
        bi = im_data.board_item
        if bi is not None:
            bi.set_tags(tags_list[:])

        return tags_list


class TaggingMixing():

    def tagging_init(self):
        self.show_tags_overlay = False
        self.TAGS_SIDEBAR_WIDTH = 500
        self.tagging_sidebar_visible = False
        self.tagging_form = None

    def toggle_tags_overlay(self):
        if self.Globals.lite_mode:
            self.show_tags_overlay = False
            self.show_center_label(_("Tags are not supposed to be used when app is running in lite mode!"), error=True)
            return
        self.show_tags_overlay = not self.show_tags_overlay
        if self.show_tags_overlay:
            # enter
            self.tagging_form = TaggingForm(self, )
            self.tagging_form.show()
            self.tagging_form.activateWindow()
            self.tagging_form.tagslist_edit.setFocus()
        else:
            # leave
            if self.tagging_form:
                self.tagging_form.close()
                self.tagging_form.setParent(None)
            self.tagging_form = None

    def draw_tags_background(self, painter):
        if self.show_tags_overlay:

            # old_font = painter.font()
            # font = QFont(old_font)
            # font.setPixelSize(250)
            # font.setWeight(1900)
            # painter.setFont(font)
            # pen = QPen(QColor(180, 180, 180), 1)
            # painter.setPen(pen)
            # painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, "TAGGING PANEL")
            # painter.setFont(old_font)

            painter.fillRect(self.rect(), QBrush(QColor(0, 0, 0, 200)))

    def draw_board_item_tags(self, painter, bounding_rect, tags_list):
        painter.save()
        font = painter.font()
        font.setPixelSize(15)
        painter.setFont(font)
        tags_text = []
        for i, tag in enumerate(tags_list):
            tags_text.append(f"#{tag.name}({len(tag.records)})")
        text = ' '.join(tags_text)
        text_rect = QRectF(bounding_rect)
        text_rect.moveTopLeft(text_rect.bottomLeft())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, text)
        painter.restore()

    def draw_tags_sidebar_overlay(self, painter):

        sidebar_rect = self.get_sidebar_rect()
        curpos = self.mapFromGlobal(QCursor().pos())

        painter.save()

        size = (sidebar_rect.width(), sidebar_rect.height())
        gradient = QLinearGradient(0, 0, *size)
        gradient.setColorAt(0, QColor(0, 0, 0, 0))
        gradient.setColorAt(1, QColor(0, 0, 0, 255))

        gradient.setFinalStop(0, 0)
        gradient.setStart(self.TAGS_SIDEBAR_WIDTH, 0)

        if self.tagging_sidebar_visible:

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 200)))
            # painter.drawRect(sidebar_rect)
            painter.fillRect(QRect(0, 0, *size), gradient)
            font = painter.font()
            font.setPixelSize(20)
            font.setWeight(1900)
            painter.setFont(font)

            test_pixmap = QPixmap(1000, 1000)
            test_painter = QPainter()
            test_painter.begin(test_pixmap)
            test_painter.setFont(font)

            painter.setPen(QPen(Qt.gray))
            painter.drawText(QPoint(50, 250), _("Image tags"))

            for i, tag in enumerate(self.tags_list):
                tag_text = f"#{tag.name} ({len(tag.records)})"
                test_rect = test_painter.drawText(QRect(0, 0, 1000, 1000),
                                                    Qt.AlignCenter | Qt.AlignVCenter, tag_text)
                # back_rect = QRect(40, 50*(i+3), self.TAGS_SIDEBAR_WIDTH, 40)
                back_rect = QRect(40, 50*(i+6), test_rect.width()+50, test_rect.height()+10)
                text_rect = back_rect.adjusted(-10, -5, 10, 5)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(Qt.white))
                painter.drawRect(back_rect)
                painter.setPen(QPen(Qt.black))
                painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, tag_text)

            test_painter.end()

        painter.restore()

    def get_tiny_sidebar_rect(self):
        return QRect(0, 0, 50, self.rect().height())

    def get_sidebar_rect(self):
        return QRect(0, 0, self.TAGS_SIDEBAR_WIDTH, self.rect().height())

    def main_wheelEvent(self, event):
        scroll_value = event.angleDelta().y()/240
        ctrl = event.modifiers() & Qt.ControlModifier
        shift = event.modifiers() & Qt.ShiftModifier
        no_mod = event.modifiers() == Qt.NoModifier

class ClickableLabel(QLabel):
    def __init__(self, tag, label_type=None):
        super().__init__()
        self.checked = False
        self.default_checked_value = False
        self.font_size = 15
        self.tag = tag
        self.type = label_type
        self.setFont(QFont("Times", self.font_size, QFont.Bold))
        self.mousePressEvent = self.mouse_button_handler
        self.tag_string = tag.name
        self.tag_records_count = len(tag.records)
        self.setMaximumHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.update_label()
        self.set_tooltip(tag.description)
        self.setStyleSheet("ClickableLabel{ padding: 4 0;}")

    def set_tooltip(self, text):
        text = text if text else _("(No description for the tag)")
        tool_tip_text = f'<b>ID: {self.tag.id}</b><br>{text}'
        self.setToolTip(tool_tip_text)

    def update_label(self):
        count = self.tag_records_count
        if self.checked and not self.default_checked_value:
            count += 1
        if not self.checked and self.default_checked_value:
            count -= 1
        label_text = f'{self.tag_string} ({count})'
        self.setText(label_text)

    def set_check(self, check, init=False):
        if init:
            self.default_checked_value = check
        self.checked = check
        self.update_label()

    def setUpdateParent(self, up):
        self.updateParent = up

    def setXYvalues(self, x, y):
        self.x_value = x
        self.y_value = y

    def updateLinkedTextWidget(self):
        text = self.plainTextEditWidget.document().toPlainText()
        tags_list = text_to_list(text)
        if self.checked:
            tags_list.append(self.tag_string)
        else:
            try:
                tags_list.remove(self.tag_string)
            except:
                pass
        self.plainTextEditWidget.document().setPlainText( list_to_text(tags_list) )

    def mouse_button_handler(self, event):
        form_window = self.parent()
        main_window = self.parent().parent()

        if self.parent().form_mode == self.parent().form_modes.EDIT_TAGS_LIST:
            if event.button() == Qt.LeftButton:
                self.checked = not self.checked
                self.updateParent.tagslist_edit.off_competer_for_one_call = True
                self.updateLinkedTextWidget()
                self.updateParent.update()
            elif event.button() == Qt.RightButton:
                contextMenu = QMenu()
                context_menu_stylesheet = main_window.context_menu_stylesheet
                contextMenu.setStyleSheet(context_menu_stylesheet)

                action_show_images = contextMenu.addAction(_('Show image'))
                action_edit_description = contextMenu.addAction(_('Edit tag description'))
                contextMenu.addSeparator()
                action_delete = contextMenu.addAction(_('Delete tag "{0}" and its metadata').format(self.tag_string))

                cur_action = contextMenu.exec_(QCursor().pos())
                if cur_action is None:
                    pass
                elif cur_action == action_show_images:
                    main_window.showMinimized()
                    print_tag_to_html(self.tag)
                elif cur_action == action_edit_description:
                    form_window.init_tag_description_editing_mode(self.tag)
                elif cur_action == action_delete:
                    dialog_menu = QMenu()
                    dialog_menu.setStyleSheet(context_menu_stylesheet)
                    cancel_action = dialog_menu.addAction(_('Cancel'))
                    dialog_menu.addSeparator()
                    confirm_action = dialog_menu.addAction(_('Delete (no confirmation)'))
                    _action = dialog_menu.exec_(QCursor().pos())
                    if _action is None:
                        pass
                    elif _action == cancel_action:
                        pass
                    elif _action == confirm_action:
                        main_window.LibraryData().delete_tag_from_library(self.tag)
                        self.setParent(None) # удаление лейбла из интерфейса
                        self.hide()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setPen(QColor(168, 34, 3))

        is_edited_tag = self.tag == self.parent().edited_tag
        if self.checked or is_edited_tag:
            if is_edited_tag:
                color = Qt.black
            else:
                color = Qt.white
            fontstyle = QFont.Bold
        else:
            color = Qt.gray
            fontstyle = QFont.Normal

        qp.setFont(QFont('Consolas', self.font_size, fontstyle))

        if self.checked or is_edited_tag:
            if is_edited_tag:
                qolor = QColor("#dddd00")
            else:
                qolor = QColor("#ee0000")
                h, s, v, alpha = qolor.getHsvF()
                s = 0.4 + 0.3 * s * self.y_value / UI_TAGGING_ELEMENTS_IN_A_ROW
                v = 0.4 + 0.3 * v * self.y_value / UI_TAGGING_ELEMENTS_IN_A_ROW
                qolor.setHslF(h, s, v)
            qp.fillRect(event.rect(), QBrush(qolor)) #ee7600 #ee0000

        textpen = QPen(color, 3, Qt.SolidLine)
        qp.setPen(textpen)
        qp.drawText(self.rect(),Qt.AlignHCenter | Qt.AlignVCenter, self.text())

        qp.end()

class TextEdit(QPlainTextEdit):

    def __init__(self, words):
        super().__init__()
        completer = QCompleter(words)
        completer.activated.connect(self.insert_completion)
        completer.setWidget(self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer = completer
        self.textChanged.connect(self.complete)
        self.off_competer_for_one_call = True

    def insert_completion(self, completion):
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.MoveOperation.Left)

        tc.select(QTextCursor.WordUnderCursor)
        tc.removeSelectedText()

        tc.insertText(completion + " ")
        tc.movePosition(QTextCursor.MoveOperation.EndOfWord)

        self.setTextCursor(tc)

    @property
    def text_under_cursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.SelectionType.WordUnderCursor)
        return tc.selectedText()

    def complete(self):
        if self.off_competer_for_one_call:
            self.off_competer_for_one_call = False
            return
        prefix = self.text_under_cursor
        if not prefix:
            return
        self.completer.setCompletionPrefix(prefix)
        popup = self.completer.popup()
        cr = self.cursorRect()
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        cr.setWidth(
            self.completer.popup().sizeHintForColumn(0)
            + self.completer.popup().verticalScrollBar().sizeHint().width()
        )
        self.completer.complete(cr)

    def keyPressEvent(self, event):
        if self.completer.popup().isVisible() and event.key() in [
            Qt.Key.Key_Enter,
            Qt.Key.Key_Return,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
            Qt.Key.Key_Tab,
            Qt.Key.Key_Backtab,
        ]:
            event.ignore()
            return
        super().keyPressEvent(event)

class TaggingForm(QWidget):

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

    def updateClickableLables(self):
        if self.form_mode == self.form_modes.EDIT_TAGS_LIST:
            tags_list = text_to_list(self.tagslist_edit.document().toPlainText())
            for child in self.children():
                if isinstance(child, ClickableLabel):
                    child.set_check(False)
                    if child.type == "tags":
                        value = child.tag_string in tags_list
                        child.set_check(value)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setOpacity(0.05)
        painter.setBrush(QBrush(Qt.black))

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)

        painter.end()

    class form_modes():
        EDIT_TAGS_LIST = 'FORM_MODE_EDIT_TAGS_LIST'
        EDIT_TAG_DESCRIPTION = 'FORM_MODE_EDIT_TAG_DESCRIPTION'

    def __init__(self, *args):
        # QWidget.__init__(self, *args)
        # super().__init__()
        parent = args[0]
        super().__init__(parent)

        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModal)

        completer_words = [str(t) for t in get_base_tags()]
        self.tagslist_edit = TextEdit(completer_words)
        style = """
        QPlainTextEdit{
            background-color: transparent;
            color: white;
            border: 1px solid green;
            font-size: 15pt;
        }
        """
        self.tagslist_edit.setStyleSheet(style)
        self.tagslist_edit.setFixedHeight(140)
        self.tagslist_edit.textChanged.connect(self.updateClickableLables)

        self.edited_tag = None
        self.form_mode = self.form_modes.EDIT_TAGS_LIST

        self.tagslabels_list = []

        def createClickableLabelsGrid(_list):
            elems = []
            for tag_elem in _list:
                cl = ClickableLabel(tag_elem, label_type="tags")
                elems.append(cl)
            layout = QGridLayout()
            for n, elem in enumerate(elems):
                elem.setUpdateParent(self)
                #add reference to corresponding PlainTextEditWidget
                elem.plainTextEditWidget = self.tagslist_edit
                #add self to special group list
                self.tagslabels_list.append(elem)
                x = n // UI_TAGGING_ELEMENTS_IN_A_ROW
                y = n % UI_TAGGING_ELEMENTS_IN_A_ROW
                layout.addWidget(elem, x, y)
                elem.setXYvalues(x, y)
            return layout

        self.existing_tags_layout = createClickableLabelsGrid(get_base_tags())

        style = """
        QWidget{
            font-size: 14pt;
        };
        QLabel {
            color: white;
        }
        """
        self.setStyleSheet(style)

        vl = QVBoxLayout()

        save_btn = QPushButton(_("Save"))
        save_btn.clicked.connect(self.save_button_handler)
        save_btn.setStyleSheet(self.button_style)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setObjectName("save")

        vl.addLayout(self.existing_tags_layout)
        vl.addWidget(self.tagslist_edit)
        vl.addWidget(save_btn)

        self.init_tagging_UI()

        self.setLayout(vl)

        self.resize(parent.width()-100, parent.height())

        desktop_rect = QDesktopWidget().screenGeometry(screen=0)
        x = (desktop_rect.width() - self.frameSize().width()) // 2
        y = (desktop_rect.height() - self.frameSize().height()) // 2
        self.move(x,y)

        # self.setParent(args[0])

    def init_tagging_UI(self):
        IMAGE_TAGS = self.parent().tags_list
        BASE_TAGS = get_base_tags()

        found_tags = []
        for base_tag in BASE_TAGS:
            if base_tag in IMAGE_TAGS:
                found_tags.append(base_tag)

        found_tags = [str(l) for l in found_tags]
        if found_tags:
            # set text
            self.tagslist_edit.document().setPlainText(" ".join(found_tags))
            # set labels checked
            found_tags = [l.lower() for l in found_tags]
            for label_tag_element in self.tagslabels_list:
                if label_tag_element.tag_string.lower() in found_tags:
                    label_tag_element.set_check(True, init=True)
        self.update()

    def init_tag_description_editing_mode(self, tag):
        self.form_mode = self.form_modes.EDIT_TAG_DESCRIPTION
        self.edited_tag = tag
        self.tagslist_edit.document().setPlainText(self.edited_tag.description)

    def save_tag_description(self):
        if self.edited_tag is not None:
            self.edited_tag.description = self.tagslist_edit.document().toPlainText()
            self.parent().LibraryData().store_tag_to_disk(self.edited_tag)
            for tag_label in self.tagslabels_list:
                if tag_label.tag is self.edited_tag:
                    tag_label.set_tooltip(self.edited_tag.description)
                    break

            self.edited_tag = None
        self.form_mode = self.form_modes.EDIT_TAGS_LIST
        self.tagslist_edit.off_competer_for_one_call = True
        self.init_tagging_UI()

    def save_button_handler(self):
        main_window = self.parent()
        LibraryData = main_window.LibraryData

        if self.form_mode == self.form_modes.EDIT_TAGS_LIST:
            self.save_tags_list(main_window, LibraryData)
        elif self.form_mode == self.form_modes.EDIT_TAG_DESCRIPTION:
            self.save_tag_description()

    def save_tags_list(self, main_window, LibraryData):
        # tagslist_data = self.tagslist_edit.document().toPlainText().strip()
        # verified_tags = bool(re.fullmatch(  r'^([^.,*]*)', tagslist_data ))
        # if not verified_tags:
        #     QMessageBox.warning(self,"Error", "Do not use commas and periods: .,")
        #     return
        tagslist_raw_string = self.tagslist_edit.document().toPlainText()
        new_tags_list = text_to_list(tagslist_raw_string)
        tags_list = LibraryData().apply_new_tag_list_to_current_image_data(main_window.tags_list, new_tags_list)
        main_window.tags_list = tags_list
        main_window.toggle_tags_overlay()

    def closeEvent(self, event):
        pass

        # self.destroy() #если раскоментировать, то процесс будет висеть вечно после закрытия главного окна

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent().toggle_tags_overlay()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent().toggle_tags_overlay()

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass



# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     w = TaggingForm()
#     app.exec_()
#     exit()


# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()


# if __name__ == '__main__':
#     load_tags_info()
