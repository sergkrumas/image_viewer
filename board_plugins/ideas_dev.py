import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *








def pluginBoardInit(self, plugin_info):
    pass






def register(board_obj, plugin_info):
    plugin_info.name = 'IDEAS DEV'
    plugin_info.pluginBoardInit = pluginBoardInit



if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
