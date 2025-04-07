






import hid
import time
from _utils import *
from functools import partial
from collections import defaultdict

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

LISTENING_STOP = 0
BOARD_SCALE_DATA = 1
BOARD_OFFSET_DATA = 2
BUTTON_STATE_DATA = 3
TRIGGER_STATE_DATA = 4

BUTTON_PRESSED = 10
BUTTON_AUTOREPEAT = 11
BUTTON_RELEASED = 12


BUTTON_TRIANGLE = 20
BUTTON_CIRCLE = 21
BUTTON_CROSS = 22
BUTTON_SQUARE = 23

BUTTON_L1 = 24
BUTTON_R1 = 25

BUTTON_OPTIONS = 50
BUTTON_SHARE = 51

LEFT_TRIGGER = 26
RIGHT_TRIGGER = 27


class ButtonsStatesHandler():

    def __init__(self, convert_dict, tag_data_dict):
        self.buttons_bit_flags = list(convert_dict.keys())
        self.tag_data_dict = tag_data_dict
        self.BUTTONS_INTS = list(convert_dict.values())
        self.buttons_count = len(self.buttons_bit_flags)
        self.states = [False] * self.buttons_count
        self.before_states = [False] * self.buttons_count

    def prepare_data(self, data):
        prepared_data = []
        for data_item in data:
            if callable(data_item):
                data_item = data_item()
            prepared_data.append(data_item)
        return prepared_data

    def handler(self, input_byte, update_signal):
        for i, flag in enumerate(self.buttons_bit_flags):
            self.states[i] = bool(input_byte & flag)

        for i in range(self.buttons_count):
            BUTTON_INT = self.BUTTONS_INTS[i]
            state = self.states[i]
            if state and self.before_states[i]:
                st = BUTTON_AUTOREPEAT
                data = self.tag_data_dict.get((st, BUTTON_INT), [])
                update_signal.emit((BUTTON_STATE_DATA, st, BUTTON_INT, *self.prepare_data(data)))
            elif state and not self.before_states[i]:
                st = BUTTON_PRESSED
                data = self.tag_data_dict.get((st, BUTTON_INT), [])
                update_signal.emit((BUTTON_STATE_DATA, st, BUTTON_INT, *self.prepare_data(data)))
            elif not state and self.before_states[i]:
                st = BUTTON_RELEASED
                data = self.tag_data_dict.get((st, BUTTON_INT), [])
                update_signal.emit((BUTTON_STATE_DATA, st, BUTTON_INT, *self.prepare_data(data)))

            self.before_states[i] = state


class ListenThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self, gamepad, gamepad_device, obj):
        QThread.__init__(self)
        self.gamepad = gamepad

        # exp от 1.0 до 4.0
        self.easeInExpo = obj.STNG_gamepad_move_stick_ease_in_expo_param

        self.dead_zone_radius = obj.STNG_gamepad_dead_zone_radius
        self.pass_deadzone_values = obj.STNG_show_gamepad_monitor

        manufacturer_string = gamepad_device['manufacturer_string']

        if manufacturer_string.startswith('ShanWan'):
            self.start_byte_left_stick = 3
            self.start_byte_right_stick = 5

        elif manufacturer_string.startswith('Sony Interactive Entertainment'):
            self.start_byte_left_stick = 1
            self.start_byte_right_stick = 3
            self.left_trigger_byte_index = 8
            self.right_trigger_byte_index = 9

        self.isPlayStation4DualShockGamepad = manufacturer_string.startswith('Sony Interactive Entertainment')

        self.byte_indexes_swapped = False

        self.triggers_factors = defaultdict(float)

    def swap_read_byte_indexes(self):
        # меняем роли стиков местами
        self.start_byte_left_stick, self.start_byte_right_stick = self.start_byte_right_stick, self.start_byte_left_stick
        self.byte_indexes_swapped = not self.byte_indexes_swapped
        return self.byte_indexes_swapped

    def change_easeInExpo(self, direction):
        eie = self.easeInExpo
        eie *= 10.0
        eie = int(eie)
        eie += direction
        eie /= 10.0
        self.easeInExpo = min(4.0, max(1.0, eie))

    def to_pass_or_not_to_pass(self, value, index):
        before_value = self.triggers_factors[index]
        self.triggers_factors[index] = value
        # мы должны пропустить в очередь сообщений первое нулевое значение, 
        # а последующие нулевые значения отбрасывать пока поток снова не сменится на ненулевые значения
        if before_value == .0 and value == .0:
            return False
        else:
            return True


    def doEaseInExpo(self, value):
        exp = self.easeInExpo
        if exp > 1.0:
            modified_value = math.pow(abs(value), exp)
            return math.copysign(modified_value, value)
        else:
            return value

    def run(self):
        try:

            PS_triangle_button_bit = 1 << 7
            PS_circle_button_bit = 1 << 6
            PS_cross_button_bit = 1 << 5
            PS_square_button_bit = 1 << 4

            PS_options_button = 1 << 5
            PS_share_button = 1 << 4

            PS_l1_button = 1 << 0
            PS_r1_button = 1 << 1

            options_share_btns_handler = ButtonsStatesHandler(
                {
                    PS_options_button: BUTTON_OPTIONS,
                    PS_share_button: BUTTON_SHARE,

                    PS_l1_button: BUTTON_L1,
                    PS_r1_button: BUTTON_R1,
                },
                {
                    (BUTTON_RELEASED, BUTTON_L1): [lambda: self.change_easeInExpo(-1)],
                    (BUTTON_RELEASED, BUTTON_R1): [lambda: self.change_easeInExpo(1)],
                }
            )

            right_btns_handler = ButtonsStatesHandler(
                {
                    PS_triangle_button_bit: BUTTON_TRIANGLE,
                    PS_circle_button_bit: BUTTON_CIRCLE,
                    PS_cross_button_bit: BUTTON_CROSS,
                    PS_square_button_bit: BUTTON_SQUARE,
                },
                {
                    (BUTTON_RELEASED, BUTTON_CROSS): [self.swap_read_byte_indexes],
                }
            )


            while True:
                data = read_gamepad(self.gamepad)
                if data:

                    x_axis, y_axis, rx1, ry1 = read_stick_data(data, start_byte_index=self.start_byte_left_stick, dead_zone=self.dead_zone_radius)
                    x_axis, y_axis = self.doEaseInExpo(x_axis), self.doEaseInExpo(y_axis)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        self.update_signal.emit((BOARD_OFFSET_DATA, offset, rx1, ry1))
                    elif self.pass_deadzone_values:
                        self.update_signal.emit((BOARD_OFFSET_DATA, QPointF(0, 0), rx1, ry1))

                    x_axis, y_axis, rx2, ry2 = read_stick_data(data, start_byte_index=self.start_byte_right_stick, dead_zone=self.dead_zone_radius)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        scroll_value = offset.y()
                        self.update_signal.emit((BOARD_SCALE_DATA, scroll_value, rx2, ry2))
                    elif self.pass_deadzone_values:
                        self.update_signal.emit((BOARD_SCALE_DATA, 0.0, rx2, ry2))


                    if self.isPlayStation4DualShockGamepad:

                        right_btns_handler.handler(data[5], self.update_signal)
                        options_share_btns_handler.handler(data[6], self.update_signal)


                    # reading triggers factors
                    for n, (index, TRG_DEF) in enumerate({
                                            self.left_trigger_byte_index: LEFT_TRIGGER,
                                            self.right_trigger_byte_index: RIGHT_TRIGGER}.items()):
                        trigger_factor = read_trigger_data(data, index)
                        if self.to_pass_or_not_to_pass(trigger_factor, n):
                            self.update_signal.emit((TRIGGER_STATE_DATA, TRG_DEF, trigger_factor))


                # Если sleep здесь не использовать, то поток будет грузить проц (Intel i5-4670) до 37-43%
                # В обратном случае использование CPU падает до привычного значения
                time.sleep(0.001)

        except OSError:
            # print('Ошибка чтения. Скорее всего, геймпад отключён.')
            self.update_signal.emit((LISTENING_STOP,))

        self.exec_()

