# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#  Author: Sergei Krumas (github.com/sergkrumas)
#
# ##### END GPL LICENSE BLOCK #####

import os
from win32com.client import Dispatch

REL_PATH = r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'

def create_windows_shortcut(src, dst):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(dst)
    shortcut.Targetpath = src
    # shortcut.WorkingDirectory = os.path.dirname(src)
    # shortcut.IconLocation = src
    shortcut.save()

def get_startup_dir():
    return os.path.expandvars(REL_PATH)

def get_app_link_path(app_id):
    return os.path.join(get_startup_dir(), f'{app_id}.lnk')

def add_to_startup(app_id, filepath):
    create_windows_shortcut(filepath, get_app_link_path(app_id))

def is_app_in_startup(app_id):
    link_path = get_app_link_path(app_id)
    return os.path.exists(link_path)

def remove_from_startup(app_id):
    link_path = get_app_link_path(app_id)
    if os.path.exists(link_path):
        os.remove(link_path)
