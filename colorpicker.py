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


# Reworked based on https://github.com/nlfmt/pyqt-colorpicker

import sys
import colorsys
from typing import Union
from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ExitButton(QPushButton):

    def __init__(self, parent):
        super().__init__(parent)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.underMouse():
            background = QColor("#aaaaaa")
        else:
            background = QColor("#666666")
        painter.setBrush(QBrush(background))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.rect())
        painter.setPen(QPen(QColor(40, 40, 40), 3))
        r = self.rect().adjusted(5, 5, -4, -4)
        painter.drawLine(r.topLeft(), r.bottomRight())
        painter.drawLine(r.bottomLeft(), r.topRight())
        painter.end()



class Slider(QSlider):
    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)

    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1;
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == Qt.Horizontal else pr.y()
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - sliderMin,
                                               sliderMax - sliderMin, opt.upsideDown)


class UI_object(object):
    def setupUi(self, ColorPicker):
        ColorPicker.setObjectName("ColorPicker")
        size_w = 450
        size_h = 400
        ColorPicker.resize(size_w, size_h)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ColorPicker.sizePolicy().hasHeightForWidth())
        ColorPicker.setSizePolicy(sizePolicy)
        ColorPicker.setMinimumSize(QSize(size_w, size_h))
        ColorPicker.setMaximumSize(QSize(size_w, size_h))
        ColorPicker.setStyleSheet("""
            QWidget{
                background-color: none;
            }
            /*  LINE EDIT */
            QLineEdit{
                color: rgb(221, 221, 221);
                background-color: #303030;
                border: 1px solid black;
                selection-color: rgb(16, 16, 16);
                selection-background-color: rgb(221, 51, 34);
                font-family: Segoe UI;
                font-size: 18px;
            }
            /* PUSH BUTTON */
            QPushButton{
                border: 0px;
                font-family: Segoe UI;
                font-size: 15px;
                color: #888;
                width: 100px;
                height: 50px;
                background: #111111;
            }
            QPushButton:hover{
                color: #eee;
            }
            QPushButton:pressed{
                color: #eee;
            }"""
        )
        self.verticalLayout = QVBoxLayout(ColorPicker)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName("verticalLayout")
        self.drop_shadow_frame = QFrame(ColorPicker)
        self.drop_shadow_frame.setObjectName("main")
        self.drop_shadow_frame.setStyleSheet("""
            QFrame{
                background: #202020;
                border: 1px solid black;
            }
        """
        )
        self.drop_shadow_frame.setFrameShape(QFrame.StyledPanel)
        self.drop_shadow_frame.setFrameShadow(QFrame.Raised)
        self.drop_shadow_frame.setObjectName("drop_shadow_frame")
        self.drop_shadow_frame_layout = QVBoxLayout(self.drop_shadow_frame)
        self.drop_shadow_frame_layout.setContentsMargins(10, 10, 10, 10)
        self.drop_shadow_frame_layout.setSpacing(10)
        self.drop_shadow_frame_layout.setObjectName("drop_shadow_frame_layout")

        self.title_bar = QFrame(self.drop_shadow_frame)
        self.title_bar.setMinimumSize(QSize(0, 32))
        self.title_bar.setStyleSheet("background-color: rgb(48, 48, 48); border: none;")
        self.title_bar.setFrameShape(QFrame.StyledPanel)
        self.title_bar.setFrameShadow(QFrame.Raised)
        self.title_bar.setObjectName("title_bar")
        self.titlebar_layout = QHBoxLayout(self.title_bar)


        self.titlebar_layout.setContentsMargins(10, 0, 10, 0)
        self.titlebar_layout.setSpacing(5)
        self.titlebar_layout.setObjectName("titlebar_layout")
        spacerItem = QSpacerItem(16, 0, QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.titlebar_layout.addItem(spacerItem)



        self.window_title = QLabel()
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.window_title.sizePolicy().hasHeightForWidth())
        self.window_title.setSizePolicy(sizePolicy)
        self.window_title.setMaximumSize(QSize(16777215, 16777215))
        self.window_title.setStyleSheet("""
            QLabel{
                color: #fff;
                font-family: Segoe UI;
                font-size: 15px;
            }"""
        )
        self.window_title.setAlignment(Qt.AlignCenter)
        self.window_title.setObjectName("window_title")
        self.titlebar_layout.addWidget(self.window_title)



        self.exit_btn = ExitButton(self.title_bar)
        self.exit_btn.setMinimumSize(QSize(16, 16))
        self.exit_btn.setMaximumSize(QSize(16, 16))
        self.exit_btn.setFocusPolicy(Qt.NoFocus)
        # self.exit_btn.setStyleSheet("""
        #     QPushButton{
        #         border: none;
        #         background-color: #aaaaaa;
        #         border-radius: 8px
        #     }
        #     QPushButton:hover{
        #         background-color: #666666;
        #     }"""
        # )
        # self.exit_btn.setText("")
        # icon = QIcon()
        # icon.addPixmap(QPixmap(":/img/exit.ico"), QIcon.Normal, QIcon.Off)
        # self.exit_btn.setIcon(icon)
        # self.exit_btn.setIconSize(QSize(12, 12))
        # self.exit_btn.setObjectName("exit_btn")



        self.titlebar_layout.addWidget(self.exit_btn, Qt.AlignRight)

        self.drop_shadow_frame_layout.addWidget(self.title_bar)

        self.content_bar = QFrame(self.drop_shadow_frame)
        self.content_bar.setLayoutDirection(Qt.LeftToRight)
        self.content_bar.setStyleSheet("""
            QWidget{
                border: none;
            }
            #color_view{
                border: 1px;
            }
            #black_overlay{
                border: 1px;
            }"""
        )
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
        self.color_view.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */; background-color: qlineargradient(x1:1, x2:0, stop:0 hsl(0%,100%,50%), stop:1 rgba(255, 255, 255, 255));")
        self.color_view.setFrameShape(QFrame.StyledPanel)
        self.color_view.setFrameShadow(QFrame.Raised)
        self.color_view.setObjectName("color_view")
        self.verticalLayout_2 = QVBoxLayout(self.color_view)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.black_overlay = QFrame(self.color_view)
        self.black_overlay.setStyleSheet("border: none; background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0, 0, 0, 0), stop:1 rgba(0, 0, 0, 255));")
        self.black_overlay.setFrameShape(QFrame.StyledPanel)
        self.black_overlay.setFrameShadow(QFrame.Raised)
        self.black_overlay.setObjectName("black_overlay")
        self.selector = QFrame(self.black_overlay)
        self.selector.setGeometry(QRect(194, 20, 12, 12))
        self.selector.setMinimumSize(QSize(12, 12))
        self.selector.setMaximumSize(QSize(12, 12))
        self.selector.setStyleSheet("background-color:none; border: 1px solid white;")
        self.selector.setFrameShape(QFrame.StyledPanel)
        self.selector.setFrameShadow(QFrame.Raised)
        self.selector.setObjectName("selector")
        self.black_ring = QLabel(self.selector)
        self.black_ring.setGeometry(QRect(1, 1, 10, 10))
        self.black_ring.setMinimumSize(QSize(10, 10))
        self.black_ring.setMaximumSize(QSize(10, 10))
        self.black_ring.setBaseSize(QSize(10, 10))
        self.black_ring.setStyleSheet("background-color: none; border: 1px solid black;")
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
        self.frame_2.setStyleSheet('border: none;')

        self.hue_bg = QFrame(self.frame_2)
        self.hue_bg.setGeometry(QRect(10, 0, 10, 200))
        self.hue_bg.setMinimumSize(QSize(10, 200))
        self.hue_bg.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(255, 0, 0, 255), stop:0.166 rgba(255, 255, 0, 255), stop:0.333 rgba(0, 255, 0, 255), stop:0.5 rgba(0, 255, 255, 255), stop:0.666 rgba(0, 0, 255, 255), stop:0.833 rgba(255, 0, 255, 255), stop:1 rgba(255, 0, 0, 255));")
        self.hue_bg.setFrameShape(QFrame.StyledPanel)
        self.hue_bg.setFrameShadow(QFrame.Raised)
        self.hue_bg.setObjectName("hue_bg")

        self.hue_selector = QLabel(self.frame_2)
        self.hue_selector.setGeometry(QRect(7, 185, 16, 15))
        self.hue_selector.setMinimumSize(QSize(16, 0))
        self.hue_selector.setStyleSheet("background-color: #aaa;")
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
        self.editfields.setMinimumSize(QSize(120, 200))
        self.editfields.setMaximumSize(QSize(120, 200))
        self.editfields.setStyleSheet("""
            QLabel{
                font-family: Segoe UI;
                font-size: 15px;
                color: #aaaaaa;
                border: none;
            }"""
        )
        self.editfields.setFrameShape(QFrame.StyledPanel)
        self.editfields.setFrameShadow(QFrame.Raised)
        self.editfields.setObjectName("editfields")
        self.formLayout = QFormLayout(self.editfields)
        self.formLayout.setContentsMargins(15, 0, 15, 1)
        self.formLayout.setSpacing(5)
        self.formLayout.setObjectName("formLayout")
        self.color_vis = QLabel(self.editfields)
        self.color_vis.setMinimumSize(QSize(0, 24))
        self.color_vis.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */; background-color: rgb(255, 255, 255);")
        self.color_vis.setText("")
        self.color_vis.setObjectName("color_vis")
        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.color_vis)
        self.lastcolor_vis = QLabel(self.editfields)
        self.lastcolor_vis.setMinimumSize(QSize(0, 24))
        self.lastcolor_vis.setStyleSheet("/* ALL CHANGES HERE WILL BE OVERWRITTEN */; background-color: rgb(0, 0, 0);")
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
        self.drop_shadow_frame_layout.addWidget(self.content_bar)
        self.button_bar = QFrame(self.drop_shadow_frame)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.button_bar.sizePolicy().hasHeightForWidth())
        self.button_bar.setSizePolicy(sizePolicy)

        self.button_bar.setFrameShape(QFrame.StyledPanel)
        self.button_bar.setFrameShadow(QFrame.Raised)
        self.button_bar.setObjectName("button_bar")
        self.button_bar.setStyleSheet('border: none;')
        self.horizontalLayout_3 = QHBoxLayout(self.button_bar)
        self.horizontalLayout_3.setContentsMargins(100, 0, 100, 0)
        self.horizontalLayout_3.setSpacing(10)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.buttonBox = QDialogButtonBox(self.button_bar)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")





        self.opacity_slider = Slider(Qt.Horizontal)
        self.opacity_slider.setTickPosition(QSlider.NoTicks)
        self.opacity_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 6px;
                    background: #333333;
                    margin: 0px 0;
                }

                QSlider::handle:horizontal {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                    width: 18px;
                    margin: -2px 0;
                }
        """)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_bar = QFrame(self.drop_shadow_frame)
        self.opacity_bar.setStyleSheet('border: none;')
        self.opacity_bar.setFrameShadow(QFrame.Raised)

        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.opacity_bar.sizePolicy().hasHeightForWidth())
        self.opacity_bar.setSizePolicy(sizePolicy)

        self.opacity_slider_layout = QHBoxLayout(self.opacity_bar)
        self.lbl_alpha_slider = QLabel(self.opacity_slider)
        self.lbl_alpha_slider.setText('Opacity:')
        self.lbl_alpha_slider.setStyleSheet(self.editfields.styleSheet())
        self.drop_shadow_frame_layout.addWidget(self.opacity_bar)
        self.opacity_slider_layout.addWidget(self.lbl_alpha_slider)
        self.opacity_slider_layout.addWidget(self.opacity_slider)
        self.lbl_alpha_slider.setBuddy(self.opacity_slider)



        self.horizontalLayout_3.addWidget(self.buttonBox)
        self.drop_shadow_frame_layout.addWidget(self.button_bar)
        self.verticalLayout.addWidget(self.drop_shadow_frame)
        self.lbl_red.setBuddy(self.red)
        self.lbl_green.setBuddy(self.green)
        self.lbl_blue.setBuddy(self.blue)
        self.lbl_hex.setBuddy(self.blue)
        self.lbl_alpha.setBuddy(self.blue)

        self.window_title.setText('<b>Select Color<b>')
        self.lbl_red.setText("R:")
        self.red.setText("255")
        self.lbl_green.setText("G:")
        self.green.setText("255")
        self.lbl_blue.setText("B:")
        self.blue.setText("255")
        self.lbl_hex.setText("#:")
        self.hex.setText("ffffff")
        self.lbl_alpha.setText("A:")
        self.alpha.setText("100")

        QMetaObject.connectSlotsByName(ColorPicker)
        ColorPicker.setTabOrder(self.red, self.green)
        ColorPicker.setTabOrder(self.green, self.blue)





class ColorPicker(QDialog):

    def __init__(self):

        # auto-create QApplication if it doesn't exist yet
        self.app = QApplication.instance()
        if self.app is None: self.app = QApplication([])

        super(ColorPicker, self).__init__()


        self.ui = UI_object()
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
        self.ui.alpha.textEdited.connect(self.alphaChanged)
        self.ui.opacity_slider.valueChanged.connect(self.alphaSliderChanged)


        self.ui.alpha.wheelEvent = partial(ColorPicker.textfield_wheelEvent, self, self.ui.alpha)
        self.ui.red.wheelEvent = partial(ColorPicker.textfield_wheelEvent, self, self.ui.red)
        self.ui.blue.wheelEvent = partial(ColorPicker.textfield_wheelEvent, self, self.ui.blue)
        self.ui.green.wheelEvent = partial(ColorPicker.textfield_wheelEvent, self, self.ui.green)

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
        self.callback = None

    def textfield_wheelEvent(self, textEditObj, event):
        value = self.i(textEditObj.text())
        if event.angleDelta().y() > 0:
            value += 1
        else:
            value -= 1
        objectName = textEditObj.objectName()
        if objectName == 'alpha':
            value = min(100, max(0, value))
        elif objectName in ['red', 'green', 'blue']:
            value = min(255, max(0, value))
        textEditObj.setText(str(value))
        textEditObj.setFocus()
        textEditObj.selectAll()
        self.rgbChanged()

    def getColor(self, lc, callback=None):
        """Open the UI and get a color from the user.

        :param lc: The color to show as previous color.
        :return: The selected color.
        """
        self.callback = callback

        lc = (lc.red(), lc.green(), lc.blue(), int((lc.alpha()/255)*100))

        alpha = lc[3]
        lc = lc[:3]
        self.setAlpha(alpha)
        self.alpha = alpha

        self.lastcolor = lc

        self.setRGB(lc)
        self.rgbChanged()
        r, g, b = lc
        self.ui.lastcolor_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")

        if self.exec_():
            r, g, b = hsv2rgb(self.color)
            self.lastcolor = (r, g, b)
            return self.getCurrentColor()
        else:
            return self.getCurrentColor(self.lastcolor)

    def getCurrentColor(self, color=None):
        if color is None:
            r, g, b = hsv2rgb(self.color)
        else:
            r, g, b = color
        r = min(255, int(r))
        g = min(255, int(g))
        b = min(255, int(b))
        a = min(255, int(self.alpha/100*255))
        return QColor(r, g, b, a)

    def doCallback(self):
        if self.callback:
            self.callback(self.getCurrentColor())

    # Update Functions
    def hsvChanged(self):
        h,s,v = (100 - self.ui.hue_selector.y() / 1.85, (self.ui.selector.x() + 6) / 2.0, (194 - self.ui.selector.y()) / 2.0)
        r,g,b = hsv2rgb(h,s,v)
        self.color = (h,s,v)
        self.setRGB((r,g,b))
        self.setHex(hsv2hex(self.color))
        self.ui.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.ui.color_view.setStyleSheet(f"background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({h}%,100%,50%), stop:1 #fff);")
        self.doCallback()

    def rgbChanged(self):
        r, g, b = self.i(self.ui.red.text()), self.i(self.ui.green.text()), self.i(self.ui.blue.text())
        cr, cg, cb = self.clampRGB((r,g,b))

        if r != cr or (r == 0 and self.ui.red.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.red.selectAll()
        if g != cg or (g == 0 and self.ui.green.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.green.selectAll()
        if b != cb or (b == 0 and self.ui.blue.hasFocus()):
            self.setRGB((cr,cg,cb))
            self.ui.blue.selectAll()

        self.color = rgb2hsv(r, g, b)
        self.setHSV(self.color)
        self.setHex(rgb2hex((r, g, b)))
        self.ui.color_vis.setStyleSheet(f"background-color: rgb({r},{g},{b})")
        self.doCallback()

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
        self.doCallback()

    def alphaChanged(self):
        alpha = self.i(self.ui.alpha.text())
        oldalpha = alpha
        if alpha < 0:
            alpha = 0
        if alpha > 100:
            alpha = 100
        if alpha != oldalpha or alpha == 0:
            self.ui.alpha.setText(str(alpha))
            self.ui.alpha.selectAll()
        self.alpha = alpha
        self.ui.opacity_slider.setValue(self.alpha)
        self.doCallback()

    def alphaSliderChanged(self):
        alpha = self.ui.opacity_slider.value()
        self.alpha = alpha
        self.ui.alpha.setText(str(alpha))
        self.doCallback()

    # Internal setting functions
    def setRGB(self, c):
        r, g, b = c
        self.ui.red.setText(str(self.i(r)))
        self.ui.green.setText(str(self.i(g)))
        self.ui.blue.setText(str(self.i(b)))

    def setHSV(self, c):
        self.ui.hue_selector.move(7, int((100 - c[0]) * 1.85))
        self.ui.color_view.setStyleSheet(f"background-color: qlineargradient(x1:1, x2:0, stop:0 hsl({c[0]}%,100%,50%), stop:1 #fff);")
        self.ui.selector.move(int(c[1] * 2 - 6), int((200 - c[2] * 2) - 6))

    def setHex(self, c):
        self.ui.hex.setText(c)

    def setAlpha(self, a):
        self.ui.alpha.setText(str(a))
        self.ui.opacity_slider.setValue(a)

    # Dragging Functions
    def setDragPos(self, event):
        self.dragPos = event.globalPos()

    def moveWindow(self, event):
        # MOVE WINDOW
        if event.buttons() == Qt.LeftButton:
            if hasattr(self, 'dragPos'):
                self.move(self.pos() + event.globalPos() - self.dragPos)
                self.dragPos = event.globalPos()
                event.accept()

    def moveSVSelector(self, event):
        if event.buttons() == Qt.LeftButton:
            pos = event.pos()
            if pos.x() < 0:
                pos.setX(0)
            if pos.y() < 0:
                pos.setY(0)
            if pos.x() > 200:
                pos.setX(200)
            if pos.y() > 200:
                pos.setY(200)
            self.ui.selector.move(pos - QPoint(6,6))
            self.hsvChanged()

    def moveHueSelector(self, event):
        if event.buttons() == Qt.LeftButton:
            pos = event.pos().y() - 7
            if pos < 0:
                pos = 0
            if pos > 185:
                pos = 185
            self.ui.hue_selector.move(QPoint(7, pos))
            self.hsvChanged()

    # Utility

    # Custom int() function, that converts invalid strings to 0
    def i(self, text):
        try:
            return int(text)
        except ValueError:
            return 0

    # clamp function to remove near-zero values
    def clampRGB(self, rgb):
        r, g, b = rgb
        if r < 0.0001:
            r = 0
        if g < 0.0001:
            g = 0
        if b < 0.0001:
            b = 0
        if r > 255:
            r = 255
        if g > 255:
            g = 255
        if b > 255:
            b = 255
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

    if isinstance(h_or_color, tuple):
        if len(h_or_color) == 4:
            h, s, v, a = h_or_color
        else:
            h, s, v = h_or_color
    else:
        h = h_or_color
    r, g, b = colorsys.hsv_to_rgb(h / 100.0, s / 100.0, v / 100.0)
    if a is not None:
        return r * 255, g * 255, b * 255, a
    return r * 255, g * 255, b * 255


def rgb2hsv(r_or_color: Union[tuple, int], g: int = 0, b: int = 0, a: int = None) -> tuple:
    """Convert rgb color to hsv color.

    :param r_or_color: The 'red' value or a color tuple.
    :param g: The 'green' value.
    :param b: The 'blue' value.
    :param a: The 'alpha' value.
    :return: The converted hsv tuple color.
    """

    if isinstance(r_or_color, tuple):
        if len(r_or_color) == 4:
            r, g, b, a = r_or_color
        else:
            r, g, b = r_or_color
    else:
        r = r_or_color
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    if a is not None:
        return h * 100, s * 100, v * 100, a
    return h * 100, s * 100, v * 100


def hex2rgb(hex: str) -> tuple:
    """Convert hex color to rgb color.

    :param hex: The hexadecimal string ("xxxxxx").
    :return: The converted rgb tuple color.
    """

    if len(hex) < 6:
        hex += "0"*(6-len(hex))
    elif len(hex) > 6:
        hex = hex[0:6]
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

    if isinstance(r_or_color, tuple):
        r, g, b = r_or_color[:3]
    else:
        r = r_or_color
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

    if isinstance(h_or_color, tuple):
        h, s, v = h_or_color[:3]
    else:
        h = h_or_color
    return rgb2hex(hsv2rgb(h, s, v))



__instance = None

def getColor(lc: tuple = None) -> tuple:

    global __instance

    if __instance is None:
        __instance = ColorPicker()

    return __instance.getColor(lc)

class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowMinimizeButtonHint)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

def main():
    app = QApplication(sys.argv)

    w = TestWidget()
    w.show()

    my_color_picker = ColorPicker()

    def callback(value):
        argb = value.name(QColor.HexArgb)
        css = f'background: {argb}'
        print(css, argb)
        w.setStyleSheet(css)
        w.update()

    old_color = QColor(255, 255, 255, 100)
    picked_color = my_color_picker.getColor(old_color, callback=callback)
    print(picked_color.name(QColor.HexArgb))

    app.exec()


if __name__ == '__main__':
    main()
