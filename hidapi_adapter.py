






import hid
import time
from _utils import *
from functools import partial



class ListenThread(QThread):
    update_signal = pyqtSignal(object)

    def __init__(self, gamepad, gamepad_device):
        QThread.__init__(self)
        self.gamepad = gamepad

        manufacturer_string = gamepad_device['manufacturer_string']

        if manufacturer_string.startswith('ShanWan'):
            self.start_byte_left_stick = 3
            self.start_byte_right_stick = 5
            self.dead_zone = 0.0

        elif manufacturer_string.startswith('Sony Interactive Entertainment'):
            self.start_byte_left_stick = 1
            self.start_byte_right_stick = 3
            self.dead_zone = 0.1

    def run(self):
        try:
            while True:
                data = read_gamepad(self.gamepad)
                if data:
                    x_axis, y_axis = read_left_stick(data, start_byte_index=self.start_byte_left_stick, dead_zone=self.dead_zone)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        offset *= 20
                        self.update_signal.emit(('offset', offset))

                    x_axis, y_axis = read_right_stick(data, start_byte_index=self.start_byte_right_stick, dead_zone=self.dead_zone)
                    offset = QPointF(x_axis, y_axis)
                    if offset:
                        scroll_value = offset.y()
                        self.update_signal.emit(('scale', scroll_value))
                # Если sleep здесь не использовать, то поток будет грузить проц (Intel i5-4670) до 37-43%
                # В обратном случае использование CPU падает до привычного значения
                time.sleep(0.001)

        except OSError:
            # print('Ошибка чтения. Скорее всего, геймпад отключён.')
            self.update_signal.emit(('stop',))

        self.exec_()

def update_board_viewer(obj, data):

    key = data[0]
    if key == 'offset':
        offset = data[1]
        obj.board_origin -= offset
    elif key == 'scale':
        scroll_value = data[1]
        pivot = obj.rect().center()
        scale_speed = fit(abs(scroll_value), 0.0, 1.0, 350.0, 50.0)
        obj.do_scale_board(-scroll_value, False, False, True, pivot=pivot, scale_speed=scale_speed)
    elif key == 'stop':
        deactivate_listening(obj)

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
            obj.thread_instance = ListenThread(obj.gamepad, gamepad_device)
            obj.thread_instance.update_signal.connect(partial(update_board_viewer, obj))
            obj.thread_instance.start()

            obj.show_center_label('Gamepad control activated!')
        else:
            obj.gamepad = None
            # obj.timer = None
            obj.show_center_label('Gamepad not found!', error=True)

def deactivate_listening(obj):
    obj.gamepad = None
    # obj.timer.stop()
    obj.thread_instance.terminate()
    obj.thread_instance = None
    obj.show_center_label('Gamepad control deactivated!', error=True)

def read_gamepad(gamepad):
    return gamepad.read(64)

def read_sticks_to_obj(obj):
    if obj.gamepad:
        try:
            data = read_gamepad(obj.gamepad)
            if data:
                x_axis, y_axis = read_left_stick(data)
                offset = QPointF(x_axis, y_axis)
                if offset:
                    offset *= 20
                    obj.board_origin -= offset
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

def apply_dead_zone(x_axis, y_axis, dead_zone):
    if abs(x_axis) < dead_zone:
        x_axis = 0.0
    if abs(y_axis) < dead_zone:
        y_axis = 0.0
    return x_axis, y_axis

def read_left_stick(data, start_byte_index=3, dead_zone=0.0):
    x_axis = fit(data[start_byte_index], 0, 256, -1.0, 1.0)
    y_axis = fit(data[start_byte_index+1], 0, 256, -1.0, 1.0)

    if dead_zone != 0.0:
        x_axis, y_axis = apply_dead_zone(x_axis, y_axis, dead_zone)

    return x_axis, y_axis

def read_right_stick(data, start_byte_index=5, dead_zone=0.0):
    x_axis = fit(data[start_byte_index], 0, 256, -1.0, 1.0)
    y_axis = fit(data[start_byte_index+1], 0, 256, -1.0, 1.0)

    if dead_zone != 0.0:
        x_axis, y_axis = apply_dead_zone(x_axis, y_axis, dead_zone)

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


                        triangle_button = 1 << 7
                        circle_button = 1 << 6
                        cross_button = 1 << 5
                        square_button = 1 << 4
                        if data_byte & triangle_button:
                            byte_descr += 't'
                        if data_byte & circle_button:
                            byte_descr += 'c'
                        if data_byte & cross_button:
                            byte_descr += 'x'
                        if data_byte & square_button:
                            byte_descr += 's'

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
            print('Ошибка чтения. Скорее всего, геймпад отключён.')
            pass

if __name__ == '__main__':
    main()

