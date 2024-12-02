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

__import__('builtins').__dict__['_'] = __import__('gettext').gettext




def retrieve_pages_help_text():

    INFO_ALL_PAGES = _("""
➜ FOR ALL PAGES
    Esc - exit program
    Tab - switch between pages in cyclic order
    ~ - show/hide settings window
    P - toggle window state between normal and always-on-top 
    Ctrl+ →/← - move full-screen window from one monitor to another
""")

    INFO_VIEWER_PAGE = _("""
➜ VIEWER PAGE
    ↑ - image zoom in
    ↓ - image zoom out
    → - show next image
    ← - show previous image
    Space - pause/resume for animated images
    W, A, S, D - image move
    Home - show first image in current folder
    End - show last image in currend folder
    Shift+Tab - switch to next folder in library
    Y - toggle between window and full-screen mode
    T - show/hide tags form
    D - show/hide thirds
    F - add to/remove from favorites
    C - show/hide image center point
    Ctrl + LMB - zoom in to user-defined region and sets magnifier mode
        - Esc - disable magnifier mode
    I - invert image colors
    R - grab window canvas with default image scale
        - as magnifier mode is enabled saves user-defined region of window canvas
        + Shift - take viewport scale instead default image scale  
    M - mirror image horizontally
        + Ctrl - vertically
    Alt + →/← - navigate through viewing history
""")

    INFO_LIBRARY_PAGE = _("""
➜ LIBRARY PAGE
    ↑ - choose previous folder in the library list
    ↓ - choose next folder in library list
    Shift+Tab - switch to next folder in the library list
    Delete - delete folder from current session
    U - update image list for the current folder
""")

    INFO_BOARD_PAGE = _("""
➜ BOARD PAGE
    left mouse click - select picture items & rectangle select
    middle mouse click - camera moving
    mouse wheel - camera zooming
    F12 - activate/desactivate gamepad control
        Playstation 4 Dualshock Gamepad & Defender Gamepad supported
        left stick - camera moving
        right stick (vertical) - camera zooming
        X gamepad button - the left and right sticks exchange/exchange back for Playstation 4 Dualshock
""")

    INFO_START_PAGE = _("""
➜ START PAGE
    not set
""")

    _vars = [
        "INFO_ALL_PAGES",
        "INFO_VIEWER_PAGE",
        "INFO_LIBRARY_PAGE",
        "INFO_BOARD_PAGE",
        "INFO_START_PAGE",
    ]
    for var in _vars:
        globals()[var] = locals()[var]


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

        exit_btn = QPushButton(_("Close"))
        exit_btn.clicked.connect(lambda: parent.toggle_infopanel())
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


        retrieve_pages_help_text()

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
