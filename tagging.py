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
from library_data import LibraryData
from collections import namedtuple


import urllib.parse
import random
import tempfile


HTML_FILEPATH = "generated.html"
HTML_FILEPATH = os.path.join(tempfile.gettempdir(), HTML_FILEPATH)


TAGGING_FOLDERPATH = os.path.join(os.path.dirname(__file__), "tagging")

TAGS_BASE = dict()
CURRENT_MAX_TAG_ID = 0


UI_TAGGING_ELEMENTS_IN_A_ROW = 14

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

TagListRecord = namedtuple('TagListRecord' , 'md5_str md5_tuple filepath')


def get_tags_for_image_data(image_data):
    return_list = list()
    for key, tag in TAGS_BASE.items():
        for record in tag.records:
            if record.md5_str == image_data.md5:
                return_list.append(tag)
    # status_string = f"{len(return_list)} get_tags_for_image_data {image_data.filepath}"
    # print(status_string)
    return return_list


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

    def store_to_disk(self):
        if not os.path.exists(TAGGING_FOLDERPATH):
            os.mkdir(TAGGING_FOLDERPATH)

        filename = f"ID{self.id:04}"
        info_filepath = os.path.join(TAGGING_FOLDERPATH, "%s.info" % filename)
        list_filepath = os.path.join(TAGGING_FOLDERPATH, "%s.list" % filename)

        info_data = "\n".join([str(self.name), self.description])
        list_data = "\n".join([f"{r.md5_str} {r.filepath}" for r in self.records])

        with open(info_filepath, "w+", encoding="utf8") as file:
            file.write(info_data)

        with open(list_filepath, "w+", encoding="utf8") as file:
            file.write(list_data)

def load_tags_info():

    global TAGS_BASE
    global CURRENT_MAX_TAG_ID

    if not os.path.exists(TAGGING_FOLDERPATH):
        print('load_tags_info::', TAGGING_FOLDERPATH, "doesn't exist! Abort")
        return

    for filename in os.listdir(TAGGING_FOLDERPATH):
        filepath = os.path.join(TAGGING_FOLDERPATH, filename)

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

            list_path = os.path.join(TAGGING_FOLDERPATH, f"ID{id_}.list")

            # чтение списка
            if os.path.exists(list_path):
                with open(list_path, "r", encoding="utf8") as file:
                    data = file.read().split("\n")
                    for record in data:
                        parts = record.split(" ")
                        if len(parts) > 1:
                            md5_str = parts[0]
                            filepath = parts[1]
                            tag.records.append(TagListRecord(md5_str, convert_md5_to_int_tuple(md5_str), filepath))

            TAGS_BASE[id_int] = tag
        else:
            print(f"\t ERROR {filepath}")

        CURRENT_MAX_TAG_ID = max(CURRENT_MAX_TAG_ID, id_int)




def get_base_tags():
    return list(TAGS_BASE.values())

def get_base_tag(tag_name):
    for tag in get_base_tags():
        if tag.name.lower() == tag_name.lower():
            return tag
    return None




def init(self):
    self.tagging_overlay_mode = False
    self.TAGS_SIDEBAR_WIDTH = 500
    self.tagging_sidebar_visible = False
    self.tagging_form = None

def toggle_overlay(parent):
    parent.tagging_overlay_mode = not parent.tagging_overlay_mode
    if parent.tagging_overlay_mode:
        # enter
        parent.tagging_form = TaggingForm(parent, )
        parent.tagging_form.show()
    else:
        # leave
        if parent.tagging_form:
            parent.tagging_form.close()
            parent.tagging_form.setParent(None)
        parent.tagging_form = None

def draw_main(self, painter):
    if self.tagging_overlay_mode:

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

def main_mousePressEvent(self, event):
    pass

def main_mouseMoveEvent(self, event):
    pass

def main_mouseReleaseEvent(self, event):
    pass