def update_board_viewer(MainWindowObj, thread, data):

    key = data[0]
    if key == BOARD_OFFSET_DATA:
        offset = data[1]
        if offset:
            offset *= MainWindowObj.STNG_gamepad_move_stick_speed
            MainWindowObj.canvas_origin -= offset
        MainWindowObj.left_stick_vec = QPointF(data[2], data[3])
    elif key == BOARD_SCALE_DATA:
        scroll_value = data[1]
        if scroll_value:
            pivot = MainWindowObj.rect().center()
            # in fact, scale_speed is reciprocal of speed, lol
            scale_speed = 1.0/fit(abs(scroll_value), 0.0, 1.0, 0.000001, 0.02)
            MainWindowObj.do_scale_board(-scroll_value, False, False, True, pivot=pivot, scale_speed=scale_speed)
        MainWindowObj.right_stick_vec = QPointF(data[2], data[3])
    elif key == LISTENING_STOP:
        deactivate_listening(MainWindowObj)
    elif key == BUTTON_STATE_DATA:
        state = data[1]
        button = data[2]
        if state == BUTTON_RELEASED:
            if button == BUTTON_CROSS:
                status = data[3]
                if status:
                    status = _("The left and right sticks exchange")
                else:
                    status = _("The left and right sticks exchange back")
                MainWindowObj.show_center_label(f'{status}')
            elif button == BUTTON_SHARE:
                MainWindowObj.board_viewport_reset(scale=False)
                MainWindowObj.show_center_label('viewport position is reset!')
            elif button == BUTTON_OPTIONS:
                MainWindowObj.board_viewport_reset(position=False, scale=False, scale_inplace=True)
                MainWindowObj.show_center_label('viewport scale is reset!')
            elif button in [BUTTON_L1, BUTTON_R1]:
                MainWindowObj.STNG_gamepad_move_stick_ease_in_expo_param = thread.easeInExpo
                MainWindowObj.show_easeInExpo_monitor = True
                MainWindowObj.show_center_label(f'easeInExponenta: {thread.easeInExpo}')
                MainWindowObj.boards_generate_expo_values()
                MainWindowObj.boards_save_expo_to_app_settings()
    elif key == TRIGGER_STATE_DATA:
        trigger = data[1]
        trigger_factor = data[2]
        if trigger == LEFT_TRIGGER:
            stick_name = 'left'
        elif trigger == RIGHT_TRIGGER:
            stick_name = 'right'
        MainWindowObj.show_center_label(f'{stick_name} trigger factor: {trigger_factor:.02}')

    MainWindowObj.update()

