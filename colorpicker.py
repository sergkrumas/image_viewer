









import colorsys
from typing import Union

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *



class Ui_Dark_Alpha(object):
    def setupUi(self, ColorPicker):
        ColorPicker.setObjectName("ColorPicker")
        ColorPicker.resize(400, 300)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ColorPicker.sizePolicy().hasHeightForWidth())
        ColorPicker.setSizePolicy(sizePolicy)
        ColorPicker.setMinimumSize(QSize(400, 300))
        ColorPicker.setMaximumSize(QSize(400, 300))
        ColorPicker.setStyleSheet("QWidget{\n"
"    background-color: none;\n"
"}\n"
"\n"
"/*  LINE EDIT */\n"
"QLineEdit{\n"
"    color: rgb(221, 221, 221);\n"
"    background-color: #303030;\n"
"    border: 2px solid #303030;\n"
"    border-radius: 5px;\n"
"    selection-color: rgb(16, 16, 16);\n"
"    selection-background-color: rgb(221, 51, 34);\n"
"    font-family: Segoe UI;\n"
"    font-size: 11pt;\n"
"}\n"
"QLineEdit::focus{\n"
"    border-color: #aaaaaa;\n"
"}\n"
"\n"
"/* PUSH BUTTON */\n"
"QPushButton{\n"
"    border: 2px solid #aaa;\n"
"    border-radius: 5px;\n"
"    font-family: Segoe UI;\n"
"    font-size: 9pt;\n"
"    font-weight: bold;\n"
"    color: #ccc;\n"
"    width: 100px;\n"
"}\n"
"QPushButton:hover{\n"
"    border: 2px solid #aaa;\n"
"    color: #222;\n"
"    background-color: #aaa;\n"
"}\n"
"QPushButton:pressed{\n"
"    border: 2px solid #aaa;\n"
"    color: #222;\n"
"    background-color: #aaa;\n"
"}")
        self.verticalLayout = QVBoxLayout(ColorPicker)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.drop_shadow_frame = QFrame(ColorPicker)
        self.drop_shadow_frame.setStyleSheet("QFrame{\n"
"background-color: #202020;\n"
"border-radius: 10px;\n"
"}")
        self.drop_shadow_frame.setFrameShape(QFrame.StyledPanel)
        self.drop_shadow_frame.setFrameShadow(QFrame.Raised)
        self.drop_shadow_frame.setObjectName("drop_shadow_frame")
        self.verticalLayout_3 = QVBoxLayout(self.drop_shadow_frame)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(10)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.title_bar = QFrame(self.drop_shadow_frame)
        self.title_bar.setMinimumSize(QSize(0, 32))
        self.title_bar.setStyleSheet("background-color: rgb(48, 48, 48);")
        self.title_bar.setFrameShape(QFrame.StyledPanel)
        self.title_bar.setFrameShadow(QFrame.Raised)
        self.title_bar.setObjectName("title_bar")
        self.horizontalLayout_2 = QHBoxLayout(self.title_bar)
        self.horizontalLayout_2.setContentsMargins(10, 0, 10, 0)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QSpacerItem(16, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.window_title = QLabel(self.title_bar)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.window_title.sizePolicy().hasHeightForWidth())
        self.window_title.setSizePolicy(sizePolicy)
        self.window_title.setMaximumSize(QSize(16777215, 16777215))
        self.window_title.setStyleSheet("QLabel{\n"
"    color: #fff;\n"
"    font-family: Segoe UI;\n"
"    font-size: 9pt;\n"
"}")
        self.window_title.setAlignment(Qt.AlignCenter)
        self.window_title.setObjectName("window_title")
        self.horizontalLayout_2.addWidget(self.window_title)
        self.exit_btn = QPushButton(self.title_bar)
        self.exit_btn.setMinimumSize(QSize(16, 16))
        self.exit_btn.setMaximumSize(QSize(16, 16))
        self.exit_btn.setFocusPolicy(Qt.NoFocus)
        self.exit_btn.setStyleSheet("QPushButton{\n"
"    border: none;\n"
"    background-color: #aaaaaa;\n"
"    border-radius: 8px\n"
"}\n"
"QPushButton:hover{\n"
"    background-color: #666666;\n"
"}")
        self.exit_btn.setText("")
        icon = QIcon()
        icon.addPixmap(QPixmap(":/img/exit.ico"), QIcon.Normal, QIcon.Off)
        self.exit_btn.setIcon(icon)
        self.exit_btn.setIconSize(QSize(12, 12))
        self.exit_btn.setObjectName("exit_btn")
        self.horizontalLayout_2.addWidget(self.exit_btn)
        self.verticalLayout_3.addWidget(self.title_bar)
        self.content_bar = QFrame(self.drop_shadow_frame)
        self.content_bar.setLayoutDirection(Qt.LeftToRight)
        self.content_bar.setStyleSheet("QWidget{\n"
"border-radius: 5px\n"
"}\n"
"#color_view{\n"
"    border-bottom-left-radius: 7px;\n"
"    border-bottom-right-radius: 7px;\n"
"}\n"
"#black_overlay{\n"
"    border-bottom-left-radius: 6px;\n"
"    border-bottom-right-radius: 6px;\n"
"}")
        self.content_bar.setFrameShape(QFrame.StyledPanel)
        self.content_bar.setFrameShadow(QFrame.Raised)
        self.content_bar.setObjectName("content_bar")
        self.horizontalLayout = QHBoxLayout(self.content_bar)
        self.horizontalLayout.setContentsMargins(10, 0, 10, 0)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.color_view = QFrame(self.content_bar)
        self.color_view.setMinimumSize(QSize(200, 200))
        self.color_view.setMaximumSize(QSize(200, 200))
        self.color_view.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: qlineargradient(x1:1, x2:0, stop:0 hsl(0%,100%,50%), stop:1 rgba(255, 255, 255, 255));\n"
