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

INFO_ALL_PAGES = """
➜ ДЛЯ ВСЕХ СТРАНИЦ
    Esc - Закрытие программы
    Tab - Переход из вьювера на страницу библиотеки и обратно
    Ё - Показать/скрыть настройки
    P - Включает и выключает отображение окна поверх всех окон
    Ctrl+ →/← перенос полноэкранного окна между доступными мониторами
"""

INFO_VIEWER_PAGE = """
➜ СТРАНИЦА ВЬЮВЕРА
    ↑ - Увеличение масштаба текущей картинки
    ↓ - Уменьшение масштаба текущей картинки
    → - Показать следующую картинку
    ← - Показать прыдыдущую картинку
    Пробел - Пауза/воспроизведение анимированных .gif- и .webp-файлов
    W, A, S, D - Клавиши перемещения в прострастве картинки вверх, влево, вниз и вправо соответственно
    Home - Переключение на первую картинку в списке текущей папки
    End - Переключение на последнюю картинку в списке текущей папки
    Shift+Tab - Переключение на следующую по порядку папку в библиотеке
    Y - Переключение между оконным и полноэкранным режимом
    T - Показать/скрыть форму тегов
    D - Показать/скрыть трети
    F - Добавить в избранное или удалить из избранного
    C - Показать/скрыть центральную точку
    Ctrl + ЛКМ - Увеличить заданную курсором область и входит в режим лупы (Esc - отмена)
    I - Инвертировать цвета у картинки
    R - Сохранить содержимое окна в масштабе исходной картинки
           - в режиме выделения сохраняет содержимое рамки выделения
           + Shift - вместо масштаба исходной картинки будет задан масштаб окна
    M - Отразить картинку по горизонтальной оси, + Ctrl - по вертикали
    Alt + →/← - Навигация по истории просмотра
"""

INFO_LIBRARY_PAGE = """
➜ СТРАНИЦА БИБЛИОТЕКИ
    ↑ - Выбор предыдущей папки в библиотеке
    ↓ - Выбор следующей папки в библиотеке
    Shift+Tab - Переключение на следующую по порядку папку в библиотеке
    Delete - Удаляет текущую папку из сессии
    U - Обновить список изображений для текущей папки
"""

INFO_BOARD_PAGE = """
➜ СТРАНИЦА BOARD
    В разработке
"""

INFO_START_PAGE = """
➜ СТАРТОВАЯ СТРАНИЦА
    Не прописано
"""



class HelpWidgetMixin():

    def init_help_infopanel(self):
        self.show_help_infopanel = False

    def toggle_infopanel(self):
        self.show_help_infopanel = not self.show_help_infopanel
        if self.show_help_infopanel:
            # enter
            self.help_widget = HelpWidget(self, )
            self.help_widget.show()
            self.help_widget.activateWindow()
            self.help_widget.setFocus()
        else:
            # leave
            if self.help_widget:
                self.help_widget.close()
                self.help_widget.setParent(None)
            self.help_widget = None

class HelpWidget(QWidget):

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

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        painter.setOpacity(0.5)
        painter.setBrush(QBrush(Qt.black))

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.drawPath(path)

        painter.end()

    def __init__(self, *args):

        parent = args[0]
        super().__init__(parent)

        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.WindowModal)


        style = """
        QWidget{
            font-size: 14pt;
        };
        QLabel {
            color: white;
        };

        """
        self.setStyleSheet(style)

        vl = QVBoxLayout()

        exit_btn = QPushButton("Закрыть")
        exit_btn.clicked.connect(lambda: toggle_infopanel(parent))
        exit_btn.setStyleSheet(self.button_style)
        exit_btn.setObjectName("exit")


        tb_style = """
        QPlainTextEdit {
            background-color: transparent;
            color: white;
            border: none;
            font-size: 15pt;
        }

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

        """



        text_browser = QPlainTextEdit()

        text_browser.setStyleSheet(tb_style)


        # сортировка частей документации по порядку:
        # сначала идёт страница для всех
        # потом идёт текущая страница
        # потом все остальные
        def page_type_to_info(page):
            return {
                'STARTPAGE': INFO_START_PAGE,
                'VIEWERPAGE': INFO_VIEWER_PAGE,
                'BOARDPAGE': INFO_BOARD_PAGE,
                'LIBRARYPAGE': INFO_LIBRARY_PAGE,
            }[page]
        all_pages = parent.pages.all()
        pages_to_render = all_pages[:]
        cur_page = pages_to_render.pop(pages_to_render.index(parent.current_page))
        pages_to_render.insert(0, cur_page)
        pages_to_render = [page_type_to_info(page) for page in pages_to_render]
        pages_to_render.insert(0, INFO_ALL_PAGES)

        help_info = "\n\n".join(pages_to_render)

        help_info_data = "\n".join((parent.globals.app_title, parent.globals.github_repo, "\n", help_info))
        text_browser.insertPlainText(f'{help_info_data}')
        font = text_browser.font()
        font.setPixelSize(20)
        font.setWeight(1900)
        font.setFamily("Consolas")
        text_browser.setFont(font)
        text_browser.moveCursor(QTextCursor.Start)
        text_browser.ensureCursorVisible()
        text_browser.move(0, 0)
        text_browser.resize(parent.width()-100, parent.height()-50)

        vl.addWidget(text_browser)
        vl.addWidget(exit_btn)
        self.setLayout(vl)

        self.resize(parent.width()-100, parent.height())

        desktop_rect = QDesktopWidget().screenGeometry(screen=0)
        x = (desktop_rect.width() - self.frameSize().width()) // 2
        y = (desktop_rect.height() - self.frameSize().height()) // 2
        self.move(x,y)


    def closeEvent(self, event):
        pass

        # self.destroy() #если раскоментировать, то процесс будет висеть вечно после закрытия главного окна

    def keyReleaseEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent().toggle_infopanel()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent().toggle_infopanel()

    def mousePressEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass


# для запуска программы прямо из этого файла при разработке и отладке
if __name__ == '__main__':
    import subprocess
    subprocess.Popen([sys.executable, "-u", "_viewer.pyw"])
    sys.exit()
