






import hid
import time
from _utils import *

def find_gamepad():
    gamepad_device = None

    for device in hid.enumerate():
        manufacturer_string = device['manufacturer_string']
        product_string = device['product_string']

        # print(manufacturer_string, product_string)

        if manufacturer_string.startswith('ShanWan') and product_string == 'PC/PS3/Android Gamepad':
            gamepad_device = device

    return gamepad_device

def open_device(device):
    gamepad = hid.device()
    gamepad.open(device['vendor_id'], device['product_id'])
    gamepad.set_nonblocking(True)
    return gamepad

def activate_gamepad(obj):
    gamepad_device = find_gamepad()
    if gamepad_device:
        gamepad = open_device(gamepad_device)
    else:
        gamepad = None
    obj.gamepad = gamepad

def deactivate_gamepad(obj):
    obj.gamepad = None

def read_gamepad(gamepad):
    return gamepad.read(64)

def read_left_stick_to_obj(obj):
    try:
        data = read_gamepad(obj.gamepad)
        if data:
            x_axis, y_axis = read_left_stick(data)

            obj.board_origin += QPointF(x_axis, y_axis)

    except OSError:
        # print('Ошибка чтения. Скорее всего, геймпад отключён.')
        deactivate_gamepad(gamepad)


def read_left_stick(data):

    x_axis = fit(data[3], 0, 256, -1.0, 1.0)
    y_axis = fit(data[4], 0, 256, -1.0, 1.0)

    return x_axis, y_axis

def main():

    gamepad_device = find_gamepad()

    if gamepad_device:
        gamepad = open_device(gamepad_device)

        def read_gamepad():
            return gamepad.read(64)

        try:
            # a = time.time()
            while True:
                data = read_gamepad()
                if data:
                    # print(data)
                    x_axis, y_axis = read_left_stick(data)

                    print(f'{x_axis}, {y_axis}')

                    # delta = time.time() - a
                    # print(delta)
        except OSError:
            print('Ошибка чтения. Скорее всего, геймпад отключён.')
            pass

if __name__ == '__main__':
    main()