"\n"
"")
        self.color_view.setFrameShape(QFrame.StyledPanel)
        self.color_view.setFrameShadow(QFrame.Raised)
        self.color_view.setObjectName("color_view")
        self.verticalLayout_2 = QVBoxLayout(self.color_view)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.black_overlay = QFrame(self.color_view)
        self.black_overlay.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(0, 0, 0, 255));\n"
"\n"
"\n"
"")
        self.black_overlay.setFrameShape(QFrame.StyledPanel)
        self.black_overlay.setFrameShadow(QFrame.Raised)
        self.black_overlay.setObjectName("black_overlay")
        self.selector = QFrame(self.black_overlay)
        self.selector.setGeometry(QRect(194, 20, 12, 12))
        self.selector.setMinimumSize(QSize(12, 12))
        self.selector.setMaximumSize(QSize(12, 12))
        self.selector.setStyleSheet("background-color:none;\n"
"border: 1px solid white;\n"
"border-radius: 5px;")
        self.selector.setFrameShape(QFrame.StyledPanel)
        self.selector.setFrameShadow(QFrame.Raised)
        self.selector.setObjectName("selector")
        self.black_ring = QLabel(self.selector)
        self.black_ring.setGeometry(QRect(1, 1, 10, 10))
        self.black_ring.setMinimumSize(QSize(10, 10))
        self.black_ring.setMaximumSize(QSize(10, 10))
        self.black_ring.setBaseSize(QSize(10, 10))
        self.black_ring.setStyleSheet("background-color: none;\n"
"border: 1px solid black;\n"
"border-radius: 5px;")
        self.black_ring.setText("")
        self.black_ring.setObjectName("black_ring")
        self.verticalLayout_2.addWidget(self.black_overlay)
        self.horizontalLayout.addWidget(self.color_view)
        self.frame_2 = QFrame(self.content_bar)
        self.frame_2.setMinimumSize(QSize(40, 0))
        self.frame_2.setStyleSheet("")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.hue_bg = QFrame(self.frame_2)
        self.hue_bg.setGeometry(QRect(10, 0, 20, 200))
        self.hue_bg.setMinimumSize(QSize(20, 200))
        self.hue_bg.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 0, 0, 255), stop:0.166 rgba(255, 255, 0, 255), stop:0.333 rgba(0, 255, 0, 255), stop:0.5 rgba(0, 255, 255, 255), stop:0.666 rgba(0, 0, 255, 255), stop:0.833 rgba(255, 0, 255, 255), stop:1 rgba(255, 0, 0, 255));\n"
