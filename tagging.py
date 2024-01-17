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

TagListRecord = namedtuple('TagListRecord' , 'md5_str disk_size filepath')

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

    def store_tag_to_disk(self, tag):
        if not os.path.exists(self.get_tagging_folderpath()):
            os.mkdir(self.get_tagging_folderpath())

        filename = f"ID{tag.id:04}"
        info_filepath = os.path.join(self.get_tagging_folderpath(), "%s.info" % filename)
        list_filepath = os.path.join(self.get_tagging_folderpath(), "%s.list" % filename)

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



class TaggingMixing():

    def tagging_init(self):
        self.show_tags_overlay = False
        self.TAGS_SIDEBAR_WIDTH = 500
        self.tagging_sidebar_visible = False
        self.tagging_form = None

    def toggle_tags_overlay(self):
        if self.Globals.lite_mode:
            self.show_tags_overlay = False
            self.show_center_label("Теги нельзя юзать в упрощённом режиме!", error=True)
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

    def draw_tags_sidebar_overlay(self, painter):

        sidebar_rect = self.get_sidebar_rect()
        curpos = self.mapFromGlobal(QCursor().pos())

        old_brush = painter.brush()
        old_pen = painter.pen()
        old_font = painter.font()

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
            font = QFont(old_font)
            font.setPixelSize(20)
            font.setWeight(1900)
            painter.setFont(font)

            test_pixmap = QPixmap(1000, 1000)
            test_painter = QPainter()
            test_painter.begin(test_pixmap)
            test_painter.setFont(font)

            painter.setPen(QPen(Qt.gray))
            painter.drawText(QPoint(50, 250), "Теги изображения")

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

        painter.setFont(old_font)
        painter.setBrush(old_brush)
        painter.setPen(old_pen)

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
        self.inverted = True if label_type == "tags" else False
        self.setFont(QFont("Times", self.font_size, QFont.Bold))
        self.mousePressEvent = self.mouseHandler
        self.tag_string = tag.name
        self.tag_records_count = len(tag.records)
        self.setMaximumHeight(50)
        self.update_label()
        self.setStyleSheet("ClickableLabel{ padding: 4 0;}")

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

    def mouseHandler(self, event):
        if event.button() == Qt.LeftButton:
            self.checked = not self.checked
            self.updateParent.tagslist_edit.off_competer_for_one_call = True
            self.updateLinkedTextWidget()
            self.updateParent.update()
        elif event.button() == Qt.RightButton:
            self.parent().parent().showMinimized()
            print_tag_to_html(self.tag)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        qp.setPen(QColor(168, 34, 3))

        if self.checked:
            color = Qt.white
            fontstyle = QFont.Bold
        else:
            color = Qt.gray
            fontstyle = QFont.Normal

        qp.setFont(QFont('Consolas', self.font_size, fontstyle))
        if self.checked:
            qolor = QColor("#00ee00")
            h, s, v, alpha = qolor.getHsvF()
            s = 0.4 + 0.3 * s * self.y_value / UI_TAGGING_ELEMENTS_IN_A_ROW
            v = 0.4 + 0.3 * v * self.y_value / UI_TAGGING_ELEMENTS_IN_A_ROW
            qolor.setHslF(h, s, v)
            if self.inverted:
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

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_handler)
        save_btn.setStyleSheet(self.button_style)
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

    def save_handler(self):
        # tagslist_data = self.tagslist_edit.document().toPlainText().strip()
        # verified_tags = bool(re.fullmatch(  r'^([^.,*]*)', tagslist_data ))
        # if not verified_tags:
        #     QMessageBox.warning(self,"Error", "Do not use commas and periods: .,")
        #     return

        new_tags_list = text_to_list(self.tagslist_edit.document().toPlainText())
        base_tags_list = [tag.name for tag in get_base_tags()]
        im_data = self.parent().LibraryData().current_folder().current_image()
        before_tags_list = self.parent().tags_list
        # список очищается - это даёт возможность не возиться отдельно с удалёнными тегами

        image_record = TagListRecord(im_data.md5, im_data.disk_size, im_data.filepath)


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
                    self.parent().LibraryData().store_tag_to_disk(tag)
                    self.parent().LibraryData().update_or_create_tag_virtual_folder(im_data, tag)

            else:
                # создаём новый тег в базе и тоже отмечаем
                Vars.CURRENT_MAX_TAG_ID += 1
                tag = Tag(Vars.CURRENT_MAX_TAG_ID, tag_text, "")
                Vars.TAGS_BASE[Vars.CURRENT_MAX_TAG_ID] = tag

                # сохранение в данных изображения и в базе
                tag.records.append(image_record)
                self.parent().LibraryData().store_tag_to_disk(tag)
                self.parent().LibraryData().update_or_create_tag_virtual_folder(im_data, tag)

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
                    self.parent().LibraryData().store_tag_to_disk(tag)
                    self.parent().LibraryData().update_or_create_tag_virtual_folder(im_data, tag, delete=True)

        self.parent().tags_list = self.parent().LibraryData().get_tags_for_image_data(im_data)

        self.parent().toggle_tags_overlay()

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
