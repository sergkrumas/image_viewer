from _utils import *



class CommentWindow(QWidget):

    isWindowVisible = False
    is_initialized = False

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
        MW = self.globals.main_window
        cp = QDesktopWidget().availableGeometry().center()
        cp = MW.rect().center()
        qr = self.frameGeometry()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.activateWindow()

    def __init__(self):
        if self.is_initialized:
            return
        super().__init__()
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowModality(Qt.WindowModal)
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
        buttons = QHBoxLayout()
        buttons.addWidget(save_button)
        buttons.addWidget(exit_button)
        # main_layout.addSpacing(0)
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        self.setParent(self.globals.main_window)

        CommentWindow.isWindowVisible = True
        self.is_initialized = True

    def exit_button_handler(self):
        self.hide()

    def save_button_handler(self):
        self.comment.text = self.editfield.toPlainText()
        LibraryData().store_comments_list()
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