def wheelEvent(self, event):
    scroll_value = event.angleDelta().y()/240
    ctrl = event.modifiers() & Qt.ControlModifier
    shift = event.modifiers() & Qt.ShiftModifier
    no_mod = event.modifiers() == Qt.NoModifier

def get_tiny_sidebar_rect(self):
    return QRect(0, 0, 50, self.rect().height())

def get_sidebar_rect(self):
    return QRect(0, 0, self.TAGS_SIDEBAR_WIDTH, self.rect().height())

def draw_tags_sidebar_overlay(self, painter):

    sidebar_rect = get_sidebar_rect(self)
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
        painter.drawText(QPoint(50, 150), "Теги изображения")

        tags_list = LibraryData().current_folder().current_image().tags_list
        for i, tag in enumerate(tags_list):
            tag_text = f"#{tag.name} ({len(tag.records)})"
            test_rect = test_painter.drawText(QRect(0, 0, 1000, 1000),
                                                Qt.AlignCenter | Qt.AlignVCenter, tag_text)
            # back_rect = QRect(40, 50*(i+3), self.TAGS_SIDEBAR_WIDTH, 40)
            back_rect = QRect(40, 50*(i+4), test_rect.width()+50, test_rect.height()+10)
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

class ClickableLabel(QLabel):
    def __init__(self, tag, label_type=None):
        super().__init__()
        self.checked = False
        self.font_size = 15
        self.tag = tag
        self.type = label_type
        self.inverted = True if label_type == "tags" else False
        self.setFont(QFont("Times", self.font_size, QFont.Bold))
        self.mousePressEvent = self.mouseHandler
        self.tag_string = tag.name
        self.setText(tag.name)
        self.setStyleSheet("ClickableLabel{ padding: 4 0;}")

    def set_check(self, check):
        self.checked = check

    def setUpdateParent(self, up):
        self.updateParent = up

    def setXYvalues(self, x, y):
        self.x_value = x
        self.y_value = y

    def updateLinkedTextWidget(self):
        text = self.plainTextEditWidget.document().toPlainText()
        tags_list = text_to_list(text)
        if self.checked:
            tags_list.append(self.text())
        else:
            try:
                tags_list.remove(self.text())
            except:
                pass
        self.plainTextEditWidget.document().setPlainText( list_to_text(tags_list) )

    def mouseHandler(self, event):
        if event.button() == Qt.LeftButton:
            self.checked = not self.checked
            self.updateLinkedTextWidget()
            self.updateParent.update()
        elif event.button() == Qt.RightButton:
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
        self.off_competer_on_first_call = True

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
        if self.off_competer_on_first_call:
            self.off_competer_on_first_call = False
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

    def updateClickableLables(self):
        tags_list = text_to_list(self.tagslist.document().toPlainText())

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
        super().__init__()

        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # self.setWindowFlags( Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)        
        self.setWindowModality(Qt.WindowModal)

        completer_words = [str(t) for t in get_base_tags()]
        self.tagslist = TextEdit(completer_words)
        style = """
        QPlainTextEdit{
            background-color: transparent;
            color: white;
            border: 1px solid green;
            font-size: 15pt;
        }
        """
        self.tagslist.setStyleSheet(style)
        self.tagslist.setFixedHeight(140)
        self.tagslist.textChanged.connect(self.updateClickableLables)


        self.tagslabels_list = []

        def createClicableLabelsGrid(_list):
            elems = []
            for tag_elem in _list:
                cl = ClickableLabel(tag_elem, label_type="tags")
                elems.append(cl)
            layout = QGridLayout()
            for n, elem in enumerate(elems):
                elem.setUpdateParent(self)
                #add reference to corresponding PlainTextEditWidget
                elem.plainTextEditWidget = self.tagslist
                #add self to special group list
                self.tagslabels_list.append(elem)
                x = n // UI_TAGGING_ELEMENTS_IN_A_ROW
                y = n % UI_TAGGING_ELEMENTS_IN_A_ROW
                layout.addWidget(elem, x, y)
                elem.setXYvalues(x, y)
            return layout

        self.existing_tags = createClicableLabelsGrid(get_base_tags())

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

        vl.addLayout(self.existing_tags)
        vl.addWidget(self.tagslist)
        vl.addWidget(save_btn)

        self.init_tagging_UI()

        self.setLayout(vl)

        self.resize(2000, self.height())

        app = QApplication.instance()
        x = (app.desktop().width()//2*1 - self.frameSize().width()) // 2
        y = (app.desktop().height() - self.frameSize().height()) // 2
        self.move(x,y)

        self.setParent(args[0])

    def save_handler(self):
        # tagslist_data = self.tagslist.document().toPlainText().strip()
        # verified_tags = bool(re.fullmatch(  r'^([^.,*]*)', tagslist_data ))
        # if not verified_tags:
        #     QMessageBox.warning(self,"Error", "Do not use commas and periods: .,")
        #     return

        tags_list = text_to_list(self.tagslist.document().toPlainText())
        base_tags_list = [tag.name for tag in get_base_tags()]
        im_data = LibraryData().current_folder().current_image()
        before_tags_list = im_data.tags_list
        # список очищается - это даёт возможность не возиться отдельно с удалёнными тегами
        im_data.tags_list = []
        image_record = TagListRecord(im_data.md5, im_data.md5_tuple, im_data.filepath)

        # обработка добавленных тегов
        for tag_text in tags_list:
            if tag_text in base_tags_list:
                # заносим существующий тег
                tag = get_base_tag(tag_text)
                # сохранение в данных изображения и в базе
                im_data.tags_list.append(tag)

                # это изображение уже может быть в базе, поэтому сначала проверяем есть ли оно там
                is_there_any_record = False
                for record in tag.records:
                    if record.md5_str == im_data.md5:
                        is_there_any_record = True
                        break
                if not is_there_any_record:
                    tag.records.append(image_record)
                    tag.store_to_disk()

            else:
                # создаём новый тег в базе и тоже отмечаем
                global CURRENT_MAX_TAG_ID
                global TAGS_BASE
                CURRENT_MAX_TAG_ID += 1
                tag = Tag(CURRENT_MAX_TAG_ID, tag_text, "")
                TAGS_BASE[CURRENT_MAX_TAG_ID] = tag

                # сохранение в данных изображения и в базе
                im_data.tags_list.append(tag)
                tag.records.append(image_record)
                tag.store_to_disk()

        # обработка снятых тегов
        tags_list_set = set(tags_list)
        before_tags_list_set = set([tag.name for tag in before_tags_list])
        deleted_tags_set = before_tags_list_set - tags_list_set

        # info = "deleted tags " + ", ".join(deleted_tags)

        def delete_record(tag, idata):
            for record in tag.records:
                if record.md5_str == idata.md5:
                    tag.records.remove(record)

        for deleted_tag_name in deleted_tags_set:
            for tag in get_base_tags():
                if tag.name == deleted_tag_name:
                    delete_record(tag, im_data)
                    tag.store_to_disk()

        toggle_overlay(self.parent())

    def init_tagging_UI(self):
        TAGS = LibraryData().current_folder().current_image().tags_list
        BASE_TAGS = get_base_tags()

        found_tags = []
        for base_tag in BASE_TAGS:
            if base_tag in TAGS:
                found_tags.append(base_tag)

        found_tags = [str(l) for l in found_tags]
        if found_tags:
            # set text
            self.tagslist.document().setPlainText(" ".join(found_tags))
            # set labels checked
            found_tags = [l.lower() for l in found_tags]
            for label_tag_element in self.tagslabels_list:
                if label_tag_element.text().lower() in found_tags:
                    label_tag_element.set_check(True)
        self.update()

    def closeEvent(self, event):
        pass

        # self.destroy() #если раскоментировать, то процесс будет висеть вечно после закрытия главного окна

    def keyReleaseEvent(self, event):
        self.parent().keyReleaseEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            toggle_overlay(self.parent())
        # else:        
        #     self.parent().keyPressEvent(event)


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