def draw_gamepad_easing_monitor(self, painter, event):

    painter.save()
    rect = self.rect()

    if not self.expo_values:
        self.boards_generate_expo_values()

    WIDTH = 300
    graph_rect = QRectF(0, 0, WIDTH, WIDTH)
    pos = QPointF(rect.center())
    pos.setY(WIDTH/2+50)
    graph_rect.moveCenter(pos)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(30, 30, 30, 200))
    painter.drawRect(graph_rect.adjusted(-30, -30, 30, 60))

    if True:
        # drawing grid
        canvas_scale_x = 1.0
        canvas_scale_y = 1.0
        icp = QPointF(0.0, 0.0)

        LINES_INTERVAL_X = 25 * canvas_scale_x
        LINES_INTERVAL_Y = 25 * canvas_scale_y
        r = QRectF(graph_rect).adjusted(0, 0, 1, 1)

        pen = QPen(QColor(220, 220, 220, 40), 1)
        painter.setPen(pen)
        offset = QPointF(icp.x() % LINES_INTERVAL_X, icp.y() % LINES_INTERVAL_Y)

        i = r.left()
        while i < r.right():
            painter.drawLine(offset+QPointF(i, r.top()), offset+QPointF(i, r.bottom()))
            i += LINES_INTERVAL_X

        i = r.top()
        while i < r.bottom():
            painter.drawLine(offset+QPointF(r.left(), i), offset+QPointF(r.right(), i))
            i += LINES_INTERVAL_Y



    pen = QPen(Qt.red, 5)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    values = self.expo_values
    for n, (x1, y1) in enumerate(values[:-1]):
        x2, y2 = values[n+1]
        a = graph_rect.bottomLeft() + QPointF(x1*WIDTH, y1*WIDTH*-1.0)
        b = graph_rect.bottomLeft() + QPointF(x2*WIDTH, y2*WIDTH*-1.0)
        painter.drawLine(a, b)

    font = painter.font()
    font.setPixelSize(15)
    painter.setFont(font)


    painter.setPen(QPen(Qt.white, 1))

    offset = QPoint(-10, 15)
    painter.drawText(graph_rect.bottomLeft()+offset, '0.0')
    painter.drawText(graph_rect.bottomRight()+offset, '1.0')
    painter.drawText(graph_rect.topLeft()+QPoint(-10, -5), '1.0')

    font = painter.font()
    font.setPixelSize(60)
    font.setWeight(1900)
    painter.setFont(font)
    painter.setPen(QPen(Qt.red, 1))
    exp = self.STNG_gamepad_move_stick_ease_in_expo_param
    painter.drawText(graph_rect.topLeft()+QPoint(50, 70), f'{exp:.02}')

    if exp > 1.0:
        painter.setPen(QPen(Qt.green, 1))
        text = 'easing modifier is applied'
    else:
        painter.setPen(QPen(Qt.gray, 1))
        text = 'easing modifier is off'


    font = painter.font()
    font.setPixelSize(15)
    painter.setFont(font)

    rect = QRectF(graph_rect.bottomLeft(), graph_rect.bottomRight()+QPointF(0, 50))
    painter.drawText(rect, Qt.AlignVCenter | Qt.AlignHCenter, text)


    curpos = self.mapFromGlobal(QCursor().pos())
    if graph_rect.contains(curpos):
        coord = curpos - graph_rect.bottomLeft()
        x = coord.x()/WIDTH
        y = math.pow(x, exp)

        xP = QPointF(x*WIDTH, 0) + graph_rect.bottomLeft()
        graphP = QPointF(x*WIDTH, -y*WIDTH) + graph_rect.bottomLeft()
        yP = QPointF(0, -y*WIDTH) + graph_rect.bottomLeft()
        painter.drawLine(xP, graphP)
        painter.drawLine(graphP, yP)

        painter.drawText(graph_rect, Qt.AlignVCenter | Qt.AlignHCenter, f'X: {x:.02} ➜ Y: {y:.02}')


    painter.restore()


def draw_gamepad_monitor(self, painter, event):

    painter.save()
    rect = self.rect()

    c = rect.center()
    stick_pixel_radius = int(rect.width() / 5.0)
    offset = QPoint(stick_pixel_radius, 0)

    left_stick_origin = c - offset
    right_stick_origin = c + offset


    # sticks whole zones
    D = stick_pixel_radius * 2
    left_stick_rect = QRect(0, 0, D, D)
    right_stick_rect = QRect(0, 0, D, D)

    left_stick_rect.moveCenter(left_stick_origin)
    right_stick_rect.moveCenter(right_stick_origin)

    painter.setPen(QPen(QColor(0, 255, 0, 255)))
    painter.setBrush(QBrush(QColor(0, 255, 0, 50)))
    painter.drawEllipse(left_stick_rect)
    painter.drawEllipse(right_stick_rect)


    # sticks dead zones
    DZ_D = int(self.STNG_gamepad_dead_zone_radius*stick_pixel_radius) * 2
    left_stick_dead_zone_rect = QRect(0, 0, DZ_D, DZ_D)
    right_stick_dead_zone_rect = QRect(0, 0, DZ_D, DZ_D)

    left_stick_dead_zone_rect.moveCenter(left_stick_origin)
    right_stick_dead_zone_rect.moveCenter(right_stick_origin)

    painter.setPen(QPen(QColor(255, 0, 0, 255)))
    painter.setBrush(QBrush(QColor(255, 0, 0, 50)))
    painter.drawEllipse(left_stick_dead_zone_rect)
    painter.drawEllipse(right_stick_dead_zone_rect)

    left_stick_vector = self.left_stick_vec*stick_pixel_radius
    right_stick_vector = self.right_stick_vec*stick_pixel_radius

    pen = QPen(Qt.white, 3)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(left_stick_origin, left_stick_origin+left_stick_vector)
    painter.drawLine(right_stick_origin, right_stick_origin+right_stick_vector)

    painter.restore()

