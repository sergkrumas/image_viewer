






import hid
import time


def find_gamepad():
    gamapad_device = None

    for device in hid.enumerate():
        manufacturer_string = device['manufacturer_string']
        product_string = device['product_string']

        if manufacturer_string.startswith('ShanWan') and product_string == 'PC/PS3/Android Gamepad':
            gamapad_device = device

    return gamapad_device

def main():

    gamapad_device = find_gamepad()

    if gamapad_device:
        gamepad = hid.device()
        gamepad.open(gamapad_device['vendor_id'], gamapad_device['product_id'])
        gamepad.set_nonblocking(True)

        # a = time.time()
        while True:
            data = gamepad.read(64)
            if data:
                print(data)
                # delta = time.time() - a
                # print(delta)

if __name__ == '__main__':
    main()