"border-radius: 5px;")
        self.hue_bg.setFrameShape(QFrame.StyledPanel)
        self.hue_bg.setFrameShadow(QFrame.Raised)
        self.hue_bg.setObjectName("hue_bg")
        self.hue_selector = QLabel(self.frame_2)
        self.hue_selector.setGeometry(QRect(7, 185, 26, 15))
        self.hue_selector.setMinimumSize(QSize(26, 0))
        self.hue_selector.setStyleSheet("background-color: #aaa;\n"
"border-radius: 5px;")
        self.hue_selector.setText("")
        self.hue_selector.setObjectName("hue_selector")
        self.hue = QFrame(self.frame_2)
        self.hue.setGeometry(QRect(7, 0, 26, 200))
        self.hue.setMinimumSize(QSize(20, 200))
        self.hue.setStyleSheet("background-color: none;")
        self.hue.setFrameShape(QFrame.StyledPanel)
        self.hue.setFrameShadow(QFrame.Raised)
        self.hue.setObjectName("hue")
        self.horizontalLayout.addWidget(self.frame_2)
        self.editfields = QFrame(self.content_bar)
        self.editfields.setMinimumSize(QSize(110, 200))
        self.editfields.setMaximumSize(QSize(120, 200))
        self.editfields.setStyleSheet("QLabel{\n"
"    font-family: Segoe UI;\n"
"font-weight: bold;\n"
"    font-size: 11pt;\n"
"    color: #aaaaaa;\n"
"    border-radius: 5px;\n"
"}\n"
"")
        self.editfields.setFrameShape(QFrame.StyledPanel)
        self.editfields.setFrameShadow(QFrame.Raised)
        self.editfields.setObjectName("editfields")
        self.formLayout = QFormLayout(self.editfields)
        self.formLayout.setContentsMargins(15, 0, 15, 1)
        self.formLayout.setSpacing(5)
        self.formLayout.setObjectName("formLayout")
        self.color_vis = QLabel(self.editfields)
        self.color_vis.setMinimumSize(QSize(0, 24))
        self.color_vis.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: rgb(255, 255, 255);\n"
"")
        self.color_vis.setText("")
        self.color_vis.setObjectName("color_vis")
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.color_vis)
        self.lastcolor_vis = QLabel(self.editfields)
        self.lastcolor_vis.setMinimumSize(QSize(0, 24))
        self.lastcolor_vis.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */;\n"
