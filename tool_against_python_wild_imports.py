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




"""
(28 фев 26, sergkrumas): Мне нравится писать программы упоминая только Qt-класс без упоминания имени модуля в котором он лежит.
Но по классике надо это делать, но вручную исправлять исходники не хочу, поэтому написал эту тулзу.
При этом, если случилось, что имя модуля предшествует имени класса, то тулза не дублирует имя модуля.

EXAMPLE INPUT:
    def greet():
        QtCore.QPoint(QRect().top(), QtCore.QRect().left())
        if True:
            QPoint(0, 1)
        QPoint(3, 3)
        QPoint(4, 4)
        if True:
            QPoint(10, 10)

OUTPUT:
    |--------------------------------------<-<  >->--------------------------------------|

    from PyQt5.QtCore import (QPoint, QRect)

    |--------------------------------------<-<  >->--------------------------------------|

    def greet():
        QtCore.QPoint(QtCore.QRect().top(), QtCore.QRect().left())
        if True:
            QtCore.QPoint(0, 1)
        QtCore.QPoint(3, 3)
        QtCore.QPoint(4, 4)
        if True:
            QtCore.QPoint(10, 10)

    |--------------------------------------<-<  >->--------------------------------------|

"""


code = """
def greet():
    QtCore.QPoint(QRect().top(), QtCore.QRect().left())
    if True:
        QPoint(0, 1)
    QPoint(3, 3)
    QPoint(4, 4)
    if True:
        QPoint(10, 10)
""".strip()

import tokenize
import io
from collections import defaultdict 

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui

QtWidgets_names = dir(QtWidgets)
QtCore_names = dir(QtCore)
QtGui_names = dir(QtGui)

MAIN_SUBMODULES_STRINGS = (
        "QtWidgets"
    ,   "QtCore"
    ,   "QtGui"
)

def main():
    tokens_by_line = defaultdict(list)
    is_line_to_be_fixed = defaultdict(bool)

    source_lines = code.split("\n")

    bytes_io = io.BytesIO(code.encode('utf-8'))
    bytes_io.seek(0)

    class TokenWrapper():
        """
            токены не поддерживают прозвольное задание аттрибутов, поэтому пришлось сделать обёртку
        """
        def __init__(self, token):
            self.token = token
            self.substitute = ""

        def setSubstitue(self, value, line_num):
            self.substitute = value
            is_line_to_be_fixed[line_num] = True

        def __repr__(self):
            return self.token.string

    for token in tokenize.tokenize(bytes_io.readline):
        tw = TokenWrapper(token)
        token_line_num = token.start[0]-1
        tokens_by_line[token_line_num].append(tw)

        # print(token)

    del tokens_by_line[-1]


    # all_qt_names = set([*QtWidgets_names, *QtCore_names, *QtGui_names])

    # for m in all_qt_names:
    #     if m.startswith("py"):
    #         print(m)


    _qt_widgets = []
    _qt_core = []
    _qt_gui = []

    for line_num, line_tws in tokens_by_line.items():
        for n, tw in enumerate(line_tws):
            # if tw.token.string in all_qt_names and not tw.token.string.startswith(MAIN_SUBMODULES_STRINGS):
            token_string = tw.token.string
            if token_string.startswith(("Q", "pyqt")) and not token_string.startswith(MAIN_SUBMODULES_STRINGS):
                prev_2_tokens = line_tws[n-2:n]
                if len(prev_2_tokens) == 2:
                    token_1 = prev_2_tokens[0].token
                    token_2 = prev_2_tokens[1].token
                    if token_1.type == tokenize.NAME and token_2.type == tokenize.OP:
                        if token_1.string in MAIN_SUBMODULES_STRINGS and token_2.string == ".":
                            continue #skip
                module_name = ""
                if token_string in QtWidgets_names:
                    module_name = 'QtWidgets'
                    _qt_widgets.append(token_string)
                elif token_string in QtCore_names:
                    module_name = 'QtCore'
                    _qt_core.append(token_string)
                elif token_string in QtGui_names:
                    module_name = 'QtGui'
                    _qt_gui.append(token_string)
                if module_name:
                    tw.setSubstitue(f"{module_name}." + token_string, line_num)

    def slice_replace(source, start, end, dest):
        return f"{source[:start]}{dest}{source[end:]}" 


    for n, line in enumerate(source_lines):
        if n in is_line_to_be_fixed:
            for tw in reversed(tokens_by_line[n]):
                if tw.substitute:
                    source_lines[n] = slice_replace(source_lines[n],
                        tw.token.start[1], tw.token.end[1],
                        tw.substitute
                    )



    _qt_widgets = set(_qt_widgets)
    _qt_core = set(_qt_core)
    _qt_gui = set(_qt_gui)

    out = "\n".join(source_lines)

    SEP = '|--------------------------------------<-<  >->--------------------------------------|'

    print(SEP)
    print()

    print("*\n по идее эти импорты уже не нужны будут,\n потому что после работы тулзы модули будут прописаны в самом коде у каждого Qt-класса\n")
    if _qt_widgets:
        print(f"    from PyQt5.QtWidgets import ({', '.join(_qt_widgets)})")
    if _qt_core:
        print(f"    from PyQt5.QtCore import ({', '.join(_qt_core)})")
    if _qt_gui:
        print(f"    from PyQt5.QtGui import ({', '.join(_qt_gui)})")

    print()
    print(SEP)
    print()
    print(out)
    print()
    print(SEP)



main()
