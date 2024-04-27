






import hid
import time
import _utils

def find_gamepad():
    gamapad_device = None

    for device in hid.enumerate():
        manufacturer_string = device['manufacturer_string']
        product_string = device['product_string']

        # print(manufacturer_string, product_string)

        if manufacturer_string.startswith('ShanWan') and product_string == 'PC/PS3/Android Gamepad':
            gamapad_device = device

    return gamapad_device

def open_device(device):
    gamepad = hid.device()
    gamepad.open(device['vendor_id'], device['product_id'])
    gamepad.set_nonblocking(True)

    return gamepad

def read_left_stick(data):

    x_axis = _utils.fit(data[3], 0, 256, -1.0, 1.0)
    y_axis = _utils.fit(data[4], 0, 256, -1.0, 1.0)

    return x_axis, y_axis

def main():

    gamapad_device = find_gamepad()

    if gamapad_device:
        gamepad = open_device(gamapad_device)

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