"background-color: rgb(0, 0, 0);")
        self.lastcolor_vis.setText("")
        self.lastcolor_vis.setObjectName("lastcolor_vis")
        self.formLayout.setWidget(1, QFormLayout.FieldRole, self.lastcolor_vis)
        self.lbl_red = QLabel(self.editfields)
        self.lbl_red.setObjectName("lbl_red")
        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.lbl_red)
        self.red = QLineEdit(self.editfields)
        self.red.setAlignment(Qt.AlignCenter)
        self.red.setClearButtonEnabled(False)
        self.red.setObjectName("red")
        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.red)
        self.lbl_green = QLabel(self.editfields)
        self.lbl_green.setObjectName("lbl_green")
        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.lbl_green)
        self.green = QLineEdit(self.editfields)
        self.green.setAlignment(Qt.AlignCenter)
        self.green.setObjectName("green")
        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.green)
        self.lbl_blue = QLabel(self.editfields)
        self.lbl_blue.setObjectName("lbl_blue")
        self.formLayout.setWidget(4, QFormLayout.LabelRole, self.lbl_blue)
        self.blue = QLineEdit(self.editfields)
        self.blue.setAlignment(Qt.AlignCenter)
        self.blue.setObjectName("blue")
        self.formLayout.setWidget(4, QFormLayout.FieldRole, self.blue)
        self.lbl_hex = QLabel(self.editfields)
        self.lbl_hex.setStyleSheet("font-size: 14pt;")
        self.lbl_hex.setObjectName("lbl_hex")
        self.formLayout.setWidget(6, QFormLayout.LabelRole, self.lbl_hex)
        self.hex = QLineEdit(self.editfields)
        self.hex.setAlignment(Qt.AlignCenter)
        self.hex.setObjectName("hex")
        self.formLayout.setWidget(6, QFormLayout.FieldRole, self.hex)
        self.lbl_alpha = QLabel(self.editfields)
        self.lbl_alpha.setObjectName("lbl_alpha")
        self.formLayout.setWidget(5, QFormLayout.LabelRole, self.lbl_alpha)
        self.alpha = QLineEdit(self.editfields)
        self.alpha.setAlignment(Qt.AlignCenter)
        self.alpha.setObjectName("alpha")
        self.formLayout.setWidget(5, QFormLayout.FieldRole, self.alpha)
        self.horizontalLayout.addWidget(self.editfields)
        self.verticalLayout_3.addWidget(self.content_bar)
        self.button_bar = QFrame(self.drop_shadow_frame)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_bar.sizePolicy().hasHeightForWidth())
        self.button_bar.setSizePolicy(sizePolicy)
        self.button_bar.setStyleSheet("QFrame{\n"
"background-color: #1d1d1d;\n"
"padding: 5px\n"
"}\n"
"")
        self.button_bar.setFrameShape(QFrame.StyledPanel)
        self.button_bar.setFrameShadow(QFrame.Raised)
        self.button_bar.setObjectName("button_bar")
        self.horizontalLayout_3 = QHBoxLayout(self.button_bar)
        self.horizontalLayout_3.setContentsMargins(100, 0, 100, 0)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.buttonBox = QDialogButtonBox(self.button_bar)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_3.addWidget(self.buttonBox)
        self.verticalLayout_3.addWidget(self.button_bar)
        self.verticalLayout.addWidget(self.drop_shadow_frame)
        self.lbl_red.setBuddy(self.red)
        self.lbl_green.setBuddy(self.green)
        self.lbl_blue.setBuddy(self.blue)
        self.lbl_hex.setBuddy(self.blue)
        self.lbl_alpha.setBuddy(self.blue)

        self.retranslateUi(ColorPicker)
        QMetaObject.connectSlotsByName(ColorPicker)
        ColorPicker.setTabOrder(self.red, self.green)
        ColorPicker.setTabOrder(self.green, self.blue)

    def retranslateUi(self, ColorPicker):
        _translate = QCoreApplication.translate
        ColorPicker.setWindowTitle(_translate("ColorPicker", "Form"))
        self.window_title.setText(_translate("ColorPicker", "<strong>COLOR</strong> PICKER"))
        self.lbl_red.setText(_translate("ColorPicker", "R"))
        self.red.setText(_translate("ColorPicker", "255"))
        self.lbl_green.setText(_translate("ColorPicker", "G"))
        self.green.setText(_translate("ColorPicker", "255"))
        self.lbl_blue.setText(_translate("ColorPicker", "B"))
        self.blue.setText(_translate("ColorPicker", "255"))
        self.lbl_hex.setText(_translate("ColorPicker", "#"))
        self.hex.setText(_translate("ColorPicker", "ffffff"))
        self.lbl_alpha.setText(_translate("ColorPicker", "A"))
        self.alpha.setText(_translate("ColorPicker", "100"))