def find_gamepad():
    gamepad_device = None

    for device in hid.enumerate():
        manufacturer_string = device['manufacturer_string']
        product_string = device['product_string']

        # print(manufacturer_string, product_string)

        if manufacturer_string.startswith('ShanWan') and product_string == 'PC/PS3/Android Gamepad':
            gamepad_device = device

        if manufacturer_string.startswith('Sony Interactive Entertainment') and product_string.startswith('Wireless Controller'):
            gamepad_device = device

    return gamepad_device

def open_device(device):
    gamepad = hid.device()
    gamepad.open(device['vendor_id'], device['product_id'])
    gamepad.set_nonblocking(True)
    return gamepad

def activate_gamepad(obj):
    if obj.gamepad:
        deactivate_listening(obj)
    else:
        gamepad_device = find_gamepad()
        if gamepad_device:
            obj.gamepad = open_device(gamepad_device)
            obj.gamepad_timer = timer = QTimer()
            # timer.setInterval(10)
            # timer.timeout.connect(partial(read_sticks_to_obj, obj))
            # timer.start()
            obj.gamepad_thread_instance = ListenThread(obj.gamepad, gamepad_device, obj)
            obj.gamepad_thread_instance.update_signal.connect(partial(update_board_viewer, obj, obj.gamepad_thread_instance))
            obj.gamepad_thread_instance.start()

            obj.show_center_label(_('Gamepad control activated!'))
        else:
            obj.gamepad = None
            # obj.timer = None
            obj.show_center_label(_('Gamepad not found!'), error=True)

def deactivate_listening(obj):
    obj.gamepad = None
    # obj.timer.stop()
    obj.gamepad_thread_instance.terminate()
    obj.gamepad_thread_instance = None

    obj.left_stick_vec = QPointF(0, 0)
    obj.right_stick_vec = QPointF(0, 0)

    obj.show_center_label(_('Gamepad control deactivated!'), error=True)

def read_gamepad(gamepad):
    return gamepad.read(64)

def read_sticks_to_obj(obj):
    if obj.gamepad:
        try:
            data = read_gamepad(obj.gamepad)
            if data:
                x_axis, y_axis, __, __ = read_stick_data(data)
                offset = QPointF(x_axis, y_axis)
                if offset:
                    offset *= 20
                    obj.canvas_origin -= offset
                    obj.update()

                x_axis, y_axis = read_right_stick(data)
                offset = QPointF(x_axis, y_axis)
                if offset:
                    scroll_value = -offset.y()
                    pivot = obj.rect().center()
                    obj.do_scale_board(scroll_value, False, False, True, pivot=pivot, scale_speed=100.0)
                    obj.update()

        except OSError:
            # print('Ошибка чтения. Скорее всего, геймпад отключён.')
            deactivate_listening(obj)

def apply_dead_zone_legacy_inaccurate(x_axis, y_axis, dead_zone):
    if abs(x_axis) < dead_zone:
        x_axis = 0.0
    if abs(y_axis) < dead_zone:
        y_axis = 0.0
    return x_axis, y_axis

