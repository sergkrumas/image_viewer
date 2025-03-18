






import hid
import time
from _utils import *
from functools import partial

__import__('builtins').__dict__['_'] = __import__('gettext').gettext

LISTENING_STOP = 0
BOARD_SCALE = 1
BOARD_OFFSET = 2
BUTTON_STATE = 3

BUTTON_PRESSED = 10
BUTTON_AUTOREPEAT = 11
BUTTON_RELEASED = 12

BUTTON_TRIANGLE = 20

class ListenThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self, gamepad, gamepad_device, obj):
        QThread.__init__(self)
        self.gamepad = gamepad

        self.dead_zone = obj.STNG_gamepad_dead_zone_radius

        manufacturer_string = gamepad_device['manufacturer_string']

        if manufacturer_string.startswith('ShanWan'):
            self.start_byte_left_stick = 3
            self.start_byte_right_stick = 5
            # self.dead_zone = 0.0

        elif manufacturer_string.startswith('Sony Interactive Entertainment'):
            self.start_byte_left_stick = 1
            self.start_byte_right_stick = 3
            # self.dead_zone = 0.1


        self.isPlayStation4DualShockGamepad = manufacturer_string.startswith('Sony Interactive Entertainment')

        self.byte_indexes_swapped = False

    def swap_read_byte_indexes(self):
        # меняем роли стиков местами
        self.start_byte_left_stick, self.start_byte_right_stick = self.start_byte_right_stick, self.start_byte_left_stick
        self.byte_indexes_swapped = not self.byte_indexes_swapped
        return self.byte_indexes_swapped

    def run(self):
        try:

            PS_triangle_button_bit = 1 << 7
            PS_circle_button_bit = 1 << 6
            PS_cross_button_bit = 1 << 5
            PS_square_button_bit = 1 << 4

            before_triangle_pressed = False

            while True:
                data = read_gamepad(self.gamepad)
                if data:

                    x_axis, y_axis = read_stick_data(data, start_byte_index=self.start_byte_left_stick, dead_zone=self.dead_zone)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        offset *= 20
                        self.update_signal.emit((BOARD_OFFSET, offset))

                    x_axis, y_axis = read_stick_data(data, start_byte_index=self.start_byte_right_stick, dead_zone=self.dead_zone)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        scroll_value = offset.y()
                        self.update_signal.emit((BOARD_SCALE, scroll_value))

                    if self.isPlayStation4DualShockGamepad:
                        rbb = data[5] #right buttons byte
                        but_state = bool(rbb & PS_cross_button_bit)

                        if but_state and before_triangle_pressed:
                            self.update_signal.emit((BUTTON_STATE, BUTTON_AUTOREPEAT, BUTTON_TRIANGLE))
                        elif but_state and not before_triangle_pressed:
                            self.update_signal.emit((BUTTON_STATE, BUTTON_PRESSED, BUTTON_TRIANGLE))
                        elif not but_state and before_triangle_pressed:
                            self.update_signal.emit((BUTTON_STATE, BUTTON_RELEASED, BUTTON_TRIANGLE, self.swap_read_byte_indexes()))

                        before_triangle_pressed = but_state

                # Если sleep здесь не использовать, то поток будет грузить проц (Intel i5-4670) до 37-43%
                # В обратном случае использование CPU падает до привычного значения
                time.sleep(0.001)

        except OSError:
            # print('Ошибка чтения. Скорее всего, геймпад отключён.')
            self.update_signal.emit((LISTENING_STOP,))

        self.exec_()

def update_board_viewer(obj, data):

    key = data[0]
    if key == BOARD_OFFSET:
        offset = data[1]
        obj.canvas_origin -= offset
    elif key == BOARD_SCALE:
        scroll_value = data[1]
        pivot = obj.rect().center()
        scale_speed = fit(abs(scroll_value), 0.0, 1.0, 350.0, 30.0)
        obj.do_scale_board(-scroll_value, False, False, True, pivot=pivot, scale_speed=scale_speed)
    elif key == LISTENING_STOP:
        deactivate_listening(obj)
    elif key == BUTTON_STATE:
        state = data[1]
        button = data[2]
        if state == BUTTON_RELEASED:
            status = data[3]
            if status:
                status = _("The left and right sticks exchange")
            else:
                status = _("The left and right sticks exchange back") 
            obj.show_center_label(f'{status}')

    obj.update()

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
            obj.gamepad_thread_instance.update_signal.connect(partial(update_board_viewer, obj))
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
    obj.show_center_label(_('Gamepad control deactivated!'), error=True)

def read_gamepad(gamepad):
    return gamepad.read(64)

def read_sticks_to_obj(obj):
    if obj.gamepad:
        try:
            data = read_gamepad(obj.gamepad)
            if data:
                x_axis, y_axis = read_stick_data(data)
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
    x_axis = fit(data[start_byte_index], 0, 256, -1.0, 1.0)
    y_axis = fit(data[start_byte_index+1], 0, 256, -1.0, 1.0)

    if dead_zone != 0.0:
        # x_axis, y_axis = apply_dead_zone_legacy_inaccurate(x_axis, y_axis, dead_zone)
        x_axis, y_axis = apply_dead_zone_accurately(x_axis, y_axis, dead_zone)

    return x_axis, y_axis

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
            return gamepad.read(64)

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

                        if n in [5, 6]:
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

