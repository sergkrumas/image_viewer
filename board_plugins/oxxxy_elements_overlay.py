import sys
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *













def register(board_obj, plugin_info):
    plugin_info.name = 'Oxxxy Elements Overlay'
    plugin_info.add_to_menu = False



if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw"])
    sys.exit()