class ColorPicker(QDialog):

    def __init__(self, useAlpha: bool = False):

        # auto-create QApplication if it doesn't exist yet
        self.app = QApplication.instance()
        if self.app is None: self.app = QApplication([])

        super(ColorPicker, self).__init__()

        self.usingAlpha = True

        self.ui = Ui_Dark_Alpha()
        self.ui.setupUi(self)

        # Make Frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Color Picker")

        # Add DropShadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(17)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.ui.drop_shadow_frame.setGraphicsEffect(self.shadow)

        # Connect update functions
        self.ui.hue.mousePressEvent = self.moveHueSelector
        self.ui.hue.mouseMoveEvent = self.moveHueSelector
        self.ui.red.textEdited.connect(self.rgbChanged)
        self.ui.green.textEdited.connect(self.rgbChanged)
        self.ui.blue.textEdited.connect(self.rgbChanged)
        self.ui.hex.textEdited.connect(self.hexChanged)
        if self.usingAlpha: self.ui.alpha.textEdited.connect(self.alphaChanged)

        # Connect window dragging functions
        self.ui.title_bar.mouseMoveEvent = self.moveWindow
        self.ui.title_bar.mousePressEvent = self.setDragPos
        self.ui.window_title.mouseMoveEvent = self.moveWindow
        self.ui.window_title.mousePressEvent = self.setDragPos

        # Connect selector moving function
        self.ui.black_overlay.mouseMoveEvent = self.moveSVSelector
        self.ui.black_overlay.mousePressEvent = self.moveSVSelector

        # Connect Ok|Cancel Button Box and X Button
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.exit_btn.clicked.connect(self.reject)

        self.lastcolor = (0, 0, 0)
        self.color = (0, 0, 0)
        self.alpha = 100

    def getColor(self, lc: tuple = None):
        """Open the UI and get a color from the user.

        :param lc: The color to show as previous color.
        :return: The selected color.
        """

        if lc != None and self.usingAlpha:
            alpha = lc[3]
            lc = lc[:3]
            self.setAlpha(alpha)
            self.alpha = alpha
        if lc == None: lc = self.lastcolor
        else: self.lastcolor = lc

        self.setRGB(lc)
        self.rgbChanged()
        r,g,b = lc
        self.ui.lastcolor_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")

        if self.exec_():
            r, g, b = hsv2rgb(self.color)
            self.lastcolor = (r,g,b)
            if self.usingAlpha: return (r,g,b,self.alpha)
            return (r,g,b)

        else:
            return self.lastcolor

    # Update Functions
    def hsvChanged(self):
        h,s,v = (100 - self.ui.hue_selector.y() / 1.85, (self.ui.selector.x() + 6) / 2.0, (194 - self.ui.selector.y()) / 2.0)
        r,g,b = hsv2rgb(h,s,v)
        self.color = (h,s,v)
        self.setRGB((r,g,b))
        self.setHex(hsv2hex(self.color))
        self.ui.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.ui.color_view.setStyleSheet(f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({h}%,100%,50%), stop:1 #fff);")

    def rgbChanged(self):
        r,g,b = self.i(self.ui.red.text()), self.i(self.ui.green.text()), self.i(self.ui.blue.text())
        cr,cg,cb = self.clampRGB((r,g,b))

        if r!=cr or (r==0 and self.ui.red.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.red.selectAll()
        if g!=cg or (g==0 and self.ui.green.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.green.selectAll()
        if b!=cb or (b==0 and self.ui.blue.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.blue.selectAll()

        self.color = rgb2hsv(r,g,b)
        self.setHSV(self.color)
        self.setHex(rgb2hex((r,g,b)))
        self.ui.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")

    def hexChanged(self):
        hex = self.ui.hex.text()
        try:
            int(hex, 16)
        except ValueError:
            hex = "000000"
            self.ui.hex.setText("")
        r, g, b = hex2rgb(hex)
        self.color = hex2hsv(hex)
        self.setHSV(self.color)
        self.setRGB((r, g, b))
        self.ui.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")

    def alphaChanged(self):
        alpha = self.i(self.ui.alpha.text())
        oldalpha = alpha
        if alpha < 0: alpha = 0
        if alpha > 100: alpha = 100
        if alpha != oldalpha or alpha == 0:
            self.ui.alpha.setText(str(alpha))
            self.ui.alpha.selectAll()
        self.alpha = alpha

    # Internal setting functions
    def setRGB(self, c):
        r,g,b = c
        self.ui.red.setText(str(self.i(r)))
        self.ui.green.setText(str(self.i(g)))
        self.ui.blue.setText(str(self.i(b)))

    def setHSV(self, c):
        self.ui.hue_selector.move(7, int((100 - c[0]) * 1.85))
        self.ui.color_view.setStyleSheet(f"border-radius: 5px;background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({c[0]}%,100%,50%), stop:1 #fff);")
        self.ui.selector.move(int(c[1] * 2 - 6), int((200 - c[2] * 2) - 6))

    def setHex(self, c):
        self.ui.hex.setText(c)

    def setAlpha(self, a):
        self.ui.alpha.setText(str(a))

    # Dragging Functions
    def setDragPos(self, event):
        self.dragPos = event.globalPos()

    def moveWindow(self, event):
        # MOVE WINDOW
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPos() - self.dragPos)
            self.dragPos = event.globalPos()
            event.accept()

    def moveSVSelector(self, event):
        if event.buttons() == Qt.LeftButton:
            pos = event.pos()
            if pos.x() < 0: pos.setX(0)
            if pos.y() < 0: pos.setY(0)
            if pos.x() > 200: pos.setX(200)
            if pos.y() > 200: pos.setY(200)
            self.ui.selector.move(pos - QPoint(6,6))
            self.hsvChanged()

    def moveHueSelector(self, event):
        if event.buttons() == Qt.LeftButton:
            pos = event.pos().y() - 7
            if pos < 0: pos = 0
            if pos > 185: pos = 185
            self.ui.hue_selector.move(QPoint(7, pos))
            self.hsvChanged()

    # Utility

    # Custom int() function, that converts invalid strings to 0
    def i(self, text):
        try: return int(text)
        except ValueError: return 0

    # clamp function to remove near-zero values
    def clampRGB(self, rgb):
        r, g, b = rgb
        if r<0.0001: r=0
        if g<0.0001: g=0
        if b<0.0001: b=0
        if r>255: r=255
        if g>255: g=255
        if b>255: b=255
        return r, g, b


# Color Utility
def hsv2rgb(h_or_color: Union[tuple, int], s: int = 0, v: int = 0, a: int = None) -> tuple:
    """Convert hsv color to rgb color.

    :param h_or_color: The 'hue' value or a color tuple.
    :param s: The 'saturation' value.
    :param v: The 'value' value.
    :param a: The 'alpha' value.
    :return: The converted rgb tuple color.
    """

    if type(h_or_color).__name__ == "tuple":
        if len(h_or_color) == 4:
            h, s, v, a = h_or_color
        else:
            h, s, v = h_or_color
    else: h = h_or_color
    r, g, b = colorsys.hsv_to_rgb(h / 100.0, s / 100.0, v / 100.0)
    if a is not None: return r * 255, g * 255, b * 255, a
    return r * 255, g * 255, b * 255


def rgb2hsv(r_or_color: Union[tuple, int], g: int = 0, b: int = 0, a: int = None) -> tuple:
    """Convert rgb color to hsv color.

    :param r_or_color: The 'red' value or a color tuple.
    :param g: The 'green' value.
    :param b: The 'blue' value.
    :param a: The 'alpha' value.
    :return: The converted hsv tuple color.
    """

    if type(r_or_color).__name__ == "tuple":
        if len(r_or_color) == 4:
            r, g, b, a = r_or_color
        else:
            r, g, b = r_or_color
    else: r = r_or_color
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if a is not None: return h * 100, s * 100, v * 100, a
    return h * 100, s * 100, v * 100


def hex2rgb(hex: str) -> tuple:
    """Convert hex color to rgb color.

    :param hex: The hexadecimal string ("xxxxxx").
    :return: The converted rgb tuple color.
    """

    if len(hex) < 6: hex += "0"*(6-len(hex))
    elif len(hex) > 6: hex = hex[0:6]
    rgb = tuple(int(hex[i:i+2], 16) for i in (0,2,4))
    return rgb


def rgb2hex(r_or_color: Union[tuple, int], g: int = 0, b: int = 0, a: int = 0) -> str:
    """Convert rgb color to hex color.

    :param r_or_color: The 'red' value or a color tuple.
    :param g: The 'green' value.
    :param b: The 'blue' value.
    :param a: The 'alpha' value.
    :return: The converted hexadecimal color.
    """

    if type(r_or_color).__name__ == "tuple": r, g, b = r_or_color[:3]
    else: r = r_or_color
    hex = '%02x%02x%02x' % (int(r), int(g), int(b))
    return hex


def hex2hsv(hex: str) -> tuple:
    """Convert hex color to hsv color.

    :param hex: The hexadecimal string ("xxxxxx").
    :return: The converted hsv tuple color.
    """

    return rgb2hsv(hex2rgb(hex))


def hsv2hex(h_or_color: Union[tuple, int], s: int = 0, v: int = 0, a: int = 0) -> str:
    """Convert hsv color to hex color.

    :param h_or_color: The 'hue' value or a color tuple.
    :param s: The 'saturation' value.
    :param v: The 'value' value.
    :param a: The 'alpha' value.
    :return: The converted hexadecimal color.
    """

    if type(h_or_color).__name__ == "tuple": h, s, v = h_or_color[:3]
    else: h = h_or_color
    return rgb2hex(hsv2rgb(h, s, v))



__instance = None

def getColor(lc: tuple = None) -> tuple:
    """Shows the ColorPicker and returns the picked color.

    :param lc: The color to display as previous color.
    :return: The picked color.
    """

    global __instance

    if __instance is None:
        __instance = ColorPicker(useAlpha=__useAlpha, lightTheme=__lightTheme)

    if __useAlpha != __instance.usingAlpha or __lightTheme != __instance.usingLightTheme:
        del __instance
        __instance = ColorPicker(useAlpha=__useAlpha, lightTheme=__lightTheme)

    return __instance.getColor(lc)

def main():
    my_color_picker = ColorPicker(useAlpha=True)


    old_color = (255, 255, 255, 50)
    picked_color = my_color_picker.getColor(old_color)
    print(picked_color)



if __name__ == '__main__':
    main()