def apply_dead_zone_accurately(x_axis, y_axis, dead_zone):
    x_ = fit(abs(x_axis), dead_zone, 1.0, 0.0, 1.0)
    y_ = fit(abs(y_axis), dead_zone, 1.0, 0.0, 1.0)
    x_axis = math.copysign(x_, x_axis)
    y_axis = math.copysign(y_, y_axis)
    return x_axis, y_axis

def read_stick_data(data, start_byte_index=3, dead_zone=0.0):
    input_x_axis = fit(data[start_byte_index], 0, 256, -1.0, 1.0)
    input_y_axis = fit(data[start_byte_index+1], 0, 256, -1.0, 1.0)

    if dead_zone != 0.0:
        # input_x_axis, input_y_axis = apply_dead_zone_legacy_inaccurate(input_x_axis, input_y_axis, dead_zone)
        x_axis, y_axis = apply_dead_zone_accurately(input_x_axis, input_y_axis, dead_zone)
    else:
        x_axis, y_axis = input_x_axis, input_y_axis

    return x_axis, y_axis, input_x_axis, input_y_axis

def read_trigger_data(data, trigger_byte_index):
    return fit(data[trigger_byte_index], 0, 255, 0.0, 1.0)

def read_right_stick(data, start_byte_index=5, dead_zone=0.0):
    x_axis = fit(data[start_byte_index], 0, 256, -1.0, 1.0)
    y_axis = fit(data[start_byte_index+1], 0, 256, -1.0, 1.0)

    if dead_zone != 0.0:
        x_axis, y_axis = apply_dead_zone_legacy_inaccurate(x_axis, y_axis, dead_zone)

    return x_axis, y_axis

def main():

    gamepad_device = find_gamepad()

    if gamepad_device:
        gamepad = open_device(gamepad_device)

        def read_gamepad():
            return gamepad.read(48)

        try:
            # a = time.time()
            before_data = None

            while True:
                data = read_gamepad()
                if data:
                    out = []
                    for n, data_byte in enumerate(data):
                        byte_value = str(data_byte).zfill(3)
                        # byte_descr = f'({n}){byte_value}'
                        # byte_descr = f'{byte_value}'
                        byte_descr = f'{data_byte:08b} {data_byte}'

                        if n == 5:
                            triangle_button = 1 << 7
                            circle_button = 1 << 6
                            cross_button = 1 << 5
                            square_button = 1 << 4
                            if data_byte & triangle_button:
                                byte_descr += ' t'
                            if data_byte & circle_button:
                                byte_descr += ' c'
                            if data_byte & cross_button:
                                byte_descr += ' x'
                            if data_byte & square_button:
                                byte_descr += ' s'
                        if n == 6:
                            right_stick = 1 << 7
                            left_stick = 1 << 6
                            options_button = 1 << 5
                            share_button = 1 << 4

                            l1_button = 1 << 0
                            r1_button = 1 << 1

                            if data_byte & share_button:
                                byte_descr += ' share'
                            if data_byte & options_button:
                                byte_descr += ' options'
                            if data_byte & left_stick:
                                byte_descr += ' left stick'
                            if data_byte & right_stick:
                                byte_descr += ' right stick'
                            if data_byte & l1_button:
                                byte_descr += ' l1_button'
                            if data_byte & r1_button:
                                byte_descr += ' r1_button'
                        if n in [8, 9]:
                            byte_descr += str(data_byte)

                        if False:
                            out.append(str(data_byte).zfill(3))
                        else:

                            if n in [5, 6, 8, 9]:
                                out.append(byte_descr)


                    out = " ".join(out)
                    print(out)
                    # x_axis, y_axis = read_left_stick(data)

                    # print(f'{x_axis}, {y_axis}')

                    # delta = time.time() - a
                    # print(delta)
                    if False and before_data is not None:
                        changed_indexes = []
                        for n, byte_value in enumerate(data):
                            if byte_value != before_data[n]:
                                changed_indexes.append(n)

                        print(changed_indexes)
                    else:

                        before_data = data
        except OSError:
            print(_("Reading error. Feels like the gamepad is off"))
            pass

if __name__ == '__main__':
    main()

