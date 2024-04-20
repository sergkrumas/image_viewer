
import sys
import os
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *








def preparePluginBoard(self, plugin_info):
    pass






def register(board_obj, plugin_info):
    plugin_info.name = 'BOOKMARKS'
    plugin_info.preparePluginBoard = preparePluginBoard



if __name__ == '__main__':
    subprocess.Popen([sys.executable, "-u", "./../_viewer.pyw", "-board", os.path.basename(__file__)])
    sys.exit()
